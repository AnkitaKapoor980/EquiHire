"""
Tests for parser service.
"""
import pytest
import requests
import os


PARSER_SERVICE_URL = os.getenv('PARSER_SERVICE_URL', 'http://localhost:5001')


def test_parser_health():
    """Test parser service health endpoint."""
    response = requests.get(f"{PARSER_SERVICE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'service' in data


def test_parse_pdf():
    """Test parsing a PDF resume."""
    # This would require an actual PDF file
    # For now, test the endpoint exists
    response = requests.post(f"{PARSER_SERVICE_URL}/api/parse")
    # Should return 400 without file
    assert response.status_code == 400


def test_parse_docx():
    """Test parsing a DOCX resume."""
    # This would require an actual DOCX file
    response = requests.post(f"{PARSER_SERVICE_URL}/api/parse")
    # Should return 400 without file
    assert response.status_code == 400

