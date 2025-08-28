"""Basic setup tests to verify environment is working."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings
from src.utils.logger import get_logger
from src.utils.http_client import HTTPClient


def test_settings_loading():
    """Test that settings are loaded correctly."""
    assert settings.environment in ["development", "staging", "production"]
    assert settings.database.host is not None
    assert settings.api.tecmundo_base_url is not None


def test_logger_creation():
    """Test that logger can be created."""
    logger = get_logger("test")
    assert logger is not None


def test_http_client_creation():
    """Test that HTTP client can be created."""
    with HTTPClient() as client:
        assert client is not None
        assert client.session is not None


def test_database_url_format():
    """Test that database URL is properly formatted."""
    db_url = settings.database.url
    assert db_url.startswith("postgresql://")
    assert settings.database.username in db_url
    assert str(settings.database.port) in db_url


def test_api_url_format():
    """Test that API URL is properly formatted."""
    full_url = settings.api.tecmundo_full_url
    assert full_url.startswith("https://")
    assert "tecmundo.com.br" in full_url