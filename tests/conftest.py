from pathlib import Path

import pytest

from pptx_agent.config import reset_config


@pytest.fixture(autouse=True)
def ignore_env_file(monkeypatch: pytest.MonkeyPatch):
    """Ignore .env file during tests to prevent interference with test configurations.

    This fixture is automatically applied to all tests (autouse=True).
    It patches the Config class's model_config to disable .env file loading,
    ensuring tests use only explicitly provided configuration values.

    Without this fixture, tests would be affected by values in the project's
    .env file, causing tests to fail when .env contains non-default values.
    """
    # Reset the global config instance to ensure clean state
    from pydantic_settings import SettingsConfigDict

    import pptx_agent.config

    reset_config()

    # Patch the Config class's model_config to disable env_file
    original_model_config = pptx_agent.config.Config.model_config

    # Create a new SettingsConfigDict without env_file
    patched_model_config = SettingsConfigDict(
        env_file=None,  # Disable .env file loading
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    monkeypatch.setattr(pptx_agent.config.Config, "model_config", patched_model_config)

    yield

    # Restore original model_config and reset config
    monkeypatch.setattr(pptx_agent.config.Config, "model_config", original_model_config)
    reset_config()


@pytest.fixture
def basic_template_path():
    """Get path to basic template for testing.

    Uses template from tests/fixtures/ to ensure availability in CI.
    """
    template_path = Path("tests/fixtures/basic-template.pptx")
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_path}")
    return str(template_path)
    return str(template_path)
