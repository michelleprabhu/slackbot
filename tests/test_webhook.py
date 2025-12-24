import pytest
from fastapi.testclient import TestClient
import json
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from day1_slack_alert.webhook_receiver import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_webhook_valid_payload():
    """Test webhook with valid EPM payload"""
    payload = {
        "incident_title": "Data Integration: Workday Sync",
        "impact_level": "Critical",
        "details": "API endpoint returned 403 Forbidden during nightly refresh."
    }
    
    token = os.getenv("WEBHOOK_SECRET", "test_secret")
    response = client.post(
        "/webhook/epm_incident",
        json=payload,
        headers={"X-Webhook-Token": token}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "timestamp" in response.json()

def test_webhook_invalid_payload():
    """Test webhook with invalid payload"""
    # Missing required fields
    payload = {
        "incident_title": "Data Integration"
    }
    
    response = client.post(
        "/webhook/epm_incident",
        json=payload
    )
    
    assert response.status_code == 422  # Validation error

def test_webhook_malformed_json():
    """Test webhook with malformed JSON"""
    response = client.post(
        "/webhook/epm_incident",
        data="not a json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main(["-v", __file__])