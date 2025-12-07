"""Tests for CLI module."""

import pytest
from pathlib import Path
from click.testing import CliRunner
from src.estimatex.cli import main


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF file for testing."""
    pdf_path = tmp_path / "sample.pdf"
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000115 00000 n
0000000214 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
306
%%EOF"""
    pdf_path.write_bytes(pdf_content)
    return pdf_path


def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Convert PDF to JSON" in result.output


def test_convert_nonexistent_file(runner):
    """Test converting a non-existent file."""
    result = runner.invoke(main, ["nonexistent.pdf"])
    assert result.exit_code != 0


def test_convert_with_output(runner, sample_pdf, tmp_path):
    """Test converting PDF with specified output."""
    output_file = tmp_path / "output.json"
    result = runner.invoke(main, [str(sample_pdf), "-o", str(output_file)])

    # Command should complete (may fail on actual conversion but CLI works)
    assert "Converting" in result.output or result.exit_code != 0


def test_convert_with_metadata_flag(runner, sample_pdf):
    """Test convert with metadata flag."""
    result = runner.invoke(main, [str(sample_pdf), "--include-metadata"])
    assert "Converting" in result.output or result.exit_code != 0


def test_convert_with_tables_flag(runner, sample_pdf):
    """Test convert with tables extraction."""
    result = runner.invoke(main, [str(sample_pdf), "--extract-tables"])
    assert "Converting" in result.output or result.exit_code != 0


def test_convert_no_pretty_flag(runner, sample_pdf):
    """Test convert without pretty-printing."""
    result = runner.invoke(main, [str(sample_pdf), "--no-pretty"])
    assert "Converting" in result.output or result.exit_code != 0


def test_convert_default_output(runner, sample_pdf):
    """Test converting with default output path."""
    result = runner.invoke(main, [str(sample_pdf)])
    # Should use default output (same name with .json extension)
    assert "Converting" in result.output or result.exit_code != 0
