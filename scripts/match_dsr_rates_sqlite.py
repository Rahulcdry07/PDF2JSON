#!/usr/bin/env python3
"""
DSR Matcher with SQLite backend.
Supports structured (recommended) and unstructured input formats.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict
from text_similarity import calculate_text_similarity


def load_input_file(input_file: Path) -> List[Dict]:
    """Load and extract DSR items from structured or unstructured format."""
    print(f"📂 Loading input file: {input_file.name}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Detect format by metadata
    if 'metadata' in data and data.get('metadata', {}).get('type') == 'input_items':
        print(f"✅ Detected structured input format")
        items = data.get('items', [])
        
        # Map to matching format
        mapped_items = []
        for item in items:
            mapped_items.append({
                'dsr_code': item.get('code', ''),
                'clean_dsr_code': item.get('clean_code', ''),
                'description': item.get('description', ''),
                'quantity': item.get('quantity', 0),
                'unit': item.get('unit', ''),
                'chapter': item.get('chapter', ''),
                'section': item.get('section', '')
            })
        
        print(f"📊 Loaded {len(mapped_items)} items from structured format")
        return mapped_items
    else:
        # Fall back to extraction
        print(f"⚠️  Detected unstructured input format (using extractor)")
        print(f"💡 TIP: Convert to structured format for better accuracy:")
        print(f"    python3 input_file_converter.py -i {input_file.name}\n")
        
        from dsr_extractor import extract_dsr_codes_from_lko
        items = extract_dsr_codes_from_lko(data)
        print(f"📊 Extracted {len(items)} items from unstructured format")
        return items


def load_dsr_database(db_path: Path) -> sqlite3.Connection:
    """Load SQLite DSR database and return connection."""
    if not db_path.exists():
        raise FileNotFoundError(f"DSR database not found: {db_path}\nRun create_alternative_formats.py first.")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def match_with_database(lko_items: List[Dict], db_conn: sqlite3.Connection, similarity_threshold: float = 0.3) -> List[Dict]:
    """Match items using SQLite database for fast lookups."""
    cursor = db_conn.cursor()
    matched_items = []
    
    for item in lko_items:
        clean_code = item.get('clean_dsr_code', item['dsr_code'])
        
        # Direct database lookup - get all matching codes (may have duplicates from different volumes)
        cursor.execute("""
            SELECT code, description, unit, rate, volume, page
            FROM dsr_codes 
            WHERE code = ?
            ORDER BY 
                CASE 
                    WHEN volume LIKE '%II%' OR volume LIKE '%2%' THEN 1  -- Prefer later volumes (simpler data)
                    ELSE 2 
                END,
                rate ASC  -- Prefer lower rates
        """, (clean_code,))
        
        results = cursor.fetchall()
        result = results[0] if results else None
        
        if result:
            # Calculate similarity
            similarity = calculate_text_similarity(item['description'], result['description'])
            
            # Show if multiple entries exist
            duplicate_info = f" ({len(results)} entries)" if len(results) > 1 else ""
            
            print(f"  DSR {clean_code} - Database match{duplicate_info}, similarity: {similarity:.3f}")
            print(f"    Input: {item['description'][:60]}...")
            print(f"    Match: {result['description'][:60]}... (Vol: {result['volume']}, Rate: ₹{result['rate']})")
            
            if similarity >= similarity_threshold:
                # Good match
                item['rate'] = result['rate']
                item['dsr_description'] = result['description']
                item['dsr_unit'] = result['unit']
                item['dsr_volume'] = result['volume']
                item['dsr_page'] = result['page']
                item['match_type'] = 'exact_with_description_match'
                item['similarity_score'] = similarity
            else:
                # Code found but low similarity
                print(f"  ⚠️  DSR {clean_code} found but similarity {similarity:.3f} below threshold")
                item['rate'] = result['rate']
                item['dsr_description'] = result['description']
                item['dsr_unit'] = result['unit']
                item['dsr_volume'] = result['volume']
                item['dsr_page'] = result['page']
                item['match_type'] = 'code_match_but_description_mismatch'
                item['similarity_score'] = similarity
        else:
            # Code not found
            item['rate'] = None
            item['dsr_description'] = "DSR code not found in reference files"
            item['dsr_unit'] = ""
            item['dsr_volume'] = ""
            item['match_type'] = 'not_found'
            item['similarity_score'] = 0.0
        
        # Calculate amount
        if item.get('quantity') and item.get('rate'):
            try:
                qty = float(item['quantity'])
                rate = float(item['rate'])
                item['amount'] = qty * rate
            except (ValueError, TypeError):
                item['amount'] = None
        
        matched_items.append(item)
    
    return matched_items


def main(input_file: Path = None, db_path: Path = None, output_dir: Path = None, similarity_threshold: float = 0.3):
    """Main function to match DSR codes with database rates."""
    # Use defaults if not provided
    if input_file is None:
        base_dir = Path(__file__).parent.parent / 'examples'
        input_file = base_dir / 'input_files' / 'Lko_Office_Repair_revise.json'
    
    if db_path is None:
        base_dir = Path(__file__).parent.parent / 'examples'
        db_path = base_dir / 'reference_files' / 'DSR_combined.db'
    
    if output_dir is None:
        base_dir = Path(__file__).parent.parent / 'examples'
        output_dir = base_dir / 'output_reports'
    
    # Check if database exists
    if not db_path.exists():
        print("⚠️  DSR database not found. Creating it now...")
        print("This is a one-time setup.\n")
        import subprocess
        subprocess.run(['python3', 'create_alternative_formats.py'], cwd=Path(__file__).parent)
        print()
    
    # Load input file (structured or unstructured)
    lko_items = load_input_file(input_file)
    
    if not lko_items:
        print("❌ No DSR items found in input file")
        return
    
    # Connect to database
    print("\n🔗 Connecting to DSR database...")
    db_conn = load_dsr_database(db_path)
    
    # Get database statistics
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dsr_codes")
    total_codes = cursor.fetchone()[0]
    print(f"📊 Database loaded: {total_codes:,} DSR codes available\n")
    
    # Match items using database
    print("Matching items with DSR database...")
    matched_items = match_with_database(lko_items, db_conn, similarity_threshold=similarity_threshold)
    
    db_conn.close()
    
    # Create output
    output = {
        'project': f'DSR Rate Matching from {input_file.name}',
        'source_files': {
            'items': str(input_file),
            'rates_database': str(db_path)
        },
        'summary': {
            'total_items': len(matched_items),
            'exact_matches': len([i for i in matched_items if i.get('match_type') == 'exact_with_description_match']),
            'code_match_description_mismatch': len([i for i in matched_items if i.get('match_type') == 'code_match_but_description_mismatch']),
            'not_found': len([i for i in matched_items if i.get('match_type') == 'not_found']),
            'total_estimated_amount': sum([i['amount'] for i in matched_items if i.get('amount')])
        },
        'matched_items': matched_items
    }
    
    # Save output
    output_file = output_dir / f'{input_file.stem}_matched_rates.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n=== MATCHING SUMMARY ===")
    print(f"Total items: {output['summary']['total_items']}")
    print(f"Exact matches (code + description): {output['summary']['exact_matches']}")
    print(f"Code matched but description mismatch: {output['summary']['code_match_description_mismatch']}")
    print(f"Not found: {output['summary']['not_found']}")
    if output['summary']['total_estimated_amount']:
        print(f"Total estimated amount: ₹{output['summary']['total_estimated_amount']:,.2f}")
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Show sample matched items
    print(f"\n=== SAMPLE MATCHED ITEMS ===")
    for item in matched_items[:5]:
        print(f"DSR Code: {item['dsr_code']}")
        print(f"Description: {item['description'][:70]}...")
        print(f"Quantity: {item.get('quantity', 'N/A')} {item.get('unit', '')}")
        print(f"Rate: ₹{item['rate']}" if item['rate'] else "Rate: Not found")
        print(f"Amount: ₹{item['amount']:,.2f}" if item.get('amount') else "Amount: N/A")
        print(f"Match: {item['match_type']} (similarity: {item.get('similarity_score', 0):.2f})")
        print("-" * 70)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Match DSR codes from input file with rates from SQLite database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Use default files
  python3 match_dsr_rates_sqlite.py
  
  # Specify custom input and database
  python3 match_dsr_rates_sqlite.py -i input.json -d dsr_database.db
  
  # Specify output directory
  python3 match_dsr_rates_sqlite.py -i input.json -o ./results
        '''
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='../examples/input_files/Lko_Office_Repair_revise.json',
        help='Path to input JSON file with DSR items (default: ../examples/input_files/Lko_Office_Repair_revise.json)'
    )
    
    parser.add_argument(
        '-d', '--database',
        type=str,
        default='../examples/reference_files/DSR_combined.db',
        help='Path to SQLite DSR database (default: ../examples/reference_files/DSR_combined.db)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='../examples/output_reports',
        help='Output directory for results (default: ../examples/output_reports)'
    )
    
    parser.add_argument(
        '-t', '--threshold',
        type=float,
        default=0.3,
        help='Similarity threshold for matching (default: 0.3)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Convert paths to Path objects
    input_file = Path(args.input)
    db_path = Path(args.database)
    output_dir = Path(args.output)
    
    # Validate input files exist
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"Error: Database file not found: {db_path}")
        print(f"Please run: python3 create_alternative_formats.py")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Override the main function's hardcoded paths by passing parameters
    # Update main() to accept parameters
    print(f"Input file: {input_file}")
    print(f"Database: {db_path}")
    print(f"Output directory: {output_dir}")
    print(f"Similarity threshold: {args.threshold}\n")
    
    main(input_file, db_path, output_dir, args.threshold)
