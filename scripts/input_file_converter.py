#!/usr/bin/env python3
"""Convert input files to structured format for reliable DSR extraction."""

import json
from pathlib import Path
from typing import Dict, List
import argparse
import sys
from extraction_utils import (
    process_blocks_for_dsr_items,
    extract_keywords_from_description,
)


def _process_item_for_structured_format(item: Dict, item_number: int, clean_code: str) -> Dict:
    """Process extracted item to add structured format fields."""
    # Parse chapter and section
    parts = clean_code.split(".")
    chapter = parts[0] if parts else ""
    section = ".".join(parts[:2]) if len(parts) >= 2 else clean_code

    return {
        "item_number": item_number,
        "code": item["dsr_code"],
        "clean_code": item["clean_dsr_code"],
        "chapter": chapter,
        "section": section,
        "description": item["description"],
        "unit": item["unit"].lower(),
        "quantity": float(item["quantity"]) if item["quantity"] else 0.0,
        "source": "input_file",
        "keywords": extract_keywords_from_description(item["description"]),
    }


def extract_input_items_structured(data: dict) -> List[Dict]:
    """Extract and structure DSR items from input file."""

    items = process_blocks_for_dsr_items(data, _process_item_for_structured_format)

    return items


def convert_input_to_structured(input_file: Path, output_file: Path = None) -> Path:
    """Convert input JSON to structured format."""

    print(f"📂 Loading input file: {input_file.name}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("🔍 Extracting DSR items...")
    items = extract_input_items_structured(data)

    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_structured.json"

    output = {
        "metadata": {
            "source_file": input_file.name,
            "total_items": len(items),
            "format_version": "1.0",
            "type": "input_items",
        },
        "items": items,
    }

    print(f"💾 Writing structured JSON to {output_file.name}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Converted {len(items)} DSR items")

    if items:
        print("\n=== Sample Item ===")
        sample = items[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))

    return output_file


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert input files to structured format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert input file to structured format
  python3 input_file_converter.py -i Lko_Office_Repair_revise.json
  
  # Specify output file
  python3 input_file_converter.py -i input.json -o input_structured.json
        """,
    )

    parser.add_argument("-i", "--input", type=str, required=True, help="Path to input JSON file")

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file path (default: <input>_structured.json)",
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
        print("\n💡 Next steps:")
        print(f"   1. Review the structured file: {result_file}")
        print("   2. Use it with match_dsr_rates_sqlite.py for better matching")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
