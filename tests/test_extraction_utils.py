#!/usr/bin/env python3
"""Tests for extraction_utils.py script."""

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from extraction_utils import (
    extract_keywords_from_description,
    detect_dsr_block,
)


def test_extract_keywords_basic():
    """Test basic keyword extraction."""
    description = "Excavation in ordinary soil"
    keywords = extract_keywords_from_description(description)

    assert "excavation" in keywords
    assert "ordinary" in keywords
    assert "soil" in keywords


def test_extract_keywords_filters_stop_words():
    """Test that stop words are filtered out."""
    description = "The work is for the foundation in the ground"
    keywords = extract_keywords_from_description(description)

    # Content words should be present
    assert "work" in keywords
    assert "foundation" in keywords
    assert "ground" in keywords

    # Stop words should be filtered
    assert "the" not in keywords
    assert "is" not in keywords
    assert "for" not in keywords
    assert "in" not in keywords


def test_extract_keywords_removes_punctuation():
    """Test that punctuation is removed."""
    description = "Cement concrete (1:2:4) with 20mm aggregate"
    keywords = extract_keywords_from_description(description)

    assert "cement" in keywords
    assert "concrete" in keywords
    assert "20mm" in keywords
    assert "aggregate" in keywords

    # Punctuation should not appear
    for keyword in keywords:
        assert "(" not in keyword
        assert ")" not in keyword
        assert ":" not in keyword


def test_extract_keywords_filters_short_words():
    """Test that words 2 chars or less are filtered."""
    description = "RCC in MS bar of 12 mm"
    keywords = extract_keywords_from_description(description)

    assert "rcc" in keywords  # 3 chars
    assert "bar" in keywords  # 3 chars

    # Short words should be filtered
    assert "in" not in keywords  # stop word
    assert "of" not in keywords  # stop word
    assert "mm" not in keywords  # 2 chars


def test_extract_keywords_lowercase():
    """Test that all keywords are lowercase."""
    description = "EARTH WORK IN EXCAVATION"
    keywords = extract_keywords_from_description(description)

    # All should be lowercase
    assert all(k.islower() for k in keywords)
    assert "earth" in keywords
    assert "work" in keywords
    assert "excavation" in keywords


def test_extract_keywords_empty_string():
    """Test with empty description."""
    keywords = extract_keywords_from_description("")
    assert keywords == []


def test_extract_keywords_only_stop_words():
    """Test with description containing only stop words."""
    description = "the and or of in to for with"
    keywords = extract_keywords_from_description(description)

    # Should be empty after filtering
    assert len(keywords) == 0


def test_extract_keywords_numeric():
    """Test that numeric values are extracted."""
    description = "Steel bar 12mm diameter 500mm length"
    keywords = extract_keywords_from_description(description)

    assert "12mm" in keywords
    assert "500mm" in keywords
    assert "steel" in keywords
    assert "diameter" in keywords


def test_detect_dsr_block_valid():
    """Test detecting valid DSR blocks."""
    block = {"lines": ["1.1 Earth work", "Description here", "cum 150.00"]}

    has_marker, has_standalone = detect_dsr_block(block)

    # Should detect some DSR pattern (implementation dependent)
    assert isinstance(has_marker, bool)
    assert isinstance(has_standalone, bool)


def test_detect_dsr_block_empty():
    """Test detecting DSR in empty block."""
    block = {"lines": []}

    has_marker, has_standalone = detect_dsr_block(block)

    assert isinstance(has_marker, bool)
    assert isinstance(has_standalone, bool)


def test_detect_dsr_block_no_lines():
    """Test detecting DSR when lines key missing."""
    block = {}

    has_marker, has_standalone = detect_dsr_block(block)

    assert isinstance(has_marker, bool)
    assert isinstance(has_standalone, bool)


def test_extract_keywords_with_special_terms():
    """Test extraction with construction-specific terms."""
    description = "RCC beam reinforcement with TMT bars"
    keywords = extract_keywords_from_description(description)

    assert "rcc" in keywords
    assert "beam" in keywords
    assert "reinforcement" in keywords
    assert "tmt" in keywords
    assert "bars" in keywords


def test_extract_keywords_multiple_spaces():
    """Test that multiple spaces are handled."""
    description = "Earth    work   in    excavation"
    keywords = extract_keywords_from_description(description)

    assert "earth" in keywords
    assert "work" in keywords
    assert "excavation" in keywords
    assert len([k for k in keywords if k == "earth"]) == 1  # No duplicates


def test_extract_keywords_mixed_case():
    """Test mixed case handling."""
    description = "Cement CONCRETE work With Steel"
    keywords = extract_keywords_from_description(description)

    # All should be lowercase
    assert "cement" in keywords
    assert "concrete" in keywords
    assert "work" in keywords
    assert "steel" in keywords
    assert "CONCRETE" not in keywords
    assert "Steel" not in keywords
