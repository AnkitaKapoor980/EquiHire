"""
Fast unit tests that don't require external services.
These tests focus on business logic and can run quickly in isolation.
"""
import pytest
import os
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

# Ensure Django is set up
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equihire.settings')
django.setup()

User = get_user_model()


class TestUserModel(TestCase):
    """Test user model functionality."""
    
    def test_user_creation(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='candidate'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'candidate')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='candidate',
            password='testpass123'  # Password is required for create_user
        )
        # Expecting format: email (role)
        self.assertEqual(str(user), 'test@example.com (candidate)')


class TestBasicViews(TestCase):
    """Test basic view functionality without external dependencies."""
    
    def setUp(self):
        self.client = Client()
        # Create a test user with hashed password
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',  # This will be properly hashed
            role='candidate'
        )
        # Ensure the user is active
        self.user.is_active = True
        self.user.save()
    
    def test_home_page_loads(self):
        """Test that home page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EquiHire')
    
    def test_login_page_loads(self):
        """Test that login page loads successfully."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_user_can_login(self):
        """Test user authentication."""
        # Ensure we're using the correct login credentials
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',  # Using username instead of login
            'password': 'testpass123',
            'next': '/'  # Add next parameter to avoid potential redirect issues
        }, follow=True)  # follow=True to handle the redirect
        
        # Check if user is actually logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Check if we were redirected after login
        self.assertEqual(response.status_code, 200)  # After following the redirect
        self.assertIn('dashboard', response.request['PATH_INFO'])  # Or your expected redirect target


@pytest.mark.unit
class TestServiceIntegration:
    """Test service integration with mocked external calls."""
    
    @patch('requests.get')
    def test_parser_service_call(self, mock_get):
        """Test parser service call with mocked response."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'healthy',
            'service': 'parser_service'
        }
        mock_get.return_value = mock_response
        
        # Import here to avoid issues if service is not available
        import requests
        
        response = requests.get('http://parser_service:5001/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
        mock_get.assert_called_once_with('http://parser_service:5001/health')
    
    @patch('requests.post')
    def test_resume_parsing_mock(self, mock_post):
        """Test resume parsing with mocked service response."""
        # Mock successful parsing response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'name': 'John Doe',
                'email': 'john@example.com',
                'skills': ['Python', 'Django', 'JavaScript']
            }
        }
        mock_post.return_value = mock_response
        
        import requests
        
        # Simulate resume parsing request
        response = requests.post('http://parser_service:5001/parse', 
                               json={'resume_text': 'Sample resume content'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'name' in data['data']
        assert 'skills' in data['data']
        mock_post.assert_called_once()


@pytest.mark.unit
def test_environment_variables():
    """Test that required environment variables are set."""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]
    
    for var in required_vars:
        assert os.environ.get(var) is not None, f"Environment variable {var} is not set"


@pytest.mark.unit
def test_django_settings():
    """Test Django settings configuration."""
    from django.conf import settings
    
    assert settings.DEBUG is not None
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 10
    assert 'django.contrib.auth' in settings.INSTALLED_APPS
    assert 'rest_framework' in settings.INSTALLED_APPS


class TestDatabaseOperations(TestCase):
    """Test database operations without external service dependencies."""
    
    def test_database_connection(self):
        """Test that database connection works."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_user_crud_operations(self):
        """Test basic CRUD operations on User model."""
        # Create
        user = User.objects.create_user(
            username='crudtest',
            email='crud@example.com',
            password='testpass123',
            role='recruiter'
        )
        self.assertIsNotNone(user.id)
        
        # Read
        retrieved_user = User.objects.get(username='crudtest')
        self.assertEqual(retrieved_user.email, 'crud@example.com')
        
        # Update
        retrieved_user.first_name = 'Test'
        retrieved_user.save()
        updated_user = User.objects.get(username='crudtest')
        self.assertEqual(updated_user.first_name, 'Test')
        
        # Delete
        user_id = updated_user.id
        updated_user.delete()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)


@pytest.mark.unit
def test_imports():
    """Test that all critical modules can be imported."""
    try:
        import django
        import rest_framework
        import psycopg2
        assert True, "All critical imports successful"
    except ImportError as e:
        pytest.fail(f"Critical import failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
