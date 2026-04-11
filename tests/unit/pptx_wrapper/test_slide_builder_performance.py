"""Performance tests for PowerPoint rendering (slide builder).

Tests ensure PowerPoint rendering meets performance requirements:
- SC-003: PowerPoint rendering completes in under 10 seconds after content generation
"""

import time
from pathlib import Path
from typing import Any

import pytest

from pptx_agent.pptx_wrapper.slide_builder import build_presentation
from pptx_agent.schemas import PresentationSchema, SlideSchema
from pptx_agent.schemas.text import TextBlock


@pytest.fixture
def simple_presentation():
    """Create a simple presentation schema for testing."""
    slides = [
        SlideSchema(
            layout_name="Title Slide",
            title="Test Presentation",
            content=[
                TextBlock(
                    placeholder_name="Subtitle 1",
                    text="Performance Test Presentation",
                    language="en",
                )
            ],
        ),
        SlideSchema(
            layout_name="Title and Content",
            title="Slide 1",
            content=[
                TextBlock(
                    placeholder_name="Content Placeholder 2",
                    text="This is test content for performance measurement.",
                    language="en",
                )
            ],
        ),
        SlideSchema(
            layout_name="Title and Content",
            title="Slide 2",
            content=[
                TextBlock(
                    placeholder_name="Content Placeholder 2",
                    text="More test content with bullet points:\n- Point 1\n- Point 2\n- Point 3",
                    language="en",
                )
            ],
        ),
    ]
    return PresentationSchema(title="Test Performance Presentation", slides=slides)


@pytest.fixture
def medium_presentation():
    """Create a medium-sized presentation (10 slides) for testing."""
    # Create title slide
    title_slide = SlideSchema(
        layout_name="Title Slide",
        title="Test Presentation",
        content=[
            TextBlock(
                placeholder_name="Subtitle 1",
                text="Performance Test - 10 Slides",
                language="en",
            )
        ],
    )

    # Create 9 content slides using list comprehension
    content_slides = [
        SlideSchema(
            layout_name="Title and Content",
            title=f"Slide {i}",
            content=[
                TextBlock(
                    placeholder_name="Content Placeholder 2",
                    text=f"Content for slide {i}:\n"
                    f"- Key point 1 for slide {i}\n"
                    f"- Key point 2 for slide {i}\n"
                    f"- Key point 3 for slide {i}\n"
                    f"- Key point 4 for slide {i}",
                    language="en",
                )
            ],
        )
        for i in range(1, 10)
    ]

    return PresentationSchema(
        title="Test Performance Presentation - 10 Slides",
        slides=[title_slide, *content_slides],
    )


def test_render_simple_presentation_performance(
    basic_template_path: Any,
    simple_presentation: Any,
    tmp_path: Any,
) -> None:
    """Test rendering performance for simple presentation (3 slides).

    Success Criteria SC-003: PowerPoint rendering completes in under 10 seconds
    after content generation.
    """
    output_path = str(tmp_path / "test_simple_performance.pptx")

    start_time = time.time()

    # Build presentation
    result_path = build_presentation(
        content=simple_presentation,
        template_path=basic_template_path,
        output_path=output_path,
    )

    elapsed_time = time.time() - start_time

    # Verify presentation was created
    assert result_path == output_path
    assert Path(output_path).exists()

    # Assert performance requirement: must complete within 10 seconds
    assert elapsed_time < 10.0, f"Rendering took {elapsed_time:.2f}s, exceeds 10.0s target (SC-003)"


def test_render_medium_presentation_performance(
    basic_template_path: Any,
    medium_presentation: Any,
    tmp_path: Any,
) -> None:
    """Test rendering performance for medium presentation (10 slides).

    Success Criteria SC-003: PowerPoint rendering completes in under 10 seconds
    after content generation.

    Target from spec: 10-slide presentation in under 60s total (SC-001),
    but rendering alone should be under 10s (SC-003).
    """
    output_path = str(tmp_path / "test_medium_performance.pptx")

    start_time = time.time()

    # Build presentation
    result_path = build_presentation(
        content=medium_presentation,
        template_path=basic_template_path,
        output_path=output_path,
    )

    elapsed_time = time.time() - start_time

    # Verify presentation was created
    assert result_path == output_path
    assert Path(output_path).exists()
    assert len(medium_presentation.slides) == 10

    # Assert performance requirement: must complete within 10 seconds
    assert elapsed_time < 10.0, (
        f"Rendering 10-slide presentation took {elapsed_time:.2f}s, exceeds 10.0s target (SC-003)"
    )


def test_render_multiple_presentations_performance(
    basic_template_path: Any,
    simple_presentation: Any,
    tmp_path: Any,
) -> None:
    """Test rendering performance across multiple presentations.

    Ensures consistent performance across multiple rendering operations.
    Each render must complete within 10 seconds.
    """
    run_count = 3
    times = []

    for i in range(run_count):
        output_path = str(tmp_path / f"test_multi_{i}.pptx")

        start_time = time.time()
        result_path = build_presentation(
            content=simple_presentation,
            template_path=basic_template_path,
            output_path=output_path,
        )
        elapsed_time = time.time() - start_time
        times.append(elapsed_time)

        # Verify presentation was created
        assert result_path == output_path
        assert Path(output_path).exists()

        # Each run must meet performance target
        assert elapsed_time < 10.0, (
            f"Run {i + 1}: Rendering took {elapsed_time:.2f}s, exceeds 10.0s target (SC-003)"
        )

    # Calculate average time
    avg_time = sum(times) / len(times)

    # Average should also be well under target
    assert avg_time < 10.0, f"Average rendering time {avg_time:.2f}s exceeds 10.0s target"
