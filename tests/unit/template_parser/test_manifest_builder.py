"""Tests for template manifest builder."""

import pytest

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.template_parser.manifest_builder import ManifestBuilder
from pptx_agent.template_parser.models import LayoutMetadata, PlaceholderMetadata, TemplateMetadata


class TestManifestBuilder:
    """Test suite for ManifestBuilder."""

    def test_build_manifest_from_template_metadata(self) -> None:
        """Test building TemplateManifest from TemplateMetadata."""
        # Arrange
        placeholder1 = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)
        placeholder2 = PlaceholderMetadata(name="Content 1", type="BODY", max_chars=500)

        layout1 = LayoutMetadata(name="Title Slide", placeholders=[placeholder1])
        layout2 = LayoutMetadata(
            name="Title and Content", placeholders=[placeholder1, placeholder2]
        )

        template_metadata = TemplateMetadata(
            template_path="templates/test-template.pptx",
            layouts=[layout1, layout2],
        )

        builder = ManifestBuilder()

        # Act
        manifest = builder.build_manifest(template_metadata, template_name="Test Template")

        # Assert
        assert isinstance(manifest, TemplateManifest)
        assert manifest.template_name == "Test Template"
        assert len(manifest.layouts) == 2
        assert manifest.default_language == "en"

    def test_build_layout_info_from_layout_metadata(self) -> None:
        """Test converting LayoutMetadata to LayoutInfo."""
        # Arrange
        placeholder1 = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)
        placeholder2 = PlaceholderMetadata(name="Content 1", type="BODY", max_chars=500)

        layout_metadata = LayoutMetadata(
            name="Title and Content",
            placeholders=[placeholder1, placeholder2],
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(layout_info, LayoutInfo)
        assert layout_info.name == "Title and Content"
        assert len(layout_info.placeholders) == 2
        assert layout_info.supports_charts is False
        assert layout_info.supports_tables is False
        assert layout_info.supports_smartart is False

    def test_build_placeholder_info_from_placeholder_metadata(self) -> None:
        """Test converting PlaceholderMetadata to PlaceholderInfo."""
        # Arrange
        placeholder_metadata = PlaceholderMetadata(
            name="Title 1",
            type="TITLE",
            max_chars=100,
        )

        builder = ManifestBuilder()

        # Act
        placeholder_info = builder._build_placeholder_info(placeholder_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(placeholder_info, PlaceholderInfo)
        assert placeholder_info.name == "Title 1"
        assert placeholder_info.type == "TITLE"
        assert placeholder_info.max_chars == 100
        assert placeholder_info.language_ratio is None

    def test_detect_chart_support(self) -> None:
        """Test that layouts with CHART placeholders support charts."""
        # Arrange
        placeholder_chart = PlaceholderMetadata(name="Chart 1", type="CHART", max_chars=1)
        placeholder_title = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)

        layout_metadata = LayoutMetadata(
            name="Title and Chart",
            placeholders=[placeholder_title, placeholder_chart],
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert layout_info.supports_charts is True

    def test_detect_table_support(self) -> None:
        """Test that layouts with TABLE placeholders support tables."""
        # Arrange
        placeholder_table = PlaceholderMetadata(name="Table 1", type="TABLE", max_chars=1)
        placeholder_title = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)

        layout_metadata = LayoutMetadata(
            name="Title and Table",
            placeholders=[placeholder_title, placeholder_table],
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert layout_info.supports_tables is True

    def test_detect_smartart_support(self) -> None:
        """Test that layouts with ORG_CHART placeholders support SmartArt."""
        # Arrange
        placeholder_org = PlaceholderMetadata(name="SmartArt 1", type="ORG_CHART", max_chars=1)
        placeholder_title = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)

        layout_metadata = LayoutMetadata(
            name="Title and SmartArt",
            placeholders=[placeholder_title, placeholder_org],
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert layout_info.supports_smartart is True

    def test_build_manifest_with_japanese_language(self) -> None:
        """Test building manifest with Japanese as default language."""
        # Arrange
        placeholder = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)
        layout = LayoutMetadata(name="Title Slide", placeholders=[placeholder])
        template_metadata = TemplateMetadata(
            template_path="templates/japanese-template.pptx",
            layouts=[layout],
        )

        builder = ManifestBuilder()

        # Act
        manifest = builder.build_manifest(
            template_metadata,
            template_name="Japanese Template",
            default_language="ja",
        )

        # Assert
        assert manifest.default_language == "ja"

    def test_build_manifest_empty_layouts_raises_error(self) -> None:
        """Test that building manifest with no layouts raises ValueError."""
        # Arrange
        template_metadata = TemplateMetadata(
            template_path="templates/empty-template.pptx",
            layouts=[],
        )

        builder = ManifestBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="at least one layout"):
            builder.build_manifest(template_metadata, template_name="Empty Template")

    def test_smartart_node_count_none_when_no_smartart(self) -> None:
        """RED: Test that layouts without SmartArt have node_count=None."""
        # Arrange
        placeholder = PlaceholderMetadata(name="Title 1", type="TITLE", max_chars=100)
        layout_metadata = LayoutMetadata(
            name="Title Slide",
            placeholders=[placeholder],
            has_smartart=False,
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert layout_info.smartart_node_count is None

    def test_smartart_node_count_set_when_smartart_present(self) -> None:
        """RED: Test that layouts with SmartArt have node_count set."""
        # Arrange
        placeholder_org = PlaceholderMetadata(name="SmartArt 1", type="ORG_CHART", max_chars=1)
        layout_metadata = LayoutMetadata(
            name="SmartArt Layout",
            placeholders=[placeholder_org],
            has_smartart=True,
            smartart_node_count=5,  # Layout has SmartArt with 5 nodes
        )

        builder = ManifestBuilder()

        # Act
        layout_info = builder._build_layout_info(layout_metadata)  # type: ignore[reportPrivateUsage]

        # Assert
        assert layout_info.smartart_node_count == 5

    def test_layout_info_has_smartart_node_count_field(self) -> None:
        """RED: Test that LayoutInfo has smartart_node_count field."""
        # Test that LayoutInfo schema supports smartart_node_count
        placeholder = PlaceholderInfo(name="Title", type="TITLE", max_chars=100)
        layout_info = LayoutInfo(
            name="Test Layout",
            placeholders=[placeholder],
            supports_smartart=True,
            smartart_node_count=3,
        )

        assert layout_info.smartart_node_count == 3
