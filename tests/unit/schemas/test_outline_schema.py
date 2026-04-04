"""Unit tests for outline schema models.

Tests for PresentationOutline and SlideContent models used in LLM agent workflow.
"""

import pytest
from pydantic import ValidationError

from pptx_agent.schemas.outline import PresentationOutline, SlideContent


class TestSlideContent:
    """Tests for SlideContent model."""

    def test_slide_content_minimal(self):
        """Test SlideContent with minimal required fields."""
        slide = SlideContent(
            slide_number=1,
            layout_name="Title Slide",
            title="Introduction",
            content="Welcome to the presentation",
        )
        assert slide.slide_number == 1
        assert slide.layout_name == "Title Slide"
        assert slide.title == "Introduction"
        assert slide.content == "Welcome to the presentation"
        assert slide.speaker_notes is None

    def test_slide_content_with_speaker_notes(self):
        """Test SlideContent with speaker notes."""
        slide = SlideContent(
            slide_number=2,
            layout_name="Content Slide",
            title="Main Topic",
            content="Key points here",
            speaker_notes="Remember to emphasize this point",
        )
        assert slide.speaker_notes == "Remember to emphasize this point"

    def test_slide_content_invalid_slide_number(self):
        """Test that slide_number must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            SlideContent(
                slide_number=0,
                layout_name="Title Slide",
                title="Test",
                content="Test content",
            )
        assert "slide_number" in str(exc_info.value)

    def test_slide_content_empty_layout_name(self):
        """Test that layout_name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            SlideContent(
                slide_number=1,
                layout_name="",
                title="Test",
                content="Test content",
            )
        assert "layout_name" in str(exc_info.value)

    def test_slide_content_empty_title(self):
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            SlideContent(
                slide_number=1,
                layout_name="Content Slide",
                title="",
                content="Test content",
            )
        assert "title" in str(exc_info.value)

    def test_slide_content_allows_empty_content(self):
        """Test that content can be empty (for layout-only slides)."""
        slide = SlideContent(
            slide_number=1,
            layout_name="Section Header",
            title="Part 1",
            content="",
        )
        assert slide.content == ""


class TestPresentationOutline:
    """Tests for PresentationOutline model."""

    def test_presentation_outline_minimal(self):
        """Test PresentationOutline with minimal required fields."""
        outline = PresentationOutline(
            title="My Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title Slide",
                    title="Introduction",
                    content="Welcome",
                )
            ],
        )
        assert outline.title == "My Presentation"
        assert len(outline.slides) == 1
        assert outline.output_language == "en"  # Default

    def test_presentation_outline_with_language(self):
        """Test PresentationOutline with specified language."""
        outline = PresentationOutline(
            title="プレゼンテーション",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="タイトル",
                    title="導入",
                    content="ようこそ",
                )
            ],
            output_language="ja",
        )
        assert outline.output_language == "ja"

    def test_presentation_outline_empty_title(self):
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            PresentationOutline(
                title="",
                slides=[
                    SlideContent(
                        slide_number=1,
                        layout_name="Title Slide",
                        title="Test",
                        content="Test content",
                    )
                ],
            )
        assert "title" in str(exc_info.value)

    def test_presentation_outline_no_slides(self):
        """Test that at least one slide is required."""
        with pytest.raises(ValidationError) as exc_info:
            PresentationOutline(
                title="Test Presentation",
                slides=[],
            )
        assert "slides" in str(exc_info.value)

    def test_presentation_outline_invalid_language(self):
        """Test that language must be 'en' or 'ja'."""
        with pytest.raises(ValidationError) as exc_info:
            PresentationOutline(
                title="Test Presentation",
                slides=[
                    SlideContent(
                        slide_number=1,
                        layout_name="Title Slide",
                        title="Test",
                        content="Test content",
                    )
                ],
                output_language="fr",  # Invalid  # type: ignore[arg-type]
            )
        assert "output_language" in str(exc_info.value)

    def test_presentation_outline_multiple_slides(self):
        """Test PresentationOutline with multiple slides."""
        outline = PresentationOutline(
            title="Multi-slide Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title Slide",
                    title="Introduction",
                    content="Welcome",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Content Slide",
                    title="Main Content",
                    content="Key points",
                ),
                SlideContent(
                    slide_number=3,
                    layout_name="Closing Slide",
                    title="Conclusion",
                    content="Thank you",
                ),
            ],
        )
        assert len(outline.slides) == 3
        assert outline.slides[0].slide_number == 1
        assert outline.slides[1].slide_number == 2
        assert outline.slides[2].slide_number == 3

    def test_presentation_outline_slide_numbers_sequential(self):
        """Test that slide numbers should be sequential (validation)."""
        # This should pass - sequential numbers
        outline = PresentationOutline(
            title="Test",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title",
                    title="Slide 1",
                    content="Content 1",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Content",
                    title="Slide 2",
                    content="Content 2",
                ),
            ],
        )
        assert len(outline.slides) == 2
