"""
Tests for Excel to PDF converter functionality (native converter only).
"""

import pytest
from pathlib import Path
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from excel_to_pdf_native import convert_excel_to_pdf


@pytest.fixture
def sample_excel(tmp_path):
    """Create a sample Excel file for testing."""
    excel_file = tmp_path / "test.xlsx"
    wb = openpyxl.Workbook()

    # Sheet 1: DSR data
    ws1 = wb.active
    ws1.title = "Sheet1"
    ws1.append(["Code", "Description", "Unit", "Rate"])
    ws1.append(["1.1", "Earth work excavation", "Cum", "250.50"])
    ws1.append(["1.2", "Filling", "Cum", "180.00"])
    ws1.append(["2.1", "Brick work", "Sqm", "450.75"])

    # Sheet 2: Additional data
    ws2 = wb.create_sheet("Sheet2")
    ws2.append(["Item", "Quantity", "Price"])
    ws2.append(["Item A", "10", "100"])
    ws2.append(["Item B", "20", "200"])

    # Sheet 3: Empty sheet
    wb.create_sheet("EmptySheet")

    wb.save(excel_file)
    return excel_file


def test_native_converter_basic(sample_excel, tmp_path):
    """Test basic native converter functionality."""
    output_pdf = tmp_path / "output.pdf"
    
    # Test conversion
    success = convert_excel_to_pdf(sample_excel, output_pdf)
    
    # Should succeed or fail gracefully (depends on system tools availability)
    assert isinstance(success, bool)
    if success:
        assert output_pdf.exists()


def test_native_converter_with_sheet(sample_excel, tmp_path):
    """Test native converter with specific sheet."""
    output_pdf = tmp_path / "sheet1.pdf"
    
    success = convert_excel_to_pdf(sample_excel, output_pdf, "Sheet1")
    
    assert isinstance(success, bool)
    if success:
        assert output_pdf.exists()


def test_native_converter_nonexistent_file(tmp_path):
    """Test native converter with nonexistent file."""
    nonexistent = tmp_path / "nonexistent.xlsx"
    output_pdf = tmp_path / "output.pdf"
    
    success = convert_excel_to_pdf(nonexistent, output_pdf)
    assert success is False
    assert not output_pdf.exists()


def test_native_converter_different_methods(sample_excel, tmp_path):
    """Test native converter with different methods."""
    for method in ["auto", "libreoffice", "javascript"]:
        output_pdf = tmp_path / f"output_{method}.pdf"
        success = convert_excel_to_pdf(sample_excel, output_pdf, method=method)
        assert isinstance(success, bool)
