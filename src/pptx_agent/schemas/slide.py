"""Slide schema with content blocks."""

from pydantic import BaseModel, Field

from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, ImageBlock, SmartArtBlock, TableBlock

# Union type for all content block types
ContentBlock = TextBlock | ImageBlock | ChartBlock | TableBlock | SmartArtBlock


class SlideSchema(BaseModel):
    """Schema for a single slide.

    Attributes:
        layout_name: Name of the slide layout from the template
        title: Slide title
        content: List of content blocks (text, images, charts, tables, SmartArt)
        notes: Speaker notes (optional)
    """

    layout_name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: list[ContentBlock] = Field(default_factory=list)
    notes: str | None = None
