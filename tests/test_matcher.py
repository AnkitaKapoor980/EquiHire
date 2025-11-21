"""
Tests for matcher service.
"""
import pytest
import requests
import os


MATCHER_SERVICE_URL = os.getenv('MATCHER_SERVICE_URL', 'http://localhost:5002')


def test_matcher_health():
    """Test matcher service health endpoint."""
    response = requests.get(f"{MATCHER_SERVICE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


def test_generate_embedding():
    """Test embedding generation."""
    response = requests.post(
        f"{MATCHER_SERVICE_URL}/api/embed",
        json={'text': 'Software engineer with Python experience'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'embedding' in data
    assert len(data['embedding']) == 384  # Sentence-BERT dimension


def test_batch_embed():
    """Test batch embedding generation."""
    texts = [
        'Software engineer with Python',
        'Data scientist with ML experience'
    ]
    response = requests.post(
        f"{MATCHER_SERVICE_URL}/api/batch_embed",
        json={'texts': texts}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'embeddings' in data
    assert len(data['embeddings']) == 2

