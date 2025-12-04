#!/usr/bin/env python3
"""Expanded tests for PDF converter to achieve >95% coverage."""

import pytest
from pathlib import Path
import tempfile
import fitz  # PyMuPDF
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf2json.converter import PDFToXMLConverter, PDFConversionError


@pytest.fixture
def sample_pdf():
    """Create a simple test PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), "Hello World!", fontsize=12)
        page.insert_text((50, 100), "Test content", fontsize=12)
        doc.save(f.name)
        doc.close()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def multi_page_pdf():
    """Create a multi-page PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 50), f"Page {i+1}", fontsize=12)
        doc.save(f.name)
        doc.close()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def pdf_with_special_chars():
    """Create PDF with special/invalid XML characters."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        # Add text with various Unicode characters
        page.insert_text((50, 50), "Special: \u0009 \u000A \u000D", fontsize=12)
        page.insert_text((50, 70), "Emoji: 😊 🎉", fontsize=12)
        doc.save(f.name)
        doc.close()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


def test_is_valid_xml_char():
    """Test XML character validation."""
    converter = PDFToXMLConverter.__new__(PDFToXMLConverter)

    # Valid characters
    assert converter._is_valid_xml_char(" ")  # 0x20
    assert converter._is_valid_xml_char("A")  # 0x41
    assert converter._is_valid_xml_char("\t")  # 0x09
    assert converter._is_valid_xml_char("\n")  # 0x0A
    assert converter._is_valid_xml_char("\r")  # 0x0D

    # Invalid characters
    assert not converter._is_valid_xml_char("\x00")  # 0x00
    assert not converter._is_valid_xml_char("\x01")  # 0x01
    assert not converter._is_valid_xml_char("\x08")  # 0x08


def test_convert_file_static_method(sample_pdf):
    """Test the static convert_file method."""
    output_path = Path(tempfile.mktemp(suffix=".json"))

    try:
        result = PDFToXMLConverter.convert_file(
            sample_pdf, output_path, include_metadata=True, extract_tables=False
        )

        # Returns Path, not data
        assert isinstance(result, Path)
        assert result.exists()

        # Verify saved file
        with open(result) as f:
            saved_data = json.load(f)
        assert "document" in saved_data
    finally:
        output_path.unlink(missing_ok=True)


def test_convert_file_no_output(sample_pdf):
    """Test convert_file without output path."""
    pytest.skip("output_path is required parameter")


def test_page_count_property(multi_page_pdf):
    """Test page_count property."""
    with PDFToXMLConverter(multi_page_pdf) as converter:
        assert converter.page_count == 3


def test_metadata_property(sample_pdf):
    """Test metadata property."""
    with PDFToXMLConverter(sample_pdf) as converter:
        metadata = converter.metadata
        assert isinstance(metadata, dict)


def test_get_page_text(sample_pdf):
    """Test getting text from specific page."""
    with PDFToXMLConverter(sample_pdf) as converter:
        text = converter.get_page_text(1)  # 1-indexed
        assert isinstance(text, str)
        assert "Hello World" in text or "Test content" in text


def test_get_page_text_invalid_page(sample_pdf):
    """Test get_page_text with invalid page number."""
    with PDFToXMLConverter(sample_pdf) as converter:
        with pytest.raises(ValueError, match="Invalid page"):
            converter.get_page_text(999)

        with pytest.raises(ValueError, match="Invalid page"):
            converter.get_page_text(-1)


def test_get_page_tables(sample_pdf):
    """Test getting tables from specific page."""
    with PDFToXMLConverter(sample_pdf) as converter:
        tables = converter.get_page_tables(1)  # 1-indexed
        assert isinstance(tables, list)


def test_get_page_tables_invalid_page(sample_pdf):
    """Test get_page_tables with invalid page number."""
    with PDFToXMLConverter(sample_pdf) as converter:
        with pytest.raises(ValueError, match="Invalid page"):
            converter.get_page_tables(999)


def test_convert_page(sample_pdf):
    """Test converting single page."""
    with PDFToXMLConverter(sample_pdf) as converter:
        page_data = converter.convert_page(1, extract_tables=False)  # 1-indexed

        assert isinstance(page_data, dict)
        assert "number" in page_data
        assert page_data["number"] == 1


def test_convert_page_with_tables(sample_pdf):
    """Test converting single page with table extraction."""
    with PDFToXMLConverter(sample_pdf) as converter:
        page_data = converter.convert_page(1, extract_tables=True)  # 1-indexed

        assert isinstance(page_data, dict)
        assert "number" in page_data


def test_convert_page_invalid_page(sample_pdf):
    """Test convert_page with invalid page number."""
    with PDFToXMLConverter(sample_pdf) as converter:
        with pytest.raises(ValueError, match="Invalid page"):
            converter.convert_page(999)


def test_save_json_with_pretty_print(sample_pdf):
    """Test saving JSON with pretty printing."""
    output_path = Path(tempfile.mktemp(suffix=".json"))

    try:
        with PDFToXMLConverter(sample_pdf) as converter:
            converter.save_json(output_path, indent=2)

        assert output_path.exists()

        # Check file is formatted with indentation
        content = output_path.read_text()
        assert "  " in content  # Should have indentation
    finally:
        output_path.unlink(missing_ok=True)


def test_save_json_no_pretty_print(sample_pdf):
    """Test saving JSON without pretty printing."""
    output_path = Path(tempfile.mktemp(suffix=".json"))

    try:
        with PDFToXMLConverter(sample_pdf) as converter:
            converter.save_json(output_path, indent=None)

        assert output_path.exists()
    finally:
        output_path.unlink(missing_ok=True)


def test_close_method(sample_pdf):
    """Test explicit close method."""
    converter = PDFToXMLConverter(sample_pdf)
    assert not converter.doc.is_closed

    converter.close()
    assert converter.doc.is_closed


def test_corrupted_pdf():
    """Test handling corrupted PDF file."""
    corrupted_path = Path(tempfile.mktemp(suffix=".pdf"))
    corrupted_path.write_text("This is not a PDF")

    try:
        with pytest.raises(PDFConversionError, match="Failed to open PDF"):
            PDFToXMLConverter(corrupted_path)
    finally:
        corrupted_path.unlink(missing_ok=True)


def test_convert_with_special_chars(pdf_with_special_chars):
    """Test converting PDF with special characters."""
    with PDFToXMLConverter(pdf_with_special_chars) as converter:
        result = converter.convert()

        assert "document" in result
        # Should handle special characters gracefully


def test_multi_page_conversion(multi_page_pdf):
    """Test converting multi-page PDF."""
    with PDFToXMLConverter(multi_page_pdf) as converter:
        result = converter.convert()

        doc = result["document"]
        assert doc["pages"] == 3
        assert len(doc["pages_data"]) == 3

        # Verify page numbers
        for i, page in enumerate(doc["pages_data"]):
            assert page["number"] == i + 1


def test_convert_all_pages_with_tables(multi_page_pdf):
    """Test converting all pages with table extraction."""
    with PDFToXMLConverter(multi_page_pdf) as converter:
        result = converter.convert(extract_tables=True)

        doc = result["document"]
        assert len(doc["pages_data"]) == 3


def test_empty_pdf():
    """Test handling PDF with no content."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # Empty page
        doc.save(f.name)
        doc.close()
        pdf_path = f.name

    try:
        with PDFToXMLConverter(pdf_path) as converter:
            result = converter.convert()

            assert "document" in result
            assert result["document"]["pages"] == 1
    finally:
        Path(pdf_path).unlink(missing_ok=True)


def test_detect_tables_empty_page():
    """Test table detection on empty page."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        doc.save(f.name)
        doc.close()
        pdf_path = f.name

    try:
        with PDFToXMLConverter(pdf_path) as converter:
            tables = converter._detect_tables(converter.doc[0])
            assert isinstance(tables, list)
    finally:
        Path(pdf_path).unlink(missing_ok=True)


def test_path_object_initialization(sample_pdf):
    """Test initialization with Path object."""
    path_obj = Path(sample_pdf)
    converter = PDFToXMLConverter(path_obj)

    assert converter.pdf_path == path_obj
    converter.close()


def test_string_path_initialization(sample_pdf):
    """Test initialization with string path."""
    converter = PDFToXMLConverter(sample_pdf)

    assert isinstance(converter.pdf_path, Path)
    converter.close()


def test_convert_file_with_all_options(sample_pdf):
    """Test convert_file with all options enabled."""
    output_path = Path(tempfile.mktemp(suffix=".json"))

    try:
        result = PDFToXMLConverter.convert_file(
            sample_pdf, output_path, include_metadata=True, extract_tables=True, indent=2
        )

        assert isinstance(result, Path)
        assert result.exists()

        # Verify saved file content
        with open(result) as f:
            data = json.load(f)
        assert "document" in data
        assert "metadata" in data["document"]
    finally:
        output_path.unlink(missing_ok=True)


def test_convert_creates_parent_directories(sample_pdf):
    """Test that save_json creates parent directories."""
    temp_dir = Path(tempfile.mkdtemp())
    output_path = temp_dir / "nested" / "dir" / "output.json"

    try:
        with PDFToXMLConverter(sample_pdf) as converter:
            converter.save_json(output_path)

        assert output_path.exists()
        assert output_path.parent.exists()
    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def test_context_manager_exception_handling(sample_pdf):
    """Test that context manager closes doc even on exception."""
    converter = None
    try:
        with PDFToXMLConverter(sample_pdf) as conv:
            converter = conv
            raise RuntimeError("Test exception")
    except RuntimeError:
        pass

    # Document should still be closed
    assert converter.doc.is_closed


def test_multiple_conversions(sample_pdf):
    """Test running multiple conversions with same converter."""
    with PDFToXMLConverter(sample_pdf) as converter:
        result1 = converter.convert(include_metadata=False)
        result2 = converter.convert(include_metadata=True)

        assert result1 is not None
        assert result2 is not None
        assert "metadata" in result2["document"]


def test_save_after_convert(sample_pdf):
    """Test saving after conversion."""
    output_path = Path(tempfile.mktemp(suffix=".json"))

    try:
        with PDFToXMLConverter(sample_pdf) as converter:
            result = converter.convert()
            converter.save_json(output_path)

        assert output_path.exists()

        with open(output_path) as f:
            saved = json.load(f)

        # Saved data should match converted data
        assert saved == result
    finally:
        output_path.unlink(missing_ok=True)
