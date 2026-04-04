"""Tests for validation functions."""

import pytest

from pptx_agent.schemas import ImageBlock, PresentationSchema, SlideSchema, TextBlock
from pptx_agent.template_parser import LayoutMetadata, PlaceholderMetadata, TemplateMetadata
from pptx_agent.validators import (
    ValidationResult,
    validate_presentation_schema,
    validate_slide_schema,
)


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Should create valid ValidationResult."""
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_result_with_errors(self):
        """Should create ValidationResult with errors."""
        result = ValidationResult(valid=False, errors=["Error 1", "Error 2"], warnings=[])
        assert result.valid is False
        assert len(result.errors) == 2
        assert result.warnings == []

    def test_result_with_warnings(self):
        """Should create ValidationResult with warnings."""
        result = ValidationResult(valid=True, errors=[], warnings=["Warning 1"])
        assert result.valid is True
        assert result.errors == []
        assert len(result.warnings) == 1


class TestPresentationValidation:
    """Tests for validate_presentation_schema."""

    def test_valid_presentation(self):
        """Should return valid result for correct schema."""
        schema = PresentationSchema(
            title="Test Presentation",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Slide 1",
                    content=[
                        TextBlock(placeholder_name="content", text="Sample text", language="en")
                    ],
                )
            ],
        )
        result = validate_presentation_schema(schema)
        assert result.valid is True
        assert result.errors == []

    def test_valid_presentation_basic(self):
        """Should validate presentation with single slide."""
        schema = PresentationSchema(
            title="Basic Presentation",
            slides=[SlideSchema(layout_name="Title Slide", title="Welcome", content=[])],
        )
        result = validate_presentation_schema(schema)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []


class TestSlideValidation:
    """Tests for validate_slide_schema."""

    @pytest.fixture
    def template_meta(self) -> TemplateMetadata:
        """Create mock template metadata."""
        return TemplateMetadata(
            template_path="test_template.pptx",
            layouts=[
                LayoutMetadata(
                    name="Title and Content",
                    placeholders=[
                        PlaceholderMetadata(name="title", type="TITLE", max_chars=100),
                        PlaceholderMetadata(name="content", type="BODY", max_chars=500),
                    ],
                ),
                LayoutMetadata(
                    name="Title Only",
                    placeholders=[PlaceholderMetadata(name="title", type="TITLE", max_chars=100)],
                ),
            ],
        )

    def test_valid_slide(self, template_meta: TemplateMetadata) -> None:
        """Should return valid result for correct slide schema."""
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[TextBlock(placeholder_name="content", text="Short text", language="en")],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is True
        assert result.errors == []

    def test_layout_not_in_template(self, template_meta: TemplateMetadata) -> None:
        """Should return error when layout doesn't exist in template."""
        schema = SlideSchema(layout_name="Non-existent Layout", title="Test Slide", content=[])
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is False
        assert "layout" in result.errors[0].lower()
        assert "not found" in result.errors[0].lower()

    def test_placeholder_not_in_layout(self, template_meta: TemplateMetadata) -> None:
        """Should return error when placeholder doesn't exist in layout."""
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[TextBlock(placeholder_name="non_existent", text="Text", language="en")],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is False
        assert "placeholder" in result.errors[0].lower()
        assert "non_existent" in result.errors[0]

    def test_text_capacity_exceeded(self, template_meta: TemplateMetadata) -> None:
        """Should return warning when text exceeds placeholder capacity."""
        # content placeholder has max_chars=500
        long_text = "x" * 600
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[TextBlock(placeholder_name="content", text=long_text, language="en")],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is True  # Still valid, but with warnings
        assert len(result.warnings) > 0
        assert "exceeds capacity" in result.warnings[0].lower()

    def test_text_capacity_japanese(self, template_meta: TemplateMetadata) -> None:
        """Should correctly calculate Japanese text capacity (0.55x)."""
        # content placeholder has max_chars=500
        # Japanese effective capacity = 500 * 0.55 = 275
        # Text with 300 chars should trigger warning
        long_text = "あ" * 300
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[TextBlock(placeholder_name="content", text=long_text, language="ja")],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "exceeds capacity" in result.warnings[0].lower()

    def test_text_capacity_english(self, template_meta: TemplateMetadata) -> None:
        """Should correctly calculate English text capacity (1.0x)."""
        # content placeholder has max_chars=500
        # English effective capacity = 500 * 1.0 = 500
        # Text with 400 chars should NOT trigger warning
        text = "x" * 400
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[TextBlock(placeholder_name="content", text=text, language="en")],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is True
        assert len(result.warnings) == 0

    def test_multiple_validation_errors(self, template_meta: TemplateMetadata) -> None:
        """Should collect multiple errors in single result."""
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[
                TextBlock(placeholder_name="non_existent_1", text="Text 1", language="en"),
                TextBlock(placeholder_name="non_existent_2", text="Text 2", language="en"),
            ],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is False
        assert len(result.errors) == 2

    def test_image_placeholder_validation(self, template_meta: TemplateMetadata) -> None:
        """Should validate image blocks against placeholders."""
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[
                ImageBlock(placeholder_name="content", image_path="test.png", alt_text="Test image")
            ],
        )
        result = validate_slide_schema(schema, template_meta)
        assert result.valid is True
        assert result.errors == []
