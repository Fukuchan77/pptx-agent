"""Pydantic Logfire configuration for LLM tracing.

This module configures Pydantic Logfire for tracing LLM interactions,
including prompts, responses, tokens, and latency.
"""

import logging
import os

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LogfireConfig(BaseModel):
    """Configuration for Pydantic Logfire.

    Attributes:
        enabled: Whether Logfire is enabled
        service_name: Service name for Logfire tracing
        environment: Environment name (dev, prod, test)
    """

    enabled: bool = False
    service_name: str = "pptx-agent"
    environment: str = "development"


def is_logfire_enabled() -> bool:
    """Check if Logfire is enabled.

    Logfire is disabled in test environments and can be controlled
    via LOGFIRE_ENABLED environment variable.

    Returns:
        True if Logfire should be enabled, False otherwise
    """
    # Disable in test environment
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False

    # Check explicit enable/disable
    enabled = os.getenv("LOGFIRE_ENABLED", "false").lower()
    return enabled in ("true", "1", "yes")


def get_logfire_config() -> LogfireConfig:
    """Get Logfire configuration.

    Returns:
        LogfireConfig instance with current settings
    """
    enabled = is_logfire_enabled()
    environment = os.getenv("ENVIRONMENT", "development")
    service_name = os.getenv("LOGFIRE_SERVICE_NAME", "pptx-agent")

    return LogfireConfig(
        enabled=enabled,
        service_name=service_name,
        environment=environment,
    )


def configure_logfire() -> None:
    """Configure Pydantic Logfire for LLM tracing.

    This function sets up Logfire with the appropriate configuration
    based on environment variables. In test environments, Logfire
    is automatically disabled.
    """
    config = get_logfire_config()

    if not config.enabled:
        # Logfire disabled, nothing to configure
        return

    try:
        import logfire  # noqa: PLC0415

        # Configure Logfire with service name and environment
        logfire.configure(
            service_name=config.service_name,
            environment=config.environment,
        )
    except ImportError:
        # Logfire not installed, silently skip configuration
        pass
    except (ValueError, RuntimeError, AttributeError, TypeError) as e:
        # Log configuration errors but don't fail
        # In production, we want the app to work even if Logfire fails
        # Security-related exceptions (PermissionError, OSError subclasses) will propagate
        logger.warning("Failed to configure Logfire: %s", e)
