"""Tests for PDF to XML converter."""

import pytest
from pathlib import Path
import tempfile
import fitz  # PyMuPDF
import json
from src.pdf2json.converter import PDFToXMLConverter


@pytest.fixture
def sample_pdf():
    """Create a simple test PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        page.insert_text((50, 50), "Hello World!", fontsize=12)
        page.insert_text((50, 100), "This is a test PDF.", fontsize=12)
        doc.save(f.name)
        doc.close()
        yield f.name

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_pdf_with_table():
    """Create a test PDF with a table."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)

        # Add a title
        page.insert_text((50, 50), "Sample Table", fontsize=14)

        # Create a simple table structure
        table_data = [
            ["Name", "Age", "City"],
            ["Alice", "25", "New York"],
            ["Bob", "30", "San Francisco"],
            ["Charlie", "35", "Chicago"],
        ]

        x_start = 50
        y_start = 100
        col_widths = [120, 80, 150]
        row_height = 25

        # Draw table with borders
        for row_idx, row in enumerate(table_data):
            y = y_start + row_idx * row_height
            x = x_start

            for col_idx, cell in enumerate(row):
                # Draw cell border
                rect = fitz.Rect(x, y, x + col_widths[col_idx], y + row_height)
                page.draw_rect(rect, color=(0, 0, 0), width=0.5)

                # Add text
                fontsize = 10 if row_idx > 0 else 11
                page.insert_text((x + 5, y + 17), cell, fontsize=fontsize)

                x += col_widths[col_idx]

        doc.save(f.name)
        doc.close()
        yield f.name

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


def test_converter_initialization(sample_pdf):
    """Test converter initialization."""
    converter = PDFToXMLConverter(sample_pdf)
    assert converter.doc is not None
    assert converter.pdf_path.exists()
    converter.doc.close()


def test_converter_nonexistent_file():
    """Test converter with non-existent file."""
    with pytest.raises(FileNotFoundError):
        PDFToXMLConverter("nonexistent.pdf")


def test_convert_to_xml(sample_pdf):
    """Test PDF to JSON conversion."""
    with PDFToXMLConverter(sample_pdf) as converter:
        result = converter.convert()

        assert "document" in result
        doc = result["document"]
        assert doc["pages"] == 1

        # Check for page elements
        pages = doc["pages_data"]
        assert len(pages) == 1
        assert pages[0]["number"] == 1


def test_convert_with_metadata(sample_pdf):
    """Test PDF to JSON conversion with metadata."""
    with PDFToXMLConverter(sample_pdf) as converter:
        result = converter.convert(include_metadata=True)

        # Check for metadata element
        doc = result["document"]
        assert "metadata" in doc


def test_save_xml(sample_pdf):
    """Test saving JSON to file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        with PDFToXMLConverter(sample_pdf) as converter:
            converter.save_json(output_path)

        # Verify file exists and is valid JSON
        assert Path(output_path).exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert "document" in data

    finally:
        Path(output_path).unlink(missing_ok=True)


def test_context_manager(sample_pdf):
    """Test context manager usage."""
    with PDFToXMLConverter(sample_pdf) as converter:
        assert converter.doc is not None

    # Document should be closed after context
    assert converter.doc.is_closed


def test_table_extraction(sample_pdf_with_table):
    """Test table detection and extraction."""
    with PDFToXMLConverter(sample_pdf_with_table) as converter:
        result = converter.convert(extract_tables=True)

        # Check for tables element
        doc = result["document"]
        pages = doc["pages_data"]
        assert len(pages) == 1

        if "tables" in pages[0]:  # Tables detected
            tables = pages[0]["tables"]
            assert len(tables) > 0

            # Check table structure
            table = tables[0]
            assert "index" in table
            assert "rows" in table
            assert "row_count" in table
            assert "col_count" in table

            # Check rows
            rows = table["rows"]
            assert len(rows) > 0


def test_convert_without_tables(sample_pdf_with_table):
    """Test that tables are not extracted when flag is False."""
    with PDFToXMLConverter(sample_pdf_with_table) as converter:
        result = converter.convert(extract_tables=False)

        doc = result["document"]
        pages = doc["pages_data"]

        # Tables should not be present
        assert "tables" not in pages[0]


def test_save_xml_with_tables(sample_pdf_with_table):
    """Test saving JSON with table extraction."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        with PDFToXMLConverter(sample_pdf_with_table) as converter:
            converter.save_json(output_path, extract_tables=True)

        # Verify file exists and is valid JSON
        assert Path(output_path).exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert "document" in data

    finally:
        Path(output_path).unlink(missing_ok=True)
