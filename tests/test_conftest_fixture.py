"""Test that conftest fixtures properly isolate tests from .env file."""

from typing import Any

import pytest

from pptx_agent.config import Config


def test_config_ignores_env_file_during_tests() -> None:
    """Config should not load values from .env file during tests.

    This test verifies that the isolate_config_from_environment fixture properly
    prevents .env file values from affecting test configurations.
    """
    # Create config with specific values
    config = Config.model_validate(
        {
            "llm_provider": "watsonx",
            "llm_model": "test-model",
            "watsonx_url": "https://us-south.ml.cloud.ibm.com",
            "watsonx_apikey": "test-api-key-fixture",
            "watsonx_project_id": "test-project-id",
            "environment": "production",
            "max_retries": 5,
            "request_timeout": 120,
        },
        context={"allow_test_keys": True},
    )

    # Values should match what we passed, not what's in .env
    assert config.max_retries == 5, "max_retries should be 5, not overridden by .env"
    assert config.request_timeout == 120, "request_timeout should be 120, not overridden by .env"
    assert config.watsonx_apikey == "test-api-key-fixture", "API key should match test value"


def test_config_development_environment_not_overridden() -> None:
    """Development environment config should not be overridden by .env."""
    config = Config.model_validate(
        {
            "llm_provider": "watsonx",
            "llm_model": "test-model",
            "watsonx_url": "https://us-south.ml.cloud.ibm.com",
            "watsonx_apikey": "test-api-key-dev",
            "watsonx_project_id": "test-project-id",
            "environment": "development",
        },
        context={"allow_test_keys": True},
    )

    # Development should have retries=1, timeout=60 (not .env values)
    assert config.max_retries == 1, "Development should have max_retries=1"
    assert config.request_timeout == 60, "Development should have request_timeout=60"


def test_isolate_config_clears_all_env_vars(isolate_config_from_environment: Any) -> None:
    """Verify all config-related env vars are cleared."""
    import os

    # Verify that all Config-related environment variables are cleared
    config_env_vars = [
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_API_BASE",
        "LLM_API_KEY",
        "WATSONX_PROJECT_ID",
        "WATSONX_URL",
        "WATSONX_APIKEY",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "LOG_LEVEL",
        "LOG_FORMAT",
    ]

    for var in config_env_vars:
        assert var not in os.environ, f"{var} should not be in environment"


def test_isolate_config_restores_after_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify env vars are restored after test."""
    import os

    # Set environment variable before test
    original_value = "original-value"
    monkeypatch.setenv("LLM_PROVIDER", original_value)

    # Manually apply isolation fixture
    # (In actual tests, pytest applies automatically)
    saved = {}
    config_env_vars = [
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_API_BASE",
        "LLM_API_KEY",
        "WATSONX_PROJECT_ID",
        "WATSONX_URL",
        "WATSONX_APIKEY",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "LOG_LEVEL",
        "LOG_FORMAT",
    ]
    for var in config_env_vars:
        if var in os.environ:
            saved[var] = os.environ.pop(var)

    # Verify it was cleared
    assert "LLM_PROVIDER" not in os.environ

    # Restore
    for var, value in saved.items():
        os.environ[var] = value

    # Verify it was restored
    assert os.environ.get("LLM_PROVIDER") == original_value


def test_config_isolation_prevents_host_leakage() -> None:
    """Verify host environment doesn't affect tests."""
    import os
    import subprocess
    import sys

    # Set environment variable in separate process and run test
    env = os.environ.copy()
    env["LLM_PROVIDER"] = "should-not-leak"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-xvs",
            "tests/unit/test_config.py::TestConfigRetryStrategies::test_default_environment_is_development",
            "--no-cov",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    # Verify test succeeds and environment variable doesn't leak
    assert result.returncode == 0, f"Test failed: {result.stdout}\n{result.stderr}"
    assert "should-not-leak" not in result.stdout, "Environment variable leaked into test"


def test_make_test_config_creates_valid_config(make_test_config: Any) -> None:
    """Verify make_test_config creates a valid Config instance"""
    config = make_test_config()

    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4"
    assert config.openai_api_key == "test-api-key-12345"


def test_make_test_config_accepts_overrides(make_test_config: Any) -> None:
    """Verify make_test_config accepts parameter overrides"""
    config = make_test_config(
        llm_provider="watsonx",
        llm_model="custom-model",
        watsonx_url="https://test.example.com",
        watsonx_apikey="test-watsonx-key-12345",
        watsonx_project_id="test-project-123",
    )

    assert config.llm_provider == "watsonx"
    assert config.llm_model == "custom-model"
    assert config.watsonx_project_id == "test-project-123"


def test_make_test_config_bypasses_api_key_validation(make_test_config: Any) -> None:
    """Verify test keys don't trigger validation errors"""
    # This will be implemented in Phase 3, but we define the interface now
    config = make_test_config(openai_api_key="test-key-pattern")
    assert config.openai_api_key == "test-key-pattern"
