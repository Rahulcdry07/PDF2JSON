"""
Tests for analytics and API documentation endpoints
"""

import pytest
from src.estimatex.web import app, analytics_tracker
import json
import time


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Reset analytics tracker before each test
        analytics_tracker.api_calls = []
        yield client


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_api_stats_endpoint_empty(client):
    """Test API stats endpoint with no data"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total_api_calls" in data
    assert "avg_response_time" in data
    assert "error_rate" in data


def test_api_stats_endpoint_with_data(client):
    """Test API stats endpoint with tracked data"""
    # Make some requests to generate analytics data
    client.get("/")
    client.get("/health")
    client.get("/upload")

    response = client.get("/api/stats")
    assert response.status_code == 200
    data = json.loads(response.data)

    # Stats are captured before the response, so the stats endpoint itself is tracked
    # Should have 4 calls: /, /health, /upload, /api/stats
    assert data["total_api_calls"] >= 3
    assert len(analytics_tracker.api_calls) >= 4


def test_analytics_dashboard(client):
    """Test analytics dashboard page"""
    response = client.get("/analytics")
    assert response.status_code == 200
    assert b"Analytics Dashboard" in response.data
    assert b"Total API Calls" in response.data
    assert b"PDF Conversions" in response.data


def test_api_docs(client):
    """Test API documentation page"""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert b"API Documentation" in response.data
    assert b"PDF2JSON" in response.data
    assert b"/upload" in response.data
    assert b"/health" in response.data


def test_analytics_tracking(client):
    """Test that analytics tracking middleware works"""
    initial_count = len(analytics_tracker.api_calls)

    # Make a request
    response = client.get("/")
    assert response.status_code == 200

    # Check that request was tracked
    assert len(analytics_tracker.api_calls) == initial_count + 1

    last_call = analytics_tracker.api_calls[-1]
    assert last_call["method"] == "GET"
    assert last_call["path"] == "/"
    assert last_call["status_code"] == 200
    assert "timestamp" in last_call
    assert "response_time" in last_call
    assert last_call["response_time"] >= 0


def test_analytics_tracks_errors(client):
    """Test that analytics tracks error responses"""
    initial_count = len(analytics_tracker.api_calls)

    # Make a request that will result in 404
    response = client.get("/nonexistent-route")

    # Check that error was tracked
    assert len(analytics_tracker.api_calls) == initial_count + 1
    last_call = analytics_tracker.api_calls[-1]
    assert last_call["status_code"] == 404


def test_analytics_stats_calculation(client):
    """Test statistics calculation accuracy"""
    # Reset tracker
    analytics_tracker.api_calls = []

    # Make some successful requests
    for _ in range(5):
        client.get("/")

    # Make some error requests
    for _ in range(2):
        client.get("/nonexistent")

    stats = analytics_tracker.get_stats()

    # Total calls should include all requests plus the stats call
    assert stats["total_api_calls"] >= 7
    assert stats["total_errors"] >= 2
    assert stats["error_rate"] > 0


def test_analytics_popular_endpoints(client):
    """Test popular endpoints tracking"""
    analytics_tracker.api_calls = []

    # Make multiple requests to different endpoints
    for _ in range(5):
        client.get("/")
    for _ in range(3):
        client.get("/health")
    client.get("/upload")

    stats = analytics_tracker.get_stats()

    assert len(stats["popular_endpoints"]) > 0
    # Root should be the most popular
    most_popular = stats["popular_endpoints"][0]
    assert most_popular["path"] == "/"
    assert most_popular["calls"] >= 5


def test_analytics_recent_activity(client):
    """Test recent activity tracking"""
    analytics_tracker.api_calls = []

    # Make some requests
    client.get("/")
    client.get("/health")
    client.get("/upload")

    stats = analytics_tracker.get_stats()

    # Should have recent activity
    assert len(stats["recent_activity"]) >= 3

    # Most recent should be last
    recent = stats["recent_activity"][-1]
    assert recent["path"] == "/upload"


def test_analytics_response_time_tracking(client):
    """Test response time tracking"""
    analytics_tracker.api_calls = []

    # Make a request
    client.get("/")

    stats = analytics_tracker.get_stats()

    # Should have response time data
    assert stats["avg_response_time"] >= 0
    assert analytics_tracker.api_calls[0]["response_time"] > 0


def test_analytics_max_history_limit(client):
    """Test that analytics respects max history limit"""
    analytics_tracker.api_calls = []
    analytics_tracker.max_history = 10

    # Make more requests than the limit
    for _ in range(15):
        client.get("/")

    # Should only keep the last 10
    assert len(analytics_tracker.api_calls) == 10


def test_api_docs_contains_all_endpoints(client):
    """Test that API docs include all major endpoints"""
    response = client.get("/api/docs")
    content = response.data.decode()

    # Check for major endpoints
    assert "/upload" in content
    assert "/health" in content
    assert "/api/stats" in content
    assert "/analytics" in content
    assert "/cost-estimation" in content
    assert "/api/excel/sheets" in content
    assert "/api/excel/convert" in content


def test_analytics_dashboard_displays_charts(client):
    """Test that analytics dashboard includes chart elements"""
    # Make some requests to generate data
    client.get("/")
    client.get("/health")

    response = client.get("/analytics")
    content = response.data.decode()

    # Check for chart.js and canvas elements
    assert "chart.js" in content.lower()
    assert "apiCallsChart" in content
    assert "endpointChart" in content


def test_analytics_endpoint_distribution(client):
    """Test endpoint distribution calculation"""
    analytics_tracker.api_calls = []

    # Make requests to different endpoints
    client.get("/")
    client.get("/")
    client.get("/health")
    client.get("/upload")

    stats = analytics_tracker.get_stats()

    # Should have endpoint distribution data
    assert len(stats["endpoint_labels"]) > 0
    assert len(stats["endpoint_data"]) > 0
    assert len(stats["endpoint_labels"]) == len(stats["endpoint_data"])


def test_analytics_hourly_breakdown(client):
    """Test hourly breakdown calculation"""
    analytics_tracker.api_calls = []

    # Make some requests
    for _ in range(5):
        client.get("/")

    stats = analytics_tracker.get_stats()

    # Should have 24 hours of data
    assert len(stats["hourly_labels"]) == 24
    assert len(stats["hourly_calls"]) == 24

    # Sum of hourly calls should equal total
    assert sum(stats["hourly_calls"]) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
