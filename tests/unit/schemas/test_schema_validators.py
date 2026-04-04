"""Unit tests for schema validators for template compatibility.

Tests for custom Pydantic validators that check presentation content
compatibility with template capabilities.
"""

import pytest

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.validators import (
    validate_content_capacity,
    validate_layout_exists,
    validate_layout_supports_charts,
    validate_layout_supports_smartart,
    validate_layout_supports_tables,
    validate_placeholder_exists,
)


# Test fixtures
@pytest.fixture
def sample_template():
    """Create a sample template manifest for testing."""
    return TemplateManifest(
        template_name="Test Template",
        layouts=[
            LayoutInfo(
                name="Title Slide",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Subtitle", type="TEXT", max_chars=150),
                ],
            ),
            LayoutInfo(
                name="Content Slide",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                    PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                ],
                supports_charts=True,
                supports_tables=True,
            ),
            LayoutInfo(
                name="SmartArt Slide",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                ],
                supports_smartart=True,
            ),
        ],
    )


class TestValidateLayoutExists:
    """Tests for validate_layout_exists validator."""

    def test_layout_exists(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when layout exists."""
        result = validate_layout_exists("Content Slide", sample_template)
        assert result == "Content Slide"

    def test_layout_not_exists(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when layout doesn't exist."""
        with pytest.raises(ValueError, match=r"Layout validation failed.*not found"):
            validate_layout_exists("Nonexistent Layout", sample_template)

    def test_case_sensitive(self, sample_template: TemplateManifest) -> None:
        """Test that layout name matching is case-sensitive."""
        with pytest.raises(ValueError, match=r"not found"):
            validate_layout_exists("content slide", sample_template)


class TestValidatePlaceholderExists:
    """Tests for validate_placeholder_exists validator."""

    def test_placeholder_exists(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when placeholder exists in layout."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        result = validate_placeholder_exists("Content", layout)
        assert result == "Content"

    def test_placeholder_not_exists(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when placeholder doesn't exist."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        with pytest.raises(ValueError, match=r"Placeholder validation failed.*not found"):
            validate_placeholder_exists("Nonexistent", layout)

    def test_multiple_placeholders(self, sample_template: TemplateManifest) -> None:
        """Test validation with layout containing multiple placeholders."""
        layout = sample_template.get_layout_by_name("Title Slide")
        assert layout is not None
        # Both should pass
        assert validate_placeholder_exists("Title", layout) == "Title"
        assert validate_placeholder_exists("Subtitle", layout) == "Subtitle"


class TestValidateContentCapacity:
    """Tests for validate_content_capacity validator."""

    def test_content_within_capacity(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when content fits within capacity."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        placeholder = next(p for p in layout.placeholders if p.name == "Content")
        content = "A" * 400  # 400 chars, max is 500
        result = validate_content_capacity(content, placeholder, "en")
        assert result == content

    def test_content_exceeds_capacity(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when content exceeds capacity."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        placeholder = next(p for p in layout.placeholders if p.name == "Content")
        content = "A" * 600  # 600 chars, max is 500
        with pytest.raises(ValueError, match=r"capacity validation failed.*exceeds"):
            validate_content_capacity(content, placeholder, "en")

    def test_content_at_exact_capacity(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when content is at exact capacity."""
        layout = sample_template.get_layout_by_name("Title Slide")
        assert layout is not None
        placeholder = next(p for p in layout.placeholders if p.name == "Title")
        content = "A" * 100  # Exactly 100 chars
        result = validate_content_capacity(content, placeholder, "en")
        assert result == content

    def test_japanese_content_capacity(self, sample_template: TemplateManifest) -> None:
        """Test validation applies language ratio for Japanese content."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        placeholder = next(p for p in layout.placeholders if p.name == "Content")
        # For Japanese, effective capacity is 500 * 0.55 = 275
        content = "あ" * 300  # 300 chars, exceeds Japanese capacity
        with pytest.raises(ValueError, match=r"capacity validation failed.*exceeds"):
            validate_content_capacity(content, placeholder, "ja")

    def test_japanese_content_within_adjusted_capacity(
        self, sample_template: TemplateManifest
    ) -> None:
        """Test Japanese content within adjusted capacity passes."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        placeholder = next(p for p in layout.placeholders if p.name == "Content")
        # For Japanese, effective capacity is 500 * 0.55 = 275
        content = "あ" * 250  # 250 chars, within Japanese capacity
        result = validate_content_capacity(content, placeholder, "ja")
        assert result == content


class TestValidateLayoutSupportsCharts:
    """Tests for validate_layout_supports_charts validator."""

    def test_layout_supports_charts(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when layout supports charts."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        result = validate_layout_supports_charts(layout)
        assert result == layout

    def test_layout_does_not_support_charts(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when layout doesn't support charts."""
        layout = sample_template.get_layout_by_name("Title Slide")
        assert layout is not None
        with pytest.raises(
            ValueError, match=r"capability validation failed.*does not support charts"
        ):
            validate_layout_supports_charts(layout)


class TestValidateLayoutSupportsTables:
    """Tests for validate_layout_supports_tables validator."""

    def test_layout_supports_tables(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when layout supports tables."""
        layout = sample_template.get_layout_by_name("Content Slide")
        assert layout is not None
        result = validate_layout_supports_tables(layout)
        assert result == layout

    def test_layout_does_not_support_tables(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when layout doesn't support tables."""
        layout = sample_template.get_layout_by_name("Title Slide")
        assert layout is not None
        with pytest.raises(
            ValueError, match=r"capability validation failed.*does not support tables"
        ):
            validate_layout_supports_tables(layout)


class TestValidateLayoutSupportsSmartArt:
    """Tests for validate_layout_supports_smartart validator."""

    def test_layout_supports_smartart(self, sample_template: TemplateManifest) -> None:
        """Test validation passes when layout supports SmartArt."""
        layout = sample_template.get_layout_by_name("SmartArt Slide")
        assert layout is not None
        result = validate_layout_supports_smartart(layout)
        assert result == layout

    def test_layout_does_not_support_smartart(self, sample_template: TemplateManifest) -> None:
        """Test validation fails when layout doesn't support SmartArt."""
        layout = sample_template.get_layout_by_name("Title Slide")
        assert layout is not None
        with pytest.raises(
            ValueError, match=r"capability validation failed.*does not support SmartArt"
        ):
            validate_layout_supports_smartart(layout)
