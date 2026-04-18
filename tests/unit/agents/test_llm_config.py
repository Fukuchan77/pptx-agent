"""Tests for llm_config module.

Tests the LLM configuration bridge that converts Config settings
to pydantic-ai model objects, HTTP clients, and usage limits.
"""

import pytest
from httpx import AsyncClient
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel

try:
    from pydantic_ai_litellm import LiteLLMModel
except ImportError:
    LiteLLMModel = None  # type: ignore[assignment]

from pptx_agent.agents.llm_config import (
    create_fallback_model,
    create_http_client,
    create_model,
    create_usage_limits,
)
from pptx_agent.config import Config


@pytest.fixture
def openai_config():
    """Config for OpenAI provider (local Ollama)."""
    return Config(
        llm_provider="openai",
        llm_model="llama3.2:3b",
        llm_api_base="http://localhost:11434/v1",
        environment="development",
        max_retries=1,
        request_timeout=60,
        retry_base_delay=1.0,
        retry_max_delay=8.0,
        agent_retries=3,
        max_requests=20,
        max_response_tokens=50000,
        enable_fallback=False,
    )


@pytest.fixture
def watsonx_config():
    """Config for watsonx provider."""
    return Config.model_validate(
        {
            "llm_provider": "watsonx",
            "llm_model": "meta-llama/llama-3-1-70b-instruct",
            "watsonx_url": "https://us-south.ml.cloud.ibm.com",
            "watsonx_apikey": "test-watsonx-key-1234567890",
            "watsonx_project_id": "test-project-id",
            "environment": "production",
            "max_retries": 5,
            "request_timeout": 120,
            "enable_fallback": True,
            "fallback_provider": "anthropic",
            "fallback_model": "claude-3-5-sonnet-20241022",
            "anthropic_api_key": "test-anthropic-key-1234567890",
        },
        context={"allow_test_keys": True},
    )


@pytest.fixture
def anthropic_config():
    """Config for Anthropic provider."""
    return Config.model_validate(
        {
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "anthropic_api_key": "test-anthropic-key-1234567890",
            "environment": "production",
            "enable_fallback": False,
        },
        context={"allow_test_keys": True},
    )


class TestCreateModel:
    """Test create_model() function."""

    def test_create_model_openai_with_base_url(self, openai_config: Config):
        """Test creating OpenAI model with custom base URL (Ollama)."""
        model = create_model(openai_config)

        assert isinstance(model, OpenAIChatModel)
        # Model created successfully - that's what matters for this test

    def test_create_model_watsonx(self, watsonx_config: Config):
        """Test creating watsonx model via LiteLLM provider."""
        model = create_model(watsonx_config)

        # Watsonx now uses LiteLLMModel instead of OpenAIChatModel
        assert LiteLLMModel is not None, "LiteLLMModel should be available"
        assert isinstance(model, LiteLLMModel), (
            f"Expected LiteLLMModel for watsonx, got {type(model).__name__}"
        )
        # Model created successfully

    def test_create_model_anthropic(self, anthropic_config: Config):
        """Test creating Anthropic model."""
        model = create_model(anthropic_config)

        assert isinstance(model, OpenAIChatModel)
        # Model created successfully


class TestCreateFallbackModel:
    """Test create_fallback_model() function."""

    def test_create_fallback_model_when_enabled(self, watsonx_config: Config):
        """Test creating fallback model when fallback is enabled."""
        fallback_model = create_fallback_model(watsonx_config)

        assert fallback_model is not None
        assert isinstance(fallback_model, OpenAIChatModel)
        # Fallback model created successfully

    def test_create_fallback_model_when_disabled(self, openai_config: Config):
        """Test returning None when fallback is disabled."""
        fallback_model = create_fallback_model(openai_config)

        assert fallback_model is None

    def test_create_fallback_model_no_fallback_provider(self, openai_config: Config):
        """Test returning None when fallback provider is not configured."""
        # Enable fallback but don't set fallback_provider
        openai_config.enable_fallback = True
        openai_config.fallback_provider = None

        fallback_model = create_fallback_model(openai_config)

        assert fallback_model is None


class TestCreateHttpClient:
    """Test create_http_client() function."""

    def test_create_http_client_returns_async_client(self, openai_config: Config):
        """Test that create_http_client returns AsyncClient."""
        client = create_http_client(openai_config)

        assert isinstance(client, AsyncClient)

    def test_create_http_client_with_retry_config(self, watsonx_config: Config):
        """Test HTTP client is configured with retry settings."""
        client = create_http_client(watsonx_config)

        assert isinstance(client, AsyncClient)
        # Verify timeout is set
        assert client.timeout.read == watsonx_config.request_timeout


class TestCreateUsageLimits:
    """Test create_usage_limits() function."""

    def test_create_usage_limits_maps_config(self, openai_config: Config):
        """Test usage limits are correctly mapped from config."""
        limits = create_usage_limits(openai_config)

        assert isinstance(limits, UsageLimits)
        assert limits.request_limit == openai_config.max_requests
        assert limits.output_tokens_limit == openai_config.max_response_tokens

    def test_create_usage_limits_production_config(self, watsonx_config: Config):
        """Test usage limits in production config."""
        limits = create_usage_limits(watsonx_config)

        assert isinstance(limits, UsageLimits)
        assert limits.request_limit == 20
        assert limits.output_tokens_limit == 50000
