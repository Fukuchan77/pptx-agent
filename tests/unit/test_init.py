"""Tests for package initialization."""

import pptx_agent


def test_package_has_version():
    """Test that package has __version__ attribute."""
    assert hasattr(pptx_agent, "__version__")
    assert isinstance(pptx_agent.__version__, str)
    assert pptx_agent.__version__ == "0.1.0"
