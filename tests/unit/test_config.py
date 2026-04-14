"""Tests for configuration management with security-focused error messages."""

import threading

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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
        )  # type: ignore[call-arg]

        assert config.watsonx_apikey == "valid-key-123"

    def test_anthropic_api_key_valid_length_passes(self) -> None:
        """API key with 10 or more characters should pass validation."""
        config = Config(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            anthropic_api_key="sk-ant-valid-key",
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
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
            allow_test_keys=True,
        )  # type: ignore[call-arg]

        # Should disable fallback when openai_api_key is not provided
        assert config.enable_fallback is False


class TestConfigReset:
    """Test configuration reset functionality for test isolation."""

    def test_reset_config_function_exists(self) -> None:
        """reset_config() function should exist and be callable."""
        from pptx_agent.config import reset_config

        # Should be callable without errors
        reset_config()

    def test_reset_config_clears_global_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """reset_config() should clear the global config instance."""
        from pptx_agent.config import get_config, reset_config

        # Set up minimal config for watsonx with non-test API key
        monkeypatch.setenv("LLM_PROVIDER", "watsonx")
        monkeypatch.setenv("LLM_MODEL", "granite-model")
        monkeypatch.setenv("WATSONX_URL", "https://cloud.ibm.com")
        monkeypatch.setenv("WATSONX_APIKEY", "abcdef1234567890")  # Non-test pattern
        monkeypatch.setenv("WATSONX_PROJECT_ID", "prod-project-id")

        # Get initial config
        config1 = get_config()
        assert config1 is not None

        # Reset config
        reset_config()

        # Get config again - should be a new instance
        config2 = get_config()
        assert config2 is not None
        assert config2 is not config1, "Should create new instance after reset"

    def test_reset_config_is_idempotent(self) -> None:
        """reset_config() should be safe to call multiple times."""
        from pptx_agent.config import reset_config

        # Should not raise any errors when called multiple times
        reset_config()
        reset_config()
        reset_config()


class TestConfigThreadSafety:
    """Test thread safety of configuration management."""

    def test_get_config_thread_safety(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify get_config() is thread-safe"""
        from pptx_agent.config import get_config, reset_config

        # Set up minimal config for watsonx with non-test API key
        monkeypatch.setenv("LLM_PROVIDER", "watsonx")
        monkeypatch.setenv("LLM_MODEL", "granite-model")
        monkeypatch.setenv("WATSONX_URL", "https://cloud.ibm.com")
        monkeypatch.setenv("WATSONX_APIKEY", "abcdef1234567890")  # Non-test pattern
        monkeypatch.setenv("WATSONX_PROJECT_ID", "prod-project-id")

        # Clear before test
        reset_config()

        # Call get_config() simultaneously from multiple threads
        configs = []
        errors = []

        def access_config() -> None:
            try:
                config = get_config()
                configs.append(id(config))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=access_config) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all threads got the same Config instance
        assert len(set(configs)) == 1, "Different threads got different Config instances"

    def test_get_config_concurrent_reset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify config reset doesn't cause race conditions"""
        from pptx_agent.config import get_config, reset_config

        # Set up minimal config for watsonx with non-test API key
        monkeypatch.setenv("LLM_PROVIDER", "watsonx")
        monkeypatch.setenv("LLM_MODEL", "granite-model")
        monkeypatch.setenv("WATSONX_URL", "https://cloud.ibm.com")
        monkeypatch.setenv("WATSONX_APIKEY", "abcdef1234567890")  # Non-test pattern
        monkeypatch.setenv("WATSONX_PROJECT_ID", "prod-project-id")

        errors = []

        def reset_and_access() -> None:
            try:
                reset_config()
                config = get_config()
                assert config is not None
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reset_and_access) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Race conditions detected: {errors}"


class TestConfigTestKeyValidation:
    """Test API key validation for test vs production keys."""

    def test_config_rejects_test_api_keys_by_default(self) -> None:
        """Verify test API key patterns are rejected in production mode."""
        test_key_patterns = [
            "test-api-key-123",
            "test_key_12345",
            "TEST_API_KEY_123",
            "my-test-key-value",
            "dummy-key-12345",
            "fake_key_value",
            "sample-key-value",
        ]

        for test_key in test_key_patterns:
            with pytest.raises(ValueError, match="API key appears to be a test value"):
                Config(
                    llm_provider="openai",
                    llm_model="gpt-4",
                    openai_api_key=test_key,
                )  # type: ignore[call-arg]

    def test_config_allows_test_keys_when_explicitly_enabled(self) -> None:
        """Verify test API keys are allowed when allow_test_keys=True."""
        test_key_patterns = [
            "test-api-key",
            "test_key_12345",
            "TEST_API_KEY",
        ]

        for test_key in test_key_patterns:
            # Should not raise when allow_test_keys=True
            config = Config(
                llm_provider="openai",
                llm_model="gpt-4",
                openai_api_key=test_key,
                allow_test_keys=True,  # Test mode
            )  # type: ignore[call-arg]
            assert config.openai_api_key == test_key

    def test_config_allows_real_looking_keys(self) -> None:
        """Verify real-looking API keys are still accepted."""
        real_key_patterns = [
            "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz",  # OpenAI format
            "AIzaSyD1234567890abcdefghijklmnopqrst",  # Google format
            "1234567890abcdef1234567890abcdef",  # Generic hex
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT format
        ]

        for real_key in real_key_patterns:
            # Should not raise
            config = Config(
                llm_provider="openai",
                llm_model="gpt-4",
                openai_api_key=real_key,
            )  # type: ignore[call-arg]
            assert config.openai_api_key == real_key

    def test_api_key_validation_edge_cases(self) -> None:
        """Test edge cases in API key validation."""
        # Too short (should be rejected even if not a test pattern)
        with pytest.raises(ValueError, match="too short"):
            Config(
                llm_provider="openai",
                llm_model="gpt-4",
                openai_api_key="abc",
            )  # type: ignore[call-arg]

        # None is always valid (handled by model_post_init)
        with pytest.raises(ValueError, match="Required configuration for openai"):
            Config(
                llm_provider="openai",
                llm_model="gpt-4",
                openai_api_key=None,
            )  # type: ignore[call-arg]
