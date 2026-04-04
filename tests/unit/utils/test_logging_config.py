"""Tests for Pydantic Logfire configuration."""

import os
from unittest.mock import MagicMock, patch

from pptx_agent.utils import logging_config
from pptx_agent.utils.logging_config import (
    configure_logfire,
    get_logfire_config,
    is_logfire_enabled,
)


def test_logging_config_module_exists():
    """Test that logging_config module can be imported."""
    assert logging_config is not None


def test_configure_logfire_function_exists():
    """Test that configure_logfire function exists."""
    assert callable(configure_logfire)


def test_configure_logfire_returns_none():
    """Test that configure_logfire executes without error."""
    # Should not raise an exception
    result = configure_logfire()
    assert result is None


def test_logfire_disabled_in_test_mode():
    """Test that Logfire is disabled in test environment."""
    # In test environment, Logfire should be disabled
    enabled = is_logfire_enabled()
    assert enabled is False


def test_get_logfire_config():
    """Test getting Logfire configuration."""
    config = get_logfire_config()
    assert config is not None
    assert hasattr(config, "enabled")
    assert hasattr(config, "service_name")


def test_is_logfire_enabled_with_true_values():
    """Test that is_logfire_enabled returns True with various true values."""
    # Test with different true values
    for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
        with patch.dict(os.environ, {"LOGFIRE_ENABLED": value}, clear=True):
            # Remove PYTEST_CURRENT_TEST to allow logfire to be enabled
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            enabled = is_logfire_enabled()
            assert enabled is True, f"Expected True for LOGFIRE_ENABLED={value}"


def test_is_logfire_enabled_with_false_values():
    """Test that is_logfire_enabled returns False with false values."""
    # Test with different false values
    for value in ["false", "False", "FALSE", "0", "no", "No", "NO", ""]:
        with patch.dict(os.environ, {"LOGFIRE_ENABLED": value}, clear=True):
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            enabled = is_logfire_enabled()
            assert enabled is False, f"Expected False for LOGFIRE_ENABLED={value}"


def test_get_logfire_config_with_environment_variables():
    """Test get_logfire_config with custom environment variables."""
    with patch.dict(
        os.environ,
        {
            "LOGFIRE_ENABLED": "true",
            "LOGFIRE_SERVICE_NAME": "test-service",
            "ENVIRONMENT": "production",
        },
        clear=True,
    ):
        os.environ.pop("PYTEST_CURRENT_TEST", None)
        config = get_logfire_config()
        assert config.enabled is True
        assert config.service_name == "test-service"
        assert config.environment == "production"


def test_configure_logfire_with_enabled_logfire():
    """Test configure_logfire when logfire is enabled and available."""
    # Mock logfire module
    mock_logfire = MagicMock()

    with patch.dict(
        os.environ, {"LOGFIRE_ENABLED": "true", "LOGFIRE_SERVICE_NAME": "test-app"}, clear=True
    ):
        os.environ.pop("PYTEST_CURRENT_TEST", None)
        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            configure_logfire()
            # Verify logfire.configure was called with correct parameters
            mock_logfire.configure.assert_called_once()
            call_kwargs = mock_logfire.configure.call_args[1]
            assert call_kwargs["service_name"] == "test-app"
            assert "environment" in call_kwargs


def test_configure_logfire_with_import_error():
    """Test configure_logfire handles ImportError gracefully."""
    with patch.dict(os.environ, {"LOGFIRE_ENABLED": "true"}, clear=True):
        os.environ.pop("PYTEST_CURRENT_TEST", None)
        # Patch __import__ to raise ImportError for logfire
        with patch("builtins.__import__", side_effect=ImportError("logfire not installed")):
            # Should not raise an exception
            result = configure_logfire()
            assert result is None


def test_configure_logfire_with_configuration_error():
    """Test configure_logfire handles configuration errors gracefully."""
    # Mock logfire module that raises exception during configure
    mock_logfire = MagicMock()
    mock_logfire.configure.side_effect = RuntimeError("Configuration failed")

    with patch.dict(os.environ, {"LOGFIRE_ENABLED": "true"}, clear=True):
        os.environ.pop("PYTEST_CURRENT_TEST", None)
        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            # Should not raise an exception even if logfire.configure fails
            result = configure_logfire()
            assert result is None
