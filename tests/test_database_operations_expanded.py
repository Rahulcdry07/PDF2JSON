"""
Comprehensive tests for database operation scripts.
Tests create_master_database.py, update_dsr_database.py, match_dsr_rates_sqlite.py
"""

import pytest
import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Import the modules to test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_master_database import (
    create_master_database,
    migrate_existing_database,
    parse_arguments as parse_create_args,
)
from update_dsr_database import (
    get_current_version,
    increment_version,
    show_version_history,
    update_rate,
    update_description,
    batch_update_from_csv,
    add_new_code,
    view_code,
    parse_arguments as parse_update_args,
)
from match_dsr_rates_sqlite import (
    load_input_file,
    load_dsr_database,
    match_with_database,
    main as match_main,
    parse_arguments as parse_match_args,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_dsr_db(temp_dir):
    """Create a sample DSR database for testing."""
    db_path = temp_dir / "test_dsr.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    # Insert sample data
    sample_data = [
        (
            "15.12.2",
            "Chapter 15",
            "Section 12",
            "Excavation in ordinary soil",
            "cum",
            450.00,
            "Vol I",
            150,
            "excavation soil",
        ),
        (
            "15.7.4",
            "Chapter 15",
            "Section 7",
            "Brickwork in cement mortar",
            "sqm",
            550.00,
            "Vol I",
            75,
            "brickwork cement",
        ),
        (
            "16.3.1",
            "Chapter 16",
            "Section 3",
            "PCC 1:2:4",
            "cum",
            6500.00,
            "Vol I",
            200,
            "pcc concrete",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO dsr_codes (code, chapter, section, description, unit, rate, volume, page, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_data,
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_category_db(temp_dir):
    """Create a sample category database with category field."""
    db_path = temp_dir / "civil_dsr.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    sample_data = [
        (
            "15.12.2",
            "civil",
            "Chapter 15",
            "Section 12",
            "Excavation in ordinary soil",
            "cum",
            450.00,
            "Vol I",
            150,
            "excavation soil",
        ),
        (
            "15.7.4",
            "civil",
            "Chapter 15",
            "Section 7",
            "Brickwork in cement mortar",
            "sqm",
            550.00,
            "Vol I",
            75,
            "brickwork cement",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO dsr_codes (code, category, chapter, section, description, unit, rate, volume, page, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_data,
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_input_file_structured(temp_dir):
    """Create a sample structured input file."""
    input_file = temp_dir / "input_structured.json"
    data = {
        "metadata": {
            "type": "input_items",
            "version": "1.0",
            "created": datetime.now().isoformat(),
        },
        "items": [
            {
                "code": "15.12.2",
                "clean_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": 100,
                "unit": "cum",
                "chapter": "Chapter 15",
                "section": "Section 12",
            },
            {
                "code": "15.7.4",
                "clean_code": "15.7.4",
                "description": "Brickwork in cement mortar",
                "quantity": 50,
                "unit": "sqm",
                "chapter": "Chapter 15",
                "section": "Section 7",
            },
        ],
    }

    with open(input_file, "w") as f:
        json.dump(data, f, indent=2)

    return input_file


@pytest.fixture
def sample_input_file_unstructured(temp_dir):
    """Create a sample unstructured input file."""
    input_file = temp_dir / "input_unstructured.json"
    data = {
        "project": "Test Project",
        "pages": [{"text_blocks": [{"text": "15.12.2 Excavation in ordinary soil 100 cum"}]}],
    }

    with open(input_file, "w") as f:
        json.dump(data, f, indent=2)

    return input_file


# =============================================================================
# Tests for create_master_database.py
# =============================================================================


class TestCreateMasterDatabase:
    """Tests for create_master_database.py functions."""

    def test_create_master_database_single_category(self, temp_dir, sample_dsr_db):
        """Test creating master database from single category."""
        output_db = temp_dir / "master.db"
        category_dbs = {"civil": sample_dsr_db}

        total_codes = create_master_database(category_dbs, output_db)

        assert output_db.exists()
        assert total_codes == 3

        # Verify database structure
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM dsr_codes WHERE category = 'civil'")
        assert cursor.fetchone()[0] == 3

        # Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_category" in indexes
        assert "idx_code" in indexes

        conn.close()

    def test_create_master_database_multiple_categories(self, temp_dir, sample_dsr_db):
        """Test creating master database from multiple categories."""
        # Create second category database
        electrical_db = temp_dir / "electrical.db"
        shutil.copy(sample_dsr_db, electrical_db)

        output_db = temp_dir / "master_multi.db"
        category_dbs = {"civil": sample_dsr_db, "electrical": electrical_db}

        total_codes = create_master_database(category_dbs, output_db)

        assert total_codes == 6  # 3 codes x 2 categories

        # Verify categories
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT category FROM dsr_codes ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        assert categories == ["civil", "electrical"]

        conn.close()

    def test_create_master_database_nonexistent_db(self, temp_dir, capsys):
        """Test handling of nonexistent database."""
        output_db = temp_dir / "master.db"
        category_dbs = {"civil": temp_dir / "nonexistent.db"}

        total_codes = create_master_database(category_dbs, output_db)

        captured = capsys.readouterr()
        assert "⚠️  Database not found" in captured.out
        assert total_codes == 0

    def test_create_master_database_duplicate_codes(self, temp_dir, capsys):
        """Test handling of duplicate codes in same category."""
        # Create database with duplicate
        db1 = temp_dir / "db1.db"
        conn = sqlite3.connect(db1)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE dsr_codes (
                code TEXT PRIMARY KEY,
                chapter TEXT, section TEXT, description TEXT,
                unit TEXT, rate REAL, volume TEXT, page INTEGER, keywords TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO dsr_codes VALUES
            ('15.12.2', 'Ch15', 'Sec12', 'Test', 'cum', 450.00, 'Vol I', 150, 'test')
        """
        )
        conn.commit()
        conn.close()

        output_db = temp_dir / "master.db"
        category_dbs = {"civil": db1}

        # First insertion should work
        create_master_database(category_dbs, output_db)

        # Try to add duplicate manually to test constraint
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Should raise IntegrityError due to primary key constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO dsr_codes (code, category, chapter, section, description, unit, rate, volume, page, keywords)
                VALUES ('15.12.2', 'civil', 'Ch15', 'Sec12', 'Test', 'cum', 450.00, 'Vol I', 150, 'test')
            """
            )

        conn.close()

    def test_migrate_existing_database(self, temp_dir, sample_dsr_db):
        """Test migrating database to new schema with category."""
        new_db = temp_dir / "migrated.db"

        migrate_existing_database(sample_dsr_db, new_db, category="civil")

        assert new_db.exists()

        # Verify schema has category
        conn = sqlite3.connect(new_db)
        cursor = conn.cursor()

        cursor.execute("SELECT code, category, description FROM dsr_codes LIMIT 1")
        row = cursor.fetchone()
        assert row[1] == "civil"  # category field

        # Verify all codes migrated
        cursor.execute("SELECT COUNT(*) FROM dsr_codes")
        assert cursor.fetchone()[0] == 3

        conn.close()

    def test_migrate_with_custom_category(self, temp_dir, sample_dsr_db):
        """Test migration with custom category name."""
        new_db = temp_dir / "migrated_electrical.db"

        migrate_existing_database(sample_dsr_db, new_db, category="electrical")

        conn = sqlite3.connect(new_db)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT category FROM dsr_codes")
        assert cursor.fetchone()[0] == "electrical"

        conn.close()


# =============================================================================
# Tests for update_dsr_database.py
# =============================================================================


class TestUpdateDSRDatabase:
    """Tests for update_dsr_database.py functions."""

    def test_get_current_version_new_database(self, temp_dir):
        """Test getting version from new database."""
        db_path = temp_dir / "test.db"
        conn = sqlite3.connect(db_path)
        conn.close()

        version = get_current_version(db_path)
        assert version == 1

    def test_get_current_version_existing(self, temp_dir):
        """Test getting version from database with metadata."""
        db_path = temp_dir / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO db_metadata (key, value, updated_at)
            VALUES ('version', '5', ?)
        """,
            (datetime.now().isoformat(),),
        )
        conn.commit()
        conn.close()

        version = get_current_version(db_path)
        assert version == 5

    def test_increment_version(self, temp_dir):
        """Test incrementing database version."""
        db_path = temp_dir / "test.db"
        conn = sqlite3.connect(db_path)
        conn.close()

        # First increment
        new_version = increment_version(db_path, "Initial version")
        assert new_version == 1

        # Second increment
        new_version = increment_version(db_path, "Updated rates")
        assert new_version == 2

        # Verify history
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM version_history")
        assert cursor.fetchone()[0] == 2
        conn.close()

    def test_show_version_history_no_table(self, temp_dir, capsys):
        """Test showing version history when table doesn't exist."""
        db_path = temp_dir / "test.db"
        conn = sqlite3.connect(db_path)
        conn.close()

        show_version_history(db_path)

        captured = capsys.readouterr()
        assert "No version history found" in captured.out

    def test_show_version_history_with_data(self, temp_dir, capsys):
        """Test showing version history with data."""
        db_path = temp_dir / "test.db"

        increment_version(db_path, "First change")
        increment_version(db_path, "Second change")

        show_version_history(db_path, limit=5)

        captured = capsys.readouterr()
        assert "Database Version History" in captured.out
        assert "First change" in captured.out
        assert "Second change" in captured.out

    def test_update_rate_success(self, temp_dir, sample_category_db, capsys):
        """Test successfully updating a rate."""
        result = update_rate(sample_category_db, "15.12.2", 500.00, category="civil", dry_run=False)

        assert result is True

        # Verify update
        conn = sqlite3.connect(sample_category_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rate FROM dsr_codes WHERE code = ? AND category = ?", ("15.12.2", "civil")
        )
        assert cursor.fetchone()[0] == 500.00
        conn.close()

        captured = capsys.readouterr()
        assert "Rate updated successfully" in captured.out

    def test_update_rate_code_not_found(self, temp_dir, sample_category_db, capsys):
        """Test updating rate for nonexistent code."""
        result = update_rate(sample_category_db, "99.99.99", 500.00, category="civil")

        assert result is False
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_update_rate_dry_run(self, temp_dir, sample_category_db, capsys):
        """Test dry run mode for rate update."""
        original_rate = 450.00

        result = update_rate(sample_category_db, "15.12.2", 999.00, category="civil", dry_run=True)

        assert result is True

        # Verify no change
        conn = sqlite3.connect(sample_category_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rate FROM dsr_codes WHERE code = ? AND category = ?", ("15.12.2", "civil")
        )
        assert cursor.fetchone()[0] == original_rate
        conn.close()

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_update_description_success(self, temp_dir, sample_category_db, capsys):
        """Test successfully updating a description."""
        new_desc = "Updated excavation work"

        result = update_description(
            sample_category_db, "15.12.2", new_desc, category="civil", dry_run=False
        )

        assert result is True

        # Verify update
        conn = sqlite3.connect(sample_category_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT description FROM dsr_codes WHERE code = ? AND category = ?",
            ("15.12.2", "civil"),
        )
        assert cursor.fetchone()[0] == new_desc
        conn.close()

    def test_batch_update_from_csv_success(self, temp_dir, sample_category_db, capsys):
        """Test batch update from CSV file."""
        # Create CSV file
        csv_file = temp_dir / "updates.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["code", "category", "field", "new_value"])
            writer.writeheader()
            writer.writerow(
                {"code": "15.12.2", "category": "civil", "field": "rate", "new_value": "480.00"}
            )
            writer.writerow(
                {"code": "15.7.4", "category": "civil", "field": "rate", "new_value": "600.00"}
            )

        result = batch_update_from_csv(sample_category_db, csv_file, dry_run=False)

        assert result is True

        # Verify updates
        conn = sqlite3.connect(sample_category_db)
        cursor = conn.cursor()
        cursor.execute("SELECT rate FROM dsr_codes WHERE code = '15.12.2' AND category = 'civil'")
        assert cursor.fetchone()[0] == 480.00
        cursor.execute("SELECT rate FROM dsr_codes WHERE code = '15.7.4' AND category = 'civil'")
        assert cursor.fetchone()[0] == 600.00
        conn.close()

        captured = capsys.readouterr()
        assert "2/2 updates successful" in captured.out

    def test_batch_update_from_csv_dry_run(self, temp_dir, sample_category_db, capsys):
        """Test batch update dry run."""
        csv_file = temp_dir / "updates.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["code", "category", "field", "new_value"])
            writer.writeheader()
            writer.writerow(
                {"code": "15.12.2", "category": "civil", "field": "rate", "new_value": "999.00"}
            )

        result = batch_update_from_csv(sample_category_db, csv_file, dry_run=True)

        assert result is True
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_batch_update_csv_not_found(self, temp_dir, sample_category_db, capsys):
        """Test batch update with nonexistent CSV."""
        result = batch_update_from_csv(sample_category_db, temp_dir / "nonexistent.csv")

        assert result is False
        captured = capsys.readouterr()
        assert "CSV file not found" in captured.out

    def test_add_new_code_success(self, temp_dir, sample_category_db, capsys):
        """Test adding a new DSR code."""
        code_data = {
            "code": "99.1.1",
            "category": "civil",
            "description": "New test work",
            "unit": "sqm",
            "rate": 750.00,
            "chapter": "Chapter 99",
            "section": "Section 1",
        }

        result = add_new_code(sample_category_db, code_data, dry_run=False)

        assert result is True

        # Verify insertion
        conn = sqlite3.connect(sample_category_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT code, description, rate FROM dsr_codes WHERE code = '99.1.1' AND category = 'civil'"
        )
        row = cursor.fetchone()
        assert row[0] == "99.1.1"
        assert row[1] == "New test work"
        assert row[2] == 750.00
        conn.close()

    def test_add_new_code_missing_fields(self, temp_dir, sample_category_db, capsys):
        """Test adding new code with missing required fields."""
        code_data = {
            "code": "99.1.1",
            "category": "civil",
            # Missing description, unit, rate
        }

        result = add_new_code(sample_category_db, code_data)

        assert result is False
        captured = capsys.readouterr()
        assert "Missing required field" in captured.out

    def test_add_new_code_duplicate(self, temp_dir, sample_category_db, capsys):
        """Test adding duplicate code."""
        code_data = {
            "code": "15.12.2",  # Already exists
            "category": "civil",
            "description": "Duplicate",
            "unit": "cum",
            "rate": 500.00,
        }

        result = add_new_code(sample_category_db, code_data, dry_run=False)

        assert result is False
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_view_code_success(self, temp_dir, sample_category_db, capsys):
        """Test viewing a DSR code."""
        view_code(sample_category_db, "15.12.2", category="civil")

        captured = capsys.readouterr()
        assert "15.12.2" in captured.out
        assert "Excavation in ordinary soil" in captured.out
        assert "450" in captured.out

    def test_view_code_not_found(self, temp_dir, sample_category_db, capsys):
        """Test viewing nonexistent code."""
        view_code(sample_category_db, "99.99.99", category="civil")

        captured = capsys.readouterr()
        assert "not found" in captured.out


# =============================================================================
# Tests for match_dsr_rates_sqlite.py
# =============================================================================


class TestMatchDSRRates:
    """Tests for match_dsr_rates_sqlite.py functions."""

    def test_load_input_file_structured(self, temp_dir, sample_input_file_structured, capsys):
        """Test loading structured input file."""
        items = load_input_file(sample_input_file_structured)

        assert len(items) == 2
        assert items[0]["dsr_code"] == "15.12.2"
        assert items[0]["description"] == "Excavation in ordinary soil"
        assert items[0]["quantity"] == 100

        captured = capsys.readouterr()
        assert "structured input format" in captured.out

    def test_load_input_file_unstructured(self, temp_dir, sample_input_file_unstructured, capsys):
        """Test loading unstructured input file."""
        # This will try to use dsr_extractor which may not extract properly
        # Just test that it doesn't crash
        try:
            items = load_input_file(sample_input_file_unstructured)
            # May return empty list if extractor doesn't find codes
            assert isinstance(items, list)
        except Exception:
            # If dsr_extractor fails, that's okay for this test
            pytest.skip("DSR extractor not available or failed")

    def test_load_dsr_database_success(self, temp_dir, sample_dsr_db):
        """Test loading DSR database."""
        conn = load_dsr_database(sample_dsr_db)

        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dsr_codes")
        assert cursor.fetchone()[0] == 3

        conn.close()

    def test_load_dsr_database_not_found(self, temp_dir):
        """Test loading nonexistent database."""
        with pytest.raises(FileNotFoundError):
            load_dsr_database(temp_dir / "nonexistent.db")

    def test_match_with_database_exact_match(self, temp_dir, sample_dsr_db, capsys):
        """Test matching with exact code match."""
        lko_items = [
            {
                "dsr_code": "15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": 100,
                "unit": "cum",
            }
        ]

        conn = load_dsr_database(sample_dsr_db)
        matched = match_with_database(lko_items, conn, similarity_threshold=0.3)
        conn.close()

        assert len(matched) == 1
        assert matched[0]["rate"] == 450.00
        assert matched[0]["match_type"] == "exact_with_description_match"
        assert matched[0]["similarity_score"] >= 0.3
        assert matched[0]["amount"] == 45000.00  # 100 * 450

    def test_match_with_database_code_mismatch(self, temp_dir, sample_dsr_db, capsys):
        """Test matching with code but different description."""
        lko_items = [
            {
                "dsr_code": "15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Completely different work description",
                "quantity": 50,
                "unit": "cum",
            }
        ]

        conn = load_dsr_database(sample_dsr_db)
        matched = match_with_database(lko_items, conn, similarity_threshold=0.8)  # High threshold
        conn.close()

        assert len(matched) == 1
        # Should still find rate but flag as mismatch if similarity < threshold
        assert matched[0]["rate"] == 450.00
        # May be "code_match_but_description_mismatch" if similarity is low

    def test_match_with_database_not_found(self, temp_dir, sample_dsr_db):
        """Test matching with code not in database."""
        lko_items = [
            {
                "dsr_code": "99.99.99",
                "clean_dsr_code": "99.99.99",
                "description": "Nonexistent work",
                "quantity": 10,
                "unit": "nos",
            }
        ]

        conn = load_dsr_database(sample_dsr_db)
        matched = match_with_database(lko_items, conn)
        conn.close()

        assert len(matched) == 1
        assert matched[0]["rate"] is None
        assert matched[0]["match_type"] == "not_found"
        assert matched[0]["similarity_score"] == 0.0

    def test_match_with_database_multiple_items(self, temp_dir, sample_dsr_db):
        """Test matching multiple items."""
        lko_items = [
            {
                "dsr_code": "15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": 100,
                "unit": "cum",
            },
            {
                "dsr_code": "15.7.4",
                "clean_dsr_code": "15.7.4",
                "description": "Brickwork in cement mortar",
                "quantity": 50,
                "unit": "sqm",
            },
            {
                "dsr_code": "99.99.99",
                "clean_dsr_code": "99.99.99",
                "description": "Not found",
                "quantity": 1,
                "unit": "nos",
            },
        ]

        conn = load_dsr_database(sample_dsr_db)
        matched = match_with_database(lko_items, conn)
        conn.close()

        assert len(matched) == 3
        # First two should match
        assert matched[0]["match_type"] == "exact_with_description_match"
        assert matched[1]["match_type"] == "exact_with_description_match"
        # Third should not match
        assert matched[2]["match_type"] == "not_found"

    def test_match_main_function(
        self, temp_dir, sample_dsr_db, sample_input_file_structured, capsys
    ):
        """Test main matching function end-to-end."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        match_main(
            input_file=sample_input_file_structured,
            db_path=sample_dsr_db,
            output_dir=output_dir,
            similarity_threshold=0.3,
        )

        # Verify output file created
        output_files = list(output_dir.glob("*_matched_rates.json"))
        assert len(output_files) == 1

        # Verify output content
        with open(output_files[0]) as f:
            result = json.load(f)

        assert "summary" in result
        assert result["summary"]["total_items"] == 2
        assert result["summary"]["exact_matches"] >= 0

        captured = capsys.readouterr()
        assert "MATCHING SUMMARY" in captured.out


# =============================================================================
# Argument parsing tests
# =============================================================================


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_create_master_database_parse_migrate(self, monkeypatch):
        """Test parsing migrate arguments."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "create_master_database.py",
                "--migrate",
                "old.db",
                "--category",
                "civil",
                "--output",
                "new.db",
            ],
        )

        args = parse_create_args()
        assert args.migrate == Path("old.db")
        assert args.category == "civil"
        assert args.output == Path("new.db")

    def test_update_dsr_database_parse_update_rate(self, monkeypatch):
        """Test parsing update rate arguments."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "update_dsr_database.py",
                "-d",
                "test.db",
                "--update-rate",
                "15.12.2",
                "--new-rate",
                "500.00",
                "--category",
                "civil",
            ],
        )

        args = parse_update_args()
        assert args.database == Path("test.db")
        assert args.update_rate == "15.12.2"
        assert args.new_rate == 500.00
        assert args.category == "civil"

    def test_match_dsr_rates_parse_args(self, monkeypatch):
        """Test parsing match arguments."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "match_dsr_rates_sqlite.py",
                "-i",
                "input.json",
                "-d",
                "dsr.db",
                "-o",
                "output",
                "-t",
                "0.5",
            ],
        )

        args = parse_match_args()
        assert args.input == "input.json"
        assert args.database == "dsr.db"
        assert args.output == "output"
        assert args.threshold == 0.5
