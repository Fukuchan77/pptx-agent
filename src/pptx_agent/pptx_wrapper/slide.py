"""Slide-level wrapper for python-pptx."""

import logging
from typing import Any

from pptx.slide import Slide

from pptx_agent.constants import EMU_PER_CHAR_WIDTH, EMU_PER_LINE_HEIGHT

logger = logging.getLogger(__name__)


class SlideWrapper:
    """Wrapper for python-pptx Slide with type hints."""

    def __init__(self, slide: Slide) -> None:
        """Initialize slide wrapper.

        Args:
            slide: python-pptx Slide object to wrap
        """
        self._slide = slide

    def set_title(self, text: str) -> None:
        """Update title placeholder.

        Args:
            text: Title text to set

        Raises:
            ValueError: If slide has no title placeholder
        """
        if not self._slide.shapes.title:
            msg = "Slide has no title placeholder"
            raise ValueError(msg)

        self._slide.shapes.title.text = text

    def add_text(
        self, placeholder_name: str, text: str, check_overflow: bool = True
    ) -> dict[str, Any]:
        """Add text to placeholder with optional overflow check.

        Args:
            placeholder_name: Name of the placeholder to update
            text: Text content to add
            check_overflow: Whether to check for text overflow

        Returns:
            Dictionary with keys:
                - success (bool): Whether operation succeeded
                - overflow (bool): Whether text overflow detected
                - warnings (list[str]): Any warnings generated
        """
        result: dict[str, Any] = {"success": False, "overflow": False, "warnings": []}

        # Find placeholder by name (flexible matching)
        placeholder = None
        for shape in self._slide.shapes:
            if shape.is_placeholder:
                # Try exact match first
                if shape.name == placeholder_name:
                    placeholder = shape
                    break
                # Try placeholder type name
                try:
                    if shape.placeholder_format.type.name == placeholder_name:
                        placeholder = shape
                        break
                except AttributeError as e:
                    # If accessing placeholder format fails, log and continue searching
                    logger.debug(
                        "Could not access placeholder_format for shape %s: %s", shape.name, e
                    )
                # Try case-insensitive partial match on name
                if placeholder_name.lower() in shape.name.lower():
                    placeholder = shape
                    break

        # If still not found and name suggests content placeholder, try generic fallback
        if placeholder is None and placeholder_name.lower() in ["content", "body", "text"]:
            for shape in self._slide.shapes:
                if shape.is_placeholder and hasattr(shape, "text_frame"):
                    # Skip title placeholder
                    try:
                        if shape.placeholder_format.type.name != "TITLE":
                            placeholder = shape
                            break
                    except AttributeError:
                        # If we can't determine type, use it anyway as fallback
                        logger.debug(
                            "Could not determine placeholder type for shape, using as fallback"
                        )
                        placeholder = shape
                        break

        if placeholder is None:
            result["warnings"].append(f"Placeholder '{placeholder_name}' not found")
            return result

        # Add text to placeholder
        if hasattr(placeholder, "text_frame"):
            # Type narrowing: hasattr check ensures text_frame exists
            placeholder.text_frame.text = text  # type: ignore[attr-defined]
            result["success"] = True

            # Check for overflow if requested
            if check_overflow:
                result["overflow"] = self._check_text_overflow(placeholder, text)
                if result["overflow"]:
                    result["warnings"].append(f"Text may overflow placeholder '{placeholder_name}'")
        else:
            result["warnings"].append(f"Placeholder '{placeholder_name}' cannot contain text")

        return result

    def get_placeholders(self) -> dict[str, dict[str, Any]]:
        """Return placeholder inventory.

        Returns:
            Dictionary mapping placeholder names to their properties:
                - type: Placeholder type
                - has_text_frame: Whether it can contain text
        """
        placeholders = {}

        for shape in self._slide.shapes:
            if shape.is_placeholder:
                name = shape.name
                placeholders[name] = {
                    "type": shape.placeholder_format.type.name,
                    "has_text_frame": hasattr(shape, "text_frame"),
                }

        return placeholders

    def _check_text_overflow(self, placeholder: Any, text: str) -> bool:
        """Internal method to detect text overflow.

        This is a simplified heuristic based on text length and
        placeholder dimensions. For production use, more sophisticated
        overflow detection would be needed.

        Args:
            placeholder: The placeholder shape
            text: Text content

        Returns:
            True if overflow is likely, False otherwise
        """
        if not hasattr(placeholder, "text_frame"):
            return False

        # Simple heuristic: estimate based on character count and dimensions
        try:
            width = placeholder.width
            height = placeholder.height

            # Rough estimate of capacity (chars per line * number of lines)
            chars_per_line = max(1, int(width / EMU_PER_CHAR_WIDTH))
            num_lines = max(1, int(height / EMU_PER_LINE_HEIGHT))
            capacity = chars_per_line * num_lines

            # Check if text exceeds estimated capacity
            return len(text) > capacity
        except (AttributeError, ZeroDivisionError):
            # If we can't estimate, assume no overflow
            return False
