"""Pydantic schemas for structured LLM outputs.

This package contains all data models used for:
- Presentation structure (PresentationSchema)
- Slide content (SlideSchema)
- Text blocks with language-aware capacity (TextBlock, TextCapacity)
- Visual assets (ImageBlock, ChartBlock, TableBlock, SmartArtBlock)
- Outline models for LLM agents (PresentationOutline, SlideContent)
- Template manifest models (TemplateManifest, LayoutInfo, PlaceholderInfo)
"""

from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import SlideSchema
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.text import TextBlock, TextCapacity
from pptx_agent.schemas.visual_assets import ChartBlock, ImageBlock, SmartArtBlock, TableBlock

__all__ = [
    "ChartBlock",
    "ImageBlock",
    "LayoutInfo",
    "PlaceholderInfo",
    "PresentationOutline",
    "PresentationSchema",
    "SlideContent",
    "SlideSchema",
    "SmartArtBlock",
    "TableBlock",
    "TemplateManifest",
    "TextBlock",
    "TextCapacity",
]
