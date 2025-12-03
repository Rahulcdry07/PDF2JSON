#!/usr/bin/env python3
"""Create CSV and SQLite formats from structured DSR JSON."""

import argparse
import json
import csv
import sqlite3
import sys
from pathlib import Path


def create_csv_format(volume_files: list, output_dir: Path):
    """Convert structured JSON to combined CSV."""
    csv_file = output_dir / "DSR_combined.csv"

    with open(csv_file, "w", encoding="utf-8", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "code",
                "chapter",
                "section",
                "description",
                "unit",
                "rate",
                "volume",
                "page",
            ],
        )
        writer.writeheader()

        for vol_file in volume_files:
            print(f"  Adding {vol_file.name} to CSV...")
            with open(vol_file, encoding="utf-8") as vf:
                data = json.load(vf)

            for entry in data["dsr_codes"]:
                writer.writerow(
                    {
                        "code": entry["code"],
                        "chapter": entry["chapter"],
                        "section": entry["section"],
                        "description": entry["description"],
                        "unit": entry["unit"],
                        "rate": entry["rate"],
                        "volume": entry["volume"],
                        "page": entry["page"],
                    }
                )

    print(f"✓ Created CSV: {csv_file}")
    return csv_file


def create_sqlite_format(volume_files: list, output_dir: Path):
    """Convert structured JSON to SQLite database with indexes."""
    db_file = output_dir / "DSR_combined.db"

    if db_file.exists():
        db_file.unlink()

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create table
    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT PRIMARY KEY,
            chapter TEXT,
            section TEXT,
            description TEXT,
            unit TEXT,
            rate REAL,
            volume TEXT,
            page INTEGER,
            keywords TEXT
        )
    """
    )

    # Create search indexes
    cursor.execute("CREATE INDEX idx_chapter ON dsr_codes(chapter)")
    cursor.execute("CREATE INDEX idx_section ON dsr_codes(section)")
    cursor.execute("CREATE INDEX idx_rate ON dsr_codes(rate)")
    cursor.execute("CREATE INDEX idx_unit ON dsr_codes(unit)")

    # Load all volumes
    for vol_file in volume_files:
        print(f"  Loading {vol_file.name}...")
        with open(vol_file, encoding="utf-8") as f:
            data = json.load(f)

        for entry in data["dsr_codes"]:
            keywords = ",".join(entry.get("keywords", []))
            cursor.execute(
                """
                INSERT OR REPLACE INTO dsr_codes 
                (code, chapter, section, description, unit, rate, volume, page, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry["code"],
                    entry["chapter"],
                    entry["section"],
                    entry["description"],
                    entry["unit"],
                    entry["rate"],
                    entry["volume"],
                    entry["page"],
                    keywords,
                ),
            )

    conn.commit()

    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM dsr_codes")
    total = cursor.fetchone()[0]

    conn.close()

    print(f"✓ Created SQLite DB: {db_file}")
    print(f"  Total codes: {total}")
    return db_file


def demonstrate_sqlite_queries(db_file):
    """Show powerful SQL queries possible with SQLite."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print("\n=== SQLite Query Examples ===\n")

    # Example 1: Direct lookup
    print("1. Direct code lookup:")
    cursor.execute("SELECT code, description, rate, unit FROM dsr_codes WHERE code = '13.5.1'")
    result = cursor.fetchone()
    print(f"   {result[0]}: ₹{result[2]}/{result[3]} - {result[1][:50]}")

    # Example 2: Chapter filtering
    print("\n2. All codes in chapter 15 (first 5):")
    cursor.execute("SELECT code, rate, description FROM dsr_codes WHERE chapter = '15' LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]}: ₹{row[1]} - {row[2][:40]}")

    # Example 3: Rate range query
    print("\n3. High-value items (rate > 5000):")
    cursor.execute("SELECT code, rate, description FROM dsr_codes WHERE rate > 5000 LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]}: ₹{row[1]:,.2f} - {row[2][:40]}")

    # Example 4: Keyword search
    print("\n4. Search for 'cement plaster':")
    cursor.execute(
        """
        SELECT code, rate, description 
        FROM dsr_codes 
        WHERE description LIKE '%cement%' AND description LIKE '%plaster%' 
        LIMIT 5
    """
    )
    for row in cursor.fetchall():
        print(f"   {row[0]}: ₹{row[1]} - {row[2][:50]}")

    # Example 5: Aggregate queries
    print("\n5. Statistics by chapter:")
    cursor.execute(
        """
        SELECT chapter, COUNT(*) as count, AVG(rate) as avg_rate, MAX(rate) as max_rate
        FROM dsr_codes 
        WHERE chapter IN ('13', '15', '11', '5')
        GROUP BY chapter
        ORDER BY chapter
    """
    )
    print("   Chapter | Count | Avg Rate  | Max Rate")
    print("   --------|-------|-----------|----------")
    for row in cursor.fetchall():
        print(f"   {row[0]:>7} | {row[1]:>5} | ₹{row[2]:>8.2f} | ₹{row[3]:>8,.2f}")

    conn.close()


def compare_file_sizes():
    """Compare file sizes of different formats (example only)."""
    import os

    base = Path("../reference_files")

    # Example files - update with your actual files
    files = {
        "Structured JSON": "DSR_Vol_2_Civil_structured.json",
        "CSV Format": "DSR_combined.csv",
        "SQLite Database": "DSR_combined.db",
    }

    print("\n=== FILE SIZE COMPARISON ===\n")
    print(f"{'Format':<30} {'Size':>15}")
    print("-" * 50)

    for name, filename in files.items():
        filepath = base / filename
        if filepath.exists():
            size = os.path.getsize(filepath)
            size_kb = size / 1024
            print(f"{name:<30} {size_kb:>10.1f} KB")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create CSV and SQLite databases from structured DSR JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create CSV and SQLite from structured JSON (volume argument required)
  python3 create_alternative_formats.py -v data/reference/civil/DSR_Vol_1_structured.json
  
  # Process multiple volumes
  python3 create_alternative_formats.py -v vol1_structured.json vol2_structured.json vol3_structured.json
  
  # Specify output directory
  python3 create_alternative_formats.py -v vol1.json vol2.json -o ./output
        """,
    )

    parser.add_argument(
        "-v",
        "--volumes",
        type=str,
        nargs="+",
        required=True,
        help="Path(s) to structured DSR JSON files (can specify multiple files)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: same as input directory)",
    )

    parser.add_argument("--skip-demo", action="store_true", help="Skip demonstration queries")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    # Use volumes from CLI arguments (required)
    volume_paths = [Path(v) for v in args.volumes]

    # Validate all input files exist
    for vol_path in volume_paths:
        if not vol_path.exists():
            print(f"Error: Structured JSON not found: {vol_path}")
            print("Run: python3 convert_to_structured_json.py first")
            sys.exit(1)

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else volume_paths[0].parent

    print("Input files:")
    for idx, vol_path in enumerate(volume_paths, 1):
        print(f"  Volume {idx}: {vol_path}")
    print()

    print("Creating alternative formats...\n")

    csv_file = create_csv_format(volume_paths, output_dir)
    db_file = create_sqlite_format(volume_paths, output_dir)

    if not args.skip_demo:
        demonstrate_sqlite_queries(db_file)
    compare_file_sizes()

    print("\n✅ All formats created successfully!")
    print("\nRECOMMENDATION:")
    print("  - For simple projects: Use CSV (smallest, easiest)")
    print("  - For medium projects: Use Structured JSON (good balance)")
    print("  - For production/large: Use SQLite (fastest, most powerful)")
