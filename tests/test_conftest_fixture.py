"""Test that conftest fixtures properly isolate tests from .env file."""

from pptx_agent.config import Config


def test_config_ignores_env_file_during_tests():
    """Config should not load values from .env file during tests.

    This test verifies that the ignore_env_file fixture properly
    prevents .env file values from affecting test configurations.
    """
    # Create config with specific values
    config = Config(
        llm_provider="watsonx",
        llm_model="test-model",
        watsonx_url="https://us-south.ml.cloud.ibm.com",
        watsonx_apikey="test-api-key-fixture",
        watsonx_project_id="test-project-id",
        environment="production",
        max_retries=5,
        request_timeout=120,
    )  # type: ignore[call-arg]

    # Values should match what we passed, not what's in .env
    assert config.max_retries == 5, "max_retries should be 5, not overridden by .env"
    assert config.request_timeout == 120, "request_timeout should be 120, not overridden by .env"
    assert config.watsonx_apikey == "test-api-key-fixture", "API key should match test value"


def test_config_development_environment_not_overridden():
    """Development environment config should not be overridden by .env."""
    config = Config(
        llm_provider="watsonx",
        llm_model="test-model",
        watsonx_url="https://us-south.ml.cloud.ibm.com",
        watsonx_apikey="test-api-key-dev",
        watsonx_project_id="test-project-id",
        environment="development",
    )  # type: ignore[call-arg]

    # Development should have retries=1, timeout=60 (not .env values)
    assert config.max_retries == 1, "Development should have max_retries=1"
    assert config.request_timeout == 60, "Development should have request_timeout=60"
