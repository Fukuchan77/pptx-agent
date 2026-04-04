"""Template parser data models.

Pydantic models for representing template metadata extracted from PPTX files.
"""

from pydantic import BaseModel, Field


class PlaceholderMetadata(BaseModel):
    """Metadata about a placeholder in a slide layout.

    Attributes:
        name: Name of the placeholder (e.g., "Title", "Content")
        type: Type of placeholder (e.g., "TITLE", "BODY", "SUBTITLE")
        max_chars: Estimated maximum character capacity
    """

    name: str = Field(..., description="Placeholder name")
    type: str = Field(..., description="Placeholder type")
    max_chars: int = Field(..., description="Estimated maximum characters")


class LayoutMetadata(BaseModel):
    """Metadata about a slide layout.

    Attributes:
        name: Name of the layout (e.g., "Title Slide", "Title and Content")
        placeholders: List of placeholders in this layout
    """

    name: str = Field(..., description="Layout name")
    placeholders: list[PlaceholderMetadata] = Field(
        default_factory=list, description="List of placeholders"
    )


class TemplateMetadata(BaseModel):
    """Metadata about a PowerPoint template.

    Attributes:
        template_path: Path to the template file
        layouts: List of slide layouts in the template
    """

    template_path: str = Field(..., description="Path to template file")
    layouts: list[LayoutMetadata] = Field(default_factory=list, description="List of layouts")

    def get_layout(self, name: str) -> LayoutMetadata | None:
        """Get layout by name.

        Args:
            name: Name of the layout to find

        Returns:
            LayoutMetadata if found, None otherwise
        """
        for layout in self.layouts:
            if layout.name == name:
                return layout
        return None
