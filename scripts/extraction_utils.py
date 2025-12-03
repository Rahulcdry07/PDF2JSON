"""Shared utilities for DSR code and text extraction.

This module contains common extraction logic used across multiple scripts
to avoid code duplication.
"""

import re
from typing import Dict, List, Tuple, Optional, Callable


def extract_keywords_from_description(description: str) -> List[str]:
    """Extract keywords from description for categorization.

    Args:
        description: Text description to extract keywords from

    Returns:
        List of extracted keywords (filtered, lowercase)

    Example:
        >>> extract_keywords_from_description("Excavation in ordinary soil")
        ['excavation', 'ordinary', 'soil']
    """
    text = description.lower()
    text = re.sub(r"[^\w\s]", " ", text)

    # Extract words (filter out common words)
    stop_words = {
        "the",
        "and",
        "or",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "from",
        "by",
        "as",
        "is",
        "are",
        "a",
        "an",
    }
    words = text.split()
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]

    return keywords


def detect_dsr_block(block: Dict) -> Tuple[bool, bool]:
    """Detect if a block contains DSR code patterns.

    Args:
        block: Block dict with 'lines' key

    Returns:
        Tuple of (has_dsr_marker, has_standalone_code)
    """
    lines = block.get("lines", [])
    block_text = " ".join(str(line) for line in lines)

    # Check for DSR marker
    has_dsr_marker = "DSR-" in block_text.upper() or bool(
        re.search(r"\b20\d{2}-\d+\.\d+", block_text)
    )

    # Check for standalone code pattern
    has_standalone_code = False
    if not has_dsr_marker and len(lines) <= 3:
        for line in lines:
            line_str = str(line).strip()
            if re.match(r"^\d+\.\d+(?:\.\d+)?$", line_str):
                has_standalone_code = True
                break

    return has_dsr_marker, has_standalone_code


def extract_dsr_code_from_lines(
    lines: List, block_idx: int, blocks: List
) -> Tuple[Optional[str], Optional[str]]:
    """Extract DSR code and clean code from block lines.

    Handles three patterns:
    1. "YYYY-15.7.4" (year-code in one line)
    2. "DSR-" "YYYY-" "15.7.4" (separate lines)
    3. "15.3" (standalone with lookback for DSR markers)

    Args:
        lines: List of lines in current block
        block_idx: Index of current block
        blocks: All blocks for lookback

    Returns:
        Tuple of (dsr_code, clean_code) or (None, None) if not found
    """
    dsr_code = None
    clean_code = None

    for i, line in enumerate(lines):
        line_str = str(line).strip()

        # Pattern 1: "YYYY-15.7.4" (year-code)
        year_code_match = re.match(r"^(20\d{2})-(\d+\.\d+(?:\.\d+)?)$", line_str)
        if year_code_match:
            year = year_code_match.group(1)
            clean_code = year_code_match.group(2)
            dsr_code = f"DSR-{year}-{clean_code}"
            break

        # Pattern 2: "DSR-" "YYYY-" "15.7.4" (separate lines)
        if "DSR-" in line_str.upper():
            year = None
            for j in range(i + 1, min(i + 3, len(lines))):
                next_line = str(lines[j]).strip()
                # Check for year
                if not year and re.match(r"^20\d{2}$", next_line):
                    year = next_line
                # Check for code (with or without year prefix)
                code_match = re.match(r"^(?:(20\d{2})-)?(\d+\.\d+(?:\.\d+)?)$", next_line)
                if code_match:
                    if not year and code_match.group(1):
                        year = code_match.group(1)
                    clean_code = code_match.group(2)
                    dsr_code = f"DSR-{year}-{clean_code}"
                    break
            if dsr_code:
                break

        # Pattern 3: "15.3" (standalone, lookback for DSR markers)
        if not dsr_code and re.match(r"^\d+\.\d+(?:\.\d+)?$", line_str):
            for prev_offset in range(1, min(4, block_idx + 1)):
                prev_block = blocks[block_idx - prev_offset]
                prev_lines = prev_block.get("lines", [])
                prev_text = " ".join(str(l) for l in prev_lines)
                # Look for DSR- and any year (20XX)
                year_match = re.search(r"\b(20\d{2})\b", prev_text)
                if "DSR-" in prev_text.upper() and year_match:
                    year = year_match.group(1)
                    clean_code = line_str
                    dsr_code = f"DSR-{year}-{clean_code}"
                    break
            if dsr_code:
                break

    return dsr_code, clean_code


def extract_item_details(blocks: List, block_idx: int) -> Tuple[str, str, str]:
    """Extract description, unit, and quantity from nearby blocks.

    Args:
        blocks: All blocks to search
        block_idx: Starting block index

    Returns:
        Tuple of (description, unit, quantity)
    """
    description = ""
    unit = ""
    quantity = ""

    # Search next blocks for description, unit, quantity
    for offset in range(1, min(6, len(blocks) - block_idx)):
        check_block = blocks[block_idx + offset]
        check_lines = check_block.get("lines", [])

        # Extract description (filter noise)
        for line in check_lines:
            line_text = str(line).strip()
            if (
                len(line_text) > 15
                and not re.match(r"^\d+\.?\d*$", line_text)
                and line_text
                not in [
                    "Nos",
                    "Cum",
                    "Sqm",
                    "Kg",
                    "Metre",
                    "Mtr",
                    "Ltr",
                    "Each",
                    "Unit",
                    "Qty",
                    "Rate",
                    "Amount",
                    "DSR-",
                ]
                and "DSR" not in line_text.upper()
                and not re.match(r"^20\d{2}$", line_text)
            ):
                if not description:
                    description = line_text
                    break

        # Extract unit and quantity
        for i, line in enumerate(check_lines):
            line_text = str(line).strip()
            if line_text in [
                "Nos",
                "Cum",
                "Sqm",
                "Kg",
                "Metre",
                "Mtr",
                "Ltr",
                "Each",
            ]:
                unit = line_text
                # Find nearby quantity value
                for j in range(max(0, i - 2), min(i + 3, len(check_lines))):
                    qty_text = str(check_lines[j]).strip()
                    if qty_text != line_text and re.match(r"^\d+\.?\d+$", qty_text):
                        try:
                            val = float(qty_text)
                            if 0.01 <= val <= 100000:
                                quantity = qty_text
                                break
                        except Exception:
                            pass
                if unit and quantity:
                    break

        if description and unit and quantity:
            break

    return description, unit, quantity


def process_blocks_for_dsr_items(
    data: dict, item_processor: Optional[Callable] = None
) -> List[Dict]:
    """Process all blocks in document to extract DSR items.

    This is the common extraction loop used by both dsr_extractor and
    input_file_converter to avoid code duplication.

    Args:
        data: Document data with pages_data
        item_processor: Optional callback to process each item before adding
                       Signature: func(item_dict, item_number, clean_code) -> item_dict

    Returns:
        List of extracted DSR item dictionaries
    """
    items = []
    processed_codes = set()
    item_number = 0

    # Parse pages for DSR codes
    for page_data in data.get("document", {}).get("pages_data", []):
        blocks = page_data.get("blocks", [])

        for block_idx, block in enumerate(blocks):
            lines = block.get("lines", [])
            if not lines:
                continue

            # Check for DSR markers or standalone pattern
            has_dsr_marker, has_standalone_code = detect_dsr_block(block)

            if has_dsr_marker or has_standalone_code:
                # Extract DSR code using shared utility
                dsr_code, clean_code = extract_dsr_code_from_lines(lines, block_idx, blocks)

                # Only proceed if we found a valid DSR code and haven't processed it
                if dsr_code and clean_code and dsr_code not in processed_codes:
                    # Extract description, unit, quantity using shared utility
                    description, unit, quantity = extract_item_details(blocks, block_idx)

                    # Add item if we have at least code and description
                    if description:
                        item_number += 1

                        item = {
                            "dsr_code": dsr_code,
                            "clean_dsr_code": clean_code,
                            "description": description,
                            "unit": unit,
                            "quantity": quantity,
                        }

                        # Allow caller to customize item
                        if item_processor:
                            item = item_processor(item, item_number, clean_code)

                        items.append(item)
                        processed_codes.add(dsr_code)

    return items
