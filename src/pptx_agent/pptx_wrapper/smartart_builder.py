"""SmartArt builder for adding SmartArt diagrams to slides.

This module provides functionality to populate SmartArt diagrams in PowerPoint
slides with node text content.
"""

from pptx_agent.pptx_wrapper.slide import SlideWrapper
from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper
from pptx_agent.schemas.visual_assets import SmartArtBlock


def add_smartart_to_slide(slide: SlideWrapper, smartart_block: SmartArtBlock) -> None:
    """Add SmartArt diagram to slide using SmartArtBlock specification.

    Populates an existing SmartArt diagram placeholder with node text content
    via direct XML manipulation of the diagram data part.

    Args:
        slide: SlideWrapper instance to add SmartArt to
        smartart_block: SmartArtBlock with placeholder name and node data

    Raises:
        ValueError: If SmartArt placeholder not found, the diagram data part
            cannot be reached, or node count does not match the template.
    """
    SmartArtWrapper.populate_smartart(
        slide.slide,  # Access underlying python-pptx Slide object
        smartart_block.placeholder_name,
        smartart_block.nodes,
    )
