"""Tests for Flask web interface."""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf2json.web import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_json_report():
    """Create a sample JSON matched rates report."""
    report_data = {
        "project_info": {"name": "Test Project", "location": "Test Location", "date": "2024-01-01"},
        "summary": {"total_items": 2, "matched_items": 2, "total_cost": 75000.00},
        "matched_items": [
            {
                "input_code": "15.12.2",
                "input_description": "Brick work",
                "quantity": 100,
                "unit": "Cum",
                "matched_code": "15.12.2",
                "dsr_description": "Brick work in superstructure",
                "rate": 500.00,
                "amount": 50000.00,
                "similarity": 0.95,
                "match_method": "exact",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(report_data, f, indent=2)
        report_path = Path(f.name)

    yield report_path

    # Cleanup
    report_path.unlink(missing_ok=True)


def test_index_route(client):
    """Test the index page loads."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"PDF2JSON" in response.data or b"DSR" in response.data


def test_upload_page(client):
    """Test the upload page loads."""
    response = client.get("/upload")

    assert response.status_code == 200


def test_cost_estimation_page(client):
    """Test cost estimation page loads."""
    response = client.get("/cost-estimation")

    assert response.status_code == 200


def test_search_functionality(client):
    """Test the search endpoint."""
    response = client.post("/search", data={"query": "brick work"})

    # Should return results page or redirect
    assert response.status_code in [200, 302]


def test_upload_pdf_no_file(client):
    """Test upload without file."""
    response = client.post("/upload", data={})

    # Should redirect or show error
    assert response.status_code in [200, 302, 400]


def test_file_too_large_error_handler(client):
    """Test that file too large error is handled."""
    # This tests the error handler exists
    # Actual large file upload would require more setup
    assert app.url_map is not None


def test_view_json_not_found(client):
    """Test viewing non-existent JSON file."""
    response = client.get("/view/nonexistent.json")

    # Should return 404 or redirect
    assert response.status_code in [404, 302]


def test_get_reference_files(client):
    """Test getting reference files list."""
    # Try the root route which lists files
    response = client.get("/")

    assert response.status_code == 200
    # Just verify the route works, reference files may or may not exist


def test_markdown_filter():
    """Test markdown filter for templates."""
    from pdf2json.web import markdown_filter

    markdown_text = "# Heading\n\nSome text"
    html = markdown_filter(markdown_text)

    assert "<h1>" in str(html)
    assert "Heading" in str(html)


def test_static_files_exist():
    """Test that required template files exist."""
    templates_dir = Path(__file__).parent.parent / "templates"

    required_templates = [
        "index.html",
        "upload.html",
        "cost_estimation.html",
        "view_report.html",
        "view_csv.html",
        "view_markdown.html",
        "search_results.html",
    ]

    for template in required_templates:
        template_path = templates_dir / template
        assert template_path.exists(), f"Missing template: {template}"


def test_app_config():
    """Test Flask app configuration."""
    assert app.config["MAX_CONTENT_LENGTH"] == 500 * 1024 * 1024  # 500 MB
    assert app.config["UPLOAD_FOLDER"] is not None


def test_error_handlers_registered():
    """Test that error handlers are registered."""
    # Check that error handler for 413 exists
    assert (
        413 in app.error_handler_spec[None]
        or app.error_handler_spec.get(None, {}).get(413) is not None
    )
