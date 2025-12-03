#!/usr/bin/env python3
"""Convert unstructured PDF JSON to structured DSR format."""

import argparse
import json
import sys
from pathlib import Path
from dsr_rate_extractor import extract_rates_from_dsr


def convert_to_structured_format(input_file: Path, output_file: Path, volume_name: str):
    """Convert to structured DSR format with searchable fields."""

    print(f"Loading {input_file.name}...")
    with open(input_file, "r") as f:
        data = json.load(f)

    print(f"Extracting DSR codes...")
    rates = extract_rates_from_dsr(data, volume_name)

    dsr_codes = []
    for code, entries in sorted(rates.items()):
        for entry in entries:
            # Parse chapter and section
            parts = code.split(".")
            chapter = parts[0] if parts else ""
            section = ".".join(parts[:2]) if len(parts) >= 2 else code

            dsr_entry = {
                "code": code,
                "chapter": chapter,
                "section": section,
                "description": entry["description"],
                "unit": entry["unit"],
                "rate": entry["rate"],
                "volume": entry["volume"],
                "page": entry["page"],
                "source": entry.get("source", ""),
                "keywords": _extract_keywords(entry["description"]),
            }
            dsr_codes.append(dsr_entry)

    # Create structured output
    output = {
        "metadata": {
            "source_file": input_file.name,
            "volume": volume_name,
            "total_codes": len(dsr_codes),
            "format_version": "1.0",
        },
        "dsr_codes": dsr_codes,
    }

    print(f"Writing structured JSON to {output_file.name}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Converted {len(dsr_codes)} DSR codes")

    # Create lookup index
    index = {entry["code"]: i for i, entry in enumerate(dsr_codes)}
    index_file = output_file.with_suffix(".index.json")
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)
    print(f"✓ Created index with {len(index)} entries")

    return len(dsr_codes)


def _extract_keywords(description: str) -> list:
    """Extract searchable keywords from description."""
    import re

    text = description.lower()
    text = re.sub(r"[^\w\s]", " ", text)

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


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert unstructured DSR JSON to structured format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single volume
  python3 convert_to_structured_json.py -v data/reference/civil/DSR_Vol_1_Civil.json
  
  # Convert multiple volumes
  python3 convert_to_structured_json.py -v data/reference/civil/DSR_Vol_1.json data/reference/civil/DSR_Vol_2.json
  
  # Specify output directory
  python3 convert_to_structured_json.py -v vol1.json vol2.json -o ./output
        """,
    )

    parser.add_argument(
        "-v",
        "--volumes",
        type=str,
        nargs="+",
        required=True,
        help="Path(s) to DSR volume JSON files (can specify multiple files)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: same as input file directory)",
    )

    return parser.parse_args()


def main(volume_inputs: list = None, output_dir: Path = None):
    """Main function to convert DSR files to structured format.

    Args:
        volume_inputs: List of Path objects for input volume JSON files
        output_dir: Output directory Path object
    """
    # Validate inputs
    if not volume_inputs:
        raise ValueError("No volume input files provided. Use -v to specify files.")

    # Determine output directory
    if output_dir is None:
        output_dir = volume_inputs[0].parent

    # Convert each volume
    total_codes = 0
    output_files = []

    for idx, vol_input in enumerate(volume_inputs, 1):
        volume_name = f"Volume {idx}"
        print(f"\n=== Converting {volume_name} ({vol_input.name}) ===")
        vol_output = output_dir / f"{vol_input.stem}_structured.json"
        count = convert_to_structured_format(vol_input, vol_output, volume_name)
        total_codes += count
        output_files.append(vol_output)
        output_files.append(vol_output.with_suffix(".index.json"))

    print(f"\n✅ Total DSR codes converted: {total_codes}")
    print(f"\nStructured files created:")
    for file in output_files:
        print(f"  - {file}")

    # Show sample from last volume
    if output_files:
        last_json = [f for f in output_files if f.suffix == ".json" and "index" not in f.name][-1]
        print(f"\n=== Sample Structured Entry ===")
        with open(last_json) as f:
            data = json.load(f)
        if data["dsr_codes"]:
            sample = data["dsr_codes"][0]
            print(json.dumps(sample, indent=2))


if __name__ == "__main__":
    args = parse_arguments()

    # Convert paths to Path objects
    volume_inputs = None
    if args.volumes:
        volume_inputs = [Path(v) for v in args.volumes]

        # Validate all input files exist
        for vol_input in volume_inputs:
            if not vol_input.exists():
                print(f"Error: Volume file not found: {vol_input}")
                sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    # Run conversion
    main(volume_inputs, output_dir)
