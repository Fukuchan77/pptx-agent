"""SmartArt builder for adding SmartArt diagrams to slides.

This module provides functionality to populate SmartArt diagrams in PowerPoint
slides with node text content.
"""

from pptx_agent.pptx_wrapper.slide import SlideWrapper
from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper
from pptx_agent.schemas.visual_assets import SmartArtBlock


def add_smartart_to_slide(slide: SlideWrapper, smartart_block: SmartArtBlock) -> None:
    """Add SmartArt diagram to slide using SmartArtBlock specification.

    Populates a SmartArt diagram placeholder with node text content.
    Note: Due to the complexity of SmartArt XML structures, this function
    currently raises NotImplementedError as acknowledged in the spec.

    Args:
        slide: SlideWrapper instance to add SmartArt to
        smartart_block: SmartArtBlock with placeholder name and node data

    Raises:
        ValueError: If SmartArt placeholder not found
        NotImplementedError: SmartArt XML manipulation requires advanced handling

    Example:
        >>> smartart_block = SmartArtBlock(
        ...     placeholder_name="Content Placeholder",
        ...     diagram_type="process",
        ...     nodes=[
        ...         {"text": "Step 1", "level": 0},
        ...         {"text": "Step 2", "level": 0},
        ...     ]
        ... )
        >>> add_smartart_to_slide(slide, smartart_block)
    """
    # Delegate to SmartArtWrapper for actual XML manipulation
    # This will raise NotImplementedError as per the spec's acknowledgment
    # that SmartArt manipulation requires advanced XML handling or commercial libraries
    SmartArtWrapper.populate_smartart(
        slide.slide,  # Access underlying python-pptx Slide object
        smartart_block.placeholder_name,
        smartart_block.nodes,
    )
