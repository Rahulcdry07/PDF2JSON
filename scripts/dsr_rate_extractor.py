"""
DSR Rate Extractor - handles both Volume I (detailed) and Volume II (simple) formats.
Two-pass strategy: collect descriptions, then extract rates prioritizing 'Say' values.
"""

import re
from typing import Dict, List
from collections import defaultdict


def extract_rates_from_dsr(data: dict, volume_name: str = "Unknown") -> Dict[str, List[Dict]]:
    """Extract DSR codes and rates, handling both Volume I and II formats."""
    rates = defaultdict(list)
    
    pages_data = data.get('document', {}).get('pages_data', [])
    if not pages_data:
        pages_data = data.get('pages', [])
    
    print(f"Extracting rates from {volume_name} using simple format")
    return _extract_rates_simple_format(pages_data, volume_name)


def _detect_simple_format(pages_data: List) -> bool:
    """Detect simple format by checking for code/description/unit/rate pattern."""
    # Check first 20 pages for pattern
    for page in pages_data[:20]:
        for block in page.get('blocks', [])[:10]:
            lines = block.get('lines', [])
            if len(lines) == 4:
                # Check if line 0 is DSR code, line 3 is a rate
                line0 = str(lines[0]).strip()
                line3 = str(lines[3]).strip()
                if re.match(r'^\d+\.\d+(?:\.\d+)?$', line0):
                    try:
                        rate = float(line3.replace(',', ''))
                        if 10 <= rate <= 100000:
                            return True
                    except:
                        pass
    return False


def _extract_rates_simple_format(pages_data: List, volume_name: str) -> Dict[str, List[Dict]]:
    """Extract from simple format: code, description (multi-line), unit, rate."""
    rates = defaultdict(list)
    
    for page_idx, page in enumerate(pages_data):
        blocks = page.get('blocks', [])
        for block in blocks:
            lines = block.get('lines', [])
            
            # Format: 3+ lines (code, description, unit, rate)
            if len(lines) >= 4:
                line0 = str(lines[0]).strip()
                
                # Check if line 0 is a DSR code (not a date or large number)
                if re.match(r'^\d+\.\d+(?:\.\d+)?$', line0) and len(line0) <= 8:
                    dsr_code = line0
                    
                    # Last line should be rate, second-to-last should be unit
                    potential_rate = str(lines[-1]).strip()
                    potential_unit = str(lines[-2]).strip()
                    
                    # Check if unit is valid
                    unit_lower = potential_unit.lower()
                    if unit_lower in ['cum', 'sqm', 'nos', 'each', 'kg', 'mtr', 'ltr', 'metre', 'quintal', 'sq.m', 'cu.m']:
                        unit = unit_lower.replace('.', '')
                        
                        # Description is everything between code and unit
                        desc_lines = lines[1:-2]
                        description = ' '.join(str(l).strip() for l in desc_lines)
                        
                        # Try to parse rate
                        try:
                            rate = float(potential_rate.replace(',', ''))
                            if 10 <= rate <= 1000000:
                                entry = {
                                    'description': description,
                                    'unit': unit,
                                    'rate': rate,
                                    'volume': volume_name,
                                    'page': page_idx + 1,
                                    'source': 'simple_format'
                                }
                                rates[dsr_code].append(entry)
                                print(f"Found DSR {dsr_code} (Vol: {volume_name}): {description[:70]}... Rate: ₹{rate}")
                        except ValueError:
                            pass
    
    return dict(rates)


def _extract_rates_detailed_format(pages_data: List, volume_name: str) -> Dict[str, List[Dict]]:
    """Extract rates from detailed format with Say values (Volume I style)."""
    rates = defaultdict(list)  # Use list to store multiple entries per code
    
    # FIRST PASS: Collect all DSR codes with their immediate descriptions (including parents)
    dsr_descriptions_map = {}
    
    for page_idx, page in enumerate(pages_data):
        blocks = page.get('blocks', [])
        for block_idx, block in enumerate(blocks):
            lines = block.get('lines', [])
            
            # Check each line for DSR codes
            for line_idx, line in enumerate(lines):
                line_text = line.strip() if isinstance(line, str) else line.get('text', '').strip()
                
                # Look for DSR code patterns - more flexible matching
                # Match codes like: 13.5.1, 13.80, 15.7.4, etc.
                code_match = re.match(r'^(\d+\.\d+(?:\.\d+)?)(?:\s|$)', line_text)
                if code_match:
                    dsr_code = code_match.group(1)
                    
                    # Extract immediate description for this code
                    desc_lines = []
                    
                    # First, check if description is on the same line after the code
                    remaining_text = line_text[len(dsr_code):].strip()
                    if len(remaining_text) > 10 and not re.match(r'^[\d\s,.₹`%]+$', remaining_text):
                        desc_lines.append(remaining_text)
                    
                    # Then look in subsequent lines
                    for search_idx in range(line_idx + 1, min(line_idx + 25, len(lines))):
                        search_line = lines[search_idx]
                        search_text = search_line.strip() if isinstance(search_line, str) else search_line.get('text', '').strip()
                        
                        # Skip headers and unit lines
                        if search_text.lower() in ['code', 'description', 'unit', 'rate', 'amount', 'details', 'cum', 'sqm', 'nos', 'each', 'kg', 'mtr', 'ltr', 'metre', 'quintal']:
                            continue
                        
                        # Stop at calculation sections or next DSR code
                        if any(kw in search_text.lower() for kw in ['add ', 'total', 'cost for', 'say', 'material', 'labour', 'details of cost']):
                            break
                        
                        # Stop if we hit another DSR code
                        if re.match(r'^\d+\.\d+(?:\.\d+)?(?:\s|$)', search_text):
                            break
                        
                        # Skip pure numbers or very short lines
                        if re.match(r'^[\d\s,.₹`%]+$', search_text) or len(search_text) < 3:
                            continue
                        
                        # Add meaningful description lines
                        if len(search_text) > 5:
                            desc_lines.append(search_text)
                            if len(desc_lines) >= 6:
                                break
                    
                    if desc_lines:
                        combined_desc = ' '.join(desc_lines)
                        # Store both with and without trailing dots for flexibility
                        dsr_descriptions_map[dsr_code] = combined_desc
                        # Also store without trailing zeros (e.g., 13.5.1 and 13.5.10)
                        if not dsr_code in dsr_descriptions_map:
                            dsr_descriptions_map[dsr_code] = combined_desc
    
    print(f"Collected {len(dsr_descriptions_map)} DSR descriptions from {volume_name}")
    
    # Print sample descriptions for debugging
    print(f"\n=== Sample DSR Descriptions from {volume_name} ===")
    sample_codes = sorted(dsr_descriptions_map.keys(), key=lambda x: [int(p) if p.isdigit() else p for p in x.split('.')])[:20]
    for code in sample_codes:
        desc = dsr_descriptions_map[code]
        print(f"{code}: {desc[:100]}{'...' if len(desc) > 100 else ''}")
    print()
    
    # SECOND PASS: Parse blocks to find DSR codes with rates, building complete descriptions
    for page_idx, page in enumerate(pages_data):
        blocks = page.get('blocks', [])
        for block_idx, block in enumerate(blocks):
            lines = block.get('lines', [])
            text = block.get('text', '')
            
            for line_idx, line in enumerate(lines):
                line_text = line.strip() if isinstance(line, str) else line.get('text', '').strip()
                
                # Look for DSR code patterns - more flexible
                code_match = re.match(r'^(\d+\.\d+(?:\.\d+)?)(?:\s|$)', line_text)
                if code_match:
                    dsr_code = code_match.group(1)
                    
                    # BUILD COMPLETE DESCRIPTION with parent context
                    description_parts = []
                    
                    # For sub-codes (e.g., 8.3.2), try to get parent description (8.3)
                    parts = dsr_code.split('.')
                    if len(parts) == 3:  # Sub-sub-code like 8.3.2
                        parent_code = f"{parts[0]}.{parts[1]}"  # Get 8.3
                        if parent_code in dsr_descriptions_map:
                            parent_desc = dsr_descriptions_map[parent_code]
                            # Add parent if it's not too short
                            if len(parent_desc) > 15:
                                description_parts.append(parent_desc)
                    elif len(parts) == 2:  # Sub-code like 8.3
                        parent_code = parts[0]  # Get 8
                        if parent_code in dsr_descriptions_map:
                            parent_desc = dsr_descriptions_map[parent_code]
                            if len(parent_desc) > 15:
                                description_parts.append(parent_desc)
                    
                    # Add current code's description
                    if dsr_code in dsr_descriptions_map:
                        description_parts.append(dsr_descriptions_map[dsr_code])
                    
                    # Combine descriptions
                    if description_parts:
                        description = ' '.join(description_parts)
                    else:
                        description = f"DSR item {dsr_code}"
                    
                    # Extract rate and unit
                    rate = None
                    unit = ""
                    rate_found = False
                    say_rate = None
                    
                    # Look for unit first
                    for search_idx in range(line_idx + 1, min(line_idx + 20, len(lines))):
                        search_line = lines[search_idx]
                        search_text = search_line.strip() if isinstance(search_line, str) else search_line.get('text', '').strip()
                        
                        # Look for unit
                        if not unit and search_text.lower() in ['cum', 'sqm', 'nos', 'each', 'kg', 'mtr', 'ltr', 'cu.m', 'sq.m', 'metre', 'quintal', 'sqm.', 'cum.']:
                            unit = search_text.lower().rstrip('.')
                    
                    # PRIORITY 1: Look for "Say" value first (most accurate final rate)
                    # Check current block for "Say" pattern
                    for search_idx in range(line_idx + 1, len(lines)):
                        search_line = lines[search_idx]
                        search_text = search_line.strip() if isinstance(search_line, str) else search_line.get('text', '').strip()
                        
                        # Look for "Say" followed by a rate value
                        if search_text.lower() == 'say':
                            # Check the next few lines for the numeric value
                            for rate_idx in range(search_idx + 1, min(search_idx + 6, len(lines))):
                                next_line = lines[rate_idx]
                                next_text = next_line.strip() if isinstance(next_line, str) else next_line.get('text', '').strip()
                                if next_text and re.match(r'^\d+\.?\d*$', next_text):
                                    try:
                                        val = float(next_text)
                                        if 10 <= val <= 1000000:
                                            say_rate = val
                                            rate_found = True
                                            break
                                    except ValueError:
                                        pass
                            if rate_found:
                                rate = say_rate
                                break
                    
                    # If "Say" not found in current block, check next blocks
                    if not rate_found:
                        blocks_to_check = []
                        
                        # Add next block on same page if exists
                        if block_idx + 1 < len(blocks):
                            blocks_to_check.append(blocks[block_idx + 1])
                        
                        # Add first few blocks on next page if exists
                        if page_idx + 1 < len(pages_data):
                            next_page = pages_data[page_idx + 1]
                            next_page_blocks = next_page.get('blocks', [])
                            blocks_to_check.extend(next_page_blocks[:3])
                        
                        # Search through collected blocks
                        for check_block in blocks_to_check:
                            if rate_found:
                                break
                                
                            check_lines = check_block.get('lines', [])
                            
                            for search_idx, search_line in enumerate(check_lines):
                                search_text = search_line.strip() if isinstance(search_line, str) else search_line.get('text', '').strip()
                                
                                # Look for "Say" followed by a rate value
                                if search_text.lower() == 'say':
                                    for rate_idx in range(search_idx + 1, min(search_idx + 6, len(check_lines))):
                                        next_line = check_lines[rate_idx]
                                        next_text = next_line.strip() if isinstance(next_line, str) else next_line.get('text', '').strip()
                                        if next_text and re.match(r'^\d+\.?\d*$', next_text):
                                            try:
                                                val = float(next_text)
                                                if 10 <= val <= 1000000:
                                                    rate = val
                                                    rate_found = True
                                                    break
                                            except ValueError:
                                                pass
                                    if rate_found:
                                        break
                                
                                # Also look for "Cost per" pattern
                                if 'cost per' in search_text.lower():
                                    for rate_idx in range(search_idx + 1, min(search_idx + 4, len(check_lines))):
                                        next_line = check_lines[rate_idx]
                                        next_text = next_line.strip() if isinstance(next_line, str) else next_line.get('text', '').strip()
                                        if next_text and re.match(r'^\d+\.?\d*$', next_text):
                                            try:
                                                val = float(next_text)
                                                if 10 <= val <= 1000000:
                                                    rate = val
                                                    rate_found = True
                                                    break
                                            except ValueError:
                                                    pass
                                        if rate_found:
                                            break
                        
                        # Also check the text field for "Say" pattern if not found in lines
                        if not rate_found:
                            text = block.get('text', '')
                            # Look for "Say" followed by optional whitespace/newlines and a rate
                            say_match = re.search(r'Say\s*\n\s*\n*\s*([0-9,]+\.?\d*)', text)
                            if say_match:
                                try:
                                    val = float(say_match.group(1).replace(',', ''))
                                    if 50 <= val <= 100000:
                                        rate = val
                                        rate_found = True
                                except ValueError:
                                    pass
                    
                    # If we found a rate, save this DSR entry with complete description
                    if rate:
                        entry = {
                            'description': description,
                            'unit': unit,
                            'rate': rate,
                            'volume': volume_name,
                            'page': page_idx + 1,
                            'source': 'enhanced_with_parent'
                        }
                        rates[dsr_code].append(entry)
                        print(f"Found DSR {dsr_code} (Vol: {volume_name}): {description[:70]}... Rate: ₹{rate}")
    
    return dict(rates)
