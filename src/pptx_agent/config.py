"""Configuration management using pydantic-settings.

Loads configuration from environment variables with support for .env files.
"""

import logging
import threading
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# API key validation constants
MIN_API_KEY_LENGTH = 10


class Config(BaseSettings):
    """Application configuration from environment variables.

    Supports three LLM providers:
    - watsonx (dev environment)
    - anthropic (production environment)
    - openai (OpenAI endpoint)

    Environment variables:
        LLM_PROVIDER: 'watsonx', 'anthropic', or 'openai'
        LLM_MODEL: Model name/ID
        LLM_API_BASE: API base URL (for local endpoint)
        WATSONX_URL: Watsonx API URL
        WATSONX_APIKEY: Watsonx API key
        WATSONX_PROJECT_ID: Watsonx project ID
        ANTHROPIC_API_KEY: Anthropic API key (for Claude)
        OPENAI_API_KEY: OpenAI API key
        ENVIRONMENT: 'development' or 'production' (default: development)
        MAX_RETRIES: Maximum HTTP retries (default: auto-set based on environment)
        REQUEST_TIMEOUT: Request timeout in seconds (default: auto-set based on environment)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Common settings
    llm_provider: Literal["watsonx", "anthropic", "openai"]
    llm_model: str
    llm_api_base: str | None = None

    # Environment and retry settings
    environment: Literal["development", "production"] = "development"
    max_retries: int | None = None  # Auto-set based on environment
    request_timeout: int | None = None  # Auto-set based on environment

    # Stage-specific timeouts (FR-047, FR-048)
    outline_timeout: int = 120  # 120 seconds for outline generation
    slide_timeout: int = 60  # 60 seconds per slide

    # Usage limits (FR-049)
    max_requests: int = 20  # Maximum 20 requests
    max_response_tokens: int = 50000  # Maximum 50,000 response tokens

    # HTTP-level retry configuration (FR-045)
    retry_base_delay: float = 1.0  # Base delay for exponential backoff (seconds)
    retry_max_delay: float = 8.0  # Maximum delay (1→2→4→8 seconds)

    # Agent-level retry (FR-046)
    agent_retries: int = 3  # 3 attempts for validation failures

    # Provider fallback (FR-050)
    enable_fallback: bool | None = None  # Auto-set based on environment
    fallback_provider: str | None = None  # Auto-set for production
    fallback_model: str | None = None  # Auto-set for production

    # Watsonx settings (required when provider=watsonx)
    watsonx_url: str | None = None
    watsonx_apikey: str | None = None
    watsonx_project_id: str | None = None

    # Anthropic settings (required when provider=anthropic)
    anthropic_api_key: str | None = None

    # OpenAI settings (required when provider=openai and not using local endpoint)
    openai_api_key: str | None = None

    @field_validator("watsonx_apikey", "anthropic_api_key", "openai_api_key", mode="before")
    @classmethod
    def validate_api_key_not_empty(cls, v: str | None) -> str | None:
        """Validate that API keys have minimum length to prevent obviously invalid values.

        Args:
            v: The API key value to validate

        Returns:
            The validated API key value with whitespace stripped (or None if None was provided)

        Raises:
            ValueError: If the API key is too short (less than MIN_API_KEY_LENGTH characters)
        """
        if v is not None:
            stripped = v.strip()
            if len(stripped) < MIN_API_KEY_LENGTH:
                msg = "API key appears to be invalid (too short)"
                raise ValueError(msg)

            placeholder_prefixes = ("your-", "sk-xxx", "placeholder")
            if any(stripped.lower().startswith(p) for p in placeholder_prefixes):
                msg = "API key appears to be a placeholder value — update .env with your actual key"
                raise ValueError(msg)
            return stripped
        return None

    def model_post_init(self, __context: Any) -> None:
        """Validate provider-specific required fields and set environment-based defaults."""
        # Set environment-specific retry and timeout defaults (FR-051, FR-079, FR-080)
        if self.max_retries is None:
            self.max_retries = 1 if self.environment == "development" else 5

        if self.request_timeout is None:
            self.request_timeout = 60 if self.environment == "development" else 120

        # Set provider fallback configuration (FR-050)
        if self.enable_fallback is None:
            self.enable_fallback = self.environment == "production"

        # Set fallback provider/model for production (FR-050)
        if self.enable_fallback and self.fallback_provider is None:
            self.fallback_provider = "anthropic"
            # Set default fallback model if not specified
            if self.fallback_model is None:
                self.fallback_model = "claude-3-5-sonnet-20241022"

        # Validate fallback configuration details
        if self.enable_fallback and self.fallback_provider:
            fallback_key_map = {
                "anthropic": self.anthropic_api_key,
                "openai": self.openai_api_key,
            }
            key = fallback_key_map.get(self.fallback_provider)
            if key is None and self.fallback_provider != "watsonx":
                logger.warning(
                    "Fallback provider '%s' configured but API key is not set",
                    self.fallback_provider,
                )
                self.enable_fallback = False

        # Validate provider-specific required fields
        if self.llm_provider == "watsonx":
            if not all([self.watsonx_url, self.watsonx_apikey, self.watsonx_project_id]):
                # Log generic warning without exposing field names to prevent information leakage
                logger.warning(
                    "Configuration validation failed for provider: %s",
                    self.llm_provider,
                )
                msg = "Required configuration for watsonx provider is incomplete"
                raise ValueError(msg)
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            # Log generic warning without exposing field names to prevent information leakage
            logger.warning(
                "Configuration validation failed for provider: %s",
                self.llm_provider,
            )
            msg = "Required configuration for anthropic provider is incomplete"
            raise ValueError(msg)
        elif self.llm_provider == "openai" and not self.openai_api_key and not self.llm_api_base:
            # For openai, require either the API key or a custom base URL (e.g. Ollama)
            logger.warning(
                "Configuration validation failed for provider: %s",
                self.llm_provider,
            )
            msg = "Required configuration for openai provider is incomplete"
            raise ValueError(msg)


# Global config instance (lazy loaded) with thread-safe initialization
_config: Config | None = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """Get or create the global config instance in a thread-safe manner.

    Uses double-checked locking pattern to ensure thread safety while
    minimizing lock contention after initial initialization.

    Returns:
        Config: Application configuration

    Thread Safety:
        This function is thread-safe and can be called concurrently from
        multiple threads. The first thread to acquire the lock will create
        the config instance, and subsequent calls will return the same instance.
    """
    global _config
    # First check without lock (optimization for already-initialized case)
    if _config is None:
        with _config_lock:
            # Double-check inside lock to prevent race condition
            if _config is None:
                _config = Config.model_validate({})
    return _config


# ---------------------------------------------------------------------------
# Backward-compatible re-exports from pptx_agent.templates
# ---------------------------------------------------------------------------
# These were originally defined here but have been moved to a dedicated module
# (pptx_agent.templates) to respect the Single Responsibility Principle.
# Re-exporting keeps existing ``from pptx_agent.config import …`` imports working.

from pptx_agent.templates import (  # noqa: E402
    generate_basic_template,
    generate_japanese_template,
    validate_templates,
)

__all__ = [
    "Config",
    "generate_basic_template",
    "generate_japanese_template",
    "get_config",
    "validate_templates",
]
