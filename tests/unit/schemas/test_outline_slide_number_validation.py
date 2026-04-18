"""Unit tests for PresentationOutline slide number sequence validation.

Tests verify that slide_number values form a continuous sequence 1..n
per Task 18 (Requirement 4.1.1).
"""

import pytest
from pydantic import ValidationError

from pptx_agent.schemas.outline import PresentationOutline, SlideContent


def test_valid_slide_number_sequence():
    """Test that valid continuous sequence 1,2,3 passes validation."""
    outline = PresentationOutline(
        title="Test Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Slide 1",
                content="Content 1",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Slide 2",
                content="Content 2",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title and Content",
                title="Slide 3",
                content="Content 3",
            ),
        ],
        output_language="en",
    )

    # Should not raise
    assert len(outline.slides) == 3
    assert outline.slides[0].slide_number == 1
    assert outline.slides[1].slide_number == 2
    assert outline.slides[2].slide_number == 3


def test_slide_number_gap_detected():
    """Test that gap in sequence (1,2,4) triggers validation error."""
    with pytest.raises(ValidationError) as exc_info:
        PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title Slide",
                    title="Slide 1",
                    content="Content 1",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Title and Content",
                    title="Slide 2",
                    content="Content 2",
                ),
                SlideContent(
                    slide_number=4,  # Gap! Missing 3
                    layout_name="Title and Content",
                    title="Slide 4",
                    content="Content 4",
                ),
            ],
            output_language="en",
        )

    # Verify error message mentions slide number sequence
    error_msg = str(exc_info.value)
    assert "slide" in error_msg.lower()
    assert "sequence" in error_msg.lower() or "continuous" in error_msg.lower()


def test_slide_number_duplicate_detected():
    """Test that duplicate slide numbers trigger validation error."""
    with pytest.raises(ValidationError) as exc_info:
        PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title Slide",
                    title="Slide 1",
                    content="Content 1",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Title and Content",
                    title="Slide 2",
                    content="Content 2",
                ),
                SlideContent(
                    slide_number=2,  # Duplicate!
                    layout_name="Title and Content",
                    title="Slide 2 Again",
                    content="Content 2 Again",
                ),
            ],
            output_language="en",
        )

    error_msg = str(exc_info.value)
    assert "slide" in error_msg.lower()
    assert (
        "sequence" in error_msg.lower()
        or "continuous" in error_msg.lower()
        or "unique" in error_msg.lower()
    )


def test_slide_number_not_starting_at_one():
    """Test that sequence not starting at 1 triggers validation error."""
    with pytest.raises(ValidationError) as exc_info:
        PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=2,  # Should start at 1
                    layout_name="Title Slide",
                    title="Slide 2",
                    content="Content 2",
                ),
                SlideContent(
                    slide_number=3,
                    layout_name="Title and Content",
                    title="Slide 3",
                    content="Content 3",
                ),
            ],
            output_language="en",
        )

    error_msg = str(exc_info.value)
    assert "slide" in error_msg.lower()
    assert (
        "sequence" in error_msg.lower()
        or "start" in error_msg.lower()
        or "continuous" in error_msg.lower()
    )


def test_single_slide_number_one_valid():
    """Test that single slide with number 1 is valid."""
    outline = PresentationOutline(
        title="Test Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Only Slide",
                content="Only Content",
            ),
        ],
        output_language="en",
    )

    assert len(outline.slides) == 1
    assert outline.slides[0].slide_number == 1


def test_large_continuous_sequence_valid():
    """Test that large continuous sequence passes validation."""
    slides = [
        SlideContent(
            slide_number=i,
            layout_name="Title and Content",
            title=f"Slide {i}",
            content=f"Content {i}",
        )
        for i in range(1, 21)  # 20 slides
    ]

    outline = PresentationOutline(
        title="Large Presentation",
        slides=slides,
        output_language="en",
    )

    assert len(outline.slides) == 20
    assert outline.slides[0].slide_number == 1
    assert outline.slides[19].slide_number == 20
