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
    print("\n" + "="*60)
    print("WAITING FOR ALL MICROSERVICES TO BE READY")
    print("="*60)
    
    session = requests.Session()
    retries = Retry(
        total=5,  # Reduced retries since we have our own retry logic
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    
    all_services_ready = True
    
    for service_name, base_url in SERVICES.items():
        health_url = f"{base_url}/health"
        max_retries = 30  # 30 attempts
        retry_delay = 2   # 2 seconds between attempts
        backoff_factor = 1.2  # Exponential backoff
        current_delay = retry_delay
        
        print(f"\n[INFO] Checking {service_name} at {health_url}...")
        
        service_ready = False
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[INFO] Attempt {attempt}/{max_retries} for {service_name}...")
                response = session.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"[SUCCESS] ✓ {service_name} is ready and healthy!")
                    service_ready = True
                    break
                else:
                    print(f"[WARNING] {service_name} responded with HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                print(f"[WARNING] {service_name} connection failed: Connection refused")
            except requests.exceptions.Timeout as e:
                print(f"[WARNING] {service_name} connection timed out")
            except requests.exceptions.RequestException as e:
                print(f"[WARNING] {service_name} request failed: {str(e)}")
            except Exception as e:
                print(f"[WARNING] {service_name} unexpected error: {str(e)}")
            
            if attempt < max_retries:
                print(f"[INFO] Waiting {current_delay:.1f}s before next attempt...")
                time.sleep(current_delay)
                current_delay = min(current_delay * backoff_factor, 10)  # Cap at 10 seconds
        
        if not service_ready:
            print(f"[ERROR] ✗ {service_name} failed to become ready after {max_retries} attempts")
            all_services_ready = False
    
    print("\n" + "="*60)
    if all_services_ready:
        print("ALL SERVICES ARE READY! ✓")
        print("="*60)
        
        # Additional verification - test actual connectivity
        print("\n[INFO] Performing final connectivity verification...")
        for service_name, base_url in SERVICES.items():
            try:
                response = session.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"[VERIFY] ✓ {service_name} final check passed")
                else:
                    print(f"[VERIFY] ✗ {service_name} final check failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"[VERIFY] ✗ {service_name} final check failed: {str(e)}")
        
        print("\n[INFO] Service readiness check completed successfully!")
        return True
    else:
        print("SOME SERVICES FAILED TO START! ✗")
        print("="*60)
        
        # Print debugging information
        print("\n[DEBUG] Service status summary:")
        for service_name, base_url in SERVICES.items():
            try:
                response = session.get(f"{base_url}/health", timeout=2)
                print(f"[DEBUG] {service_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"[DEBUG] {service_name}: FAILED - {str(e)}")
        
        raise Exception("Not all services became ready. Check the logs above for details.")

@pytest.fixture(scope="session", autouse=True)
def wait_for_services_fixture():
    """Fixture to wait for all services to be ready before running tests."""
    print("\n" + "="*80)
    print("PYTEST SESSION STARTING - CHECKING SERVICE READINESS")
    print("="*80)
    
    try:
        wait_for_services()
        print("\n[SUCCESS] All services are ready! Starting tests...")
    except Exception as e:
        print(f"\n[FATAL ERROR] Service readiness check failed: {str(e)}")
        print("\nThis usually means:")
        print("1. Services are not running (check docker compose logs)")
        print("2. Services are not on the same network")
        print("3. Health check endpoints are not responding")
        print("4. DNS resolution is not working between containers")
        print("\nDebugging steps:")
        print("1. Run: docker compose ps")
        print("2. Run: docker compose logs [service_name]")
        print("3. Check if services are on equihire_network")
        print("4. Verify health endpoints manually")
        raise
    
    yield  # This is where the tests run
    
    print("\n" + "="*80)
    print("PYTEST SESSION COMPLETED")
    print("="*80)

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

@pytest.fixture
def service_health_check():
    """Fixture to verify a specific service is healthy."""
    def _check_service(service_name):
        if service_name not in SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        
        base_url = SERVICES[service_name]
        health_url = f"{base_url}/health"
        
        try:
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    return _check_service

@pytest.fixture
def wait_for_specific_service():
    """Fixture to wait for a specific service to be ready."""
    def _wait_for_service(service_name, max_wait_seconds=30):
        if service_name not in SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        
        base_url = SERVICES[service_name]
        health_url = f"{base_url}/health"
        
        print(f"\n[INFO] Waiting for {service_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    print(f"[SUCCESS] {service_name} is ready!")
                    return True
            except Exception:
                pass
            
            time.sleep(1)
        
        print(f"[ERROR] {service_name} did not become ready within {max_wait_seconds} seconds")
        return False
    
    return _wait_for_service