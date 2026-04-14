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
    # Using non-test-pattern keys to pass validation (Phase 3 requirement)
    monkeypatch.setenv("LLM_PROVIDER", "watsonx")
    monkeypatch.setenv("LLM_MODEL", "granite-model")
    monkeypatch.setenv("WATSONX_URL", "https://cloud.ibm.com")
    monkeypatch.setenv("WATSONX_APIKEY", "abcdef1234567890")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "prod-project-id")
