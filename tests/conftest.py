from pathlib import Path

import pytest


@pytest.fixture
def basic_template_path():
    """Get path to basic template for testing.

    Uses template from tests/fixtures/ to ensure availability in CI.
    """
    template_path = Path("tests/fixtures/basic-template.pptx")
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_path}")
    return str(template_path)
