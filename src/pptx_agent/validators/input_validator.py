"""Input validation for presentation generation."""

import logging
import re

logger = logging.getLogger(__name__)

# Input length bounds (FR-005)
MIN_INPUT_LENGTH = 10
MAX_INPUT_LENGTH = 30000

# Control character code ranges for security validation
CONTROL_CHAR_START = 0x01
CONTROL_CHAR_END = 0x1F
TAB = 0x09
LINE_FEED = 0x0A
CARRIAGE_RETURN = 0x0D

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


def validate_text_security(text: str) -> None:
    """Validate text for security threats and raise ValueError if detected.

    This function detects suspicious characters that may indicate malicious input:
    - Null bytes (\\x00)
    - Control characters (except common whitespace: \\t, \\n, \\r)
    - Unicode bidirectional override characters (spoofing)
    - Zero-width characters (obfuscation)
    - Japanese full-width null (\\uff00)

    Unlike sanitize_dangerous_characters(), this function does NOT modify the input.
    Instead, it raises an exception to transparently reject suspicious input.

    Args:
        text: Input text to validate

    Raises:
        ValueError: If suspicious characters are detected, with details about
                   what was found and where

    Requirements:
        - REQ-011: Reject input with null bytes
        - REQ-012: Reject input with control characters
        - REQ-013: Reject input with Japanese-specific malicious patterns
        - REQ-014: Provide clear error messages with actionable guidance

    Example:
        >>> validate_text_security("Clean text")  # No exception
        >>> validate_text_security("Bad\\x00text")  # Raises ValueError
    """
    if not text:
        return  # Empty text is acceptable

    # Check for null bytes
    null_pos = text.find("\x00")
    if null_pos != -1:
        msg = (
            f"Input contains suspicious character: null byte (\\x00) at position {null_pos}. "
            "Please remove it before submitting."
        )
        raise ValueError(msg)

    # Check for control characters (except tab, newline, carriage return)
    for i, char in enumerate(text):
        code = ord(char)
        # Control characters are 0x01-0x1F, excluding tab(0x09), LF(0x0A), CR(0x0D)
        if CONTROL_CHAR_START <= code <= CONTROL_CHAR_END and code not in (
            TAB,
            LINE_FEED,
            CARRIAGE_RETURN,
        ):
            msg = (
                f"Input contains suspicious character: control character "
                f"(code {hex(code)}) at position {i}. "
                "Please remove it before submitting."
            )
            raise ValueError(msg)

    # Check for Unicode bidirectional override characters (spoofing)
    for i, char in enumerate(text):
        if char in ("\u202e", "\u202d"):
            char_name = "right-to-left override" if char == "\u202e" else "left-to-right override"
            msg = (
                f"Input contains suspicious character: {char_name} "
                f"(\\u{ord(char):04x}) at position {i}. "
                "Please remove it before submitting."
            )
            raise ValueError(msg)

    # Check for zero-width characters (obfuscation)
    for i, char in enumerate(text):
        if char in ("\u200b", "\u200c", "\u200d", "\ufeff"):
            char_name = {
                "\u200b": "zero-width space",
                "\u200c": "zero-width non-joiner",
                "\u200d": "zero-width joiner",
                "\ufeff": "zero-width no-break space (BOM)",
            }[char]
            msg = (
                f"Input contains suspicious character: {char_name} "
                f"(\\u{ord(char):04x}) at position {i}. "
                "Please remove it before submitting."
            )
            raise ValueError(msg)

    # Check for Japanese full-width null (REQ-013)
    fullwidth_null_pos = text.find("\uff00")
    if fullwidth_null_pos != -1:
        msg = (
            f"Input contains suspicious character: full-width null (\\uff00) "
            f"at position {fullwidth_null_pos}. "
            "Please remove it before submitting."
        )
        raise ValueError(msg)
