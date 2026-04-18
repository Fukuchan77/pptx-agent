"""Configuration management using pydantic-settings.

Loads configuration from environment variables with support for .env files.
"""

import logging
import re
import threading
from typing import Any, Literal

# Thread-local storage for tracking validation state
_validation_state = threading.local()

from pydantic import PrivateAttr, ValidationInfo, field_validator, model_validator  # noqa: E402
from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: E402

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
        case_sensitive=False,
        extra="ignore",
    )

    # Common settings
    llm_provider: Literal["watsonx", "anthropic", "openai"]
    llm_model: str
    llm_api_base: str | None = None

    # Internal test mode flag - PRIVATE to prevent environment variable bypass
    _allow_test_keys: bool = PrivateAttr(default=False)
    """Private attribute to prevent test key bypass via environment variables.

    Can only be set via model_validate(..., context={"allow_test_keys": True}).
    This ensures explicit opt-in for test mode and prevents accidental bypass.
    """

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

    # HTTP-level retry and timeout configuration (FR-045)
    retry_base_delay: float = 1.0  # Base delay for exponential backoff (seconds)
    retry_max_delay: float = 8.0  # Maximum delay (1→2→4→8 seconds)
    connect_timeout: float = 10.0  # Connection timeout
    write_timeout: float = 10.0  # Write timeout
    pool_timeout: float = 10.0  # Pool timeout

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
        """Validate that API keys have minimum length and strip whitespace.

        Basic validation only - test pattern checking is done in model_validator
        where validation context is accessible in BaseSettings.

        Args:
            v: The API key value to validate

        Returns:
            The validated API key value with whitespace stripped (or None if None was provided)

        Raises:
            ValueError: If the API key is too short
        """
        if v is not None:
            stripped = v.strip()
            if len(stripped) < MIN_API_KEY_LENGTH:
                msg = "API key appears to be invalid (too short)"
                raise ValueError(msg)

            # Check for placeholder patterns (always reject these)
            placeholder_pattern = r"^(your|sk-xxx|placeholder|todo|replace)-?"
            if re.match(placeholder_pattern, stripped, re.IGNORECASE):
                msg = "API key appears to be a placeholder value — update .env with your actual key"
                raise ValueError(msg)

            return stripped
        return None

    @model_validator(mode="wrap")
    @classmethod
    def validate_test_keys_with_context(
        cls, values: Any, handler: Any, info: ValidationInfo
    ) -> "Config":
        """Validate test API keys using validation context.

        In Pydantic v2 BaseSettings, field_validator doesn't receive validation context
        from model_validate(..., context={...}). This wrap validator has access to the
        context and performs test key validation after basic field validation.

        BaseSettings calls this validator twice in a nested fashion:
        1. Outer call: has the user's original context
        2. Inner call (nested inside handler): context=None

        We only validate in the outer call to avoid duplicate/conflicting validation.

        Args:
            values: Input values to validate
            handler: The default validation handler
            info: Validation info containing context

        Returns:
            The validated Config instance

        Raises:
            ValueError: If test keys are used without allow_test_keys=True in context
        """
        # Check if we're already validating (nested call detection)
        # BaseSettings calls this validator twice - we only validate in the outer call
        is_nested_call = getattr(_validation_state, "validating", False)

        if is_nested_call:
            # This is the nested inner call - just run handler and return
            return handler(values)

        # Mark that we're now validating (for nested call detection)
        _validation_state.validating = True

        try:
            # Extract allow_test_keys from context (from outer call)
            allow_test_keys = info.context.get("allow_test_keys", False) if info.context else False

            # Call the default handler to perform field validation
            result = handler(values)

            # Perform test key validation only in production mode
            if not allow_test_keys:
                # Production mode: check all API keys for test patterns
                test_patterns = [
                    "test",
                    "dummy",
                    "fake",
                    "sample",
                    "example",
                    "placeholder",
                    "your-api-key",
                    "xxx",
                ]

                # Check each API key field
                for field_name in ["watsonx_apikey", "anthropic_api_key", "openai_api_key"]:
                    key_value = getattr(result, field_name, None)
                    if key_value:
                        v_lower = key_value.lower()
                        for pattern in test_patterns:
                            if pattern in v_lower:
                                msg = (
                                    f"API key appears to be a test value (contains '{pattern}'). "
                                    f"Please use a real API key in production."
                                )
                                raise ValueError(msg)

            return result
        finally:
            # Clear the validation flag
            _validation_state.validating = False

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


def reset_config() -> None:
    """Reset the global config instance in a thread-safe manner.

    This function is primarily intended for testing purposes to ensure
    test isolation by clearing the cached configuration between tests.

    Thread Safety:
        This function is thread-safe and can be called concurrently from
        multiple threads. The lock ensures that concurrent resets and
        get_config() calls are properly synchronized.
    """
    global _config
    with _config_lock:
        _config = None


__all__ = [
    "Config",
    "get_config",
    "reset_config",
]
