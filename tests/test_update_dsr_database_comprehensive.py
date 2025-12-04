#!/usr/bin/env python3
"""
Comprehensive tests for update_dsr_database.py to achieve >90% coverage.
"""

import sys
from pathlib import Path
import pytest
import sqlite3
from datetime import datetime
from unittest.mock import patch
import tempfile
import csv

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_dsr_database import (
    get_current_version,
    increment_version,
    show_version_history,
    update_rate,
    update_description,
    batch_update_from_csv,
    add_new_code,
    view_code,
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
    db_path = temp_dir / "test_dsr.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create dsr_codes table
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

    # Insert sample data
    cursor.execute(
        """
        INSERT INTO dsr_codes VALUES
        ('15.12.2', 'civil', '15', '15.12', 'Excavation in ordinary soil', 'cum', 100.50, 'Vol 1', 45, 'excavation soil'),
        ('15.12.2', 'electrical', '15', '15.12', 'Cable laying', 'mtr', 50.00, 'Vol 2', 67, 'cable laying'),
        ('16.3.1', 'civil', '16', '16.3', 'PCC 1:2:4', 'sqm', 250.00, 'Vol 1', 89, 'concrete pcc'),
        ('1.1.1', 'civil', '1', '1.1', 'Site clearance', 'sqm', 15.00, 'Vol 1', 10, 'clearance site')
    """
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_csv(temp_dir):
    """Create sample CSV for batch updates."""
    csv_path = temp_dir / "updates.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "category", "field", "new_value"])
        writer.writerow(["15.12.2", "civil", "rate", "110.00"])
        writer.writerow(["16.3.1", "civil", "description", "Updated PCC description"])
        writer.writerow(["1.1.1", "civil", "rate", "17.50"])

    return csv_path


# =============================================================================
# Tests for get_current_version
# =============================================================================


def test_get_current_version_no_metadata(sample_db):
    """Test getting version when metadata table doesn't exist."""
    version = get_current_version(sample_db)

    # Should initialize to version 1
    assert version == 1

    # Verify metadata table was created
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM db_metadata WHERE key = 'version'")
    result = cursor.fetchone()
    assert result[0] == "1"
    conn.close()


def test_get_current_version_existing_metadata(sample_db):
    """Test getting version when metadata exists."""
    # Set version to 5
    conn = sqlite3.connect(sample_db)
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
        "INSERT INTO db_metadata VALUES ('version', '5', ?)", (datetime.now().isoformat(),)
    )
    conn.commit()
    conn.close()

    version = get_current_version(sample_db)
    assert version == 5


# =============================================================================
# Tests for increment_version
# =============================================================================


def test_increment_version_first_time(sample_db):
    """Test incrementing version for the first time."""
    new_version = increment_version(sample_db, "Initial version")

    assert new_version == 1

    # Verify version history
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT version, change_log FROM version_history WHERE version = 1")
    result = cursor.fetchone()
    assert result[0] == 1
    assert result[1] == "Initial version"
    conn.close()


def test_increment_version_subsequent(sample_db):
    """Test incrementing version when metadata exists."""
    # Initialize version
    increment_version(sample_db, "First change")

    # Increment again
    new_version = increment_version(sample_db, "Second change")

    assert new_version == 2


def test_increment_version_with_username(sample_db, monkeypatch):
    """Test that username is captured."""
    import getpass

    monkeypatch.setattr(getpass, "getuser", lambda: "testuser")

    increment_version(sample_db, "Test change")

    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT user FROM version_history WHERE version = 1")
    result = cursor.fetchone()
    assert result[0] == "testuser"
    conn.close()


def test_increment_version_username_error(sample_db, monkeypatch):
    """Test handling of getuser() error."""
    import getpass

    monkeypatch.setattr(getpass, "getuser", lambda: (_ for _ in ()).throw(Exception("No user")))

    new_version = increment_version(sample_db, "Test change")

    # Should still succeed with 'unknown' user
    assert new_version == 1

    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT user FROM version_history WHERE version = 1")
    result = cursor.fetchone()
    assert result[0] == "unknown"
    conn.close()


# =============================================================================
# Tests for show_version_history
# =============================================================================


def test_show_version_history_no_table(sample_db, capsys):
    """Test showing history when table doesn't exist."""
    show_version_history(sample_db)

    captured = capsys.readouterr()
    assert "No version history found" in captured.out


def test_show_version_history_with_data(sample_db, capsys):
    """Test showing version history with data."""
    increment_version(sample_db, "First change")
    increment_version(sample_db, "Second change")
    increment_version(sample_db, "Third change")

    show_version_history(sample_db, limit=2)

    captured = capsys.readouterr()
    assert "Database Version History" in captured.out
    assert "Current: v3" in captured.out
    assert "Third change" in captured.out
    assert "Second change" in captured.out


# =============================================================================
# Tests for update_rate
# =============================================================================


def test_update_rate_success(sample_db, capsys):
    """Test successful rate update."""
    result = update_rate(sample_db, "15.12.2", 120.00, category="civil")

    assert result is True

    captured = capsys.readouterr()
    assert "Update Details" in captured.out
    assert "Old Rate: ₹100.5" in captured.out
    assert "New Rate: ₹120.0" in captured.out
    assert "Rate updated successfully" in captured.out

    # Verify database was updated
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM dsr_codes WHERE code = '15.12.2' AND category = 'civil'")
    result = cursor.fetchone()
    assert result[0] == 120.00
    conn.close()


def test_update_rate_code_not_found(sample_db, capsys):
    """Test updating rate for non-existent code."""
    result = update_rate(sample_db, "99.99.99", 100.00, category="civil")

    assert result is False

    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_update_rate_multiple_matches_no_category(sample_db, capsys):
    """Test updating rate when multiple matches and no category specified."""
    result = update_rate(sample_db, "15.12.2", 150.00)

    assert result is False

    captured = capsys.readouterr()
    assert "Found 2 entries" in captured.out
    assert "Please specify --category" in captured.out


def test_update_rate_dry_run(sample_db, capsys):
    """Test dry-run mode for rate update."""
    original_rate = 100.50

    result = update_rate(sample_db, "15.12.2", 150.00, category="civil", dry_run=True)

    assert result is True

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "No changes made" in captured.out

    # Verify rate was NOT updated
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM dsr_codes WHERE code = '15.12.2' AND category = 'civil'")
    result = cursor.fetchone()
    assert result[0] == original_rate
    conn.close()


def test_update_rate_no_category(sample_db, capsys):
    """Test update rate when single match and no category specified."""
    result = update_rate(sample_db, "16.3.1", 275.00)

    assert result is True

    # Verify update
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM dsr_codes WHERE code = '16.3.1' AND category = 'civil'")
    result = cursor.fetchone()
    assert result[0] == 275.00
    conn.close()


# =============================================================================
# Tests for update_description
# =============================================================================


def test_update_description_success(sample_db, capsys):
    """Test successful description update."""
    new_desc = "Updated excavation description"

    result = update_description(sample_db, "15.12.2", new_desc, category="civil")

    assert result is True

    captured = capsys.readouterr()
    assert "Update Description" in captured.out
    assert new_desc in captured.out
    assert "Description updated successfully" in captured.out


def test_update_description_not_found(sample_db, capsys):
    """Test updating description for non-existent code."""
    result = update_description(sample_db, "99.99.99", "New desc", category="civil")

    assert result is False

    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_update_description_multiple_matches(sample_db, capsys):
    """Test updating description with multiple matches."""
    result = update_description(sample_db, "15.12.2", "New description")

    assert result is False

    captured = capsys.readouterr()
    assert "Multiple entries found" in captured.out


def test_update_description_dry_run(sample_db, capsys):
    """Test dry-run mode for description update."""
    result = update_description(
        sample_db, "16.3.1", "New PCC description", category="civil", dry_run=True
    )

    assert result is True

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out


# =============================================================================
# Tests for batch_update_from_csv
# =============================================================================


def test_batch_update_from_csv_success(sample_db, sample_csv, capsys):
    """Test successful batch update from CSV."""
    result = batch_update_from_csv(sample_db, sample_csv)

    assert result is True

    captured = capsys.readouterr()
    assert "Found 3 updates in CSV" in captured.out
    assert "3/3 updates successful" in captured.out

    # Verify updates
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM dsr_codes WHERE code = '15.12.2' AND category = 'civil'")
    assert cursor.fetchone()[0] == 110.00
    conn.close()


def test_batch_update_csv_not_found(temp_dir, sample_db, capsys):
    """Test batch update with non-existent CSV."""
    fake_csv = temp_dir / "nonexistent.csv"

    result = batch_update_from_csv(sample_db, fake_csv)

    assert result is False

    captured = capsys.readouterr()
    assert "CSV file not found" in captured.out


def test_batch_update_dry_run(sample_db, sample_csv, capsys):
    """Test dry-run mode for batch update."""
    result = batch_update_from_csv(sample_db, sample_csv, dry_run=True)

    assert result is True

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "Preview of changes" in captured.out
    assert "15.12.2" in captured.out


def test_batch_update_code_not_found(sample_db, temp_dir, capsys):
    """Test batch update with non-existent code in CSV."""
    csv_path = temp_dir / "bad_updates.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "category", "field", "new_value"])
        writer.writerow(["99.99.99", "civil", "rate", "999.00"])
        writer.writerow(["15.12.2", "civil", "rate", "110.00"])  # Valid one

    result = batch_update_from_csv(sample_db, csv_path)

    assert result is True

    captured = capsys.readouterr()
    assert "Skipping: 99.99.99" in captured.out
    assert "1/2 updates successful" in captured.out


def test_batch_update_error_handling(sample_db, temp_dir, capsys):
    """Test batch update error handling with invalid data."""
    csv_path = temp_dir / "error_updates.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "category", "field", "new_value"])
        writer.writerow(["15.12.2", "civil", "rate", "invalid_number"])  # Invalid rate

    result = batch_update_from_csv(sample_db, csv_path)

    # Should still return True but show errors
    captured = capsys.readouterr()
    assert "Error updating" in captured.out or "0/1 updates successful" in captured.out


# =============================================================================
# Tests for add_new_code
# =============================================================================


def test_add_new_code_success(sample_db, capsys):
    """Test successfully adding a new code."""
    code_data = {
        "code": "20.1.1",
        "category": "civil",
        "description": "New work item",
        "unit": "nos",
        "rate": 500.00,
        "chapter": "20",
        "section": "20.1",
    }

    result = add_new_code(sample_db, code_data)

    assert result is True

    captured = capsys.readouterr()
    assert "Adding new code" in captured.out
    assert "20.1.1" in captured.out
    assert "New code added successfully" in captured.out

    # Verify code was added
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT code, rate FROM dsr_codes WHERE code = '20.1.1' AND category = 'civil'")
    result = cursor.fetchone()
    assert result[0] == "20.1.1"
    assert result[1] == 500.00
    conn.close()


def test_add_new_code_missing_fields(sample_db, capsys):
    """Test adding code with missing required fields."""
    code_data = {
        "code": "20.1.1",
        "category": "civil",
        # Missing description, unit, rate
    }

    result = add_new_code(sample_db, code_data)

    assert result is False

    captured = capsys.readouterr()
    assert "Missing required field" in captured.out


def test_add_new_code_already_exists(sample_db, capsys):
    """Test adding code that already exists."""
    code_data = {
        "code": "15.12.2",
        "category": "civil",
        "description": "Duplicate",
        "unit": "cum",
        "rate": 100.00,
    }

    result = add_new_code(sample_db, code_data)

    assert result is False

    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_add_new_code_dry_run(sample_db, capsys):
    """Test dry-run mode for adding new code."""
    code_data = {
        "code": "20.1.1",
        "category": "civil",
        "description": "New work item",
        "unit": "nos",
        "rate": 500.00,
    }

    result = add_new_code(sample_db, code_data, dry_run=True)

    assert result is True

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out

    # Verify code was NOT added
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM dsr_codes WHERE code = '20.1.1'")
    result = cursor.fetchone()
    assert result is None
    conn.close()


# =============================================================================
# Tests for view_code
# =============================================================================


def test_view_code_success(sample_db, capsys):
    """Test viewing code details."""
    view_code(sample_db, "15.12.2", category="civil")

    captured = capsys.readouterr()
    assert "Found 1 entry" in captured.out
    assert "15.12.2" in captured.out
    assert "Excavation in ordinary soil" in captured.out
    assert "₹100.5" in captured.out


def test_view_code_multiple_matches(sample_db, capsys):
    """Test viewing code with multiple category matches."""
    view_code(sample_db, "15.12.2")

    captured = capsys.readouterr()
    assert "Found 2 entry(ies)" in captured.out
    assert "civil" in captured.out
    assert "electrical" in captured.out


def test_view_code_not_found(sample_db, capsys):
    """Test viewing non-existent code."""
    view_code(sample_db, "99.99.99")

    captured = capsys.readouterr()
    assert "not found" in captured.out


# =============================================================================
# Tests for parse_arguments
# =============================================================================


def test_parse_arguments_database_required():
    """Test that database argument is required."""
    with patch("sys.argv", ["update_dsr_database.py"]):
        with pytest.raises(SystemExit):
            parse_arguments()


def test_parse_arguments_show_version():
    """Test parsing --show-version argument."""
    with patch("sys.argv", ["update_dsr_database.py", "-d", "test.db", "--show-version"]):
        args = parse_arguments()
        assert args.show_version is True
        assert args.database == Path("test.db")


def test_parse_arguments_update_rate():
    """Test parsing update rate arguments."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            "test.db",
            "--update-rate",
            "15.12.2",
            "--new-rate",
            "150.00",
            "--category",
            "civil",
        ],
    ):
        args = parse_arguments()
        assert args.update_rate == "15.12.2"
        assert args.new_rate == 150.00
        assert args.category == "civil"


def test_parse_arguments_batch_update():
    """Test parsing batch update argument."""
    with patch(
        "sys.argv", ["update_dsr_database.py", "-d", "test.db", "--batch-update", "updates.csv"]
    ):
        args = parse_arguments()
        assert args.batch_update == Path("updates.csv")


# =============================================================================
# Tests for main() function
# =============================================================================


def test_main_database_not_found(capsys):
    """Test main with non-existent database."""
    with patch("sys.argv", ["update_dsr_database.py", "-d", "nonexistent.db"]):
        main()

        captured = capsys.readouterr()
        assert "Database not found" in captured.out


def test_main_show_version(sample_db, capsys):
    """Test main with --show-version."""
    with patch("sys.argv", ["update_dsr_database.py", "-d", str(sample_db), "--show-version"]):
        main()

        captured = capsys.readouterr()
        assert (
            "Database Version History" in captured.out or "No version history found" in captured.out
        )


def test_main_view_code(sample_db, capsys):
    """Test main with --view."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            str(sample_db),
            "--view",
            "15.12.2",
            "--category",
            "civil",
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "15.12.2" in captured.out


def test_main_update_rate(sample_db, capsys):
    """Test main with --update-rate."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            str(sample_db),
            "--update-rate",
            "15.12.2",
            "--new-rate",
            "150.00",
            "--category",
            "civil",
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "Rate updated successfully" in captured.out


def test_main_update_description(sample_db, capsys):
    """Test main with --update-description."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            str(sample_db),
            "--update-description",
            "16.3.1",
            "--new-description",
            "Updated PCC",
            "--category",
            "civil",
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "Description updated successfully" in captured.out


def test_main_batch_update(sample_db, sample_csv, capsys):
    """Test main with --batch-update."""
    with patch(
        "sys.argv",
        ["update_dsr_database.py", "-d", str(sample_db), "--batch-update", str(sample_csv)],
    ):
        main()

        captured = capsys.readouterr()
        assert "updates successful" in captured.out


def test_main_add_code(sample_db, capsys):
    """Test main with --add-code."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            str(sample_db),
            "--add-code",
            "--code",
            "20.1.1",
            "--category",
            "civil",
            "--description",
            "New work",
            "--unit",
            "nos",
            "--rate",
            "500.00",
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "New code added successfully" in captured.out


def test_main_add_code_missing_fields(sample_db, capsys):
    """Test main with --add-code but missing fields."""
    with patch(
        "sys.argv",
        [
            "update_dsr_database.py",
            "-d",
            str(sample_db),
            "--add-code",
            "--code",
            "20.1.1",
            # Missing other required fields
        ],
    ):
        main()

        captured = capsys.readouterr()
        assert "Missing required fields" in captured.out


def test_main_no_action(sample_db, capsys):
    """Test main with no action specified."""
    with patch("sys.argv", ["update_dsr_database.py", "-d", str(sample_db)]):
        main()

        captured = capsys.readouterr()
        assert "No action specified" in captured.out
        assert "Use --help" in captured.out
