"""Tests for configuration management with security-focused error messages."""

import pytest

from pptx_agent.config import Config


class TestConfigSecureErrorMessages:
    """Test that error messages don't leak sensitive information."""

    def test_watsonx_config_incomplete_no_env_var_names(self) -> None:
        """Error message for incomplete watsonx config.

        Should not contain environment variable names.
        Security requirement: Error messages must not expose system configuration
        details like environment variable names that could aid attackers.
        """
        # Pass values directly to constructor - watsonx provider but missing credentials
        with pytest.raises(
            ValueError,
            match="Required configuration for watsonx provider is incomplete",
        ) as exc_info:
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
            )  # type: ignore[call-arg]

        error_msg = str(exc_info.value)

        # These environment variable names should NOT appear in error messages
        assert "WATSONX_URL" not in error_msg, "Error message leaks WATSONX_URL env var name"
        assert "WATSONX_APIKEY" not in error_msg, "Error message leaks WATSONX_APIKEY env var name"
        assert "WATSONX_PROJECT_ID" not in error_msg, (
            "Error message leaks WATSONX_PROJECT_ID env var name"
        )

        # Error message should be generic but informative
        assert "watsonx" in error_msg.lower(), "Error should mention the provider"
        assert "config" in error_msg.lower() or "required" in error_msg.lower(), (
            "Error should indicate configuration is incomplete"
        )

    def test_anthropic_config_incomplete_no_env_var_names(self) -> None:
        """Error message for incomplete anthropic config.

        Should not contain environment variable names.
        Security requirement: Error messages must not expose system configuration.
        """
        # Pass values directly to constructor - anthropic provider but missing credentials
        with pytest.raises(
            ValueError,
            match="Required configuration for anthropic provider is incomplete",
        ) as exc_info:
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
            )  # type: ignore[call-arg]

        error_msg = str(exc_info.value)

        # Environment variable name should NOT appear
        assert "ANTHROPIC_API_KEY" not in error_msg, (
            "Error message leaks ANTHROPIC_API_KEY env var name"
        )
        assert "API_KEY" not in error_msg, "Error message leaks API_KEY pattern"

        # Error message should be generic but informative
        assert "anthropic" in error_msg.lower(), "Error should mention the provider"
        assert "config" in error_msg.lower() or "required" in error_msg.lower(), (
            "Error should indicate configuration is incomplete"
        )

    def test_watsonx_config_error_message_is_generic(self) -> None:
        """Watsonx configuration error should provide generic message."""
        with pytest.raises(
            ValueError,
            match="Required configuration for watsonx provider is incomplete",
        ) as exc_info:
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
            )  # type: ignore[call-arg]

        error_msg = str(exc_info.value)

        # Message should be helpful but not expose internals
        expected_keywords = ["required", "configuration", "incomplete", "watsonx"]
        assert any(keyword in error_msg.lower() for keyword in expected_keywords), (
            f"Error message should contain helpful keywords: {error_msg}"
        )

    def test_anthropic_config_error_message_is_generic(self) -> None:
        """Anthropic configuration error should provide generic message."""
        with pytest.raises(
            ValueError,
            match="Required configuration for anthropic provider is incomplete",
        ) as exc_info:
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
            )  # type: ignore[call-arg]

        error_msg = str(exc_info.value)

        # Message should be helpful but not expose internals
        expected_keywords = ["required", "configuration", "incomplete", "anthropic"]
        assert any(keyword in error_msg.lower() for keyword in expected_keywords), (
            f"Error message should contain helpful keywords: {error_msg}"
        )


class TestConfigValidConfiguration:
    """Test that valid configurations work correctly."""

    def test_watsonx_config_complete_works(self) -> None:
        """Valid watsonx configuration should work."""
        config = Config(
            llm_provider="watsonx",
            llm_model="ibm/granite-13b-chat-v2",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.llm_provider == "watsonx"
        assert config.llm_model == "ibm/granite-13b-chat-v2"
        assert config.watsonx_url == "https://us-south.ml.cloud.ibm.com"
        assert config.watsonx_apikey == "test-api-key"
        assert config.watsonx_project_id == "test-project-id"

    def test_anthropic_config_complete_works(self) -> None:
        """Valid anthropic configuration should work."""
        config = Config(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            anthropic_api_key="sk-ant-test-key",
        )  # type: ignore[call-arg]

        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-5-sonnet-20241022"
        assert config.anthropic_api_key == "sk-ant-test-key"
