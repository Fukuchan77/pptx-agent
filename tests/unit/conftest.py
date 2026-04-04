"""Shared pytest fixtures for unit tests."""

from pathlib import Path

import pytest


@pytest.fixture
def template_path() -> str:
    """Provide absolute path to basic template file.

    Returns:
        Absolute path to templates/basic-template.pptx
    """
    # Get project root (three levels up from this conftest.py file)
    project_root = Path(__file__).parent.parent.parent
    template = project_root / "templates" / "basic-template.pptx"

    # Return as string for compatibility with existing tests
    return str(template)
