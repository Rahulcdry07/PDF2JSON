#!/usr/bin/env python3
"""Convert input files to structured format for reliable DSR extraction."""

import json
import re
from pathlib import Path
from typing import Dict, List
import argparse
import sys


def extract_input_items_structured(data: dict) -> List[Dict]:
    """Extract and structure DSR items from input file."""
    
    items = []
    processed_codes = set()
    item_number = 0
    
    # Parse pages looking for DSR items
    for page_data in data.get('document', {}).get('pages_data', []):
        blocks = page_data.get('blocks', [])
        
        for block_idx, block in enumerate(blocks):
            lines = block.get('lines', [])
            if not lines:
                continue
            
            # Check for DSR markers or standalone code pattern
            has_dsr_marker = any('DSR-' in str(line).upper() or '2023-' in str(line) for line in lines)
            
            has_standalone_code = False
            if not has_dsr_marker and len(lines) <= 3:
                for line in lines:
                    line_str = str(line).strip()
                    if re.match(r'^\d+\.\d+(?:\.\d+)?$', line_str):
                        has_standalone_code = True
                        break
            
            if has_dsr_marker or has_standalone_code:
                dsr_code = None
                clean_code = None
                
                for i, line in enumerate(lines):
                    line_str = str(line).strip()
                    
                    # Pattern 1: "YYYY-15.7.4" (year-code)
                    year_code_match = re.match(r'^(20\d{2})-(\d+\.\d+(?:\.\d+)?)$', line_str)
                    if year_code_match:
                        year = year_code_match.group(1)
                        clean_code = year_code_match.group(2)
                        dsr_code = f"DSR-{year}-{clean_code}"
                        break
                    
                    # Pattern 2: "DSR-" "YYYY-" "15.7.4" (separate lines)
                    if 'DSR-' in line_str.upper():
                        year = None
                        for j in range(i+1, min(i+3, len(lines))):
                            next_line = str(lines[j]).strip()
                            # Check for year
                            if not year and re.match(r'^20\d{2}$', next_line):
                                year = next_line
                            # Check for code (with or without year prefix)
                            code_match = re.match(r'^(?:(20\d{2})-)?(\d+\.\d+(?:\.\d+)?)$', next_line)
                            if code_match:
                                year = code_match.group(1) or year or '2023'
                                clean_code = code_match.group(2)
                                dsr_code = f"DSR-{year}-{clean_code}"
                                break
                        if dsr_code:
                            break
                    
                    # Pattern 3: "15.3" (standalone, lookback for DSR markers)
                    if not dsr_code and re.match(r'^\d+\.\d+(?:\.\d+)?$', line_str):
                        for prev_offset in range(1, min(4, block_idx + 1)):
                            prev_block = blocks[block_idx - prev_offset]
                            prev_lines = prev_block.get('lines', [])
                            prev_text = ' '.join(str(l) for l in prev_lines)
                            # Look for DSR- and any year (20XX)
                            year_match = re.search(r'\b(20\d{2})\b', prev_text)
                            if 'DSR-' in prev_text.upper() and year_match:
                                year = year_match.group(1)
                                clean_code = line_str
                                dsr_code = f"DSR-{year}-{clean_code}"
                                break
                        if dsr_code:
                            break
                
                # Proceed only if valid DSR code found
                if dsr_code and clean_code and dsr_code not in processed_codes:
                    description = ""
                    unit = ""
                    quantity = ""
                    
                    # Search next blocks for description, unit, quantity
                    for offset in range(1, min(6, len(blocks) - block_idx)):
                        check_block = blocks[block_idx + offset]
                        check_lines = check_block.get('lines', [])
                        
                        # Extract description (filter noise)
                        for line in check_lines:
                            line_text = str(line).strip()
                            if (len(line_text) > 15 and
                                not re.match(r'^\d+\.?\d*$', line_text) and
                                line_text not in ['Nos', 'Cum', 'Sqm', 'Kg', 'Metre', 'Mtr', 'Ltr', 'Each', 'Unit', 'Qty', 'Rate', 'Amount', 'DSR-'] and
                                'DSR' not in line_text.upper() and
                                not re.match(r'^20\d{2}$', line_text)):
                                if not description:
                                    description = line_text
                                    break
                        
                        # Extract unit and quantity
                        for i, line in enumerate(check_lines):
                            line_text = str(line).strip()
                            if line_text in ['Nos', 'Cum', 'Sqm', 'Kg', 'Metre', 'Mtr', 'Ltr', 'Each']:
                                unit = line_text
                                # Find nearby quantity value
                                for j in range(max(0, i-2), min(i+3, len(check_lines))):
                                    qty_text = str(check_lines[j]).strip()
                                    if qty_text != line_text and re.match(r'^\d+\.?\d+$', qty_text):
                                        try:
                                            val = float(qty_text)
                                            if 0.01 <= val <= 100000:
                                                quantity = qty_text
                                                break
                                        except:
                                            pass
                                if unit and quantity:
                                    break
                        
                        if description and unit and quantity:
                            break
                    
                    # Add item (requires code and description)
                    if description:
                        item_number += 1
                        
                        # Parse chapter and section
                        parts = clean_code.split('.')
                        chapter = parts[0] if parts else ""
                        section = '.'.join(parts[:2]) if len(parts) >= 2 else clean_code
                        
                        items.append({
                            "item_number": item_number,
                            "code": dsr_code,
                            "clean_code": clean_code,
                            "chapter": chapter,
                            "section": section,
                            "description": description,
                            "unit": unit.lower(),
                            "quantity": float(quantity) if quantity else 0.0,
                            "source": "input_file",
                            "keywords": _extract_keywords(description)
                        })
                        processed_codes.add(dsr_code)
    
    return items


def _extract_keywords(description: str) -> list:
    """Extract searchable keywords from description."""
    import re
    
    # Normalize
    text = description.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Extract words (filter out common words)
    stop_words = {'the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by', 'as', 'is', 'are', 'a', 'an'}
    words = text.split()
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    
    return keywords


def convert_input_to_structured(input_file: Path, output_file: Path = None) -> Path:
    """Convert input JSON to structured format."""
    
    print(f"📂 Loading input file: {input_file.name}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"🔍 Extracting DSR items...")
    items = extract_input_items_structured(data)
    
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_structured.json"
    
    output = {
        "metadata": {
            "source_file": input_file.name,
            "total_items": len(items),
            "format_version": "1.0",
            "type": "input_items"
        },
        "items": items
    }
    
    print(f"💾 Writing structured JSON to {output_file.name}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(items)} DSR items")
    
    if items:
        print(f"\n=== Sample Item ===")
        sample = items[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))
    
    return output_file


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert input files to structured format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Convert input file to structured format
  python3 input_file_converter.py -i Lko_Office_Repair_revise.json
  
  # Specify output file
  python3 input_file_converter.py -i input.json -o input_structured.json
        '''
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Path to input JSON file'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file path (default: <input>_structured.json)'
    )
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()
    
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    output_file = Path(args.output) if args.output else None
    
    try:
        result_file = convert_input_to_structured(input_file, output_file)
        print(f"\n✅ Success! Structured file created: {result_file}")
        print(f"\n💡 Next steps:")
        print(f"   1. Review the structured file: {result_file}")
        print(f"   2. Use it with match_dsr_rates_sqlite.py for better matching")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
