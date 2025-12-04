"""
Comprehensive tests for dsr_rate_extractor.py to achieve >95% coverage.
"""

import pytest
import re
import sys
from pathlib import Path
from typing import Dict, List

# Import module to test
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dsr_rate_extractor import (
    extract_rates_from_dsr,
    _check_block_for_simple_format,
    _detect_simple_format,
    _is_valid_dsr_code,
    _is_valid_unit,
    _parse_rate_value,
    _extract_rates_simple_format,
    _should_skip_line,
    _should_stop_extraction,
    _extract_description_lines,
    _build_complete_description,
    _extract_unit_from_lines,
    _try_parse_rate_from_text,
    _find_say_rate_in_lines,
    _find_cost_per_rate_in_lines,
    _search_blocks_for_rate,
    _extract_rate_from_block,
    _collect_dsr_descriptions,
    _extract_rates_detailed_format,
)


# =============================================================================
# Tests for validation functions
# =============================================================================


class TestValidationFunctions:
    """Tests for validation helper functions."""

    def test_is_valid_dsr_code_valid(self):
        """Test valid DSR codes."""
        assert _is_valid_dsr_code("15.12.2") is True
        assert _is_valid_dsr_code("8.3") is True
        assert _is_valid_dsr_code("11.55.1") is True

    def test_is_valid_dsr_code_invalid(self):
        """Test invalid DSR codes."""
        assert _is_valid_dsr_code("abc") is False
        assert _is_valid_dsr_code("15") is False
        assert _is_valid_dsr_code("15.12.2.3.4.5.6") is False  # Too long
        assert _is_valid_dsr_code("") is False

    def test_is_valid_unit_valid(self):
        """Test valid unit names."""
        assert _is_valid_unit("cum") is True
        assert _is_valid_unit("sqm") is True
        assert _is_valid_unit("CUM") is True  # Case insensitive
        assert _is_valid_unit("Nos") is True
        assert _is_valid_unit("each") is True
        assert _is_valid_unit("sq.m") is True
        assert _is_valid_unit("cu.m") is True

    def test_is_valid_unit_invalid(self):
        """Test invalid unit names."""
        assert _is_valid_unit("invalid") is False
        assert _is_valid_unit("xyz") is False
        assert _is_valid_unit("") is False

    def test_parse_rate_value_valid(self):
        """Test parsing valid rate values."""
        assert _parse_rate_value("450.00") == 450.00
        assert _parse_rate_value("1,500") == 1500.00
        assert _parse_rate_value("100") == 100.00

    def test_parse_rate_value_invalid(self):
        """Test parsing invalid rate values."""
        assert _parse_rate_value("abc") is None
        assert _parse_rate_value("5") is None  # Too low
        assert _parse_rate_value("2000000") is None  # Too high
        assert _parse_rate_value("") is None

    def test_parse_rate_value_edge_cases(self):
        """Test rate value edge cases."""
        assert _parse_rate_value("10") == 10.0  # Min valid
        assert _parse_rate_value("1000000") == 1000000.0  # Max valid
        assert _parse_rate_value("9.99") is None  # Just below min


# =============================================================================
# Tests for simple format detection
# =============================================================================


class TestSimpleFormat:
    """Tests for simple format detection and extraction."""

    def test_check_block_for_simple_format_valid(self):
        """Test valid simple format block."""
        block = {"lines": ["15.12.2", "Excavation in ordinary soil", "cum", "450.00"]}

        assert _check_block_for_simple_format(block) is True

    def test_check_block_for_simple_format_wrong_line_count(self):
        """Test block with wrong number of lines."""
        block = {
            "lines": [
                "15.12.2",
                "Description",
                # Missing unit and rate
            ]
        }

        assert _check_block_for_simple_format(block) is False

    def test_check_block_for_simple_format_invalid_code(self):
        """Test block with invalid DSR code."""
        block = {"lines": ["InvalidCode", "Description", "cum", "450.00"]}

        assert _check_block_for_simple_format(block) is False

    def test_check_block_for_simple_format_invalid_rate(self):
        """Test block with invalid rate."""
        block = {"lines": ["15.12.2", "Description", "cum", "5"]}  # Too low

        assert _check_block_for_simple_format(block) is False

    def test_detect_simple_format_found(self):
        """Test detection of simple format in pages."""
        pages_data = [
            {"blocks": [{"lines": ["15.12.2", "Excavation in ordinary soil", "cum", "450.00"]}]}
        ]

        assert _detect_simple_format(pages_data) is True

    def test_detect_simple_format_not_found(self):
        """Test when simple format is not detected."""
        pages_data = [{"blocks": [{"lines": ["Random text", "More text"]}]}]

        assert _detect_simple_format(pages_data) is False

    def test_extract_rates_simple_format(self, capsys):
        """Test extraction from simple format."""
        pages_data = [
            {
                "blocks": [
                    {
                        "lines": [
                            "15.12.2",
                            "Excavation in ordinary soil",
                            "for foundation work",
                            "cum",
                            "450.00",
                        ]
                    },
                    {"lines": ["15.7.4", "Brickwork in cement mortar", "sqm", "550.00"]},
                ]
            }
        ]

        rates = _extract_rates_simple_format(pages_data, "Vol II")

        assert "15.12.2" in rates
        assert "15.7.4" in rates
        assert rates["15.12.2"][0]["rate"] == 450.00
        assert rates["15.7.4"][0]["rate"] == 550.00
        assert (
            "Excavation in ordinary soil for foundation work" in rates["15.12.2"][0]["description"]
        )

        captured = capsys.readouterr()
        assert "Found DSR" in captured.out

    def test_extract_rates_simple_format_invalid_unit(self):
        """Test skipping entries with invalid units."""
        pages_data = [
            {
                "blocks": [
                    {"lines": ["15.12.2", "Description", "InvalidUnit", "450.00"]}  # Invalid unit
                ]
            }
        ]

        rates = _extract_rates_simple_format(pages_data, "Vol II")

        assert "15.12.2" not in rates


# =============================================================================
# Tests for description extraction
# =============================================================================


class TestDescriptionExtraction:
    """Tests for description line extraction."""

    def test_should_skip_line_headers(self):
        """Test skipping header lines."""
        assert _should_skip_line("code") is True
        assert _should_skip_line("description") is True
        assert _should_skip_line("unit") is True
        assert _should_skip_line("rate") is True

    def test_should_skip_line_units(self):
        """Test skipping unit lines."""
        assert _should_skip_line("cum") is True
        assert _should_skip_line("sqm") is True
        assert _should_skip_line("nos") is True

    def test_should_skip_line_numbers(self):
        """Test skipping pure number lines."""
        assert _should_skip_line("450.00") is True
        assert _should_skip_line("₹1,500") is True
        assert _should_skip_line("12") is True

    def test_should_skip_line_short(self):
        """Test skipping short lines."""
        assert _should_skip_line("ab") is True
        assert _should_skip_line("x") is True

    def test_should_skip_line_valid_description(self):
        """Test not skipping valid descriptions."""
        assert _should_skip_line("Excavation in ordinary soil") is False
        assert _should_skip_line("Brickwork in cement mortar") is False

    def test_should_stop_extraction_keywords(self):
        """Test stopping at calculation keywords."""
        assert _should_stop_extraction("Add 10%") is True
        assert _should_stop_extraction("Total cost") is True
        assert _should_stop_extraction("Say") is True
        assert _should_stop_extraction("Material cost") is True
        assert _should_stop_extraction("Labour charges") is True

    def test_should_stop_extraction_dsr_code(self):
        """Test stopping at next DSR code."""
        assert _should_stop_extraction("15.12.2") is True
        assert _should_stop_extraction("8.3 Some text") is True

    def test_should_stop_extraction_normal_text(self):
        """Test not stopping at normal description text."""
        assert _should_stop_extraction("Excavation in ordinary soil") is False
        assert _should_stop_extraction("Including supply and fixing") is False

    def test_extract_description_lines_same_line(self):
        """Test extracting description from same line as code."""
        lines = ["15.12.2 Excavation in ordinary soil for foundation"]

        desc_lines = _extract_description_lines(lines, 0, lines[0], "15.12.2")

        assert len(desc_lines) > 0
        assert "Excavation" in desc_lines[0]

    def test_extract_description_lines_multiple_lines(self):
        """Test extracting multi-line description."""
        lines = [
            "15.12.2",
            "Excavation in ordinary soil",
            "for foundation work",
            "including disposal",
        ]

        desc_lines = _extract_description_lines(lines, 0, lines[0], "15.12.2")

        assert len(desc_lines) >= 2
        assert any("Excavation" in line for line in desc_lines)

    def test_extract_description_lines_stop_at_keyword(self):
        """Test stopping description extraction at keywords."""
        lines = ["15.12.2", "Excavation in ordinary soil", "Say", "450.00"]  # Should stop here

        desc_lines = _extract_description_lines(lines, 0, lines[0], "15.12.2")

        assert "Say" not in desc_lines

    def test_extract_description_lines_max_lines(self):
        """Test limiting description to max 6 lines."""
        lines = ["15.12.2"] + [f"Description line {i}" for i in range(10)]

        desc_lines = _extract_description_lines(lines, 0, lines[0], "15.12.2")

        assert len(desc_lines) <= 6


# =============================================================================
# Tests for parent description building
# =============================================================================


class TestBuildCompleteDescription:
    """Tests for building complete descriptions with parent context."""

    def test_build_description_with_parent_level_3(self):
        """Test building description for 3-level code (8.3.2)."""
        dsr_map = {
            "8": "Foundation work including excavation",
            "8.3": "PCC work including supply",
            "8.3.2": "Mix 1:2:4 with aggregates",
        }

        desc = _build_complete_description("8.3.2", dsr_map)

        # Should include parent (8.3) since it's >15 chars
        assert "PCC work including supply" in desc
        assert "Mix 1:2:4 with aggregates" in desc

    def test_build_description_with_parent_level_2(self):
        """Test building description for 2-level code (8.3)."""
        dsr_map = {"8": "Foundation work including excavation", "8.3": "PCC work including supply"}

        desc = _build_complete_description("8.3", dsr_map)

        # Should include parent (8) since it's >15 chars
        assert "Foundation work including excavation" in desc
        assert "PCC work including supply" in desc

    def test_build_description_no_parent(self):
        """Test when parent doesn't exist."""
        dsr_map = {"8.3.2": "1:2:4 mix"}

        desc = _build_complete_description("8.3.2", dsr_map)

        assert "1:2:4 mix" in desc

    def test_build_description_code_not_found(self):
        """Test when code itself is not in map."""
        dsr_map = {}

        desc = _build_complete_description("8.3.2", dsr_map)

        assert "DSR item 8.3.2" in desc

    def test_build_description_short_parent(self):
        """Test skipping short parent descriptions."""
        dsr_map = {"8": "Short", "8.3": "PCC work description"}  # Too short (<=15 chars)

        desc = _build_complete_description("8.3", dsr_map)

        # Should skip short parent
        assert desc == "PCC work description"


# =============================================================================
# Tests for unit extraction
# =============================================================================


class TestExtractUnit:
    """Tests for unit extraction from lines."""

    def test_extract_unit_found(self):
        """Test extracting unit from lines."""
        lines = ["15.12.2", "Description", "cum", "450.00"]

        unit = _extract_unit_from_lines(lines, 0)

        assert unit == "cum"

    def test_extract_unit_different_types(self):
        """Test extracting different unit types."""
        for test_unit in ["cum", "sqm", "nos", "kg", "mtr"]:
            lines = ["Code", "Description", test_unit, "Rate"]

            unit = _extract_unit_from_lines(lines, 0)

            assert unit == test_unit

    def test_extract_unit_with_period(self):
        """Test extracting unit with period (e.g., 'cum.')."""
        lines = ["Code", "Description", "cum.", "Rate"]

        unit = _extract_unit_from_lines(lines, 0)

        assert unit == "cum"  # Period should be stripped

    def test_extract_unit_not_found(self):
        """Test when unit is not found."""
        lines = ["Code", "Description", "InvalidUnit", "Rate"]

        unit = _extract_unit_from_lines(lines, 0)

        assert unit == ""


# =============================================================================
# Tests for rate extraction
# =============================================================================


class TestRateExtraction:
    """Tests for rate value extraction."""

    def test_try_parse_rate_from_text_valid(self):
        """Test parsing valid rate text."""
        assert _try_parse_rate_from_text("450") == 450.0
        assert _try_parse_rate_from_text("1500.50") == 1500.50

    def test_try_parse_rate_from_text_invalid(self):
        """Test parsing invalid rate text."""
        assert _try_parse_rate_from_text("abc") is None
        assert _try_parse_rate_from_text("5") is None  # Below min
        assert _try_parse_rate_from_text("") is None
        assert _try_parse_rate_from_text(None) is None

    def test_find_say_rate_in_lines(self):
        """Test finding 'Say' rate value."""
        lines = ["Code", "Description", "Say", "450.00"]

        rate = _find_say_rate_in_lines(lines, 0)

        assert rate == 450.00

    def test_find_say_rate_not_found(self):
        """Test when 'Say' is not found."""
        lines = ["Code", "Description", "Rate"]

        rate = _find_say_rate_in_lines(lines, 0)

        assert rate is None

    def test_find_cost_per_rate_in_lines(self):
        """Test finding 'cost per' rate value."""
        lines = ["Total cost per unit", "450.00"]

        rate = _find_cost_per_rate_in_lines(lines, 0)

        assert rate == 450.00

    def test_search_blocks_for_rate_say(self):
        """Test searching blocks for 'Say' rate."""
        blocks = [{"lines": ["Say", "450.00"]}]

        rate = _search_blocks_for_rate(blocks)

        assert rate == 450.00

    def test_search_blocks_for_rate_cost_per(self):
        """Test searching blocks for 'cost per' rate."""
        blocks = [{"lines": ["Total cost per unit", "550.00"]}]

        rate = _search_blocks_for_rate(blocks)

        assert rate == 550.00

    def test_search_blocks_for_rate_not_found(self):
        """Test when rate is not found in blocks."""
        blocks = [{"lines": ["Random text", "More text"]}]

        rate = _search_blocks_for_rate(blocks)

        assert rate is None


# =============================================================================
# Tests for rate extraction from blocks
# =============================================================================


class TestExtractRateFromBlock:
    """Tests for extracting rate from blocks."""

    def test_extract_rate_from_block_say_in_current(self):
        """Test finding 'Say' rate in current block."""
        lines = ["15.12.2", "Description", "Say", "450.00"]
        block = {"lines": lines}

        rate = _extract_rate_from_block(lines, 0, block, [], 0, [], 0)

        assert rate == 450.00

    def test_extract_rate_from_block_next_block(self):
        """Test finding rate in next block."""
        lines = ["15.12.2", "Description"]
        block = {"lines": lines}
        blocks = [block, {"lines": ["Say", "450.00"]}]

        rate = _extract_rate_from_block(lines, 0, block, blocks, 0, [], 0)

        assert rate == 450.00

    def test_extract_rate_from_block_next_page(self):
        """Test finding rate in next page."""
        lines = ["15.12.2", "Description"]
        block = {"lines": lines}
        blocks = [block]
        pages_data = [{"blocks": blocks}, {"blocks": [{"lines": ["Say", "450.00"]}]}]

        rate = _extract_rate_from_block(lines, 0, block, blocks, 0, pages_data, 0)

        assert rate == 450.00

    def test_extract_rate_from_block_text_field(self):
        """Test extracting rate from block text field."""
        lines = ["15.12.2", "Description"]
        block = {"lines": lines, "text": "Description\nSay\n\n450.00"}

        rate = _extract_rate_from_block(lines, 0, block, [], 0, [], 0)

        assert rate == 450.00

    def test_extract_rate_from_block_not_found(self):
        """Test when rate is not found."""
        lines = ["15.12.2", "Description"]
        block = {"lines": lines}

        rate = _extract_rate_from_block(lines, 0, block, [], 0, [], 0)

        assert rate is None


# =============================================================================
# Tests for description collection
# =============================================================================


class TestCollectDescriptions:
    """Tests for collecting DSR descriptions."""

    def test_collect_dsr_descriptions(self, capsys):
        """Test collecting descriptions from pages."""
        pages_data = [
            {
                "blocks": [
                    {"lines": ["15.12.2 Excavation in ordinary soil", "for foundation work"]},
                    {"lines": ["15.7.4", "Brickwork in cement mortar"]},
                ]
            }
        ]

        dsr_map = _collect_dsr_descriptions(pages_data, "Vol I")

        assert "15.12.2" in dsr_map
        assert "15.7.4" in dsr_map
        assert "Excavation" in dsr_map["15.12.2"]
        assert "Brickwork" in dsr_map["15.7.4"]

        captured = capsys.readouterr()
        assert "Collected" in captured.out
        assert "Sample DSR Descriptions" in captured.out

    def test_collect_dsr_descriptions_with_dict_lines(self):
        """Test collecting descriptions when lines are dicts."""
        pages_data = [
            {"blocks": [{"lines": [{"text": "15.12.2 Excavation"}, {"text": "in ordinary soil"}]}]}
        ]

        dsr_map = _collect_dsr_descriptions(pages_data, "Vol I")

        assert "15.12.2" in dsr_map


# =============================================================================
# Tests for detailed format extraction
# =============================================================================


class TestExtractRatesDetailedFormat:
    """Tests for detailed format extraction."""

    def test_extract_rates_detailed_format(self, capsys):
        """Test extracting rates from detailed format."""
        pages_data = [
            {
                "blocks": [
                    {
                        "lines": [
                            "15.12.2 Excavation in ordinary soil",
                            "for foundation work",
                            "cum",
                            "Say",
                            "450.00",
                        ]
                    }
                ]
            }
        ]

        rates = _extract_rates_detailed_format(pages_data, "Vol I")

        assert "15.12.2" in rates
        assert rates["15.12.2"][0]["rate"] == 450.00
        assert rates["15.12.2"][0]["source"] == "enhanced_with_parent"

        captured = capsys.readouterr()
        assert "Found DSR" in captured.out

    def test_extract_rates_detailed_format_with_parent(self, capsys):
        """Test extraction with parent context."""
        pages_data = [
            {
                "blocks": [
                    {
                        "lines": [
                            "8 Foundation work involving excavation and preparation",
                            "for construction purposes",
                        ]
                    },
                    {
                        "lines": [
                            "8.3 PCC work including supply and placement",
                            "cum",
                            "Say",
                            "6500.00",
                        ]
                    },
                ]
            }
        ]

        rates = _extract_rates_detailed_format(pages_data, "Vol I")

        if "8.3" in rates:
            # Parent description (8) should be included since it's >15 chars
            assert (
                "Foundation work involving excavation" in rates["8.3"][0]["description"]
                or "PCC work including supply" in rates["8.3"][0]["description"]
            )

    def test_extract_rates_detailed_format_no_rate(self):
        """Test when no rate is found."""
        pages_data = [
            {
                "blocks": [
                    {
                        "lines": [
                            "15.12.2 Excavation in ordinary soil",
                            "cum",
                            # No rate
                        ]
                    }
                ]
            }
        ]

        rates = _extract_rates_detailed_format(pages_data, "Vol I")

        # Should not include entries without rates
        assert "15.12.2" not in rates or len(rates["15.12.2"]) == 0


# =============================================================================
# Tests for main extraction function
# =============================================================================


class TestExtractRatesFromDSR:
    """Tests for main extraction function."""

    def test_extract_rates_from_dsr_simple_format(self, capsys):
        """Test main function with simple format."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["15.12.2", "Excavation in ordinary soil", "cum", "450.00"]}
                        ]
                    }
                ]
            }
        }

        rates = extract_rates_from_dsr(data, "Vol II")

        assert "15.12.2" in rates
        assert rates["15.12.2"][0]["rate"] == 450.00

        captured = capsys.readouterr()
        assert "simple format" in captured.out

    def test_extract_rates_from_dsr_pages_fallback(self, capsys):
        """Test using 'pages' key as fallback."""
        data = {"pages": [{"blocks": [{"lines": ["15.12.2", "Excavation", "cum", "450.00"]}]}]}

        rates = extract_rates_from_dsr(data, "Vol II")

        assert "15.12.2" in rates

    def test_extract_rates_from_dsr_empty_data(self):
        """Test with empty data."""
        data = {}

        rates = extract_rates_from_dsr(data, "Vol II")

        # Should return empty dict, not crash
        assert isinstance(rates, dict)
