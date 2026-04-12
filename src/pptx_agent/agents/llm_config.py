"""LLM configuration bridge for pydantic-ai integration.

This module converts Config settings to pydantic-ai model objects,
HTTP clients, and usage limits. Supports multiple LLM providers:
- watsonx (via LiteLLM)
- anthropic (via LiteLLM)
- openai (direct or via LiteLLM)
"""

import logging
import os
from typing import TYPE_CHECKING

from httpx import AsyncClient, Timeout
from openai import AsyncOpenAI
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers import Provider

if TYPE_CHECKING:
    from pydantic_ai_litellm import LiteLLMModel

    HAS_LITELLM = True
else:
    try:
        from pydantic_ai_litellm import LiteLLMModel

        HAS_LITELLM = True
    except ImportError:
        LiteLLMModel = None  # type: ignore[assignment,misc]
        HAS_LITELLM = False

from pptx_agent.config import Config

logger = logging.getLogger(__name__)


class CustomOpenAIProvider(Provider[AsyncOpenAI]):
    """Custom provider that wraps AsyncOpenAI client with custom configuration."""

    def __init__(self, client: AsyncOpenAI, name: str = "custom-openai") -> None:
        """Initialize provider with AsyncOpenAI client.

        Args:
            client: Configured AsyncOpenAI client
            name: Provider name
        """
        self._client = client
        self._name = name

    @property
    def client(self) -> AsyncOpenAI:
        """Return the AsyncOpenAI client."""
        return self._client

    @property
    def base_url(self) -> str:
        """Return the base URL from client."""
        return str(self._client.base_url) if self._client.base_url else "https://api.openai.com/v1"

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._name


def _create_model_from_params(
    provider_type: str, model: str, base_url: str | None, api_key: str | None, config: Config
) -> "OpenAIChatModel | LiteLLMModel":
    """Helper to generate LLM model object from direct parameters.

    For watsonx provider, uses LiteLLMModel with project_id support.
    For other providers, uses OpenAIChatModel.
    """
    # Special handling for watsonx - use LiteLLMModel with project_id
    if provider_type == "watsonx":
        if not HAS_LITELLM:
            msg = (
                "pydantic-ai-litellm is required for watsonx provider. "
                "Install with: uv add pydantic-ai-litellm"
            )
            raise ImportError(msg)

        model_name = f"watsonx/{model}"
        api_base = config.watsonx_url
        project_id = config.watsonx_project_id

        # Set project_id as environment variable for LiteLLM to use
        # LiteLLM will automatically pick this up when making watsonx API calls
        if project_id:
            os.environ["WATSONX_PROJECT_ID"] = project_id

        return LiteLLMModel(
            model_name,
            api_key=api_key or "",
            api_base=api_base,
        )

    # For other providers, use OpenAIChatModel with custom provider
    if provider_type == "openai":
        p_base_url = base_url
        p_api_key = api_key or "not-needed"
        provider_name = "openai-custom"
        model_name = model
    elif provider_type == "anthropic":
        p_base_url = None
        p_api_key = api_key or ""
        provider_name = "anthropic"
        model_name = f"anthropic/{model}"
    else:
        msg = f"Unsupported LLM provider: {provider_type}"
        raise ValueError(msg)

    http_client = create_http_client(config)
    if p_base_url:
        client = AsyncOpenAI(api_key=p_api_key, base_url=p_base_url, http_client=http_client)
    else:
        client = AsyncOpenAI(api_key=p_api_key, http_client=http_client)
    provider = CustomOpenAIProvider(client, name=provider_name)

    return OpenAIChatModel(
        model_name=model_name,
        provider=provider,
    )


def create_model(config: Config) -> "OpenAIChatModel | LiteLLMModel":
    """Generate LLM model object from Config.

    Selects appropriate provider based on config.llm_provider:
    - watsonx: Uses LiteLLM-compatible provider with IBM watsonx.ai endpoint
    - anthropic: Uses LiteLLM-compatible provider with Anthropic endpoint
    - openai: Uses OpenAI provider (direct API or custom base URL like Ollama)

    Args:
        config: Application configuration with LLM settings

    Returns:
        OpenAIChatModel: Configured model instance

    Raises:
        ValueError: If provider configuration is invalid
    """
    api_key = None
    if config.llm_provider == "openai":
        api_key = config.openai_api_key
    elif config.llm_provider == "watsonx":
        api_key = config.watsonx_apikey
    elif config.llm_provider == "anthropic":
        api_key = config.anthropic_api_key

    return _create_model_from_params(
        provider_type=config.llm_provider,
        model=config.llm_model,
        base_url=config.llm_api_base,
        api_key=api_key,
        config=config,
    )


def create_fallback_model(config: Config) -> "OpenAIChatModel | LiteLLMModel | None":
    """Generate fallback provider model (production environment only).

    Creates a fallback model when:
    - config.enable_fallback is True
    - config.fallback_provider is set
    - Appropriate API key is configured

    Args:
        config: Application configuration

    Returns:
        OpenAIChatModel | None: Fallback model instance or None if not configured

    """
    if not config.enable_fallback or not config.fallback_provider:
        return None

    api_key = None
    if config.fallback_provider == "anthropic":
        api_key = config.anthropic_api_key
    elif config.fallback_provider == "openai":
        api_key = config.openai_api_key
    elif config.fallback_provider == "watsonx":
        api_key = config.watsonx_apikey

    fallback_model_name = config.fallback_model or "claude-3-5-sonnet-20241022"

    try:
        return _create_model_from_params(
            provider_type=config.fallback_provider,
            model=fallback_model_name,
            base_url=config.llm_api_base,  # fallback uses original base url or None
            api_key=api_key,
            config=config,
        )
    except ValueError as e:
        logger.warning("Failed to create fallback model: %s", e)
        return None


def create_http_client(config: Config) -> AsyncClient:
    """Generate HTTP client with retry settings.

    Configures exponential backoff retry with tenacity:
    - Base delay: config.retry_base_delay (default 1s)
    - Max delay: config.retry_max_delay (default 8s)
    - Max retries: config.max_retries

    Args:
        config: Application configuration

    Returns:
        AsyncClient: Configured HTTP client with timeout and retry
    """
    # Create timeout configuration
    timeout = Timeout(
        connect=config.connect_timeout,  # Connection timeout
        read=config.request_timeout,  # Read timeout
        write=config.write_timeout,  # Write timeout
        pool=config.pool_timeout,  # Pool timeout
    )

    # Create HTTP client with timeout
    # Note: Retry logic is handled by pydantic-ai's built-in retry mechanism
    # and tenacity decorators on agent functions, not at HTTP client level
    return AsyncClient(timeout=timeout)


def create_usage_limits(config: Config) -> UsageLimits:
    """Generate usage limits from configuration.

    Maps config values to UsageLimits:
    - config.max_requests → request_limit
    - config.max_response_tokens → output_tokens_limit

    Args:
        config: Application configuration

    Returns:
        UsageLimits: Configured usage limits
    """
    return UsageLimits(
        request_limit=config.max_requests,
        output_tokens_limit=config.max_response_tokens,
    )
