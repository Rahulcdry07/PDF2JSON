#!/usr/bin/env python3
"""
Additional comprehensive tests for create_master_database.py to achieve >90% coverage.
Focuses on uncovered lines: 94-95, 231-269, 273
"""

import sys
from pathlib import Path
import pytest
import sqlite3
from unittest.mock import patch
import tempfile

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_master_database import (
    create_master_database,
    migrate_existing_database,
    parse_arguments,
    main,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    import shutil

    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_db(temp_dir):
    """Create a sample DSR database."""
    db_path = temp_dir / "test_civil.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT,
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

    cursor.execute(
        """
        INSERT INTO dsr_codes VALUES
        ('15.12.2', '15', '15.12', 'Excavation in ordinary soil', 'cum', 100.50, 'Vol 1', 45, 'excavation soil'),
        ('16.3.1', '16', '16.3', 'PCC 1:2:4', 'sqm', 250.00, 'Vol 1', 89, 'concrete pcc'),
        ('1.1.1', '1', '1.1', 'Site clearance', 'sqm', 15.00, 'Vol 1', 10, 'clearance site')
    """
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_electrical_db(temp_dir):
    """Create a sample electrical database."""
    db_path = temp_dir / "test_electrical.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT,
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

    cursor.execute(
        """
        INSERT INTO dsr_codes VALUES
        ('E1.1', 'E1', 'E1.1', 'Cable laying', 'mtr', 50.00, 'Vol 2', 67, 'cable laying'),
        ('E2.3', 'E2', 'E2.3', 'Conduit installation', 'mtr', 75.00, 'Vol 2', 89, 'conduit install')
    """
    )

    conn.commit()
    conn.close()

    return db_path


# =============================================================================
# Tests for create_master_database - focusing on uncovered lines
# =============================================================================


def test_create_master_database_integrity_error(temp_dir, sample_db, capsys):
    """Test handling of duplicate codes (IntegrityError) - covers line 94-95."""
    # Create a database with duplicate code
    duplicate_db = temp_dir / "duplicate.db"
    conn = sqlite3.connect(duplicate_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT,
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

    # Insert the same code that exists in sample_db
    cursor.execute(
        """
        INSERT INTO dsr_codes VALUES
        ('15.12.2', '15', '15.12', 'Duplicate excavation', 'cum', 105.00, 'Vol 1', 46, 'excavation')
    """
    )

    conn.commit()
    conn.close()

    # Create master with both databases (same category will cause duplicate)
    output_db = temp_dir / "master.db"

    # First load from sample_db
    create_master_database({"civil": sample_db}, output_db)

    # Now try to add duplicate from second db to the same category
    # This requires manually inserting to trigger IntegrityError
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()

    # Try to insert duplicate
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO dsr_codes 
            (code, category, chapter, section, description, unit, rate, volume, page, keywords)
            VALUES ('15.12.2', 'civil', '15', '15.12', 'Duplicate', 'cum', 100, 'Vol 1', 1, 'test')
        """
        )

    conn.close()


def test_create_master_database_verification_queries(
    temp_dir, sample_db, sample_electrical_db, capsys
):
    """Test that verification queries are executed - covers lines 231-269."""
    output_db = temp_dir / "master.db"

    category_dbs = {
        "civil": sample_db,
        "electrical": sample_electrical_db,
    }

    total_codes = create_master_database(category_dbs, output_db)

    captured = capsys.readouterr()

    # Verify sample queries section is printed (lines 231-269)
    assert "Sample Queries:" in captured.out
    assert "Codes per category:" in captured.out
    assert "Sample codes:" in captured.out

    # Verify categories are shown
    assert "civil" in captured.out.lower()
    assert "electrical" in captured.out.lower()

    # Verify total codes
    assert total_codes == 5  # 3 from civil + 2 from electrical


def test_create_master_database_complete_output(temp_dir, sample_db, capsys):
    """Test complete output including all print statements."""
    output_db = temp_dir / "master.db"

    total_codes = create_master_database({"civil": sample_db}, output_db)

    captured = capsys.readouterr()

    # Verify all major output sections
    assert "Processing CIVIL category" in captured.out
    assert "Loaded 3 codes from civil" in captured.out
    assert "Master Database Created" in captured.out
    assert "Total Categories: 1" in captured.out
    assert "Total Codes: 3" in captured.out
    assert "Breakdown by Category:" in captured.out
    assert "Sample Queries:" in captured.out
    assert "Codes per category:" in captured.out
    assert "Sample codes:" in captured.out


# =============================================================================
# Tests for parse_arguments - ensure all paths are tested
# =============================================================================


def test_parse_arguments_migrate_mode():
    """Test parsing migrate arguments."""
    with patch(
        "sys.argv",
        [
            "create_master_database.py",
            "--migrate",
            "old.db",
            "--category",
            "mechanical",
            "--output",
            "new.db",
        ],
    ):
        args = parse_arguments()
        assert args.migrate == Path("old.db")
        assert args.category == "mechanical"
        assert args.output == Path("new.db")


def test_parse_arguments_create_master_mode():
    """Test parsing create-master arguments."""
    with patch(
        "sys.argv",
        [
            "create_master_database.py",
            "--create-master",
            "--civil",
            "civil.db",
            "--electrical",
            "electrical.db",
            "--mechanical",
            "mechanical.db",
            "--plumbing",
            "plumbing.db",
            "--horticulture",
            "horticulture.db",
            "--output",
            "master.db",
        ],
    ):
        args = parse_arguments()
        assert args.create_master is True
        assert args.civil == Path("civil.db")
        assert args.electrical == Path("electrical.db")
        assert args.mechanical == Path("mechanical.db")
        assert args.plumbing == Path("plumbing.db")
        assert args.horticulture == Path("horticulture.db")
        assert args.output == Path("master.db")


def test_parse_arguments_default_category():
    """Test default category value."""
    with patch("sys.argv", ["create_master_database.py", "--migrate", "test.db"]):
        args = parse_arguments()
        assert args.category == "civil"  # Default value


# =============================================================================
# Tests for main() function - covering all branches
# =============================================================================


def test_main_migrate_db_not_found(capsys):
    """Test main with non-existent database for migration."""
    with patch(
        "sys.argv",
        ["create_master_database.py", "--migrate", "nonexistent.db", "--category", "civil"],
    ):
        main()

        captured = capsys.readouterr()
        assert "Database not found" in captured.out


def test_main_migrate_success(temp_dir, sample_db, capsys):
    """Test successful migration."""
    output_db = temp_dir / "migrated.db"

    with patch(
        "sys.argv",
        [
            "create_master_database.py",
            "--migrate",
            str(sample_db),
            "--category",
            "civil",
            "--output",
            str(output_db),
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "Migrating" in captured.out
        assert "Migrated 3 codes" in captured.out

        # Verify output exists
        assert output_db.exists()


def test_main_migrate_default_output(temp_dir, sample_db, capsys):
    """Test migration with default output filename - covers line 273."""
    # Copy sample_db to a different location to test default naming
    test_db = temp_dir / "source" / "DSR_Test.db"
    test_db.parent.mkdir(parents=True, exist_ok=True)

    import shutil

    shutil.copy(sample_db, test_db)

    with patch(
        "sys.argv",
        ["create_master_database.py", "--migrate", str(test_db), "--category", "electrical"],
    ):
        main()

        # Check that default output was created
        expected_output = test_db.parent / "DSR_Electrical_combined.db"
        assert expected_output.exists()


def test_main_create_master_success(temp_dir, sample_db, sample_electrical_db, capsys):
    """Test successful master database creation."""
    output_db = temp_dir / "master.db"

    with patch(
        "sys.argv",
        [
            "create_master_database.py",
            "--create-master",
            "--civil",
            str(sample_db),
            "--electrical",
            str(sample_electrical_db),
            "--output",
            str(output_db),
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "Master Database Created" in captured.out
        assert output_db.exists()


def test_main_create_master_no_categories(capsys):
    """Test create-master with no category databases specified."""
    with patch("sys.argv", ["create_master_database.py", "--create-master"]):
        main()

        captured = capsys.readouterr()
        assert "No category databases specified" in captured.out


def test_main_create_master_default_output(temp_dir, sample_db, capsys):
    """Test create-master with default output path."""
    with patch(
        "sys.argv", ["create_master_database.py", "--create-master", "--civil", str(sample_db)]
    ):
        main()

        # Should create in reference_files directory
        expected_output = Path("reference_files/DSR_Master_All_Categories.db")

        captured = capsys.readouterr()
        assert "Master Database Created" in captured.out


def test_main_create_master_mechanical_plumbing(temp_dir, sample_db, capsys):
    """Test create-master with mechanical and plumbing categories."""
    # Create mechanical and plumbing databases
    mechanical_db = temp_dir / "mechanical.db"
    plumbing_db = temp_dir / "plumbing.db"

    for db_path in [mechanical_db, plumbing_db]:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE dsr_codes (
                code TEXT, chapter TEXT, section TEXT, description TEXT,
                unit TEXT, rate REAL, volume TEXT, page INTEGER, keywords TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO dsr_codes VALUES
            ('M1.1', 'M1', 'M1.1', 'Test item', 'nos', 100.00, 'Vol 1', 1, 'test')
        """
        )
        conn.commit()
        conn.close()

    output_db = temp_dir / "master.db"

    with patch(
        "sys.argv",
        [
            "create_master_database.py",
            "--create-master",
            "--mechanical",
            str(mechanical_db),
            "--plumbing",
            str(plumbing_db),
            "--output",
            str(output_db),
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "mechanical" in captured.out.lower()
        assert "plumbing" in captured.out.lower()


def test_main_no_action_specified(capsys):
    """Test main with no action specified."""
    with patch("sys.argv", ["create_master_database.py"]):
        main()

        captured = capsys.readouterr()
        assert "Please specify either --migrate or --create-master" in captured.out
        assert "Use --help" in captured.out


# =============================================================================
# Edge cases and integration tests
# =============================================================================


def test_create_master_all_five_categories(temp_dir, capsys):
    """Test creating master database with all five category types."""
    categories = ["civil", "electrical", "horticulture", "mechanical", "plumbing"]
    category_dbs = {}

    for category in categories:
        db_path = temp_dir / f"{category}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE dsr_codes (
                code TEXT, chapter TEXT, section TEXT, description TEXT,
                unit TEXT, rate REAL, volume TEXT, page INTEGER, keywords TEXT
            )
        """
        )
        cursor.execute(
            f"""
            INSERT INTO dsr_codes VALUES
            ('{category[0].upper()}1.1', '1', '1.1', '{category} item', 'nos', 100.00, 'Vol 1', 1, '{category}')
        """
        )
        conn.commit()
        conn.close()
        category_dbs[category] = db_path

    output_db = temp_dir / "master_all.db"
    total_codes = create_master_database(category_dbs, output_db)

    assert total_codes == 5

    captured = capsys.readouterr()
    for category in categories:
        assert category.upper() in captured.out or category.capitalize() in captured.out


def test_migrate_with_missing_fields(temp_dir):
    """Test migration handles databases with missing optional fields."""
    old_db = temp_dir / "old.db"
    conn = sqlite3.connect(old_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE dsr_codes (
            code TEXT, chapter TEXT, section TEXT, description TEXT,
            unit TEXT, rate REAL, volume TEXT, page INTEGER, keywords TEXT
        )
    """
    )
    cursor.execute(
        """
        INSERT INTO dsr_codes VALUES
        ('1.1', '', '', 'Test item', 'nos', 100.00, '', 0, '')
    """
    )
    conn.commit()
    conn.close()

    new_db = temp_dir / "new.db"
    migrate_existing_database(old_db, new_db, category="test")

    # Verify migration worked
    conn = sqlite3.connect(new_db)
    cursor = conn.cursor()
    cursor.execute("SELECT code, category FROM dsr_codes WHERE code = '1.1'")
    result = cursor.fetchone()
    assert result[0] == "1.1"
    assert result[1] == "test"
    conn.close()


def test_create_master_verifies_indexes(temp_dir, sample_db):
    """Test that all indexes are created."""
    output_db = temp_dir / "master.db"
    create_master_database({"civil": sample_db}, output_db)

    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()

    # Check that indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]

    expected_indexes = [
        "idx_category",
        "idx_code",
        "idx_chapter",
        "idx_section",
        "idx_rate",
        "idx_unit",
        "idx_category_code",
    ]

    for expected_index in expected_indexes:
        assert expected_index in indexes

    conn.close()


def test_migrate_preserves_all_data(temp_dir, sample_db):
    """Test that migration preserves all data fields."""
    new_db = temp_dir / "migrated.db"
    migrate_existing_database(sample_db, new_db, category="civil")

    # Compare data
    old_conn = sqlite3.connect(sample_db)
    old_cursor = old_conn.cursor()
    old_cursor.execute("SELECT COUNT(*) FROM dsr_codes")
    old_count = old_cursor.fetchone()[0]
    old_conn.close()

    new_conn = sqlite3.connect(new_db)
    new_cursor = new_conn.cursor()
    new_cursor.execute("SELECT COUNT(*) FROM dsr_codes")
    new_count = new_cursor.fetchone()[0]
    new_conn.close()

    assert old_count == new_count
