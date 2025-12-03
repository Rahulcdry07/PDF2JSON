#!/usr/bin/env python3
"""Extract DSR codes from unstructured input files."""

from typing import Dict, List
from extraction_utils import process_blocks_for_dsr_items


def extract_dsr_codes_from_lko(data: dict) -> List[Dict]:
    """Extract DSR codes and details (requires DSR-/year markers)."""

    items = process_blocks_for_dsr_items(data)

    print(f"✅ Extracted {len(items)} DSR items from input file")
    return items
