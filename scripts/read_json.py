#!/usr/bin/env python3
"""Utility to read the generated PDF->JSON and extract text blocks.

Features:
- Print all text blocks
- Search text blocks by text/regex

Usage examples:
  ./scripts/read_json.py --json examples/PLINTH_AREA_RATES_2025.json --print-text
  ./scripts/read_json.py --json examples/PLINTH_AREA_RATES_2025.json --search "Plinth"

"""

import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
import click


def load_json(json_path: Path) -> Dict:
    """Load JSON data from file."""
    with json_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def get_all_text_blocks(data: Dict) -> List[str]:
    """Extract all text blocks from the JSON data."""
    texts = []
    for page in data.get('document', {}).get('pages_data', []):
        for block in page.get('blocks', []):
            lines = block.get('lines', [])
            for line in lines:
                text = line.strip()
                if text:
                    texts.append(text)
    return texts


@click.command()
@click.option('--json', 'json_path', type=click.Path(exists=True, path_type=Path), required=True, help='Path to the JSON file')
@click.option('--print-text', is_flag=True, help='Print all text blocks')
@click.option('--search', 'search_term', help='Search for text/regex in blocks')
def main(json_path: Path, print_text: bool, search_term: str):
    data = load_json(json_path)
    texts = get_all_text_blocks(data)

    if print_text:
        for i, text in enumerate(texts):
            print(f"Block {i}: {text}")
    elif search_term:
        pattern = re.compile(search_term, re.IGNORECASE)
        matches = [text for text in texts if pattern.search(text)]
        if matches:
            for match in matches:
                print(match)
        else:
            print("No matches found.")
    else:
        print("Use --print-text or --search option.")


if __name__ == '__main__':
    main()