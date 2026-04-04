"""Python-pptx wrapper modules for type-safe PowerPoint manipulation."""

from .presentation import PresentationWrapper
from .shapes import ChartWrapper, ImageWrapper, TableWrapper
from .slide import SlideWrapper
from .smartart import SmartArtWrapper

__all__ = [
    "ChartWrapper",
    "ImageWrapper",
    "PresentationWrapper",
    "SlideWrapper",
    "SmartArtWrapper",
    "TableWrapper",
]
