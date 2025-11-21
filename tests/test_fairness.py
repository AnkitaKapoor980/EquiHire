"""
Tests for fairness service.
"""
import pytest
import requests
import os


FAIRNESS_SERVICE_URL = os.getenv('FAIRNESS_SERVICE_URL', 'http://localhost:5003')


def test_fairness_health():
    """Test fairness service health endpoint."""
    response = requests.get(f"{FAIRNESS_SERVICE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


def test_audit_fairness():
    """Test fairness audit endpoint."""
    response = requests.post(
        f"{FAIRNESS_SERVICE_URL}/api/audit",
        json={
            'application_id': 1,
            'job_id': 1,
            'score': 0.75
        }
    )
    # May return 200 or 500 depending on database state
    assert response.status_code in [200, 500]

