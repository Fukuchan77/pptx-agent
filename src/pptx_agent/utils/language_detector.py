"""Language detection utility for Japanese and English text.

This module provides utilities to detect the language of input text,
primarily distinguishing between Japanese (ja) and English (en).
"""

from typing import Literal

# Unicode ranges for Japanese characters
HIRAGANA_START = 0x3040
HIRAGANA_END = 0x309F
KATAKANA_START = 0x30A0
KATAKANA_END = 0x30FF
KANJI_START = 0x4E00
KANJI_END = 0x9FFF

# Language detection threshold
JAPANESE_CHAR_THRESHOLD = 0.3  # If >30% chars are Japanese, classify as Japanese


def is_japanese_char(char: str) -> bool:
    """Check if a character is Japanese (hiragana, katakana, or kanji).

    Japanese character ranges:
    - Hiragana: 0x3040-0x309F
    - Katakana: 0x30A0-0x30FF
    - Kanji (CJK Unified Ideographs): 0x4E00-0x9FFF

    Args:
        char: Single character to check

    Returns:
        True if character is Japanese, False otherwise
    """
    if len(char) != 1:
        return False

    code_point = ord(char)

    # Check hiragana range
    if HIRAGANA_START <= code_point <= HIRAGANA_END:
        return True

    # Check katakana range
    if KATAKANA_START <= code_point <= KATAKANA_END:
        return True

    # Check kanji (CJK Unified Ideographs) range
    return KANJI_START <= code_point <= KANJI_END


def detect_language(text: str) -> Literal["ja", "en"]:
    """Detect the dominant language of the input text.

    Detects whether text is primarily Japanese or English based on
    character composition. Uses a simple character-counting approach:
    - If >30% of characters are Japanese, return "ja"
    - Otherwise, return "en"

    Empty strings and numeric-only text default to "en".

    Args:
        text: Input text to analyze

    Returns:
        "ja" for Japanese-dominant text, "en" for English-dominant text
    """
    if not text or not text.strip():
        return "en"

    # Count Japanese characters
    japanese_count = sum(1 for char in text if is_japanese_char(char))

    # Count total non-whitespace characters
    total_chars = sum(1 for char in text if not char.isspace())

    # If no non-whitespace characters, default to English
    if total_chars == 0:
        return "en"

    # Calculate Japanese character ratio
    japanese_ratio = japanese_count / total_chars

    # If more than threshold% are Japanese characters, classify as Japanese
    # This threshold handles mixed-language text appropriately
    if japanese_ratio > JAPANESE_CHAR_THRESHOLD:
        return "ja"

    return "en"
