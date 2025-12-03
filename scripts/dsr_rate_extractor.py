"""
DSR Rate Extractor - handles both Volume I (detailed) and Volume II (simple) formats.
Two-pass strategy: collect descriptions, then extract rates prioritizing 'Say' values.
"""

import re
from typing import Dict, List, Optional
from collections import defaultdict


def extract_rates_from_dsr(data: dict, volume_name: str = "Unknown") -> Dict[str, List[Dict]]:
    """Extract DSR codes and rates, handling both Volume I and II formats."""
    rates = defaultdict(list)

    pages_data = data.get("document", {}).get("pages_data", [])
    if not pages_data:
        pages_data = data.get("pages", [])

    print(f"Extracting rates from {volume_name} using simple format")
    return _extract_rates_simple_format(pages_data, volume_name)


def _check_block_for_simple_format(block: Dict) -> bool:
    """Check if a block matches simple format pattern.

    Args:
        block: Block dictionary with lines

    Returns:
        True if block matches simple format
    """
    lines = block.get("lines", [])
    if len(lines) != 4:
        return False

    # Check if line 0 is DSR code, line 3 is a rate
    line0 = str(lines[0]).strip()
    line3 = str(lines[3]).strip()

    if not re.match(r"^\d+\.\d+(?:\.\d+)?$", line0):
        return False

    try:
        rate = float(line3.replace(",", ""))
        return 10 <= rate <= 100000
    except Exception:
        return False


def _detect_simple_format(pages_data: List) -> bool:
    """Detect simple format by checking for code/description/unit/rate pattern."""
    # Check first 20 pages for pattern
    for page in pages_data[:20]:
        for block in page.get("blocks", [])[:10]:
            if _check_block_for_simple_format(block):
                return True
    return False


def _is_valid_dsr_code(line: str) -> bool:
    """Check if line contains a valid DSR code."""
    line_text = line.strip()
    return bool(re.match(r"^\d+\.\d+(?:\.\d+)?$", line_text) and len(line_text) <= 8)


def _is_valid_unit(unit_text: str) -> bool:
    """Check if text is a valid unit."""
    unit_lower = unit_text.lower()
    return unit_lower in [
        "cum",
        "sqm",
        "nos",
        "each",
        "kg",
        "mtr",
        "ltr",
        "metre",
        "quintal",
        "sq.m",
        "cu.m",
    ]


def _parse_rate_value(rate_text: str) -> Optional[float]:
    """Parse and validate rate value.

    Args:
        rate_text: Text containing rate value

    Returns:
        Rate as float or None if invalid
    """
    try:
        rate = float(rate_text.replace(",", ""))
        if 10 <= rate <= 1000000:
            return rate
    except ValueError:
        pass
    return None


def _extract_rates_simple_format(pages_data: List, volume_name: str) -> Dict[str, List[Dict]]:
    """Extract from simple format: code, description (multi-line), unit, rate."""
    rates = defaultdict(list)

    for page_idx, page in enumerate(pages_data):
        blocks = page.get("blocks", [])
        for block in blocks:
            lines = block.get("lines", [])

            # Format: 3+ lines (code, description, unit, rate)
            if len(lines) < 4:
                continue

            # Check if line 0 is a DSR code
            line0 = str(lines[0]).strip()
            if not _is_valid_dsr_code(line0):
                continue

            dsr_code = line0

            # Last line should be rate, second-to-last should be unit
            potential_rate = str(lines[-1]).strip()
            potential_unit = str(lines[-2]).strip()

            # Check if unit is valid
            if not _is_valid_unit(potential_unit):
                continue

            unit = potential_unit.lower().replace(".", "")

            # Description is everything between code and unit
            desc_lines = lines[1:-2]
            description = " ".join(str(l).strip() for l in desc_lines)

            # Try to parse rate
            rate = _parse_rate_value(potential_rate)
            if rate:
                entry = {
                    "description": description,
                    "unit": unit,
                    "rate": rate,
                    "volume": volume_name,
                    "page": page_idx + 1,
                    "source": "simple_format",
                }
                rates[dsr_code].append(entry)
                print(
                    f"Found DSR {dsr_code} (Vol: {volume_name}): "
                    f"{description[:70]}... Rate: ₹{rate}"
                )

    return dict(rates)


def _should_skip_line(search_text: str) -> bool:
    """Check if line should be skipped in description extraction."""
    # Skip headers and unit lines
    if search_text.lower() in [
        "code",
        "description",
        "unit",
        "rate",
        "amount",
        "details",
        "cum",
        "sqm",
        "nos",
        "each",
        "kg",
        "mtr",
        "ltr",
        "metre",
        "quintal",
    ]:
        return True

    # Skip pure numbers or very short lines
    if re.match(r"^[\d\s,.₹`%]+$", search_text) or len(search_text) < 3:
        return True

    return False


def _should_stop_extraction(search_text: str) -> bool:
    """Check if we should stop description extraction at this line."""
    # Stop at calculation sections
    if any(
        kw in search_text.lower()
        for kw in [
            "add ",
            "total",
            "cost for",
            "say",
            "material",
            "labour",
            "details of cost",
        ]
    ):
        return True

    # Stop if we hit another DSR code
    if re.match(r"^\d+\.\d+(?:\.\d+)?(?:\s|$)", search_text):
        return True

    return False


def _extract_description_lines(
    lines: List, line_idx: int, line_text: str, dsr_code: str
) -> List[str]:
    """Extract description lines for a DSR code.

    Args:
        lines: All lines in the block
        line_idx: Index of the DSR code line
        line_text: Text of the DSR code line
        dsr_code: The DSR code found

    Returns:
        List of description text lines
    """
    desc_lines = []

    # Check if description is on the same line after the code
    remaining_text = line_text[len(dsr_code) :].strip()
    if len(remaining_text) > 10 and not re.match(r"^[\d\s,.₹`%]+$", remaining_text):
        desc_lines.append(remaining_text)

    # Look in subsequent lines
    for search_idx in range(line_idx + 1, min(line_idx + 25, len(lines))):
        search_line = lines[search_idx]
        search_text = (
            search_line.strip()
            if isinstance(search_line, str)
            else search_line.get("text", "").strip()
        )

        # Check if should stop extraction
        if _should_stop_extraction(search_text):
            break

        # Skip non-description lines
        if _should_skip_line(search_text):
            continue

        # Add meaningful description lines
        if len(search_text) > 5:
            desc_lines.append(search_text)
            if len(desc_lines) >= 6:
                break

    return desc_lines


def _build_complete_description(dsr_code: str, dsr_descriptions_map: Dict[str, str]) -> str:
    """Build complete description with parent context.

    Args:
        dsr_code: The DSR code
        dsr_descriptions_map: Map of DSR codes to descriptions

    Returns:
        Complete description string
    """
    description_parts = []

    # For sub-codes (e.g., 8.3.2), try to get parent description (8.3)
    parts = dsr_code.split(".")
    if len(parts) == 3:  # Sub-sub-code like 8.3.2
        parent_code = f"{parts[0]}.{parts[1]}"  # Get 8.3
        if parent_code in dsr_descriptions_map:
            parent_desc = dsr_descriptions_map[parent_code]
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
        return " ".join(description_parts)
    else:
        return f"DSR item {dsr_code}"


def _extract_unit_from_lines(lines: List, line_idx: int) -> str:
    """Extract unit from lines following the DSR code.

    Args:
        lines: All lines in the block
        line_idx: Index to start searching from

    Returns:
        Unit string (empty if not found)
    """
    unit = ""
    for search_idx in range(line_idx + 1, min(line_idx + 20, len(lines))):
        search_line = lines[search_idx]
        search_text = (
            search_line.strip()
            if isinstance(search_line, str)
            else search_line.get("text", "").strip()
        )

        if search_text.lower() in [
            "cum",
            "sqm",
            "nos",
            "each",
            "kg",
            "mtr",
            "ltr",
            "cu.m",
            "sq.m",
            "metre",
            "quintal",
            "sqm.",
            "cum.",
        ]:
            unit = search_text.lower().rstrip(".")
            break

    return unit


def _try_parse_rate_from_text(next_text: str) -> Optional[float]:
    """Try to parse rate value from text.

    Args:
        next_text: Text to parse

    Returns:
        Rate value or None
    """
    if not next_text or not re.match(r"^\d+\.?\d*$", next_text):
        return None

    try:
        val = float(next_text)
        if 10 <= val <= 1000000:
            return val
    except ValueError:
        pass
    return None


def _find_say_rate_in_lines(lines: List, start_idx: int) -> Optional[float]:
    """Find 'Say' rate value in lines.

    Args:
        lines: Lines to search
        start_idx: Starting index

    Returns:
        Rate value or None
    """
    for search_idx in range(start_idx, len(lines)):
        search_line = lines[search_idx]
        search_text = (
            search_line.strip()
            if isinstance(search_line, str)
            else search_line.get("text", "").strip()
        )

        if search_text.lower() != "say":
            continue

        # Check the next few lines for the numeric value
        for rate_idx in range(search_idx + 1, min(search_idx + 6, len(lines))):
            next_line = lines[rate_idx]
            next_text = (
                next_line.strip()
                if isinstance(next_line, str)
                else next_line.get("text", "").strip()
            )
            rate = _try_parse_rate_from_text(next_text)
            if rate:
                return rate
    return None


def _find_cost_per_rate_in_lines(lines: List, search_idx: int) -> Optional[float]:
    """Find 'cost per' rate value in lines.

    Args:
        lines: Lines to search
        search_idx: Current index

    Returns:
        Rate value or None
    """
    for rate_idx in range(search_idx + 1, min(search_idx + 4, len(lines))):
        next_line = lines[rate_idx]
        next_text = (
            next_line.strip() if isinstance(next_line, str) else next_line.get("text", "").strip()
        )
        rate = _try_parse_rate_from_text(next_text)
        if rate:
            return rate
    return None


def _search_blocks_for_rate(blocks_to_check: List[Dict]) -> Optional[float]:
    """Search through multiple blocks for 'Say' or 'cost per' rate.

    Args:
        blocks_to_check: List of blocks to search

    Returns:
        Rate value or None
    """
    for check_block in blocks_to_check:
        check_lines = check_block.get("lines", [])

        for search_idx, search_line in enumerate(check_lines):
            search_text = (
                search_line.strip()
                if isinstance(search_line, str)
                else search_line.get("text", "").strip()
            )

            # Look for "Say" pattern
            if search_text.lower() == "say":
                rate = _find_say_rate_in_lines(check_lines, search_idx)
                if rate:
                    return rate

            # Look for "cost per" pattern
            if "cost per" in search_text.lower():
                rate = _find_cost_per_rate_in_lines(check_lines, search_idx)
                if rate:
                    return rate

    return None


def _extract_rate_from_block(
    lines: List,
    line_idx: int,
    block: Dict,
    blocks: List[Dict],
    block_idx: int,
    pages_data: List,
    page_idx: int,
) -> Optional[float]:
    """Extract rate value prioritizing 'Say' values.

    Args:
        lines: Lines in current block
        line_idx: Index of DSR code line
        block: Current block dict
        blocks: All blocks on current page
        block_idx: Index of current block
        pages_data: All pages data
        page_idx: Current page index

    Returns:
        Rate value or None
    """
    # PRIORITY 1: Look for "Say" value in current block
    rate = _find_say_rate_in_lines(lines, line_idx + 1)
    if rate:
        return rate

    # PRIORITY 2: Check next blocks
    blocks_to_check = []

    # Add next block on same page if exists
    if block_idx + 1 < len(blocks):
        blocks_to_check.append(blocks[block_idx + 1])

    # Add first few blocks on next page if exists
    if page_idx + 1 < len(pages_data):
        next_page = pages_data[page_idx + 1]
        next_page_blocks = next_page.get("blocks", [])
        blocks_to_check.extend(next_page_blocks[:3])

    rate = _search_blocks_for_rate(blocks_to_check)
    if rate:
        return rate

    # PRIORITY 3: Check the text field for "Say" pattern
    text = block.get("text", "")
    say_match = re.search(r"Say\s*\n\s*\n*\s*([0-9,]+\.?\d*)", text)
    if say_match:
        try:
            val = float(say_match.group(1).replace(",", ""))
            if 50 <= val <= 100000:
                return val
        except ValueError:
            pass

    return None


def _collect_dsr_descriptions(pages_data: List, volume_name: str) -> Dict[str, str]:
    """First pass: Collect all DSR codes with their descriptions.

    Args:
        pages_data: All pages data
        volume_name: Volume identifier

    Returns:
        Dictionary mapping DSR codes to descriptions
    """
    dsr_descriptions_map = {}

    for page in pages_data:
        blocks = page.get("blocks", [])
        for block in blocks:
            lines = block.get("lines", [])

            for line_idx, line in enumerate(lines):
                line_text = line.strip() if isinstance(line, str) else line.get("text", "").strip()

                # Look for DSR code patterns
                code_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)(?:\s|$)", line_text)
                if code_match:
                    dsr_code = code_match.group(1)
                    desc_lines = _extract_description_lines(lines, line_idx, line_text, dsr_code)

                    if desc_lines:
                        combined_desc = " ".join(desc_lines)
                        dsr_descriptions_map[dsr_code] = combined_desc

    print(f"Collected {len(dsr_descriptions_map)} DSR descriptions from {volume_name}")

    # Print sample descriptions
    print(f"\n=== Sample DSR Descriptions from {volume_name} ===")
    sample_codes = sorted(
        dsr_descriptions_map.keys(),
        key=lambda x: [int(p) if p.isdigit() else p for p in x.split(".")],
    )[:20]
    for code in sample_codes:
        desc = dsr_descriptions_map[code]
        print(f"{code}: {desc[:100]}{'...' if len(desc) > 100 else ''}")
    print()

    return dsr_descriptions_map


def _extract_rates_detailed_format(pages_data: List, volume_name: str) -> Dict[str, List[Dict]]:
    """Extract rates from detailed format with Say values (Volume I style)."""
    rates = defaultdict(list)

    # FIRST PASS: Collect all DSR descriptions
    dsr_descriptions_map = _collect_dsr_descriptions(pages_data, volume_name)

    # SECOND PASS: Parse blocks to find DSR codes with rates
    for page_idx, page in enumerate(pages_data):
        blocks = page.get("blocks", [])
        for block_idx, block in enumerate(blocks):
            lines = block.get("lines", [])

            for line_idx, line in enumerate(lines):
                line_text = line.strip() if isinstance(line, str) else line.get("text", "").strip()

                # Look for DSR code patterns
                code_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)(?:\s|$)", line_text)
                if code_match:
                    dsr_code = code_match.group(1)

                    # Build complete description with parent context
                    description = _build_complete_description(dsr_code, dsr_descriptions_map)

                    # Extract unit
                    unit = _extract_unit_from_lines(lines, line_idx)

                    # Extract rate
                    rate = _extract_rate_from_block(
                        lines, line_idx, block, blocks, block_idx, pages_data, page_idx
                    )

                    # If we found a rate, save this DSR entry
                    if rate:
                        entry = {
                            "description": description,
                            "unit": unit,
                            "rate": rate,
                            "volume": volume_name,
                            "page": page_idx + 1,
                            "source": "enhanced_with_parent",
                        }
                        rates[dsr_code].append(entry)
                        print(
                            f"Found DSR {dsr_code} (Vol: {volume_name}): "
                            f"{description[:70]}... Rate: ₹{rate}"
                        )

    return dict(rates)
