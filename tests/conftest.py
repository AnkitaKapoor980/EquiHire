"""
Pytest configuration and fixtures.
"""
import pytest
import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equihire.settings')
django.setup()


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

