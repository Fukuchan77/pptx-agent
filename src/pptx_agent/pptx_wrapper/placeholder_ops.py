"""Placeholder operations for shape wrappers.

Common placeholder search, extraction, and removal operations
shared across ChartWrapper, TableWrapper, and ImageWrapper.
"""

import logging
from typing import Any

from pptx.slide import Slide

from pptx_agent.pptx_wrapper.xml_utils import safe_get_element, safe_remove_element

logger = logging.getLogger(__name__)


def find_placeholder(slide: Slide, placeholder_name: str) -> Any | None:
    """Find placeholder by name or type.

    Args:
        slide: Slide to search in
        placeholder_name: Name or type name of placeholder to find

    Returns:
        Placeholder shape if found, None otherwise
    """
    for shape in slide.shapes:
        if shape.is_placeholder and (
            placeholder_name in (shape.name, shape.placeholder_format.type.name)
        ):
            return shape
    return None


def get_placeholder_bounds(placeholder: Any) -> tuple[int, int, int, int]:
    """Extract position and dimensions from placeholder.

    Args:
        placeholder: Placeholder shape

    Returns:
        Tuple of (left, top, width, height)
    """
    return placeholder.left, placeholder.top, placeholder.width, placeholder.height


def remove_placeholder_safely(placeholder: Any) -> None:
    """Safely remove placeholder using xml_utils.

    Args:
        placeholder: Placeholder shape to remove

    Raises:
        ValueError: If placeholder removal fails
    """
    sp = safe_get_element(placeholder, "element")
    if sp is None or not safe_remove_element(sp):
        msg = (
            "Placeholder removal failed: unable to remove placeholder element. "
            "Expected: valid removable placeholder."
        )
        raise ValueError(msg)
