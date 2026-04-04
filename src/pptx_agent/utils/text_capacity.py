"""Language-aware text capacity calculator.

This module provides utilities for calculating text capacity based on language,
accounting for the different visual space requirements of Japanese vs English text.
"""

import math
from typing import Literal

# Language multipliers for text capacity
# Japanese text requires more visual space per information unit
LANGUAGE_MULTIPLIERS = {
    "en": 1.0,  # English: 1.0x (baseline)
    "ja": 0.55,  # Japanese: 0.55x (denser information)
}


def get_language_multiplier(language: Literal["en", "ja"]) -> float:
    """Get the capacity multiplier for a given language.

    Args:
        language: Language code ("en" or "ja")

    Returns:
        Capacity multiplier (1.0 for English, 0.55 for Japanese)
    """
    return LANGUAGE_MULTIPLIERS[language]


def calculate_effective_capacity(max_chars: int, language: Literal["en", "ja"]) -> int:
    """Calculate effective text capacity for a given language.

    Applies language-specific multiplier to the maximum character capacity.

    Args:
        max_chars: Maximum character capacity without language adjustment
        language: Language code ("en" or "ja")

    Returns:
        Effective capacity after applying language multiplier
    """
    multiplier = get_language_multiplier(language)
    return int(max_chars * multiplier)


def text_fits_within_capacity(
    text: str,
    max_chars: int,
    language: Literal["en", "ja"],
) -> bool:
    """Check if text fits within the specified capacity for the given language.

    Args:
        text: Text content to check
        max_chars: Maximum character capacity without language adjustment
        language: Language code ("en" or "ja")

    Returns:
        True if text fits within effective capacity, False otherwise
    """
    effective_capacity = calculate_effective_capacity(max_chars, language)
    text_length = len(text)
    return text_length <= effective_capacity


def calculate_required_capacity(text: str, language: Literal["en", "ja"]) -> int:
    """Calculate the required capacity to fit the given text.

    Inverse calculation: given text length and language, calculate the
    max_chars needed to accommodate the text.

    Args:
        text: Text content to calculate capacity for
        language: Language code ("en" or "ja")

    Returns:
        Required max_chars to fit the text
    """
    text_length = len(text)
    multiplier = get_language_multiplier(language)

    # Inverse calculation to find required max_chars:
    # Since text_length = max_chars * multiplier,
    # we need max_chars = text_length / multiplier
    required_capacity = text_length / multiplier

    # Round up to ensure text fits
    return math.ceil(required_capacity)
