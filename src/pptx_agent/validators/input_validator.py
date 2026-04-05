"""Input validation for presentation generation."""

import logging
import re

logger = logging.getLogger(__name__)

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

# Pre-computed translation table for O(n) single-pass character removal
_SANITIZE_TABLE = str.maketrans("", "", "".join(DANGEROUS_CHARS))


class InputValidationError(Exception):
    """Raised when input validation fails."""


def sanitize_dangerous_characters(text: str) -> str:
    """Sanitize input text by removing dangerous characters.

    This function can be used independently for sanitization without validation.

    Removes:
    - Null bytes
    - Control characters (except common whitespace: space, tab, newline, CR)
    - Unicode bidirectional override characters (spoofing prevention)
    - Zero-width characters (obfuscation prevention)

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text with dangerous characters removed and whitespace normalized

    Example:
        >>> sanitize_dangerous_characters("Text\\x00with\\x01control")
        'Textwithcontrol'
    """
    if not text:
        return text

    # Remove dangerous characters using single-pass translate (O(n) vs O(n*m))
    sanitized = text.translate(_SANITIZE_TABLE)

    # Normalize excessive spaces (more than 2 consecutive spaces)
    # Only target spaces, not newlines or tabs
    sanitized = re.sub(r" {3,}", "  ", sanitized)

    return sanitized.strip()


def validate_and_sanitize(
    text: str,
    min_length: int = MIN_INPUT_LENGTH,
    max_length: int = MAX_INPUT_LENGTH,
    field_name: str = "text",
) -> str:
    """Sanitize and validate input text in the correct order.

    This function ensures the correct execution order:
    1. First sanitize dangerous characters
    2. Then validate the sanitized text

    This prevents control characters from bypassing validation and ensures
    all text is properly cleaned before being checked.

    Args:
        text: Input text to sanitize and validate
        min_length: Minimum allowed length (default: 10)
        max_length: Maximum allowed length (default: 30,000)
        field_name: Field name for error messages (default: "text")

    Returns:
        str: Sanitized and validated text

    Raises:
        InputValidationError: If validation fails after sanitization

    Note:
        This is the recommended function to use for user input processing.
        It guarantees proper execution order and eliminates the risk of
        control characters bypassing validation.

    Example:
        >>> clean_text = validate_and_sanitize(user_input)
        >>> # Text is now sanitized and validated in one step
    """
    # Step 1: Sanitize dangerous characters first
    sanitized = sanitize_dangerous_characters(text)

    # Step 2: Validate the sanitized text with custom parameters
    # Strip whitespace for validation
    stripped = sanitized.strip()

    # Log function entry
    logger.debug(
        "Validating input %s: length=%d",
        field_name,
        len(stripped),
    )

    # Check for empty or whitespace-only input
    if not stripped:
        msg = (
            f"Input validation failed: {field_name} cannot be empty or contain only whitespace. "
            "Expected: non-empty text content."
        )
        raise InputValidationError(msg)

    # Check length bounds with custom parameters
    text_length = len(stripped)
    if text_length < min_length or text_length > max_length:
        # Log validation failure
        logger.error(
            "Input validation failed for %s: length=%d (expected: %d-%d)",
            field_name,
            text_length,
            min_length,
            max_length,
        )
        msg = (
            f"Input length validation failed for {field_name}: "
            f"provided text has {text_length} characters. "
            f"Expected: between {min_length} and {max_length:,} characters."
        )
        raise InputValidationError(msg)

    # Log validation success
    logger.debug(
        "Input validation successful for %s: length=%d",
        field_name,
        text_length,
    )

    return stripped
