"""Simple flask app unit tests."""
# pylint: disable=E0401
# pylint: disable=E1101

from cats import main
import pytest


@pytest.fixture
def client():
    """Test client"""
    app = main.app

    with app.test_client() as client:
        yield client

def test_root_route(client):
    """Test root route."""

    response = client.get('/')
    assert b'Hello, World!' in response.data

def test_greeting_route(client):
    """Test root route."""

    response = client.get('/___test___')
    assert b'___test___' in response.data
