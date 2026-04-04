"""Unit tests for template manifest schema models.

Tests for TemplateManifest, LayoutInfo, and PlaceholderInfo models used by
the template parser to describe template capabilities.
"""

import pytest
from pydantic import ValidationError

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest


class TestPlaceholderInfo:
    """Tests for PlaceholderInfo model."""

    def test_placeholder_info_minimal(self):
        """Test PlaceholderInfo with minimal required fields."""
        placeholder = PlaceholderInfo(
            name="Title",
            type="TITLE",
            max_chars=100,
        )
        assert placeholder.name == "Title"
        assert placeholder.type == "TITLE"
        assert placeholder.max_chars == 100
        assert placeholder.language_ratio is None

    def test_placeholder_info_with_language_ratio(self):
        """Test PlaceholderInfo with language ratio for Japanese."""
        placeholder = PlaceholderInfo(
            name="Content",
            type="TEXT",
            max_chars=500,
            language_ratio=0.55,
        )
        assert placeholder.language_ratio == 0.55

    def test_placeholder_info_empty_name(self):
        """Test that name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            PlaceholderInfo(
                name="",
                type="TEXT",
                max_chars=100,
            )
        assert "name" in str(exc_info.value)

    def test_placeholder_info_empty_type(self):
        """Test that type cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            PlaceholderInfo(
                name="Title",
                type="",
                max_chars=100,
            )
        assert "type" in str(exc_info.value)

    def test_placeholder_info_zero_max_chars(self):
        """Test that max_chars must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            PlaceholderInfo(
                name="Title",
                type="TITLE",
                max_chars=0,
            )
        assert "max_chars" in str(exc_info.value)

    def test_placeholder_info_negative_language_ratio(self):
        """Test that language_ratio must be between 0 and 1."""
        with pytest.raises(ValidationError) as exc_info:
            PlaceholderInfo(
                name="Content",
                type="TEXT",
                max_chars=100,
                language_ratio=-0.1,
            )
        assert "language_ratio" in str(exc_info.value)

    def test_placeholder_info_language_ratio_too_large(self):
        """Test that language_ratio cannot exceed 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            PlaceholderInfo(
                name="Content",
                type="TEXT",
                max_chars=100,
                language_ratio=1.5,
            )
        assert "language_ratio" in str(exc_info.value)


class TestLayoutInfo:
    """Tests for LayoutInfo model."""

    def test_layout_info_minimal(self):
        """Test LayoutInfo with minimal required fields."""
        layout = LayoutInfo(
            name="Title Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
            ],
        )
        assert layout.name == "Title Slide"
        assert len(layout.placeholders) == 1
        assert layout.supports_charts is False
        assert layout.supports_tables is False
        assert layout.supports_smartart is False

    def test_layout_info_with_capabilities(self):
        """Test LayoutInfo with chart/table/smartart support flags."""
        layout = LayoutInfo(
            name="Content Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
            ],
            supports_charts=True,
            supports_tables=True,
            supports_smartart=False,
        )
        assert layout.supports_charts is True
        assert layout.supports_tables is True
        assert layout.supports_smartart is False

    def test_layout_info_empty_name(self):
        """Test that name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            LayoutInfo(
                name="",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                ],
            )
        assert "name" in str(exc_info.value)

    def test_layout_info_no_placeholders(self):
        """Test that at least one placeholder is required."""
        with pytest.raises(ValidationError) as exc_info:
            LayoutInfo(
                name="Empty Layout",
                placeholders=[],
            )
        assert "placeholders" in str(exc_info.value)

    def test_layout_info_multiple_placeholders(self):
        """Test LayoutInfo with multiple placeholders."""
        layout = LayoutInfo(
            name="Content Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                PlaceholderInfo(name="Subtitle", type="TEXT", max_chars=120),
                PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
            ],
        )
        assert len(layout.placeholders) == 3
        assert layout.placeholders[0].name == "Title"
        assert layout.placeholders[1].name == "Subtitle"
        assert layout.placeholders[2].name == "Content"


class TestTemplateManifest:
    """Tests for TemplateManifest model."""

    def test_template_manifest_minimal(self):
        """Test TemplateManifest with minimal required fields."""
        manifest = TemplateManifest(
            template_name="Basic Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    ],
                ),
            ],
        )
        assert manifest.template_name == "Basic Template"
        assert len(manifest.layouts) == 1
        assert manifest.default_language == "en"

    def test_template_manifest_with_language(self):
        """Test TemplateManifest with Japanese as default language."""
        manifest = TemplateManifest(
            template_name="Japanese Template",
            layouts=[
                LayoutInfo(
                    name="タイトルスライド",
                    placeholders=[
                        PlaceholderInfo(name="タイトル", type="TITLE", max_chars=80),
                    ],
                ),
            ],
            default_language="ja",
        )
        assert manifest.default_language == "ja"

    def test_template_manifest_empty_name(self):
        """Test that template_name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateManifest(
                template_name="",
                layouts=[
                    LayoutInfo(
                        name="Title Slide",
                        placeholders=[
                            PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                        ],
                    ),
                ],
            )
        assert "template_name" in str(exc_info.value)

    def test_template_manifest_no_layouts(self):
        """Test that at least one layout is required."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateManifest(
                template_name="Empty Template",
                layouts=[],
            )
        assert "layouts" in str(exc_info.value)

    def test_template_manifest_invalid_language(self):
        """Test that default_language must be 'en' or 'ja'."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateManifest(
                template_name="Test Template",
                layouts=[
                    LayoutInfo(
                        name="Title Slide",
                        placeholders=[
                            PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                        ],
                    ),
                ],
                default_language="fr",  # Invalid  # type: ignore[arg-type]
            )
        assert "default_language" in str(exc_info.value)

    def test_template_manifest_multiple_layouts(self):
        """Test TemplateManifest with multiple layouts."""
        manifest = TemplateManifest(
            template_name="Multi-Layout Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    ],
                ),
                LayoutInfo(
                    name="Content Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                        PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                    ],
                    supports_charts=True,
                ),
                LayoutInfo(
                    name="Closing Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                    ],
                ),
            ],
        )
        assert len(manifest.layouts) == 3
        assert manifest.layouts[0].name == "Title Slide"
        assert manifest.layouts[1].name == "Content Slide"
        assert manifest.layouts[1].supports_charts is True
        assert manifest.layouts[2].name == "Closing Slide"

    def test_template_manifest_get_layout_by_name(self):
        """Test helper method to get layout by name."""
        manifest = TemplateManifest(
            template_name="Test Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    ],
                ),
                LayoutInfo(
                    name="Content Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                        PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                    ],
                ),
            ],
        )

        # Test finding existing layout
        content_layout = manifest.get_layout_by_name("Content Slide")
        assert content_layout is not None
        assert content_layout.name == "Content Slide"
        assert len(content_layout.placeholders) == 2

        # Test layout not found
        missing_layout = manifest.get_layout_by_name("Nonexistent Layout")
        assert missing_layout is None
