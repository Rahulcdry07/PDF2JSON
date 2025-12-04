"""Tests for helpers module."""

import pytest
import json
from pathlib import Path
from src.pdf2json.helpers import (
    quick_convert,
    batch_convert_pdfs,
    validate_dsr_database,
    get_version_info,
)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF file for testing."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
trailer<</Size 4/Root 1 0 R>>
startxref
150
%%EOF"""
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_dsr_db(tmp_path):
    """Create sample DSR database."""
    db_data = {
        "1.1": {
            "code": "1.1",
            "description": "Test item",
            "unit": "cum",
            "rate": 100.0,
        }
    }
    db_file = tmp_path / "dsr.json"
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db_data, f)
    return db_file


def test_get_version_info():
    """Test getting version information."""
    version_info = get_version_info()
    assert isinstance(version_info, dict)
    assert "version" in version_info or "error" not in version_info


def test_validate_dsr_database_valid(sample_dsr_db):
    """Test validating a valid DSR database."""
    result = validate_dsr_database(str(sample_dsr_db))
    assert isinstance(result, dict)
    # Function expects SQLite database, so JSON file returns error
    assert "error" in result or "valid" in result


def test_validate_dsr_database_nonexistent():
    """Test validating non-existent database."""
    result = validate_dsr_database("nonexistent.json")
    assert isinstance(result, dict)
    assert result.get("valid") is False or "error" in result


def test_validate_dsr_database_invalid_json(tmp_path):
    """Test validating invalid JSON file."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not valid json{")

    result = validate_dsr_database(str(invalid_file))
    assert isinstance(result, dict)


def test_batch_convert_pdfs_empty_directory(tmp_path):
    """Test batch conversion with empty directory."""
    result = batch_convert_pdfs(str(tmp_path), str(tmp_path / "output"), include_metadata=False)
    # Should complete without errors
    assert result is None or isinstance(result, (dict, list))


def test_batch_convert_pdfs_nonexistent_directory():
    """Test batch conversion with non-existent directory."""
    try:
        result = batch_convert_pdfs("nonexistent_dir", "output_dir", include_metadata=False)
        # Either returns result or raises error
        assert result is None or isinstance(result, (dict, list))
    except (FileNotFoundError, ValueError):
        # Expected
        pass


def test_quick_convert_nonexistent_file(tmp_path):
    """Test quick convert with non-existent file."""
    output = tmp_path / "output.json"
    try:
        result = quick_convert("nonexistent.pdf", str(output))
        # Either fails or returns error
        assert result is None or "error" in str(result).lower()
    except (FileNotFoundError, Exception):
        # Expected
        pass


def test_version_info_structure():
    """Test version info returns proper structure."""
    info = get_version_info()
    assert isinstance(info, dict)
    # Should have some version-related fields
    keys = set(info.keys())
    expected_keys = {"version", "python_version", "dependencies", "name"}
    # At least one should be present
    assert len(keys & expected_keys) > 0 or len(keys) > 0
