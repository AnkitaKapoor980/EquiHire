"""
Pytest configuration and fixtures.
"""
import pytest
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equihire.settings')
django.setup()

# Service URLs - these should match your docker-compose service names
SERVICES = {
    'parser_service': 'http://parser_service:5001',
    'matcher_service': 'http://matcher_service:5002',
    'fairness_service': 'http://fairness_service:5003',
    'explainability_service': 'http://explainability_service:5004',
}

def wait_for_services():
    """Wait for all services to be ready before running tests."""
    session = requests.Session()
    retries = Retry(
        total=30,  # 30 retries
        backoff_factor=1,  # Exponential backoff factor
        status_forcelist=[500, 502, 503, 504],
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    
    for service_name, base_url in SERVICES.items():
        health_url = f"{base_url}/health"
        max_retries = 30
        retry_delay = 5  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                response = session.get(health_url, timeout=5)
                if response.status_code == 200:
                    print(f"[INFO] {service_name} is ready")
                    break
                else:
                    print(f"[INFO] {service_name} not ready yet (HTTP {response.status_code}), retrying in {retry_delay}s...")
            except requests.RequestException as e:
                print(f"[INFO] {service_name} not reachable: {str(e)}, retrying in {retry_delay}s...")
            
            if attempt == max_retries:
                raise Exception(f"Timed out waiting for {service_name} to become ready")
                
            time.sleep(retry_delay)

@pytest.fixture(scope="session", autouse=True)
def wait_for_services_fixture():
    """Fixture to wait for all services to be ready before running tests."""
    print("\n[INFO] Waiting for all services to be ready...")
    wait_for_services()
    print("[INFO] All services are ready!\n")

@pytest.fixture
def api_client():
    """Fixture for API client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def user_data():
    """Fixture for test user data."""
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'testpass123',
        'role': 'candidate'
    }

@pytest.fixture
def service_urls():
    """Fixture providing base URLs for all services."""
    return dict(SERVICES)

