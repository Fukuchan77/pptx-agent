import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def isolate_config_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Isolate tests from environment variables.

    This fixture:
    1. Disables .env file loading
    2. Clears ALL config-related environment variables
    3. Ensures tests are deterministic regardless of host environment
    """
    # Disable .env file loading
    monkeypatch.setenv("PPTX_AGENT_IGNORE_ENV_FILE", "1")

    # Clear all Config-related environment variables
    config_env_vars = [
        # LLM settings
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_API_BASE",
        "LLM_API_KEY",
        # Watsonx-specific
        "WATSONX_PROJECT_ID",
        "WATSONX_URL",
        "WATSONX_APIKEY",
        # OpenAI-specific
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        # Anthropic-specific
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        # Log settings
        "LOG_LEVEL",
        "LOG_FORMAT",
    ]

    # Save existing values for restoration - monkeypatch handles automatically
    for var in config_env_vars:
        if var in os.environ:
            monkeypatch.delenv(var, raising=False)
    # Values are automatically restored after test (handled by monkeypatch)


@pytest.fixture
def basic_template_path() -> str:
    """Get path to basic template for testing.

    Uses template from tests/fixtures/ to ensure availability in CI.
    """
    template_path = Path("tests/fixtures/basic-template.pptx")
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_path}")
    return str(template_path)


@pytest.fixture
def make_test_config() -> Callable[..., Any]:
    """
    Factory fixture for creating test Config instances.

    Usage:
        def test_something(make_test_config):
            config = make_test_config(llm_provider="openai")
            # Use config in test

    Returns:
        A factory function that creates Config instances with test-safe defaults.
    """

    def _make_config(**overrides: Any) -> Any:
        """
        Create a Config instance for testing.

        Args:
            **overrides: Any Config field to override from defaults

        Returns:
            Config: A Config instance with test-safe values
        """
        from pptx_agent.config import Config

        # Test-safe defaults
        defaults = {
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "openai_api_key": "test-api-key-12345",  # OpenAI provider needs openai_api_key
            "llm_api_base": None,
            "watsonx_project_id": None,
            "watsonx_url": None,
        }

        # Merge overrides
        config_params = {**defaults, **overrides}

        # Create config with test keys allowed via validation context
        # This is the only way to allow test keys after security hardening
        return Config.model_validate(config_params, context={"allow_test_keys": True})

    return _make_config
