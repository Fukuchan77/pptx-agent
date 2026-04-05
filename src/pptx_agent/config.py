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

    Supports two LLM providers:
    - watsonx (dev environment)
    - anthropic (production environment)

    Environment variables:
        LLM_PROVIDER: 'watsonx' or 'anthropic'
        LLM_MODEL: Model name/ID
        LLM_API_BASE: API base URL (for watsonx dev)
        WATSONX_URL: Watsonx API URL
        WATSONX_APIKEY: Watsonx API key
        WATSONX_PROJECT_ID: Watsonx project ID
        ANTHROPIC_API_KEY: Anthropic API key (for Claude)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Common settings
    llm_provider: Literal["watsonx", "anthropic"]
    llm_model: str
    llm_api_base: str | None = None

    # Watsonx settings (required when provider=watsonx)
    watsonx_url: str | None = None
    watsonx_apikey: str | None = None
    watsonx_project_id: str | None = None

    # Anthropic settings (required when provider=anthropic)
    anthropic_api_key: str | None = None

    @field_validator("watsonx_apikey", "anthropic_api_key", mode="before")
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
        if v is not None and len(v.strip()) < MIN_API_KEY_LENGTH:
            msg = "API key appears to be invalid (too short)"
            raise ValueError(msg)
        return v.strip() if v is not None else None

    def model_post_init(self, __context: Any) -> None:
        """Validate provider-specific required fields."""
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
                _config = Config()  # type: ignore[call-arg]
    return _config
