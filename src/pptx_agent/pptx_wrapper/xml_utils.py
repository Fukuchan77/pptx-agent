"""Safe XML manipulation utilities."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_remove_element(element: Any) -> bool:
    """
    Safely remove an XML element from its parent.

    Args:
        element: XML element to remove

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If element has no parent
    """
    try:
        parent = element.getparent()
        if parent is None:
            msg = "Element has no parent, cannot remove"
            raise ValueError(msg)

        parent.remove(element)
        logger.debug("Successfully removed element")
    except (AttributeError, TypeError):
        logger.exception("Failed to remove element")
        return False
    else:
        return True


def safe_get_element(obj: Any, element_attr: str = "_element") -> Any:
    """
    Safely access protected _element attribute.

    Args:
        obj: Object with _element attribute
        element_attr: Name of element attribute (default: "_element")

    Returns:
        XML element if accessible, None otherwise
    """
    try:
        element = getattr(obj, element_attr)
        if element is None:
            logger.warning("Element attribute is None")
    except AttributeError:
        logger.exception("Failed to access element")
        return None
    else:
        return element
