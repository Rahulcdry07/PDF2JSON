"""
Additional comprehensive tests for helpers.py to achieve >95% coverage.
Focuses on quick_convert, quick_match, batch_convert_pdfs, and other utility functions.
"""

import pytest
import sys
import sqlite3
import tempfile
import json
from pathlib import Path
import shutil

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf2json.helpers import (
    DSRMatcherHelper,
    quick_convert,
    quick_match,
    batch_convert_pdfs,
    validate_dsr_database,
    get_version_info,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF file for testing."""
    import fitz
    
    pdf_file = temp_dir / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test PDF content for conversion")
    doc.save(str(pdf_file))
    doc.close()
    
    return pdf_file


@pytest.fixture
def sample_dsr_db(temp_dir):
    """Create a sample DSR database with dsr_codes table (for quick_match tests)."""
    db_path = temp_dir / "test_dsr.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
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
    """)
    
    cursor.executemany("""
        INSERT INTO dsr_codes (code, chapter, section, description, unit, rate, volume, page, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ("1.1", "Chapter 1", "Section 1", "Excavation in ordinary soil", "cum", 450.00, "Vol I", 10, "excavation soil"),
        ("1.2", "1.2", "Section 1", "Brickwork in cement mortar", "sqm", 550.00, "Vol I", 15, "brickwork cement"),
        ("2.1", "Chapter 2", "Section 1", "PCC 1:2:4", "cum", 6500.00, "Vol I", 20, "pcc concrete"),
    ])
    
    conn.commit()
    conn.close()
    
    return db_path


@pytest.fixture
def sample_dsr_rates_db(temp_dir):
    """Create a sample DSR database with dsr_rates table (for DSRMatcherHelper tests)."""
    db_path = temp_dir / "test_dsr_rates.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE dsr_rates (
            code TEXT,
            clean_code TEXT,
            description TEXT,
            unit TEXT,
            rate REAL,
            category TEXT,
            chapter_no INTEGER,
            PRIMARY KEY (code, category)
        )
    """)
    
    cursor.executemany("""
        INSERT INTO dsr_rates (code, clean_code, description, unit, rate, category, chapter_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("1.1", "1.1", "Excavation in ordinary soil", "cum", 450.00, "civil", 1),
        ("1.2", "1.2", "Brickwork in cement mortar", "sqm", 550.00, "civil", 1),
        ("2.1", "2.1", "PCC 1:2:4", "cum", 6500.00, "civil", 2),
    ])
    
    conn.commit()
    conn.close()
    
    return db_path


@pytest.fixture
def sample_input_json(temp_dir):
    """Create a sample structured input JSON file."""
    input_file = temp_dir / "input.json"
    data = {
        "metadata": {
            "type": "input_items",
            "version": "1.0"
        },
        "items": [
            {
                "dsr_code": "1.1",
                "clean_dsr_code": "1.1",
                "description": "Excavation work",
                "quantity": 100,
                "unit": "cum"
            }
        ]
    }
    
    with open(input_file, "w") as f:
        json.dump(data, f)
    
    return input_file


# =============================================================================
# Tests for DSRMatcherHelper advanced functionality
# =============================================================================

class TestDSRMatcherHelperAdvanced:
    """Additional tests for DSRMatcherHelper class."""
    
    def test_context_manager(self, sample_dsr_rates_db):
        """Test using DSRMatcherHelper as context manager."""
        with DSRMatcherHelper(sample_dsr_rates_db) as matcher:
            assert matcher.conn is not None
            stats = matcher.get_statistics()
            assert stats["total_codes"] == 3
        
        # Connection should be closed after context exit
        # (we can't easily test this without accessing private state)
    
    def test_search_by_code_clean_code(self, sample_dsr_rates_db):
        """Test searching by clean code."""
        matcher = DSRMatcherHelper(sample_dsr_rates_db)
        
        result = matcher.search_by_code("1.1")
        
        assert result is not None
        assert result["code"] == "1.1"
        assert "Excavation" in result["description"]
        
        matcher.close()
    
    def test_search_by_code_with_whitespace(self, sample_dsr_rates_db):
        """Test searching with whitespace in code."""
        matcher = DSRMatcherHelper(sample_dsr_rates_db)
        
        result = matcher.search_by_code("  1.1  ")
        
        assert result is not None
        assert result["code"] == "1.1"
        
        matcher.close()
    
    def test_search_by_description_multiple_results(self, sample_dsr_rates_db):
        """Test searching by description with multiple results."""
        matcher = DSRMatcherHelper(sample_dsr_rates_db)
        
        results = matcher.search_by_description("cement", limit=5)
        
        # Should find "Brickwork in cement mortar" and "PCC" if it contains cement
        assert len(results) >= 1
        assert any("cement" in r["description"].lower() for r in results)
        
        matcher.close()
    
    def test_search_by_description_with_limit(self, sample_dsr_rates_db):
        """Test that limit parameter works."""
        matcher = DSRMatcherHelper(sample_dsr_rates_db)
        
        results = matcher.search_by_description("", limit=2)
        
        assert len(results) <= 2
        
        matcher.close()
    
    def test_get_statistics_with_categories(self, sample_dsr_rates_db):
        """Test getting statistics with category information."""
        matcher = DSRMatcherHelper(sample_dsr_rates_db)
        
        stats = matcher.get_statistics()
        
        assert stats["total_codes"] == 3
        assert stats["categories"] >= 1  # At least civil category
        assert stats["chapters"] >= 1  # At least 1 chapter
        assert "database" in stats
        
        matcher.close()


# =============================================================================
# Tests for quick_convert
# =============================================================================

class TestQuickConvert:
    """Tests for quick_convert utility function."""
    
    def test_quick_convert_with_output_path(self, sample_pdf, temp_dir):
        """Test quick convert with specified output path."""
        output_file = temp_dir / "output.json"
        
        data = quick_convert(sample_pdf, output_file)
        
        assert output_file.exists()
        assert "document" in data
        assert data["document"]["pages"] > 0
    
    def test_quick_convert_auto_output(self, sample_pdf):
        """Test quick convert with auto-generated output path."""
        data = quick_convert(sample_pdf)
        
        expected_output = sample_pdf.with_suffix(".json")
        assert expected_output.exists()
        assert "document" in data
        
        # Cleanup
        expected_output.unlink()
    
    def test_quick_convert_with_kwargs(self, sample_pdf, temp_dir):
        """Test quick convert with additional converter options."""
        output_file = temp_dir / "output.json"
        
        data = quick_convert(sample_pdf, output_file, include_metadata=True, extract_tables=True)
        
        assert output_file.exists()
        assert "metadata" in data["document"]  # Should have metadata
    
    def test_quick_convert_path_objects(self, sample_pdf, temp_dir):
        """Test quick convert with Path objects."""
        output_file = temp_dir / "output.json"
        
        # Both should be Path objects
        assert isinstance(sample_pdf, Path)
        assert isinstance(output_file, Path)
        
        data = quick_convert(sample_pdf, output_file)
        
        assert output_file.exists()


# =============================================================================
# Tests for quick_match
# =============================================================================

class TestQuickMatch:
    """Tests for quick_match utility function."""
    
    def test_quick_match_with_list(self, sample_dsr_db):
        """Test quick match with list of items."""
        items = [
            {
                "dsr_code": "1.1",
                "clean_dsr_code": "1.1",
                "description": "Excavation work",
                "quantity": 100,
                "unit": "cum"
            }
        ]
        
        results = quick_match(items, db_path=sample_dsr_db)
        
        assert len(results) > 0
        assert results[0]["dsr_code"] == "1.1"
    
    def test_quick_match_with_json_file(self, sample_input_json, sample_dsr_db):
        """Test quick match with JSON file input."""
        results = quick_match(sample_input_json, db_path=sample_dsr_db)
        
        assert len(results) > 0
    
    def test_quick_match_string_path(self, sample_input_json, sample_dsr_db):
        """Test quick match with string path."""
        results = quick_match(str(sample_input_json), db_path=str(sample_dsr_db))
        
        assert len(results) > 0
    
    def test_quick_match_custom_threshold(self, sample_dsr_db):
        """Test quick match with custom similarity threshold."""
        items = [
            {
                "dsr_code": "1.1",
                "description": "Different description",
                "quantity": 100
            }
        ]
        
        results = quick_match(items, db_path=sample_dsr_db, similarity_threshold=0.1)
        
        assert len(results) > 0
    
    def test_quick_match_auto_detect_db(self, temp_dir, sample_dsr_db, monkeypatch):
        """Test auto-detection of database."""
        # Create database in expected location
        ref_dir = temp_dir / "data" / "reference"
        ref_dir.mkdir(parents=True)
        target_db = ref_dir / "DSR_combined.db"
        shutil.copy(sample_dsr_db, target_db)
        
        # Change to temp directory
        monkeypatch.chdir(temp_dir)
        
        items = [{"dsr_code": "1.1", "description": "Excavation", "quantity": 100}]
        
        results = quick_match(items)  # No db_path specified
        
        assert len(results) > 0
    
    def test_quick_match_no_db_found(self, temp_dir, monkeypatch):
        """Test error when no database is found."""
        monkeypatch.chdir(temp_dir)
        
        items = [{"dsr_code": "1.1", "description": "Test", "quantity": 100}]
        
        with pytest.raises(FileNotFoundError, match="Could not auto-detect"):
            quick_match(items)


# =============================================================================
# Tests for batch_convert_pdfs
# =============================================================================

class TestBatchConvertPDFs:
    """Tests for batch_convert_pdfs utility function."""
    
    def test_batch_convert_same_directory(self, temp_dir):
        """Test batch conversion in same directory."""
        import fitz
        
        # Create multiple PDFs
        for i in range(3):
            pdf_file = temp_dir / f"test{i}.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), f"Test PDF {i}")
            doc.save(str(pdf_file))
            doc.close()
        
        converted = batch_convert_pdfs(temp_dir)
        
        assert len(converted) == 3
        assert all(f.suffix == ".json" for f in converted)
        assert all(f.exists() for f in converted)
    
    def test_batch_convert_different_directory(self, temp_dir):
        """Test batch conversion to different output directory."""
        import fitz
        
        # Create input PDFs
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        for i in range(2):
            pdf_file = input_dir / f"doc{i}.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), f"Document {i}")
            doc.save(str(pdf_file))
            doc.close()
        
        output_dir = temp_dir / "output"
        
        converted = batch_convert_pdfs(input_dir, output_dir)
        
        assert len(converted) == 2
        assert all(f.parent == output_dir for f in converted)
        assert output_dir.exists()
    
    def test_batch_convert_with_options(self, temp_dir):
        """Test batch conversion with converter options."""
        import fitz
        
        pdf_file = temp_dir / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test")
        doc.save(str(pdf_file))
        doc.close()
        
        converted = batch_convert_pdfs(temp_dir, indent=2)
        
        assert len(converted) == 1
        # Check that output has indentation
        with open(converted[0]) as f:
            content = f.read()
            assert "  " in content
    
    def test_batch_convert_empty_directory(self, temp_dir):
        """Test batch conversion with no PDFs."""
        converted = batch_convert_pdfs(temp_dir)
        
        assert len(converted) == 0
    
    def test_batch_convert_creates_output_dir(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        import fitz
        
        pdf_file = temp_dir / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test")
        doc.save(str(pdf_file))
        doc.close()
        
        output_dir = temp_dir / "nonexistent" / "output"
        
        converted = batch_convert_pdfs(temp_dir, output_dir)
        
        assert output_dir.exists()
        assert len(converted) == 1


# =============================================================================
# Tests for validate_dsr_database
# =============================================================================

class TestValidateDSRDatabase:
    """Tests for validate_dsr_database function."""
    
    def test_validate_valid_database(self, sample_dsr_rates_db):
        """Test validating a valid database."""
        result = validate_dsr_database(sample_dsr_rates_db)
        
        assert result["valid"] is True
        assert result["total_codes"] == 3
        assert result["null_rates"] == 0
        assert "code" in result["columns"]
        assert "rate" in result["columns"]
    
    def test_validate_nonexistent_database(self, temp_dir):
        """Test validating non-existent database."""
        result = validate_dsr_database(temp_dir / "nonexistent.db")
        
        assert result["valid"] is False
        assert "not found" in result["error"]
    
    def test_validate_database_missing_table(self, temp_dir):
        """Test database with missing table."""
        db_path = temp_dir / "bad.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE wrong_table (id INTEGER)")
        conn.commit()
        conn.close()
        
        result = validate_dsr_database(db_path)
        
        assert result["valid"] is False
        assert "not found" in result["error"]
    
    def test_validate_database_missing_columns(self, temp_dir):
        """Test database with missing required columns."""
        db_path = temp_dir / "incomplete.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE dsr_rates (code TEXT)")  # Missing required columns
        conn.commit()
        conn.close()
        
        result = validate_dsr_database(db_path)
        
        assert result["valid"] is False
        assert "Missing columns" in result["error"]
    
    def test_validate_database_with_null_rates(self, temp_dir):
        """Test database with some null rates."""
        db_path = temp_dir / "nulls.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE dsr_rates (
                code TEXT, description TEXT, rate REAL, unit TEXT
            )
        """)
        cursor.execute("INSERT INTO dsr_rates VALUES ('1.1', 'Test', NULL, 'cum')")
        cursor.execute("INSERT INTO dsr_rates VALUES ('1.2', 'Test2', 450.0, 'sqm')")
        
        conn.commit()
        conn.close()
        
        result = validate_dsr_database(db_path)
        
        assert result["valid"] is True
        assert result["null_rates"] == 1
    
    def test_validate_database_exception_handling(self, temp_dir):
        """Test validation with corrupted database."""
        db_path = temp_dir / "corrupt.db"
        
        # Create invalid database file
        with open(db_path, "w") as f:
            f.write("This is not a valid SQLite database")
        
        result = validate_dsr_database(db_path)
        
        assert result["valid"] is False
        assert "error" in result


# =============================================================================
# Tests for get_version_info
# =============================================================================

class TestGetVersionInfo:
    """Tests for get_version_info function."""
    
    def test_get_version_info_structure(self):
        """Test that version info has correct structure."""
        info = get_version_info()
        
        assert "pdf2json" in info
        assert "python" in info
        assert "pymupdf" in info
        assert "flask" in info
    
    def test_get_version_info_python_version(self):
        """Test that Python version is reported."""
        info = get_version_info()
        
        assert isinstance(info["python"], str)
        assert len(info["python"]) > 0
        # Should be in format like "3.8.10"
        assert "." in info["python"]
    
    def test_get_version_info_pymupdf(self):
        """Test that PyMuPDF version is reported."""
        info = get_version_info()
        
        # PyMuPDF should be installed in test environment
        assert info["pymupdf"] != "unknown"
    
    def test_get_version_info_pdf2json_version(self):
        """Test that pdf2json version is reported."""
        info = get_version_info()
        
        # Should have either detected version or fallback
        assert isinstance(info["pdf2json"], str)
        assert len(info["pdf2json"]) > 0
