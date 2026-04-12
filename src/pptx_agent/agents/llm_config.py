"""LLM configuration bridge for pydantic-ai integration.

This module converts Config settings to pydantic-ai model objects,
HTTP clients, and usage limits. Supports multiple LLM providers:
- watsonx (via LiteLLM)
- anthropic (via LiteLLM)
- openai (direct or via LiteLLM)
"""

import logging

from httpx import AsyncClient, Timeout
from openai import AsyncOpenAI
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers import Provider

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


def create_model(config: Config) -> OpenAIChatModel:
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
    # For OpenAI provider with custom base URL (e.g., Ollama)
    if config.llm_provider == "openai":
        # Create AsyncOpenAI client with custom configuration
        client = AsyncOpenAI(
            base_url=config.llm_api_base,
            api_key=config.openai_api_key or "not-needed",  # Ollama doesn't need key
            http_client=create_http_client(config),
        )
        provider = CustomOpenAIProvider(client, name="openai-custom")
        return OpenAIChatModel(
            model_name=config.llm_model,
            provider=provider,
        )

    # For watsonx provider via LiteLLM
    if config.llm_provider == "watsonx":
        # LiteLLM format: watsonx/model_name
        client = AsyncOpenAI(
            base_url=f"{config.watsonx_url}/ml/v1/text/generation?version=2023-05-29",
            api_key=config.watsonx_apikey or "",
            http_client=create_http_client(config),
        )
        provider = CustomOpenAIProvider(client, name="watsonx")
        return OpenAIChatModel(
            model_name=f"watsonx/{config.llm_model}",
            provider=provider,
        )

    # For Anthropic provider via LiteLLM
    if config.llm_provider == "anthropic":
        # LiteLLM format: anthropic/model_name
        client = AsyncOpenAI(
            api_key=config.anthropic_api_key or "",
            http_client=create_http_client(config),
        )
        provider = CustomOpenAIProvider(client, name="anthropic")
        return OpenAIChatModel(
            model_name=f"anthropic/{config.llm_model}",
            provider=provider,
        )

    msg = f"Unsupported LLM provider: {config.llm_provider}"
    raise ValueError(msg)


def create_fallback_model(config: Config) -> OpenAIChatModel | None:
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
    # Return None if fallback is disabled or not configured
    if not config.enable_fallback:
        return None

    if not config.fallback_provider:
        return None

    # Create temporary config for fallback provider
    fallback_config = Config(
        llm_provider=config.fallback_provider,  # type: ignore[arg-type]
        llm_model=config.fallback_model or "claude-3-5-sonnet-20241022",
        anthropic_api_key=config.anthropic_api_key,
        openai_api_key=config.openai_api_key,
        llm_api_base=config.llm_api_base,
        environment=config.environment,
        max_retries=config.max_retries,
        request_timeout=config.request_timeout,
        retry_base_delay=config.retry_base_delay,
        retry_max_delay=config.retry_max_delay,
    )

    try:
        return create_model(fallback_config)
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
        connect=10.0,  # Connection timeout
        read=config.request_timeout,  # Read timeout
        write=10.0,  # Write timeout
        pool=10.0,  # Pool timeout
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
