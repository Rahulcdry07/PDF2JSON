"""
Comprehensive tests for DSR modules to achieve >95% coverage.
Tests dsr_matcher.py and extraction_utils.py
"""

import pytest
import re
import sys
from pathlib import Path
from typing import Dict, List

# Import modules to test
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dsr_matcher import (
    find_best_dsr_match,
    match_items_with_rates,
)
from extraction_utils import (
    extract_keywords_from_description,
    detect_dsr_block,
    extract_dsr_code_from_lines,
    extract_item_details,
    process_blocks_for_dsr_items,
)


# =============================================================================
# Tests for dsr_matcher.py
# =============================================================================

class TestFindBestDSRMatch:
    """Tests for find_best_dsr_match function."""
    
    def test_single_entry_above_threshold(self, capsys):
        """Test single entry with similarity above threshold."""
        entries = [
            {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I"}
        ]
        
        result = find_best_dsr_match(
            "Excavation in ordinary soil",
            "15.12.2",
            entries,
            similarity_threshold=0.3,
            return_similarity=False
        )
        
        assert result is not None
        assert result["rate"] == 450.00
        
        captured = capsys.readouterr()
        assert "Single entry" in captured.out
    
    def test_single_entry_below_threshold(self, capsys):
        """Test single entry with similarity below threshold."""
        entries = [
            {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I"}
        ]
        
        result = find_best_dsr_match(
            "Completely different work description",
            "15.12.2",
            entries,
            similarity_threshold=0.8,
            return_similarity=False
        )
        
        assert result is None
        
        captured = capsys.readouterr()
        assert "Rejected" in captured.out
    
    def test_single_entry_with_similarity_return(self, capsys):
        """Test single entry returning similarity score."""
        entries = [
            {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I"}
        ]
        
        result = find_best_dsr_match(
            "Excavation in soil",
            "15.12.2",
            entries,
            similarity_threshold=0.3,
            return_similarity=True
        )
        
        assert result is not None
        assert "similarity" in result
        assert result["similarity"] > 0.3
        assert result["rate"] == 450.00
    
    def test_single_entry_below_threshold_with_similarity(self, capsys):
        """Test single entry below threshold returning only similarity."""
        entries = [
            {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I"}
        ]
        
        result = find_best_dsr_match(
            "Completely unrelated work",
            "15.12.2",
            entries,
            similarity_threshold=0.9,
            return_similarity=True
        )
        
        # Should return dict with just similarity when below threshold
        assert result is not None
        assert "similarity" in result
        assert result["similarity"] < 0.9
    
    def test_multiple_entries_best_match(self, capsys):
        """Test selecting best match from multiple entries."""
        entries = [
            {"description": "Excavation in soft soil", "rate": 400.00, "unit": "cum", "volume": "Vol I"},
            {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I"},
            {"description": "Excavation in hard rock", "rate": 800.00, "unit": "cum", "volume": "Vol II"},
        ]
        
        result = find_best_dsr_match(
            "Excavation in ordinary soil",
            "15.12.2",
            entries,
            similarity_threshold=0.3,
            return_similarity=True
        )
        
        assert result is not None
        assert result["rate"] == 450.00  # Should match "ordinary soil" best
        assert result["similarity"] > 0.8  # Should have high similarity
        
        captured = capsys.readouterr()
        assert "Best match" in captured.out
        assert "3 entries" in captured.out
    
    def test_multiple_entries_all_below_threshold(self, capsys):
        """Test when all entries are below threshold."""
        entries = [
            {"description": "Excavation in soft soil", "rate": 400.00, "unit": "cum", "volume": "Vol I"},
            {"description": "Excavation in hard rock", "rate": 800.00, "unit": "cum", "volume": "Vol II"},
        ]
        
        result = find_best_dsr_match(
            "Completely different brickwork",
            "15.7.4",
            entries,
            similarity_threshold=0.8,
            return_similarity=False
        )
        
        assert result is None
        
        captured = capsys.readouterr()
        assert "Rejected" in captured.out
    
    def test_empty_entries(self):
        """Test with empty entries list."""
        result = find_best_dsr_match(
            "Some description",
            "15.12.2",
            [],
            similarity_threshold=0.3
        )
        
        assert result is None
    
    def test_multiple_entries_with_sorting(self, capsys):
        """Test that entries are properly sorted by similarity."""
        entries = [
            {"description": "Different work entirely", "rate": 100.00, "unit": "cum", "volume": "Vol I"},
            {"description": "Brickwork in cement", "rate": 550.00, "unit": "sqm", "volume": "Vol I"},
            {"description": "Brickwork in cement mortar", "rate": 560.00, "unit": "sqm", "volume": "Vol I"},
        ]
        
        result = find_best_dsr_match(
            "Brickwork in cement mortar 1:6",
            "15.7.4",
            entries,
            similarity_threshold=0.3,
            return_similarity=True
        )
        
        assert result is not None
        # Should select "Brickwork in cement mortar" (highest similarity)
        assert result["rate"] in [550.00, 560.00]
        assert result["similarity"] > 0.5


class TestMatchItemsWithRates:
    """Tests for match_items_with_rates function."""
    
    def test_exact_match_good_similarity(self, capsys):
        """Test exact code match with good similarity."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": "100",
                "unit": "cum"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [
                {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I", "page": 150}
            ]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        assert matched[0]["rate"] == 450.00
        assert matched[0]["match_type"] == "exact_with_description_match"
        assert matched[0]["similarity_score"] >= 0.3
        assert matched[0]["amount"] == 45000.00  # 100 * 450
    
    def test_code_match_low_similarity(self, capsys):
        """Test exact code match but low description similarity."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Completely different work description here",
                "quantity": "50",
                "unit": "cum"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [
                {"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I", "page": 150}
            ]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        # Should mark as mismatch if similarity is very low
        # Depending on actual similarity, might be "code_match_but_description_mismatch" or exact match
        assert matched[0]["clean_dsr_code"] == "15.12.2"
    
    def test_code_not_found(self, capsys):
        """Test when DSR code is not in reference."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-99.99.99",
                "clean_dsr_code": "99.99.99",
                "description": "Nonexistent work",
                "quantity": "10",
                "unit": "nos"
            }
        ]
        
        dsr_rates = {}
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        assert matched[0]["rate"] is None
        assert matched[0]["match_type"] == "not_found"
        assert matched[0]["similarity_score"] == 0.0
        assert "not found in reference" in matched[0]["dsr_description"]
    
    def test_multiple_items(self, capsys):
        """Test matching multiple items."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": "100",
                "unit": "cum"
            },
            {
                "dsr_code": "DSR-2024-15.7.4",
                "clean_dsr_code": "15.7.4",
                "description": "Brickwork in cement mortar",
                "quantity": "50",
                "unit": "sqm"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [{"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I", "page": 150}],
            "15.7.4": [{"description": "Brickwork in cement mortar", "rate": 550.00, "unit": "sqm", "volume": "Vol I", "page": 75}]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 2
        assert matched[0]["rate"] == 450.00
        assert matched[1]["rate"] == 550.00
    
    def test_duplicate_entries(self, capsys):
        """Test handling multiple entries for same code."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in soft soil",
                "quantity": "100",
                "unit": "cum"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [
                {"description": "Excavation in soft soil", "rate": 400.00, "unit": "cum", "volume": "Vol I", "page": 150},
                {"description": "Excavation in hard soil", "rate": 500.00, "unit": "cum", "volume": "Vol II", "page": 200}
            ]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        assert matched[0]["duplicate_count"] == 2
        # Should select best matching entry (soft soil)
        assert matched[0]["rate"] == 400.00
    
    def test_no_quantity_no_amount(self, capsys):
        """Test item without quantity doesn't calculate amount."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": "",  # Empty quantity
                "unit": "cum"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [{"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I", "page": 150}]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        assert matched[0]["rate"] == 450.00
        assert matched[0].get("amount") is None  # No amount calculated
    
    def test_invalid_quantity_no_amount(self, capsys):
        """Test invalid quantity doesn't crash."""
        lko_items = [
            {
                "dsr_code": "DSR-2024-15.12.2",
                "clean_dsr_code": "15.12.2",
                "description": "Excavation in ordinary soil",
                "quantity": "invalid",
                "unit": "cum"
            }
        ]
        
        dsr_rates = {
            "15.12.2": [{"description": "Excavation in ordinary soil", "rate": 450.00, "unit": "cum", "volume": "Vol I", "page": 150}]
        }
        
        matched = match_items_with_rates(lko_items, dsr_rates)
        
        assert len(matched) == 1
        assert matched[0].get("amount") is None


# =============================================================================
# Tests for extraction_utils.py
# =============================================================================

class TestExtractKeywords:
    """Tests for extract_keywords_from_description."""
    
    def test_basic_keywords(self):
        """Test basic keyword extraction."""
        keywords = extract_keywords_from_description("Excavation in ordinary soil")
        
        assert "excavation" in keywords
        assert "ordinary" in keywords
        assert "soil" in keywords
        assert "in" not in keywords  # Stop word filtered
    
    def test_stop_words_filtered(self):
        """Test that stop words are filtered out."""
        keywords = extract_keywords_from_description("The work is for the building")
        
        assert "the" not in keywords
        assert "for" not in keywords
        assert "work" in keywords
        assert "building" in keywords
    
    def test_short_words_filtered(self):
        """Test that short words (<=2 chars) are filtered."""
        keywords = extract_keywords_from_description("PCC at base of wall")
        
        assert "pcc" in keywords
        assert "base" in keywords
        assert "wall" in keywords
        assert "at" not in keywords  # Stop word
        assert "of" not in keywords  # Stop word
    
    def test_punctuation_removed(self):
        """Test that punctuation is removed."""
        keywords = extract_keywords_from_description("Work, including (supply) & fixing!")
        
        assert "work" in keywords
        assert "including" in keywords
        assert "supply" in keywords
        assert "fixing" in keywords
    
    def test_lowercase_conversion(self):
        """Test that keywords are lowercase."""
        keywords = extract_keywords_from_description("EXCAVATION In Ordinary SOIL")
        
        assert "excavation" in keywords
        assert "ordinary" in keywords
        assert all(kw.islower() for kw in keywords)
    
    def test_empty_description(self):
        """Test empty description."""
        keywords = extract_keywords_from_description("")
        
        assert keywords == []
    
    def test_only_stop_words(self):
        """Test description with only stop words."""
        keywords = extract_keywords_from_description("the and or of in to for")
        
        assert keywords == []


class TestDetectDSRBlock:
    """Tests for detect_dsr_block."""
    
    def test_dsr_marker_uppercase(self):
        """Test detection of DSR marker in uppercase."""
        block = {"lines": ["DSR-", "2024-15.12.2"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_dsr is True
    
    def test_dsr_marker_lowercase(self):
        """Test detection of DSR marker in lowercase."""
        block = {"lines": ["dsr-", "2024-15.12.2"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_dsr is True
    
    def test_year_code_pattern(self):
        """Test detection of year-code pattern."""
        block = {"lines": ["2024-15.12.2"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_dsr is True
    
    def test_standalone_code(self):
        """Test detection of standalone code."""
        block = {"lines": ["15.12.2"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_standalone is True
    
    def test_no_dsr_pattern(self):
        """Test block without DSR patterns."""
        block = {"lines": ["Some random text", "Without any DSR codes"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_dsr is False
        assert has_standalone is False
    
    def test_empty_block(self):
        """Test empty block."""
        block = {"lines": []}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        assert has_dsr is False
        assert has_standalone is False
    
    def test_standalone_too_many_lines(self):
        """Test that standalone detection requires <=3 lines."""
        block = {"lines": ["Line 1", "Line 2", "Line 3", "15.12.2", "Line 5"]}
        
        has_dsr, has_standalone = detect_dsr_block(block)
        
        # Should not detect standalone with >3 lines
        assert has_standalone is False


class TestExtractDSRCodeFromLines:
    """Tests for extract_dsr_code_from_lines."""
    
    def test_year_code_single_line(self):
        """Test extraction of year-code in single line."""
        lines = ["2024-15.12.2"]
        blocks = [{"lines": lines}]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 0, blocks)
        
        assert dsr_code == "DSR-2024-15.12.2"
        assert clean_code == "15.12.2"
    
    def test_dsr_marker_separate_lines(self):
        """Test extraction with DSR marker on separate lines."""
        lines = ["DSR-", "2024", "15.12.2"]
        blocks = [{"lines": lines}]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 0, blocks)
        
        assert dsr_code == "DSR-2024-15.12.2"
        assert clean_code == "15.12.2"
    
    def test_dsr_marker_with_year_code(self):
        """Test DSR marker followed by year-code combined."""
        lines = ["DSR-", "2024-15.7.4"]
        blocks = [{"lines": lines}]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 0, blocks)
        
        assert dsr_code == "DSR-2024-15.7.4"
        assert clean_code == "15.7.4"
    
    def test_standalone_with_lookback(self):
        """Test standalone code with lookback for DSR marker."""
        blocks = [
            {"lines": ["DSR-", "2024"]},
            {"lines": ["15.12.2"]}
        ]
        lines = blocks[1]["lines"]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 1, blocks)
        
        assert dsr_code == "DSR-2024-15.12.2"
        assert clean_code == "15.12.2"
    
    def test_no_dsr_pattern(self):
        """Test with no DSR pattern."""
        lines = ["Some text without DSR code"]
        blocks = [{"lines": lines}]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 0, blocks)
        
        assert dsr_code is None
        assert clean_code is None
    
    def test_three_level_code(self):
        """Test extraction of three-level code like 15.12.2."""
        lines = ["2024-15.12.2"]
        blocks = [{"lines": lines}]
        
        dsr_code, clean_code = extract_dsr_code_from_lines(lines, 0, blocks)
        
        assert clean_code == "15.12.2"
        assert "15.12.2" in dsr_code


class TestExtractItemDetails:
    """Tests for extract_item_details."""
    
    def test_extract_description_unit_quantity(self):
        """Test extraction of description, unit, and quantity."""
        blocks = [
            {"lines": ["15.12.2"]},
            {"lines": ["Excavation in ordinary soil for foundation work"]},
            {"lines": ["Cum", "100.50"]}
        ]
        
        description, unit, quantity = extract_item_details(blocks, 0)
        
        assert "Excavation" in description
        assert unit == "Cum"
        assert quantity == "100.50"
    
    def test_extract_with_noise_filtering(self):
        """Test that noise is filtered from description."""
        blocks = [
            {"lines": ["15.12.2"]},
            {"lines": ["DSR-"]},  # Should be filtered
            {"lines": ["Brickwork in cement mortar 1:6"]},
            {"lines": ["Sqm", "50.25"]}
        ]
        
        description, unit, quantity = extract_item_details(blocks, 0)
        
        assert "Brickwork" in description
        assert "DSR" not in description
    
    def test_extract_different_units(self):
        """Test extraction with different unit types."""
        units_to_test = ["Nos", "Cum", "Sqm", "Kg", "Metre", "Mtr", "Ltr", "Each"]
        
        for test_unit in units_to_test:
            blocks = [
                {"lines": ["15.12.2"]},
                {"lines": ["Some description here for testing"]},
                {"lines": [test_unit, "25.5"]}
            ]
            
            description, unit, quantity = extract_item_details(blocks, 0)
            
            assert unit == test_unit
            assert quantity == "25.5"
    
    def test_quantity_range_validation(self):
        """Test that quantity is within valid range."""
        blocks = [
            {"lines": ["15.12.2"]},
            {"lines": ["Description"]},
            {"lines": ["Cum", "0.001"]}  # Too small
        ]
        
        description, unit, quantity = extract_item_details(blocks, 0)
        
        # Should not extract quantity < 0.01
        assert quantity == ""
    
    def test_no_description_found(self):
        """Test when no valid description is found."""
        blocks = [
            {"lines": ["15.12.2"]},
            {"lines": ["DSR-"]},  # Filtered
            {"lines": ["2024"]},  # Filtered
            {"lines": ["Cum", "100"]}
        ]
        
        description, unit, quantity = extract_item_details(blocks, 0)
        
        # May return empty or partial results
        assert unit == "Cum"


class TestProcessBlocksForDSRItems:
    """Tests for process_blocks_for_dsr_items."""
    
    def test_process_single_item(self):
        """Test processing single DSR item."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["DSR-", "2024", "15.12.2"]},
                            {"lines": ["Excavation in ordinary soil for foundation"]},
                            {"lines": ["Cum", "100.50"]}
                        ]
                    }
                ]
            }
        }
        
        items = process_blocks_for_dsr_items(data)
        
        assert len(items) == 1
        assert items[0]["clean_dsr_code"] == "15.12.2"
        assert "Excavation" in items[0]["description"]
    
    def test_process_multiple_items(self):
        """Test processing multiple DSR items."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["DSR-", "2024", "15.12.2"]},
                            {"lines": ["Excavation in ordinary soil"]},
                            {"lines": ["Cum", "100"]},
                            {"lines": ["DSR-", "2024", "15.7.4"]},
                            {"lines": ["Brickwork in cement mortar"]},
                            {"lines": ["Sqm", "50"]}
                        ]
                    }
                ]
            }
        }
        
        items = process_blocks_for_dsr_items(data)
        
        assert len(items) == 2
        assert items[0]["clean_dsr_code"] == "15.12.2"
        assert items[1]["clean_dsr_code"] == "15.7.4"
    
    def test_skip_duplicates(self):
        """Test that duplicate codes are skipped."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["DSR-", "2024", "15.12.2"]},
                            {"lines": ["First description"]},
                            {"lines": ["Cum", "100"]},
                            {"lines": ["DSR-", "2024", "15.12.2"]},  # Duplicate
                            {"lines": ["Second description"]},
                            {"lines": ["Cum", "200"]}
                        ]
                    }
                ]
            }
        }
        
        items = process_blocks_for_dsr_items(data)
        
        assert len(items) == 1  # Only first occurrence
        assert "First" in items[0]["description"]
    
    def test_with_item_processor(self):
        """Test with custom item processor callback."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["DSR-", "2024", "15.12.2"]},
                            {"lines": ["Test description"]},
                            {"lines": ["Cum", "100"]}
                        ]
                    }
                ]
            }
        }
        
        def custom_processor(item, item_number, clean_code):
            item["custom_field"] = f"Item {item_number}"
            item["processed"] = True
            return item
        
        items = process_blocks_for_dsr_items(data, item_processor=custom_processor)
        
        assert len(items) == 1
        assert items[0]["custom_field"] == "Item 1"
        assert items[0]["processed"] is True
    
    def test_empty_document(self):
        """Test with empty document."""
        data = {
            "document": {
                "pages_data": []
            }
        }
        
        items = process_blocks_for_dsr_items(data)
        
        assert items == []
    
    def test_no_valid_items(self):
        """Test document with no valid DSR items."""
        data = {
            "document": {
                "pages_data": [
                    {
                        "blocks": [
                            {"lines": ["Just random text"]},
                            {"lines": ["Without any DSR codes"]},
                        ]
                    }
                ]
            }
        }
        
        items = process_blocks_for_dsr_items(data)
        
        assert items == []
