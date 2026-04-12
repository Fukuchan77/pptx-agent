"""Shared fixtures for agent tests."""

import pytest


@pytest.fixture(autouse=True)
def mock_llm_config(monkeypatch: pytest.MonkeyPatch):
    """Provide minimal LLM configuration for agent tests.

    This fixture is automatically applied to all agent tests.
    It sets minimal environment variables needed for Config validation
    when tests call get_config(), even though the actual LLM calls are mocked.
    """
    # Set minimal required environment variables for Config validation
    monkeypatch.setenv("LLM_PROVIDER", "watsonx")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("WATSONX_URL", "https://test.example.com")
    monkeypatch.setenv("WATSONX_APIKEY", "test-api-key-1234567890")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "test-project-id")
