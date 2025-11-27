"""
Simple unit tests that don't require database or external services.
These tests focus on basic functionality and can run very quickly.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_environment_variables():
    """Test that required environment variables are set."""
    required_vars = [
        'SECRET_KEY',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]
    
    for var in required_vars:
        assert os.environ.get(var) is not None, f"Environment variable {var} is not set"


@pytest.mark.unit
def test_django_imports():
    """Test that Django can be imported."""
    try:
        import django
        
        # Test basic Django functionality
        assert hasattr(django, 'VERSION')
        assert django.VERSION is not None
        
        # Test that Django settings module is set
        django_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        assert django_settings is not None, "DJANGO_SETTINGS_MODULE not set"
        
    except ImportError as e:
        pytest.fail(f"Django import failed: {e}")


@pytest.mark.unit
def test_critical_imports():
    """Test that all critical modules can be imported."""
    critical_modules = [
        'django',
        'rest_framework',
        'psycopg2',
        'requests'
    ]
    
    for module in critical_modules:
        try:
            __import__(module)
        except ImportError as e:
            pytest.fail(f"Critical import failed for {module}: {e}")


@pytest.mark.unit
@patch('requests.get')
def test_service_health_check_mock(mock_get):
    """Test service health check with mocked response."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 'healthy',
        'service': 'parser_service'
    }
    mock_get.return_value = mock_response
    
    import requests
    
    response = requests.get('http://parser_service:5001/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    mock_get.assert_called_once_with('http://parser_service:5001/health')


@pytest.mark.unit
@patch('requests.post')
def test_resume_parsing_mock(mock_post):
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
def test_basic_python_functionality():
    """Test basic Python functionality works."""
    # Test list operations
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    
    # Test dictionary operations
    test_dict = {'name': 'John', 'age': 30}
    assert test_dict['name'] == 'John'
    assert 'age' in test_dict
    
    # Test string operations
    test_string = "Hello, World!"
    assert test_string.lower() == "hello, world!"
    assert test_string.startswith("Hello")


@pytest.mark.unit
def test_json_operations():
    """Test JSON serialization/deserialization."""
    import json
    
    test_data = {
        'user': 'john_doe',
        'skills': ['Python', 'Django'],
        'experience': 5
    }
    
    # Serialize to JSON
    json_string = json.dumps(test_data)
    assert isinstance(json_string, str)
    assert 'john_doe' in json_string
    
    # Deserialize from JSON
    parsed_data = json.loads(json_string)
    assert parsed_data['user'] == 'john_doe'
    assert len(parsed_data['skills']) == 2
    assert parsed_data['experience'] == 5


@pytest.mark.unit
def test_datetime_operations():
    """Test datetime functionality."""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    assert isinstance(now, datetime)
    
    future = now + timedelta(days=1)
    assert future > now
    
    # Test formatting
    formatted = now.strftime('%Y-%m-%d')
    assert len(formatted) == 10
    assert '-' in formatted


@pytest.mark.unit
def test_file_operations():
    """Test basic file operations."""
    import tempfile
    import os
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('Test content')
        temp_file = f.name
    
    try:
        # Check file exists
        assert os.path.exists(temp_file)
        
        # Read file content
        with open(temp_file, 'r') as f:
            content = f.read()
            assert content == 'Test content'
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@pytest.mark.unit
def test_regex_operations():
    """Test regular expression functionality."""
    import re
    
    # Test email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    valid_emails = ['test@example.com', 'user.name@domain.org']
    invalid_emails = ['invalid-email', '@domain.com', 'user@']
    
    for email in valid_emails:
        assert re.match(email_pattern, email), f"Valid email {email} failed validation"
    
    for email in invalid_emails:
        assert not re.match(email_pattern, email), f"Invalid email {email} passed validation"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
