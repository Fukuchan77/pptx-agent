"""Template parser module for extracting metadata from PowerPoint templates.

This module provides functionality to parse PPTX templates and extract
information about layouts, placeholders, and their properties.
"""

from .models import LayoutMetadata, PlaceholderMetadata, TemplateMetadata
from .parser import TemplateParser

__all__ = [
    "LayoutMetadata",
    "PlaceholderMetadata",
    "TemplateMetadata",
    "TemplateParser",
]
