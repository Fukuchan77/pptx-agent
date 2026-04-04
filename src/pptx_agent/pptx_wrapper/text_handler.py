"""Text handler for text fitting and overflow detection.

This module provides functionality to check if text fits within placeholders
and detect overflow, with support for language-aware capacity calculations.
"""

from pptx_agent.constants import PERCENTAGE_MULTIPLIER

# Length of ellipsis string ("...")
ELLIPSIS_LENGTH = 3


class TextHandler:
    """Handler for text fitting and overflow detection.

    Provides methods to check if text fits within a given capacity,
    calculate overflow, and handle text truncation.
    """

    def text_fits(self, text: str, max_capacity: int) -> bool:
        """Check if text fits within the maximum capacity.

        Args:
            text: The text to check
            max_capacity: Maximum character capacity

        Returns:
            True if text fits, False otherwise
        """
        return len(text) <= max_capacity

    def calculate_overflow(self, text: str, max_capacity: int) -> int:
        """Calculate the overflow amount when text exceeds capacity.

        Args:
            text: The text to check
            max_capacity: Maximum character capacity

        Returns:
            Number of characters exceeding capacity (0 if text fits)
        """
        text_length = len(text)
        if text_length <= max_capacity:
            return 0
        return text_length - max_capacity

    def text_fits_with_language(
        self, text: str, max_capacity: int, _language: str, language_ratio: float
    ) -> bool:
        """Check if text fits with language-specific capacity adjustment.

        Args:
            text: The text to check
            max_capacity: Maximum character capacity
            _language: Language code (e.g., 'en', 'ja') - reserved for future use
            language_ratio: Language-specific capacity multiplier (0.0-1.0)

        Returns:
            True if text fits with adjusted capacity, False otherwise
        """
        effective_capacity = int(max_capacity * language_ratio)
        return len(text) <= effective_capacity

    def calculate_overflow_with_language(
        self, text: str, max_capacity: int, _language: str, language_ratio: float
    ) -> int:
        """Calculate overflow with language-specific capacity adjustment.

        Args:
            text: The text to check
            max_capacity: Maximum character capacity
            _language: Language code (e.g., 'en', 'ja') - reserved for future use
            language_ratio: Language-specific capacity multiplier (0.0-1.0)

        Returns:
            Number of characters exceeding adjusted capacity (0 if text fits)
        """
        effective_capacity = int(max_capacity * language_ratio)
        text_length = len(text)
        if text_length <= effective_capacity:
            return 0
        return text_length - effective_capacity

    def get_overflow_percentage(self, text: str, max_capacity: int) -> float:
        """Calculate overflow as a percentage of capacity.

        Args:
            text: The text to check
            max_capacity: Maximum character capacity

        Returns:
            Overflow percentage (0.0 if text fits)
        """
        overflow = self.calculate_overflow(text, max_capacity)
        if overflow == 0 or max_capacity == 0:
            return 0.0
        return (overflow / max_capacity) * PERCENTAGE_MULTIPLIER

    def truncate_text(self, text: str, max_capacity: int) -> str:
        """Truncate text to fit within capacity, adding ellipsis if needed.

        Args:
            text: The text to truncate
            max_capacity: Maximum character capacity

        Returns:
            Truncated text with ellipsis if truncation occurred, or original text if it fits
        """
        if len(text) <= max_capacity:
            return text

        # Reserve space for ellipsis
        if max_capacity < ELLIPSIS_LENGTH:
            # If capacity is too small for ellipsis, just truncate
            return text[:max_capacity]

        # Truncate and add ellipsis
        truncated_length = max_capacity - ELLIPSIS_LENGTH
        return text[:truncated_length] + "..."
