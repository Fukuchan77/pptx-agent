"""Unit tests for content validator."""

import pytest

from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import SlideSchema
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.text import TextBlock
from pptx_agent.validators.content_validator import validate_content
from pptx_agent.validators.exceptions import ContentValidationError


class TestContentValidator:
    """Test cases for content validator."""

    @pytest.fixture
    def valid_presentation(self) -> PresentationSchema:
        """Create a valid presentation with 3 slides."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[
                    TextBlock(placeholder_name="Title", text="Welcome", language="en"),
                    TextBlock(placeholder_name="Subtitle", text="Overview", language="en"),
                ],
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[
                    TextBlock(placeholder_name="Title", text="Main Content", language="en"),
                    TextBlock(
                        placeholder_name="Content",
                        text="This is the main content",
                        language="en",
                    ),
                ],
            ),
            SlideSchema(
                layout_name="Content",
                title="Conclusion",
                content=[
                    TextBlock(placeholder_name="Title", text="Conclusion", language="en"),
                    TextBlock(placeholder_name="Content", text="Thank you", language="en"),
                ],
            ),
        ]
        return PresentationSchema(title="Test Presentation", slides=slides)

    @pytest.fixture
    def valid_outline(self) -> PresentationOutline:
        """Create a valid outline with 3 slides."""
        slides = [
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Introduction",
                content="Welcome",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Content",
                title="Main Content",
                content="Content",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Content",
                title="Conclusion",
                content="Thank you",
            ),
        ]
        return PresentationOutline(title="Test Presentation", slides=slides)

    @pytest.fixture
    def sample_template_manifest(self) -> TemplateManifest:
        """Create a sample template manifest."""
        layouts = [
            LayoutInfo(
                name="Title Slide",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Subtitle", type="TEXT", max_chars=200),
                ],
            ),
            LayoutInfo(
                name="Content",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                ],
            ),
        ]
        return TemplateManifest(template_name="test_template", layouts=layouts)

    def test_validate_valid_content_without_outline(
        self, valid_presentation: PresentationSchema
    ) -> None:
        """Test that valid content passes validation without outline."""
        result = validate_content(valid_presentation)
        assert result == valid_presentation

    def test_validate_valid_content_with_outline(
        self, valid_presentation: PresentationSchema, valid_outline: PresentationOutline
    ) -> None:
        """Test that valid content passes validation with outline."""
        result = validate_content(valid_presentation, valid_outline)
        assert result == valid_presentation

    def test_validate_valid_content_with_template_manifest(
        self,
        valid_presentation: PresentationSchema,
        sample_template_manifest: TemplateManifest,
    ) -> None:
        """Test that valid content passes validation with template manifest."""
        result = validate_content(valid_presentation, _template_manifest=sample_template_manifest)
        assert result == valid_presentation

    def test_validate_content_slide_count_mismatch_with_outline(
        self, valid_outline: PresentationOutline
    ) -> None:
        """Test that slide count mismatch with outline raises error."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[TextBlock(placeholder_name="Title", text="Welcome", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[TextBlock(placeholder_name="Title", text="Content", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError, match="Presentation has 2 slides but outline specified 3"
        ):
            validate_content(presentation, valid_outline)

    def test_validate_content_empty_content_blocks(self) -> None:
        """Test that slides with empty content blocks raise error."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[],  # Empty content list
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[TextBlock(placeholder_name="Title", text="Content", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Conclusion",
                content=[TextBlock(placeholder_name="Title", text="Conclusion", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError, match="Slide 1 'Introduction' has no content blocks"
        ):
            validate_content(presentation)

    def test_validate_content_empty_text_in_text_block(self) -> None:
        """Test that text blocks with empty text raise error."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[
                    TextBlock(placeholder_name="Title", text="", language="en"),  # Empty text
                    TextBlock(placeholder_name="Subtitle", text="Overview", language="en"),
                ],
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[TextBlock(placeholder_name="Title", text="Content", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Conclusion",
                content=[TextBlock(placeholder_name="Title", text="Conclusion", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Introduction' has empty text in placeholder 'Title'",
        ):
            validate_content(presentation)

    def test_validate_content_whitespace_only_text(self) -> None:
        """Test that text blocks with whitespace-only text raise error."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[
                    TextBlock(
                        placeholder_name="Title", text="   ", language="en"
                    ),  # Whitespace only
                    TextBlock(placeholder_name="Subtitle", text="Overview", language="en"),
                ],
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[TextBlock(placeholder_name="Title", text="Content", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Conclusion",
                content=[TextBlock(placeholder_name="Title", text="Conclusion", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Introduction' has empty text in placeholder 'Title'",
        ):
            validate_content(presentation)

    def test_validate_content_multiple_slides_with_empty_content(self) -> None:
        """Test that error is raised for first slide with empty content."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Introduction",
                content=[TextBlock(placeholder_name="Title", text="Welcome", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Main Content",
                content=[],  # Empty content
            ),
            SlideSchema(
                layout_name="Content",
                title="Conclusion",
                content=[],  # Empty content
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        # Should report the first empty slide (slide 2)
        with pytest.raises(
            ContentValidationError, match="Slide 2 'Main Content' has no content blocks"
        ):
            validate_content(presentation)

    def test_validate_content_all_slides_have_content(
        self, valid_presentation: PresentationSchema
    ) -> None:
        """Test that all slides with content blocks pass validation."""
        result = validate_content(valid_presentation)
        assert result == valid_presentation
        # Verify all slides have content
        for slide in result.slides:
            assert len(slide.content) > 0

    def test_validate_content_with_all_parameters(
        self,
        valid_presentation: PresentationSchema,
        valid_outline: PresentationOutline,
        sample_template_manifest: TemplateManifest,
    ) -> None:
        """Test validation with all optional parameters provided."""
        result = validate_content(
            valid_presentation, valid_outline, _template_manifest=sample_template_manifest
        )
        assert result == valid_presentation

    def test_validate_content_title_mismatch_ignored(
        self, valid_presentation: PresentationSchema
    ) -> None:
        """Test that title mismatch between presentation and outline is not validated."""
        # This test documents that we're not validating title mismatch
        # (could be added in future if needed)
        outline = PresentationOutline(
            title="Different Title",  # Different from presentation title
            slides=[
                SlideContent(
                    slide_number=i,
                    layout_name="Content",
                    title=f"Slide {i}",
                    content="Content",
                )
                for i in range(1, 4)
            ],
        )
        result = validate_content(valid_presentation, outline)
        assert result == valid_presentation

    def test_validate_content_edge_case_minimal_valid_presentation(self) -> None:
        """Test validation with minimal valid presentation (1 slide, 1 text block)."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Minimal",
                content=[TextBlock(placeholder_name="Title", text="X", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Minimal", slides=slides)
        result = validate_content(presentation)
        assert result == presentation

    def test_validate_content_edge_case_single_character_text(self) -> None:
        """Test that single character text is valid."""
        slides = [
            SlideSchema(
                layout_name="Title Slide",
                title="Single Char",
                content=[TextBlock(placeholder_name="Title", text="A", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Another",
                content=[TextBlock(placeholder_name="Title", text="B", language="en")],
            ),
            SlideSchema(
                layout_name="Content",
                title="Third",
                content=[TextBlock(placeholder_name="Title", text="C", language="en")],
            ),
        ]
        presentation = PresentationSchema(title="Single Characters", slides=slides)
        result = validate_content(presentation)
        assert result == presentation
