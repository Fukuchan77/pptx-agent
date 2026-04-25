"""Template manifest schema models.

These models describe the structure and capabilities of PowerPoint templates:
- PlaceholderInfo: Information about a placeholder in a layout
- LayoutInfo: Information about a layout with its placeholders and capabilities
- TemplateManifest: Complete template metadata with all layouts

Used by the template parser to extract and describe template capabilities.
"""

from typing import Literal

from pydantic import BaseModel, Field


class PlaceholderInfo(BaseModel):
    """Information about a placeholder in a layout.

    Attributes:
        name: Placeholder name/identifier
        type: Placeholder type (TITLE, TEXT, PICTURE, etc.)
        max_chars: Maximum character capacity
        language_ratio: Optional language-specific capacity multiplier (0.0-1.0)
    """

    name: str = Field(min_length=1, description="Placeholder name")
    type: str = Field(min_length=1, description="Placeholder type")
    max_chars: int = Field(gt=0, description="Maximum character capacity")
    language_ratio: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Language-specific capacity multiplier (0.0-1.0)",
    )


class LayoutInfo(BaseModel):
    """Information about a slide layout.

    Attributes:
        name: Layout name
        placeholders: List of placeholders in this layout
        supports_charts: Whether this layout supports chart insertion
        supports_tables: Whether this layout supports table insertion
        supports_smartart: Whether this layout supports SmartArt insertion
        smartart_node_count: Number of nodes in SmartArt diagram (if present)
    """

    name: str = Field(min_length=1, description="Layout name")
    placeholders: list[PlaceholderInfo] = Field(min_length=1, description="List of placeholders")
    supports_charts: bool = Field(default=False, description="Supports charts")
    supports_tables: bool = Field(default=False, description="Supports tables")
    supports_smartart: bool = Field(default=False, description="Supports SmartArt")
    smartart_node_count: int | None = Field(
        default=None, description="Number of nodes in SmartArt diagram (None if no SmartArt)"
    )


class TemplateManifest(BaseModel):
    """Complete template manifest with all layouts and capabilities.

    Attributes:
        template_name: Template name/identifier
        layouts: List of available layouts in the template
        default_language: Default language for the template ('en' or 'ja')
    """

    template_name: str = Field(min_length=1, description="Template name")
    layouts: list[LayoutInfo] = Field(min_length=1, description="List of layouts")
    default_language: Literal["en", "ja"] = Field(
        default="en", description="Default language (en=English, ja=Japanese)"
    )

    def get_layout_by_name(self, name: str) -> LayoutInfo | None:
        """Get a layout by its name.

        Args:
            name: Layout name to search for

        Returns:
            LayoutInfo if found, None otherwise
        """
        for layout in self.layouts:
            if layout.name == name:
                return layout
        return None

    def to_json(self, indent: int = 2) -> str:
        """Export manifest as JSON string.

        Args:
            indent: Number of spaces for indentation (default: 2)

        Returns:
            JSON string representation of the manifest
        """
        return self.model_dump_json(indent=indent)
