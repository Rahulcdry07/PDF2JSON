#!/usr/bin/env python3
"""Tests for read_json.py script."""

import json
import sys
from pathlib import Path
import pytest
from click.testing import CliRunner

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from read_json import load_json, get_all_text_blocks, main


@pytest.fixture
def sample_json_data():
    """Sample JSON data with text blocks."""
    return {
        "document": {
            "pages_data": [
                {
                    "page": 1,
                    "blocks": [
                        {
                            "lines": [
                                "First line of text",
                                "Second line of text",
                                "",  # Empty line should be filtered
                                "Third line with keyword",
                            ]
                        },
                        {"lines": ["Another block", "With multiple lines"]},
                    ],
                },
                {
                    "page": 2,
                    "blocks": [{"lines": ["Page 2 content", "More text here"]}],
                },
            ]
        }
    }


@pytest.fixture
def temp_json_file(tmp_path, sample_json_data):
    """Create temporary JSON file."""
    json_file = tmp_path / "test.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sample_json_data, f)
    return json_file


def test_load_json(temp_json_file, sample_json_data):
    """Test loading JSON data from file."""
    data = load_json(temp_json_file)
    assert data == sample_json_data
    assert "document" in data
    assert "pages_data" in data["document"]


def test_get_all_text_blocks(sample_json_data):
    """Test extracting all text blocks."""
    texts = get_all_text_blocks(sample_json_data)

    # Should have 7 non-empty lines
    assert len(texts) == 7

    # Check specific content
    assert "First line of text" in texts
    assert "Second line of text" in texts
    assert "Third line with keyword" in texts
    assert "Another block" in texts
    assert "Page 2 content" in texts

    # Empty lines should be filtered
    assert "" not in texts


def test_get_all_text_blocks_empty_document():
    """Test with empty document."""
    data = {"document": {"pages_data": []}}
    texts = get_all_text_blocks(data)
    assert texts == []


def test_get_all_text_blocks_no_blocks():
    """Test with pages but no blocks."""
    data = {"document": {"pages_data": [{"page": 1, "blocks": []}]}}
    texts = get_all_text_blocks(data)
    assert texts == []


def test_main_print_text(temp_json_file):
    """Test CLI with --print-text option."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", str(temp_json_file), "--print-text"])

    assert result.exit_code == 0
    assert "Block 0:" in result.output
    assert "First line of text" in result.output


def test_main_search_found(temp_json_file):
    """Test CLI search that finds matches."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", str(temp_json_file), "--search", "keyword"])

    assert result.exit_code == 0
    assert "Third line with keyword" in result.output


def test_main_search_not_found(temp_json_file):
    """Test CLI search with no matches."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["--json", str(temp_json_file), "--search", "nonexistent"]
    )

    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_main_search_case_insensitive(temp_json_file):
    """Test that search is case-insensitive."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", str(temp_json_file), "--search", "KEYWORD"])

    assert result.exit_code == 0
    assert "Third line with keyword" in result.output


def test_main_no_options(temp_json_file):
    """Test CLI with no print or search options."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", str(temp_json_file)])

    assert result.exit_code == 0
    assert "Use --print-text or --search option" in result.output


def test_main_missing_file():
    """Test CLI with non-existent file."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", "nonexistent.json", "--print-text"])

    # Click should report error for non-existent file
    assert result.exit_code != 0


def test_main_search_regex(temp_json_file):
    """Test search with regex pattern."""
    runner = CliRunner()
    result = runner.invoke(main, ["--json", str(temp_json_file), "--search", "line.*text"])

    assert result.exit_code == 0
    # Should match lines containing "line" followed by "text"
    assert "First line of text" in result.output or "Second line of text" in result.output


def test_get_all_text_blocks_whitespace():
    """Test that whitespace-only lines are filtered."""
    data = {
        "document": {
            "pages_data": [
                {
                    "page": 1,
                    "blocks": [
                        {"lines": ["Valid text", "   ", "\t", "\n", "More valid text"]}
                    ],
                }
            ]
        }
    }
    texts = get_all_text_blocks(data)

    assert len(texts) == 2
    assert "Valid text" in texts
    assert "More valid text" in texts
    # Whitespace-only lines should be filtered
    assert "   " not in texts
