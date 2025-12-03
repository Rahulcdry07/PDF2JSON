"""Tests for text similarity calculations."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from text_similarity import calculate_text_similarity


def test_calculate_text_similarity_identical():
    """Test similarity with identical texts."""
    text1 = "Brick work in superstructure"
    text2 = "Brick work in superstructure"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert similarity == 1.0


def test_calculate_text_similarity_similar():
    """Test similarity with similar texts."""
    text1 = "Brick work in superstructure with common burnt clay"
    text2 = "Brick work in superstructure"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert 0.6 <= similarity <= 1.0


def test_calculate_text_similarity_different():
    """Test similarity with different texts."""
    text1 = "Brick work in superstructure"
    text2 = "Painting with oil paint"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert 0.0 <= similarity <= 0.3


def test_calculate_text_similarity_empty():
    """Test similarity with empty strings."""
    similarity1 = calculate_text_similarity("", "some text")
    similarity2 = calculate_text_similarity("some text", "")
    similarity3 = calculate_text_similarity("", "")
    
    assert similarity1 == 0.0
    assert similarity2 == 0.0
    # Empty strings should match perfectly
    assert similarity3 == 1.0 or similarity3 == 0.0  # Implementation dependent


def test_fuzzy_match_exact():
    """Test fuzzy matching with exact match."""
    query = "15.12.2"
    candidates = ["15.12.2", "15.12.3", "16.5.1"]
    

    text2 = "brick work"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert similarity > 0.9  # Should be nearly identical


def test_fuzzy_match_exact():
    """Test exact text matching."""
    text1 = "15.12.2"
    text2 = "15.12.2"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert similarity == 1.0  # Perfect match


def test_special_characters_handling():
    """Test handling of special characters."""
    text1 = "Brick-work (12mm)"
    text2 = "Brick work 12mm"
    
    similarity = calculate_text_similarity(text1, text2)
    
    # Should still recognize similarity despite punctuation
    assert similarity > 0.7


def test_numeric_code_matching():
    """Test matching numeric codes."""
    code1 = "15.12.2"
    code2 = "15.12.2"
    code3 = "15.12.3"
    
    sim_exact = calculate_text_similarity(code1, code2)
    sim_close = calculate_text_similarity(code1, code3)
    
    assert sim_exact == 1.0
    assert 0.7 <= sim_close < 1.0  # Similar but not identical
