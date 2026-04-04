"""Input validation for presentation generation."""

import re

# Input length bounds (FR-005)
MIN_INPUT_LENGTH = 10
MAX_INPUT_LENGTH = 30000

# Dangerous characters to remove for security
DANGEROUS_CHARS = [
    "\x00",  # Null byte
    "\x01",
    "\x02",
    "\x03",
    "\x04",
    "\x05",
    "\x06",
    "\x07",
    "\x08",  # Control chars
    "\x0b",
    "\x0c",  # Vertical tab, form feed (keep \n=0x0A, \r=0x0D, \t=0x09)
    "\x0e",
    "\x0f",
    "\x10",
    "\x11",
    "\x12",
    "\x13",
    "\x14",
    "\x15",
    "\x16",
    "\x17",
    "\x18",
    "\x19",
    "\x1a",
    "\x1b",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x1f",
    "\u202e",  # Right-to-left override
    "\u202d",  # Left-to-right override
    "\u200b",  # Zero-width space
    "\u200c",  # Zero-width non-joiner
    "\u200d",  # Zero-width joiner
    "\ufeff",  # Zero-width no-break space (BOM)
]


class InputValidationError(Exception):
    """Raised when input validation fails."""


def validate_input_text(text: str) -> str:
    """Validate input text for presentation generation.

    Args:
        text: Input text to validate

    Returns:
        Validated and stripped text

    Raises:
        InputValidationError: If text is empty, whitespace-only, too short, or too long

    Requirements:
        - FR-005: Validate input text length is between 10 and 30,000 characters
        - FR-006: Reject empty or whitespace-only input with clear error message
    """
    # Strip leading and trailing whitespace
    stripped_text = text.strip()

    # Check for empty or whitespace-only input
    if not stripped_text:
        msg = (
            "Input validation failed: text cannot be empty or contain only whitespace. "
            "Expected: non-empty text content."
        )
        raise InputValidationError(msg)

    # Check length bounds
    text_length = len(stripped_text)
    if text_length < MIN_INPUT_LENGTH or text_length > MAX_INPUT_LENGTH:
        msg = (
            f"Input length validation failed: provided text has {text_length} characters. "
            f"Expected: between {MIN_INPUT_LENGTH} and {MAX_INPUT_LENGTH:,} characters."
        )
        raise InputValidationError(msg)

    return stripped_text


def sanitize_dangerous_characters(text: str) -> str:
    """Sanitize input text by removing dangerous characters.

    Removes:
    - Null bytes
    - Control characters (except common whitespace: space, tab, newline, CR)
    - Unicode bidirectional override characters (spoofing prevention)
    - Zero-width characters (obfuscation prevention)

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text with dangerous characters removed and whitespace normalized

    """
    if not text:
        return text

    # Remove dangerous characters
    sanitized = text
    for char in DANGEROUS_CHARS:
        sanitized = sanitized.replace(char, "")

    # Normalize excessive spaces (more than 2 consecutive spaces)
    # Only target spaces, not newlines or tabs
    sanitized = re.sub(r" {3,}", "  ", sanitized)

    return sanitized.strip()
