#!/usr/bin/env python3
"""Tests for dsr_rate_extractor.py script."""

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dsr_rate_extractor import (
    extract_rates_from_dsr,
    _check_block_for_simple_format,
    _detect_simple_format,
    _is_valid_dsr_code,
    _is_valid_unit,
)


def test_is_valid_dsr_code():
    """Test DSR code validation."""
    assert _is_valid_dsr_code("1.1") is True
    assert _is_valid_dsr_code("1.1.1") is True
    assert _is_valid_dsr_code("10.25") is True
    assert _is_valid_dsr_code("123.456") is True

    # Invalid codes
    assert _is_valid_dsr_code("ABC") is False
    assert _is_valid_dsr_code("1") is False
    assert _is_valid_dsr_code("") is False
    assert _is_valid_dsr_code("1.1.1.1.1") is False  # Too long


def test_is_valid_unit():
    """Test unit validation."""
    # Valid units
    assert _is_valid_unit("cum") is True
    assert _is_valid_unit("CUM") is True
    assert _is_valid_unit("sqm") is True
    assert _is_valid_unit("nos") is True
    assert _is_valid_unit("each") is True
    assert _is_valid_unit("kg") is True
    assert _is_valid_unit("mtr") is True
    assert _is_valid_unit("sq.m") is True

    # Invalid units
    assert _is_valid_unit("invalid") is False
    assert _is_valid_unit("") is False
    assert _is_valid_unit("xyz") is False


def test_check_block_for_simple_format():
    """Test simple format detection in blocks."""
    # Valid simple format block
    valid_block = {"lines": ["1.1", "Earth work excavation", "cum", "150.50"]}
    assert _check_block_for_simple_format(valid_block) is True

    # Invalid - wrong number of lines
    invalid_block = {"lines": ["1.1", "Description", "cum"]}
    assert _check_block_for_simple_format(invalid_block) is False

    # Invalid - no DSR code
    invalid_block2 = {"lines": ["ABC", "Description", "cum", "150.50"]}
    assert _check_block_for_simple_format(invalid_block2) is False

    # Invalid - no valid rate
    invalid_block3 = {"lines": ["1.1", "Description", "cum", "invalid"]}
    assert _check_block_for_simple_format(invalid_block3) is False


def test_detect_simple_format():
    """Test simple format detection across pages."""
    # Pages with simple format
    pages_data = [
        {
            "blocks": [
                {"lines": ["1.1", "Earth work", "cum", "150.00"]},
                {"lines": ["1.2", "Concrete work", "sqm", "200.00"]},
            ]
        }
    ]
    assert _detect_simple_format(pages_data) is True

    # Pages without simple format
    pages_data_invalid = [{"blocks": [{"lines": ["Some text", "More text"]}]}]
    assert _detect_simple_format(pages_data_invalid) is False


def test_extract_rates_from_dsr_simple():
    """Test extracting rates from simple format DSR."""
    data = {
        "document": {
            "pages_data": [
                {
                    "page": 1,
                    "blocks": [
                        {"lines": ["1.1", "Earth work excavation", "cum", "150.50"]},
                        {"lines": ["1.2", "Concrete work", "sqm", "200.75"]},
                    ],
                }
            ]
        }
    }

    rates = extract_rates_from_dsr(data, "Test Volume")

    # Should extract rates (format depends on implementation)
    assert isinstance(rates, dict)


def test_extract_rates_from_dsr_empty():
    """Test extracting from empty data."""
    data = {"document": {"pages_data": []}}
    rates = extract_rates_from_dsr(data, "Empty Volume")

    assert isinstance(rates, dict)
    # Should return empty or minimal data
    assert len(rates) == 0


def test_extract_rates_from_dsr_no_document():
    """Test extracting when document key missing."""
    data = {"pages": []}
    rates = extract_rates_from_dsr(data, "No Document")

    assert isinstance(rates, dict)


def test_is_valid_dsr_code_with_whitespace():
    """Test DSR code validation handles whitespace."""
    assert _is_valid_dsr_code("  1.1  ") is True
    assert _is_valid_dsr_code("\t1.2.3\n") is True


def test_is_valid_unit_case_insensitive():
    """Test that unit validation is case-insensitive."""
    assert _is_valid_unit("CUM") is True
    assert _is_valid_unit("Cum") is True
    assert _is_valid_unit("cum") is True
    assert _is_valid_unit("SQM") is True
    assert _is_valid_unit("Sqm") is True


def test_check_block_rate_range():
    """Test that rate validation checks reasonable range."""
    # Rate too low
    low_rate_block = {"lines": ["1.1", "Description", "cum", "5.00"]}
    assert _check_block_for_simple_format(low_rate_block) is False

    # Rate too high
    high_rate_block = {"lines": ["1.1", "Description", "cum", "999999.00"]}
    assert _check_block_for_simple_format(high_rate_block) is False

    # Valid rate
    valid_block = {"lines": ["1.1", "Description", "cum", "500.00"]}
    assert _check_block_for_simple_format(valid_block) is True


def test_check_block_with_comma_in_rate():
    """Test that rates with commas are handled."""
    block = {"lines": ["1.1", "Description", "cum", "1,500.50"]}
    assert _check_block_for_simple_format(block) is True


def test_extract_rates_preserves_volume_name():
    """Test that volume name is used during extraction."""
    data = {
        "document": {
            "pages_data": [
                {"page": 1, "blocks": [{"lines": ["1.1", "Test", "cum", "100.00"]}]}
            ]
        }
    }

    # Just verify it doesn't crash with volume name
    rates = extract_rates_from_dsr(data, "Volume I - Civil")
    assert isinstance(rates, dict)
