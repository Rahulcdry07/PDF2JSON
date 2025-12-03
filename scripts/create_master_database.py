"""
Create a master DSR database combining multiple categories (Civil, Electrical, Horticulture, etc.)
Adds category tracking and enhanced search capabilities.
"""

import sqlite3
from pathlib import Path
from typing import Dict
import argparse


def create_master_database(category_databases: Dict[str, Path], output_db: Path):
    """Create a master database combining multiple category databases."""

    # Create master database with enhanced schema
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()

    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS dsr_codes")

    # Create enhanced schema with category field
    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT,
            category TEXT,
            chapter TEXT,
            section TEXT,
            description TEXT,
            unit TEXT,
            rate REAL,
            volume TEXT,
            page INTEGER,
            keywords TEXT,
            PRIMARY KEY (code, category)
        )
    """
    )

    # Create indexes for efficient searching
    cursor.execute("CREATE INDEX idx_category ON dsr_codes(category)")
    cursor.execute("CREATE INDEX idx_code ON dsr_codes(code)")
    cursor.execute("CREATE INDEX idx_chapter ON dsr_codes(chapter)")
    cursor.execute("CREATE INDEX idx_section ON dsr_codes(section)")
    cursor.execute("CREATE INDEX idx_rate ON dsr_codes(rate)")
    cursor.execute("CREATE INDEX idx_unit ON dsr_codes(unit)")
    cursor.execute("CREATE INDEX idx_category_code ON dsr_codes(category, code)")

    total_codes = 0
    category_counts = {}

    # Load data from each category database
    for category, db_path in category_databases.items():
        print(f"\n📂 Processing {category.upper()} category from {db_path.name}...")

        if not db_path.exists():
            print(f"   ⚠️  Database not found: {db_path}")
            continue

        # Connect to source database
        source_conn = sqlite3.connect(db_path)
        source_cursor = source_conn.cursor()

        # Read all codes from source
        source_cursor.execute(
            "SELECT code, chapter, section, description, unit, rate, volume, page, keywords FROM dsr_codes"
        )
        rows = source_cursor.fetchall()

        # Insert into master database with category
        count = 0
        for row in rows:
            try:
                cursor.execute(
                    """
                    INSERT INTO dsr_codes (code, category, chapter, section, description, unit, rate, volume, page, keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row[0],
                        category,
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                    ),
                )
                count += 1
            except sqlite3.IntegrityError:
                print(f"   ⚠️  Duplicate code: {row[0]} in {category}")

        category_counts[category] = count
        total_codes += count
        print(f"   ✅ Loaded {count} codes from {category}")

        source_conn.close()

    conn.commit()

    # Print summary
    print(f"\n{'='*60}")
    print(f"✅ Master Database Created: {output_db.name}")
    print(f"{'='*60}")
    print(f"Total Categories: {len(category_counts)}")
    print(f"Total Codes: {total_codes}")
    print("\nBreakdown by Category:")
    for category, count in category_counts.items():
        print(f"  • {category.capitalize()}: {count} codes")
    print(f"{'='*60}")

    # Verify with sample queries
    print("\n🔍 Sample Queries:")

    # Query 1: Total codes per category
    cursor.execute("SELECT category, COUNT(*) FROM dsr_codes GROUP BY category")
    print("\nCodes per category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Query 2: Sample codes from each category
    cursor.execute("SELECT category, code, description FROM dsr_codes GROUP BY category LIMIT 3")
    print("\nSample codes:")
    for row in cursor.fetchall():
        print(f"  [{row[0]}] {row[1]}: {row[2][:50]}...")

    conn.close()
    return total_codes


def migrate_existing_database(old_db: Path, new_db: Path, category: str = "civil"):
    """Migrate existing database to new schema with category."""

    print(f"\n📦 Migrating {old_db.name} to new schema as '{category}' category...")

    # Read from old database
    old_conn = sqlite3.connect(old_db)
    old_cursor = old_conn.cursor()
    old_cursor.execute(
        "SELECT code, chapter, section, description, unit, rate, volume, page, keywords FROM dsr_codes"
    )
    rows = old_cursor.fetchall()

    # Create new database with enhanced schema
    new_conn = sqlite3.connect(new_db)
    new_cursor = new_conn.cursor()

    new_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dsr_codes (
            code TEXT,
            category TEXT,
            chapter TEXT,
            section TEXT,
            description TEXT,
            unit TEXT,
            rate REAL,
            volume TEXT,
            page INTEGER,
            keywords TEXT,
            PRIMARY KEY (code, category)
        )
    """
    )

    # Create indexes
    new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON dsr_codes(category)")
    new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_code ON dsr_codes(code)")
    new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_code ON dsr_codes(category, code)")

    # Insert with category
    for row in rows:
        new_cursor.execute(
            """
            INSERT OR REPLACE INTO dsr_codes (code, category, chapter, section, description, unit, rate, volume, page, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (row[0], category, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]),
        )

    new_conn.commit()
    print(f"✅ Migrated {len(rows)} codes to {new_db.name}")

    old_conn.close()
    new_conn.close()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create master DSR database from multiple category databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate existing database to new schema
  python create_master_database.py --migrate DSR_combined.db --category civil
  
  # Create master database from multiple categories
  python create_master_database.py --create-master \\
    --civil civil/DSR_Civil_combined.db \\
    --electrical electrical/DSR_Electrical_combined.db \\
    --horticulture horticulture/DSR_Horticulture_combined.db \\
    --output DSR_Master_All_Categories.db
        """,
    )

    parser.add_argument("--migrate", type=Path, help="Migrate existing database to new schema")
    parser.add_argument(
        "--category", type=str, default="civil", help="Category name for migration (default: civil)"
    )
    parser.add_argument("--output", type=Path, help="Output database file")

    parser.add_argument(
        "--create-master",
        action="store_true",
        help="Create master database from multiple categories",
    )
    parser.add_argument("--civil", type=Path, help="Path to Civil database")
    parser.add_argument("--electrical", type=Path, help="Path to Electrical database")
    parser.add_argument("--horticulture", type=Path, help="Path to Horticulture database")
    parser.add_argument("--mechanical", type=Path, help="Path to Mechanical database")
    parser.add_argument("--plumbing", type=Path, help="Path to Plumbing database")

    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.migrate:
        # Migration mode
        if not args.migrate.exists():
            print(f"❌ Database not found: {args.migrate}")
            return

        output_db = (
            args.output or args.migrate.parent / f"DSR_{args.category.capitalize()}_combined.db"
        )
        migrate_existing_database(args.migrate, output_db, args.category)

    elif args.create_master:
        # Master database creation mode
        category_databases = {}

        if args.civil:
            category_databases["civil"] = args.civil
        if args.electrical:
            category_databases["electrical"] = args.electrical
        if args.horticulture:
            category_databases["horticulture"] = args.horticulture
        if args.mechanical:
            category_databases["mechanical"] = args.mechanical
        if args.plumbing:
            category_databases["plumbing"] = args.plumbing

        if not category_databases:
            print("❌ No category databases specified. Use --civil, --electrical, etc.")
            return

        output_db = args.output or Path("reference_files/DSR_Master_All_Categories.db")
        output_db.parent.mkdir(parents=True, exist_ok=True)

        create_master_database(category_databases, output_db)
    else:
        print("❌ Please specify either --migrate or --create-master")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
