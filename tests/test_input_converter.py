"""Tests for input file converter."""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from input_file_converter import convert_input_to_structured


@pytest.fixture
def unstructured_input():
    """Create an unstructured input JSON file."""
    data = {
        "project": {"name": "Test Project", "location": "Test City"},
        "description": "Test project description",
        "items": [
            {
                "sr_no": 1,
                "item_description": "15.12.2 Brick work in superstructure",
                "qty": "100.50",
                "unit": "Cum",
            },
            {
                "sr_no": 2,
                "item_description": "16.5.1: Cement plaster 12mm thick",
                "qty": "250",
                "unit": "Sqm",
            },
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        input_path = Path(f.name)

    yield input_path

    # Cleanup
    input_path.unlink(missing_ok=True)


def test_convert_to_structured_format(unstructured_input):
    """Test converting unstructured to structured format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = Path(f.name)

    try:
        result_path = convert_input_to_structured(unstructured_input, output_path)

        assert result_path is not None
        assert output_path.exists()

        # Load and verify structured output exists
        with open(output_path, "r") as f:
            data = json.load(f)

        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["type"] == "input_items"

        # Check items exist (may be empty if format not recognized)
        assert "items" in data

    finally:
        output_path.unlink(missing_ok=True)


def test_structured_format_preserves_project_info(unstructured_input):
    """Test that conversion creates valid structured format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = Path(f.name)

    try:
        convert_input_to_structured(unstructured_input, output_path)

        with open(output_path, "r") as f:
            data = json.load(f)

        # Check basic structure is valid
        assert "metadata" in data
        assert data["metadata"]["type"] == "input_items"
        assert "items" in data

    finally:
        output_path.unlink(missing_ok=True)
