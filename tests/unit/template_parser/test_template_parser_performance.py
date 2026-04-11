"""Performance tests for template parser.

Tests ensure template parsing meets performance requirements:
- SC-002: Template parsing completes in under 5 seconds for typical templates
"""

import time
from pathlib import Path
from typing import Any

import pytest

from pptx_agent.template_parser.parser import TemplateParser


@pytest.fixture
def parser():
    """Create a TemplateParser instance."""
    return TemplateParser()


@pytest.fixture
def japanese_template_path():
    """Get path to Japanese template for testing."""
    template_path = Path("templates/japanese-template.pptx")
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_path}")
    return str(template_path)


def test_parse_template_performance_basic(parser: Any, basic_template_path: Any) -> None:
    """Test that template parsing completes within 5 seconds for basic template.

    Success Criteria SC-002: Template parsing completes in under 5 seconds
    for typical templates.
    """
    start_time = time.time()

    # Parse template
    template_metadata = parser.parse_template(basic_template_path)

    elapsed_time = time.time() - start_time

    # Verify template was parsed successfully
    assert template_metadata is not None
    assert len(template_metadata.layouts) > 0

    # Assert performance requirement: must complete within 5 seconds
    assert elapsed_time < 5.0, (
        f"Template parsing took {elapsed_time:.2f}s, exceeds 5.0s target (SC-002)"
    )


def test_parse_template_performance_japanese(parser: Any, japanese_template_path: Any) -> None:
    """Test that template parsing completes within 5 seconds for Japanese template.

    Success Criteria SC-002: Template parsing completes in under 5 seconds
    for typical templates.
    """
    start_time = time.time()

    # Parse template
    template_metadata = parser.parse_template(japanese_template_path)

    elapsed_time = time.time() - start_time

    # Verify template was parsed successfully
    assert template_metadata is not None
    assert len(template_metadata.layouts) > 0

    # Assert performance requirement: must complete within 5 seconds
    assert elapsed_time < 5.0, (
        f"Template parsing took {elapsed_time:.2f}s, exceeds 5.0s target (SC-002)"
    )


def test_parse_template_performance_multiple_runs(parser: Any, basic_template_path: Any) -> None:
    """Test template parsing performance across multiple runs.

    Ensures consistent performance across multiple parsing operations.
    Each run must complete within 5 seconds.
    """
    run_count = 3
    times = []

    for i in range(run_count):
        start_time = time.time()
        template_metadata = parser.parse_template(basic_template_path)
        elapsed_time = time.time() - start_time
        times.append(elapsed_time)

        # Verify template was parsed successfully
        assert template_metadata is not None
        assert len(template_metadata.layouts) > 0

        # Each run must meet performance target
        assert elapsed_time < 5.0, (
            f"Run {i + 1}: Template parsing took {elapsed_time:.2f}s, exceeds 5.0s target (SC-002)"
        )

    # Calculate average time
    avg_time = sum(times) / len(times)

    # Average should also be well under target
    assert avg_time < 5.0, f"Average parsing time {avg_time:.2f}s exceeds 5.0s target"
