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


class TestConfigAPIKeyFormatValidation:
    """Test API key format validation."""

    def test_watsonx_apikey_empty_string_fails(self) -> None:
        """Empty string API key should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
                watsonx_url="https://us-south.ml.cloud.ibm.com",
                watsonx_apikey="",
                watsonx_project_id="test-project-id",
            )  # type: ignore[call-arg]

    def test_watsonx_apikey_too_short_fails(self) -> None:
        """API key shorter than 10 characters should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
                watsonx_url="https://us-south.ml.cloud.ibm.com",
                watsonx_apikey="short",
                watsonx_project_id="test-project-id",
            )  # type: ignore[call-arg]

    def test_watsonx_apikey_whitespace_only_fails(self) -> None:
        """Whitespace-only API key should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
                watsonx_url="https://us-south.ml.cloud.ibm.com",
                watsonx_apikey="     ",
                watsonx_project_id="test-project-id",
            )  # type: ignore[call-arg]

    def test_watsonx_apikey_with_leading_trailing_whitespace_validates_content(
        self,
    ) -> None:
        """API key with whitespace should validate stripped content."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
                watsonx_url="https://us-south.ml.cloud.ibm.com",
                watsonx_apikey="  short  ",
                watsonx_project_id="test-project-id",
            )  # type: ignore[call-arg]

    def test_anthropic_api_key_empty_string_fails(self) -> None:
        """Empty string API key should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
                anthropic_api_key="",
            )  # type: ignore[call-arg]

    def test_anthropic_api_key_too_short_fails(self) -> None:
        """API key shorter than 10 characters should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
                anthropic_api_key="short",
            )  # type: ignore[call-arg]

    def test_anthropic_api_key_whitespace_only_fails(self) -> None:
        """Whitespace-only API key should fail validation."""
        with pytest.raises(ValueError, match="API key appears to be invalid"):
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
                anthropic_api_key="     ",
            )  # type: ignore[call-arg]

    def test_watsonx_apikey_valid_length_passes(self) -> None:
        """API key with 10 or more characters should pass validation."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="valid-key-123",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.watsonx_apikey == "valid-key-123"

    def test_anthropic_api_key_valid_length_passes(self) -> None:
        """API key with 10 or more characters should pass validation."""
        config = Config(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            anthropic_api_key="sk-ant-valid-key",
        )  # type: ignore[call-arg]

        assert config.anthropic_api_key == "sk-ant-valid-key"

    def test_watsonx_apikey_strips_whitespace(self) -> None:
        """API key with leading/trailing whitespace should be stripped."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="  valid-key-123  ",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.watsonx_apikey == "valid-key-123", (
            "API key should be stripped of leading/trailing whitespace"
        )

    def test_anthropic_api_key_strips_whitespace(self) -> None:
        """API key with leading/trailing whitespace should be stripped."""
        config = Config(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            anthropic_api_key="  sk-ant-valid-key  ",
        )  # type: ignore[call-arg]

        assert config.anthropic_api_key == "sk-ant-valid-key", (
            "API key should be stripped of leading/trailing whitespace"
        )

    def test_watsonx_apikey_none_passes(self) -> None:
        """None API key should pass through validation (handled by model_post_init)."""
        # This will fail at model_post_init, not at field validation
        with pytest.raises(ValueError, match="Required configuration for watsonx"):
            Config(
                llm_provider="watsonx",
                llm_model="test-model",
                watsonx_url="https://us-south.ml.cloud.ibm.com",
                watsonx_apikey=None,
                watsonx_project_id="test-project-id",
            )  # type: ignore[call-arg]

    def test_anthropic_api_key_none_passes(self) -> None:
        """None API key should pass through validation (handled by model_post_init)."""
        # This will fail at model_post_init, not at field validation
        with pytest.raises(ValueError, match="Required configuration for anthropic"):
            Config(
                llm_provider="anthropic",
                llm_model="claude-3-5-sonnet-20241022",
                anthropic_api_key=None,
            )  # type: ignore[call-arg]


class TestConfigRetryStrategies:
    """Test retry strategy configuration for different environments."""

    def test_development_environment_has_fail_fast_retry_config(self) -> None:
        """Development environment should have retries=1, timeout=60s."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            environment="development",
        )  # type: ignore[call-arg]

        assert config.environment == "development"
        assert config.max_retries == 1
        assert config.request_timeout == 60

    def test_production_environment_has_resilience_retry_config(self) -> None:
        """Production environment should have retries=5, timeout=120s."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            environment="production",
        )  # type: ignore[call-arg]

        assert config.environment == "production"
        assert config.max_retries == 5
        assert config.request_timeout == 120

    def test_default_environment_is_development(self) -> None:
        """Default environment should be development."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.environment == "development"
        assert config.max_retries == 1


class TestConfigTimeouts:
    """Test timeout configuration."""

    def test_outline_generation_timeout_is_120_seconds(self) -> None:
        """Outline generation should have 120s timeout."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.outline_timeout == 120

    def test_slide_generation_timeout_is_60_seconds(self) -> None:
        """Individual slide generation should have 60s timeout."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.slide_timeout == 60


class TestConfigUsageLimits:
    """Test usage limits enforcement."""

    def test_max_requests_limit_is_20(self) -> None:
        """Maximum requests should be limited to 20."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.max_requests == 20

    def test_max_response_tokens_limit_is_50000(self) -> None:
        """Maximum response tokens should be limited to 50,000."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.max_response_tokens == 50000


class TestConfigHTTPRetry:
    """Test HTTP-level retry configuration."""

    def test_http_retry_has_exponential_backoff_config(self) -> None:
        """HTTP retry should have exponential backoff configuration."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        # Should have exponential backoff params: base_delay, max_delay
        assert hasattr(config, "retry_base_delay")
        assert hasattr(config, "retry_max_delay")
        assert config.retry_base_delay == 1.0  # 1 second base
        assert config.retry_max_delay == 8.0  # 8 seconds max (1→2→4→8)

    def test_agent_level_retry_is_3_attempts(self) -> None:
        """Agent-level validation failures should retry 3 times."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
        )  # type: ignore[call-arg]

        assert config.agent_retries == 3


class TestConfigProviderFallback:
    """Test provider fallback configuration."""

    def test_production_enables_provider_fallback(self) -> None:
        """Production environment should enable provider fallback."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            anthropic_api_key="sk-ant-fallback-key",
            environment="production",
        )  # type: ignore[call-arg]

        assert config.enable_fallback is True
        assert config.fallback_provider == "anthropic"
        assert config.fallback_model is not None

    def test_development_disables_provider_fallback(self) -> None:
        """Development environment should disable provider fallback."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            environment="development",
        )  # type: ignore[call-arg]

        assert config.enable_fallback is False

    def test_openai_fallback_requires_openai_api_key(self) -> None:
        """OpenAI fallback provider should require OPENAI_API_KEY."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            openai_api_key="sk-test-openai-key",
            environment="production",
            enable_fallback=True,
            fallback_provider="openai",
            fallback_model="gpt-4",
        )  # type: ignore[call-arg]

        assert config.enable_fallback is True
        assert config.fallback_provider == "openai"

    def test_openai_fallback_disables_when_key_missing(self) -> None:
        """OpenAI fallback should disable when OPENAI_API_KEY is missing."""
        config = Config(
            llm_provider="watsonx",
            llm_model="test-model",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-api-key",
            watsonx_project_id="test-project-id",
            environment="production",
            enable_fallback=True,
            fallback_provider="openai",
            fallback_model="gpt-4",
        )  # type: ignore[call-arg]

        # Should disable fallback when openai_api_key is not provided
        assert config.enable_fallback is False
