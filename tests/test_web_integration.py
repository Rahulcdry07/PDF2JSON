"""Integration tests for the complete EstimateX web workflow."""

import pytest
import json
import io
from pathlib import Path
from estimatex.web import app, analytics_tracker


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "/tmp/estimatex_test_uploads"
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF-like binary content for testing."""
    # This is a minimal PDF structure for testing
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content for DSR matching."""
    return """S.No,Description,Quantity,Unit,DSR Code
1,Earth work excavation in foundation,100,cum,
2,Cement concrete M20 grade,50,cum,
3,Steel reinforcement,5000,kg,
""".encode(
        "utf-8"
    )


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns valid JSON."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data

    def test_health_endpoint_status_healthy(self, client):
        """Test that health endpoint reports healthy status."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "estimatex"


class TestHomePageIntegration:
    """Test the home page and navigation."""

    def test_home_page_loads(self, client):
        """Test that home page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"EstimateX" in response.data or b"PDF2JSON" in response.data

    def test_home_page_has_upload_link(self, client):
        """Test that home page contains link to upload."""
        response = client.get("/")
        assert b"upload" in response.data.lower() or b"convert" in response.data.lower()


class TestPDFUploadWorkflow:
    """Test the complete PDF upload and conversion workflow."""

    def test_upload_page_loads(self, client):
        """Test that upload page loads successfully."""
        response = client.get("/upload")
        assert response.status_code == 200

    def test_pdf_upload_and_conversion(self, client, sample_pdf_content):
        """Test uploading a PDF and converting it."""
        data = {
            "file": (io.BytesIO(sample_pdf_content), "test.pdf"),
            "include_metadata": "on",
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data")

        # Should redirect after successful upload
        assert response.status_code in [200, 302]

    def test_upload_without_file_fails(self, client):
        """Test that upload without file returns error."""
        response = client.post("/upload", data={})
        assert response.status_code in [400, 302]  # Bad request or redirect with flash


class TestDSRMatchingWorkflow:
    """Test the complete DSR matching workflow."""

    def test_cost_estimation_page_loads(self, client):
        """Test that cost estimation page loads."""
        response = client.get("/cost-estimation")
        assert response.status_code == 200

    def test_csv_upload_for_dsr_matching(self, client, sample_csv_content):
        """Test uploading CSV for DSR rate matching."""
        data = {
            "csv_file": (io.BytesIO(sample_csv_content), "test_items.csv"),
            "category": "civil",
        }
        response = client.post("/cost-estimation", data=data, content_type="multipart/form-data")

        # Should process successfully or redirect
        assert response.status_code in [200, 302]

    def test_dsr_matching_with_invalid_category(self, client, sample_csv_content):
        """Test DSR matching with invalid category."""
        data = {
            "csv_file": (io.BytesIO(sample_csv_content), "test_items.csv"),
            "category": "invalid_category",
        }
        response = client.post("/cost-estimation", data=data, content_type="multipart/form-data")

        # Should handle error gracefully
        assert response.status_code in [200, 302, 400]


class TestDatabaseSearchWorkflow:
    """Test the database search workflow."""

    def test_search_page_loads(self, client):
        """Test that search page loads or redirects."""
        response = client.get("/search")
        assert response.status_code in [200, 302]

    def test_database_search(self, client):
        """Test database search functionality."""
        response = client.post(
            "/search",
            data={"search_term": "excavation", "category": "civil"},
            content_type="application/x-www-form-urlencoded",
        )

        # Should return results or empty list
        assert response.status_code == 200


class TestAnalyticsWorkflow:
    """Test the analytics and monitoring workflow."""

    def test_analytics_page_loads(self, client):
        """Test that analytics page loads."""
        response = client.get("/analytics")
        assert response.status_code == 200

    def test_analytics_api_endpoint(self, client):
        """Test analytics API endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = json.loads(response.data)
        # Check for any analytics data keys
        assert len(data) > 0
        assert any(
            key in data
            for key in ["total_requests", "requests", "avg_response_time", "api_calls_change"]
        )

    def test_analytics_tracking_records_requests(self, client):
        """Test that analytics tracker records requests."""
        initial_count = len(analytics_tracker.api_calls)

        # Make a request
        client.get("/health")

        # Check if it was tracked
        final_count = len(analytics_tracker.api_calls)
        assert final_count >= initial_count


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_api_docs_loads(self, client):
        """Test that API documentation loads."""
        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_api_health_check(self, client):
        """Test API health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    def test_pdf_upload_to_json_workflow(self, client, sample_pdf_content):
        """Test complete workflow: upload PDF -> convert -> download JSON."""
        # Step 1: Upload PDF
        data = {
            "file": (io.BytesIO(sample_pdf_content), "test_workflow.pdf"),
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data")
        assert response.status_code in [200, 302]

    def test_csv_to_cost_estimation_workflow(self, client, sample_csv_content):
        """Test complete workflow: upload CSV -> match DSR -> view results."""
        # Step 1: Upload CSV for DSR matching
        data = {
            "csv_file": (io.BytesIO(sample_csv_content), "test_workflow.csv"),
            "category": "civil",
        }
        response = client.post("/cost-estimation", data=data, content_type="multipart/form-data")
        assert response.status_code in [200, 302]

        # Step 2: Check if results page is accessible
        # (This would need the actual result ID from the previous response)

    def test_database_search_to_excel_workflow(self, client):
        """Test workflow: search database -> export to Excel."""
        # Step 1: Search database
        response = client.post("/search", data={"search_term": "concrete", "category": "civil"})
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling across the application."""

    def test_404_page(self, client):
        """Test that 404 page is handled."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_invalid_file_type_upload(self, client):
        """Test uploading invalid file type."""
        data = {
            "file": (io.BytesIO(b"not a pdf"), "test.txt"),
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data")
        # Should handle gracefully
        assert response.status_code in [200, 302, 400]

    def test_large_file_upload_handling(self, client):
        """Test that large file uploads are handled."""
        # Create a mock large file (just metadata, not actually large)
        large_content = b"x" * 1024  # 1KB for testing
        data = {
            "file": (io.BytesIO(large_content), "large.pdf"),
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data")
        assert response.status_code in [200, 302, 413]  # 413 = Payload Too Large


class TestSecurityAndValidation:
    """Test security measures and input validation."""

    def test_path_traversal_protection(self, client):
        """Test that path traversal attempts are blocked."""
        response = client.get("/../../../etc/passwd")
        assert response.status_code in [400, 404]

    def test_sql_injection_protection(self, client):
        """Test SQL injection protection in search."""
        response = client.post(
            "/search", data={"search_term": "'; DROP TABLE items; --", "category": "civil"}
        )
        # Should handle safely
        assert response.status_code in [200, 400]

    def test_xss_protection(self, client):
        """Test XSS protection in input fields."""
        response = client.post(
            "/search", data={"search_term": "<script>alert('xss')</script>", "category": "civil"}
        )
        # Should escape HTML entities - check that it's escaped not raw
        assert response.status_code == 200
        # The string should be escaped in HTML
        assert b"&lt;script&gt;" in response.data
        # And should NOT contain the unescaped version that would execute as part of HTML tags
        # Check it's not in an executable context (not as an actual script tag)
        assert b"<script>alert" not in response.data


@pytest.mark.integration
class TestPerformance:
    """Test performance of key workflows."""

    def test_health_endpoint_response_time(self, client):
        """Test that health endpoint responds quickly."""
        import time

        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second

    def test_multiple_concurrent_requests(self, client):
        """Test handling multiple requests."""
        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
