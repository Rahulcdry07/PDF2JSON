#!/usr/bin/env python3
"""Extract DSR codes from unstructured input files."""

import re
from typing import Dict, List


def extract_dsr_codes_from_lko(data: dict) -> List[Dict]:
    """Extract DSR codes and details (requires DSR-/year markers)."""
    
    items = []
    processed_codes = set()
    
    # Parse pages for DSR codes
    for page_data in data.get('document', {}).get('pages_data', []):
        blocks = page_data.get('blocks', [])
        
        for block_idx, block in enumerate(blocks):
            lines = block.get('lines', [])
            if not lines:
                continue
            
            # Check for DSR markers or standalone pattern
            has_dsr_marker = any('DSR-' in str(line).upper() or re.search(r'\b(20\d{2})-', str(line)) for line in lines)
            
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
                        # Look for year and code in next lines
                        year = None
                        for j in range(i+1, min(i+3, len(lines))):
                            next_line = str(lines[j]).strip()
                            # Check for year
                            if not year and re.match(r'^20\d{2}$', next_line):
                                year = next_line
                            # Check for code (with or without year prefix)
                            code_match = re.match(r'^(?:(20\d{2})-)?(\d+\.\d+(?:\.\d+)?)$', next_line)
                            if code_match:
                                year = code_match.group(1) or year or '2023'  # fallback to 2023 if no year found
                                clean_code = code_match.group(2)
                                dsr_code = f"DSR-{year}-{clean_code}"
                                break
                        if dsr_code:
                            break
                    
                    # Pattern 3: "15.3" (standalone, lookback for markers)
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
                
                # Only proceed if we found a valid DSR code and haven't processed it
                if dsr_code and clean_code and dsr_code not in processed_codes:
                    # Extract description, unit, quantity from nearby blocks
                    description = ""
                    unit = ""
                    quantity = ""
                    
                    # Search next 5 blocks for data
                    for offset in range(1, min(6, len(blocks) - block_idx)):
                        check_block = blocks[block_idx + offset]
                        check_lines = check_block.get('lines', [])
                        
                        # Get description (meaningful text, not numbers/units)
                        for line in check_lines:
                            line_text = str(line).strip()
                            if (len(line_text) > 15 and  # Long enough to be description
                                not re.match(r'^\d+\.?\d*$', line_text) and  # Not just a number
                                line_text not in ['Nos', 'Cum', 'Sqm', 'Kg', 'Metre', 'Mtr', 'Ltr', 'Each', 'Unit', 'Qty', 'Rate', 'Amount', 'DSR-'] and
                                'DSR' not in line_text.upper() and
                                not re.match(r'^20\d{2}$', line_text)):
                                if not description:  # Take first valid description
                                    description = line_text
                                    break
                        
                        # Get unit and quantity
                        for i, line in enumerate(check_lines):
                            line_text = str(line).strip()
                            if line_text in ['Nos', 'Cum', 'Sqm', 'Kg', 'Metre', 'Mtr', 'Ltr', 'Each']:
                                unit = line_text
                                # Look for quantity nearby (within 3 lines)
                                for j in range(max(0, i-2), min(i+3, len(check_lines))):
                                    qty_text = str(check_lines[j]).strip()
                                    if qty_text != line_text and re.match(r'^\d+\.?\d+$', qty_text):
                                        try:
                                            val = float(qty_text)
                                            if 0.01 <= val <= 100000:  # Reasonable quantity range
                                                quantity = qty_text
                                                break
                                        except:
                                            pass
                                if unit and quantity:
                                    break
                        
                        # Stop searching if we have all data
                        if description and unit and quantity:
                            break
                    
                    # Add item if we have at least code and description
                    if description:
                        items.append({
                            'dsr_code': dsr_code,
                            'clean_dsr_code': clean_code,
                            'description': description,
                            'unit': unit,
                            'quantity': quantity
                        })
                        processed_codes.add(dsr_code)
    
    print(f"✅ Extracted {len(items)} DSR items from input file")
    return items
