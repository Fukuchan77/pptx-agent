"""Unit tests for outline validator."""

import pytest

from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.validators.exceptions import InvalidFileError
from pptx_agent.validators.outline_validator import validate_outline


class TestOutlineValidator:
    """Test cases for outline validator."""

    @pytest.fixture
    def valid_outline(self) -> PresentationOutline:
        """Create a valid presentation outline with 5 slides."""
        slides = [
            SlideContent(
                slide_number=i,
                layout_name="Title Slide" if i == 1 else "Content",
                title=f"Slide {i}",
                content=f"Content for slide {i}",
            )
            for i in range(1, 6)
        ]
        return PresentationOutline(title="Test Presentation", slides=slides, output_language="en")

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
            LayoutInfo(
                name="Two Content",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Left Content", type="TEXT", max_chars=300),
                    PlaceholderInfo(name="Right Content", type="TEXT", max_chars=300),
                ],
            ),
        ]
        return TemplateManifest(template_name="test_template", layouts=layouts)

    def test_validate_valid_outline_without_template(
        self, valid_outline: PresentationOutline
    ) -> None:
        """Test that a valid outline passes validation without template manifest."""
        result = validate_outline(valid_outline)
        assert result == valid_outline

    def test_validate_valid_outline_with_template(
        self, valid_outline: PresentationOutline, sample_template_manifest: TemplateManifest
    ) -> None:
        """Test that a valid outline passes validation with template manifest."""
        result = validate_outline(valid_outline, sample_template_manifest)
        assert result == valid_outline

    def test_validate_outline_too_few_slides(self) -> None:
        """Test that outline with fewer than 3 slides raises error."""
        slides = [
            SlideContent(
                slide_number=1, layout_name="Title Slide", title="Slide 1", content="Content 1"
            ),
            SlideContent(
                slide_number=2, layout_name="Content", title="Slide 2", content="Content 2"
            ),
        ]
        outline = PresentationOutline(title="Too Few Slides", slides=slides)

        with pytest.raises(InvalidFileError, match="must contain between 3 and 30 slides"):
            validate_outline(outline)

    def test_validate_outline_too_many_slides(self) -> None:
        """Test that outline with more than 30 slides raises error."""
        slides = [
            SlideContent(
                slide_number=i, layout_name="Content", title=f"Slide {i}", content=f"Content {i}"
            )
            for i in range(1, 32)  # 31 slides
        ]
        outline = PresentationOutline(title="Too Many Slides", slides=slides)

        with pytest.raises(InvalidFileError, match="must contain between 3 and 30 slides"):
            validate_outline(outline)

    def test_validate_outline_exactly_3_slides(self) -> None:
        """Test that outline with exactly 3 slides passes validation (edge case)."""
        slides = [
            SlideContent(
                slide_number=i, layout_name="Content", title=f"Slide {i}", content=f"Content {i}"
            )
            for i in range(1, 4)  # Exactly 3 slides
        ]
        outline = PresentationOutline(title="Exactly 3 Slides", slides=slides)

        result = validate_outline(outline)
        assert result == outline

    def test_validate_outline_exactly_30_slides(self) -> None:
        """Test that outline with exactly 30 slides passes validation (edge case)."""
        slides = [
            SlideContent(
                slide_number=i, layout_name="Content", title=f"Slide {i}", content=f"Content {i}"
            )
            for i in range(1, 31)  # Exactly 30 slides
        ]
        outline = PresentationOutline(title="Exactly 30 Slides", slides=slides)

        result = validate_outline(outline)
        assert result == outline

    def test_validate_outline_invalid_layout_type(
        self, sample_template_manifest: TemplateManifest
    ) -> None:
        """Test that outline with invalid layout type raises error when template provided."""
        slides = [
            SlideContent(
                slide_number=1, layout_name="Title Slide", title="Slide 1", content="Content 1"
            ),
            SlideContent(
                slide_number=2,
                layout_name="NonExistentLayout",
                title="Slide 2",
                content="Content 2",
            ),
            SlideContent(
                slide_number=3, layout_name="Content", title="Slide 3", content="Content 3"
            ),
        ]
        outline = PresentationOutline(title="Invalid Layout", slides=slides)

        with pytest.raises(
            InvalidFileError, match="Layout 'NonExistentLayout' not found in template"
        ):
            validate_outline(outline, sample_template_manifest)

    def test_validate_outline_missing_title(self) -> None:
        """Test that outline with missing title raises error via Pydantic validation."""
        # This should be caught by Pydantic validation before reaching our validator
        slides = [
            SlideContent(
                slide_number=i, layout_name="Content", title=f"Slide {i}", content=f"Content {i}"
            )
            for i in range(1, 4)
        ]

        with pytest.raises(ValueError, match="String should have at least 1 character"):
            PresentationOutline(title="", slides=slides)  # type: ignore[arg-type]

    def test_validate_outline_empty_slide_list(self) -> None:
        """Test that outline with empty slide list raises error via Pydantic validation."""
        # This should be caught by Pydantic validation before reaching our validator
        with pytest.raises(ValueError, match="List should have at least 1 item"):
            PresentationOutline(title="Empty Slides", slides=[])

    def test_validate_outline_missing_slide_title(self) -> None:
        """Test that slide with missing title raises error via Pydantic validation."""
        # This should be caught by Pydantic validation before reaching our validator
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            SlideContent(slide_number=1, layout_name="Content", title="", content="Content")  # type: ignore[arg-type]

    def test_validate_outline_all_layouts_exist_in_template(
        self, sample_template_manifest: TemplateManifest
    ) -> None:
        """Test that all layout names in outline exist in template."""
        slides = [
            SlideContent(
                slide_number=1, layout_name="Title Slide", title="Title", content="Content 1"
            ),
            SlideContent(
                slide_number=2, layout_name="Content", title="Slide 2", content="Content 2"
            ),
            SlideContent(
                slide_number=3, layout_name="Two Content", title="Slide 3", content="Content 3"
            ),
        ]
        outline = PresentationOutline(title="All Valid Layouts", slides=slides)

        result = validate_outline(outline, sample_template_manifest)
        assert result == outline

    def test_validate_outline_multiple_invalid_layouts(
        self, sample_template_manifest: TemplateManifest
    ) -> None:
        """Test that error message lists all invalid layouts."""
        slides = [
            SlideContent(
                slide_number=1, layout_name="InvalidLayout1", title="Slide 1", content="Content 1"
            ),
            SlideContent(
                slide_number=2, layout_name="Content", title="Slide 2", content="Content 2"
            ),
            SlideContent(
                slide_number=3, layout_name="InvalidLayout2", title="Slide 3", content="Content 3"
            ),
        ]
        outline = PresentationOutline(title="Multiple Invalid", slides=slides)

        with pytest.raises(InvalidFileError, match="InvalidLayout1"):
            validate_outline(outline, sample_template_manifest)

    def test_validate_outline_without_template_allows_any_layout(self) -> None:
        """Test that validation without template manifest allows any layout name."""
        slides = [
            SlideContent(
                slide_number=1, layout_name="AnyLayoutName", title="Slide 1", content="Content 1"
            ),
            SlideContent(
                slide_number=2, layout_name="AnotherLayout", title="Slide 2", content="Content 2"
            ),
            SlideContent(
                slide_number=3, layout_name="CustomLayout", title="Slide 3", content="Content 3"
            ),
        ]
        outline = PresentationOutline(title="Any Layouts", slides=slides)

        # Should pass without template validation
        result = validate_outline(outline)
        assert result == outline
