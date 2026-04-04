"""Template manifest builder for converting parser models to schema models.

This module provides functionality to build TemplateManifest objects from
TemplateMetadata extracted by the template parser.
"""

from typing import ClassVar, Literal

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest

from .models import LayoutMetadata, PlaceholderMetadata, TemplateMetadata


class ManifestBuilder:
    """Builder for converting TemplateMetadata to TemplateManifest.

    Converts template parser models (TemplateMetadata, LayoutMetadata,
    PlaceholderMetadata) into schema models (TemplateManifest, LayoutInfo,
    PlaceholderInfo) with enhanced metadata detection.
    """

    # Placeholder types that indicate chart support
    CHART_PLACEHOLDER_TYPES: ClassVar[set[str]] = {"CHART", "OBJECT"}

    # Placeholder types that indicate table support
    TABLE_PLACEHOLDER_TYPES: ClassVar[set[str]] = {"TABLE", "OBJECT"}

    # Placeholder types that indicate SmartArt support
    SMARTART_PLACEHOLDER_TYPES: ClassVar[set[str]] = {"ORG_CHART", "OBJECT"}

    def build_manifest(
        self,
        template_metadata: TemplateMetadata,
        template_name: str,
        default_language: Literal["en", "ja"] = "en",
    ) -> TemplateManifest:
        """Build TemplateManifest from TemplateMetadata.

        Args:
            template_meta Template metadata from parser
            template_name: Name for the template
            default_language: Default language (en or ja)

        Returns:
            TemplateManifest with all layouts and capabilities

        Raises:
            ValueError: If template has no layouts
        """
        if not template_metadata.layouts:
            msg = "Template must have at least one layout"
            raise ValueError(msg)

        layouts = [self._build_layout_info(layout) for layout in template_metadata.layouts]

        return TemplateManifest(
            template_name=template_name,
            layouts=layouts,
            default_language=default_language,
        )

    def _build_layout_info(self, layout_meta: LayoutMetadata) -> LayoutInfo:
        """Build LayoutInfo from LayoutMetadata.

        Args:
            layout_meta Layout metadata from parser

        Returns:
            LayoutInfo with placeholders and detected capabilities
        """
        placeholders = [self._build_placeholder_info(ph) for ph in layout_meta.placeholders]

        # Detect capabilities based on placeholder types
        placeholder_types = {ph.type for ph in layout_meta.placeholders}

        supports_charts = bool(placeholder_types & self.CHART_PLACEHOLDER_TYPES)
        supports_tables = bool(placeholder_types & self.TABLE_PLACEHOLDER_TYPES)
        supports_smartart = bool(placeholder_types & self.SMARTART_PLACEHOLDER_TYPES)

        return LayoutInfo(
            name=layout_meta.name,
            placeholders=placeholders,
            supports_charts=supports_charts,
            supports_tables=supports_tables,
            supports_smartart=supports_smartart,
        )

    def _build_placeholder_info(self, placeholder_meta: PlaceholderMetadata) -> PlaceholderInfo:
        """Build PlaceholderInfo from PlaceholderMetadata.

        Args:
            placeholder_meta: Placeholder metadata from parser

        Returns:
            PlaceholderInfo with all metadata
        """
        return PlaceholderInfo(
            name=placeholder_meta.name,
            type=placeholder_meta.type,
            max_chars=placeholder_meta.max_chars,
            language_ratio=None,  # Will be set by language-specific processing
        )
