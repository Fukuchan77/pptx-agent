"""Security validation and prompt injection detection."""

import logging
import re

from pydantic import BaseModel

# Configure logger
logger = logging.getLogger(__name__)

# Prompt injection patterns to detect (case-insensitive)
INJECTION_PATTERNS = [
    r"ignore\s+(?:previous|all|above|everything)",
    r"disregard\s+(?:previous|all|above)",
    r"forget\s+(?:your\s+)?instructions?",
    r"system\s+prompt",
    r"you\s+are\s+now",
    r"override",
    r"new\s+instructions?",
]


class SecurityValidationResult(BaseModel):
    """Result of security validation with detected threats and sanitized text."""

    has_threats: bool
    detected_patterns: list[str]
    sanitized_text: str
    original_text: str


def detect_prompt_injection(text: str) -> SecurityValidationResult:
    """Detect prompt injection attempts in input text.

    Args:
        text: Input text to check for injection patterns

    Returns:
        SecurityValidationResult with detection results and sanitized text

    Requirements:
        - FR-055: Detect suspicious input patterns, sanitize, and log
    """
    detected_patterns = []
    text_lower = text.lower()

    # Check each pattern
    for pattern in INJECTION_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            matched_text = text[match.start() : match.end()]
            if matched_text not in detected_patterns:
                detected_patterns.append(matched_text)

    has_threats = len(detected_patterns) > 0

    # Log detection if threats found
    if has_threats:
        logger.warning(
            "Prompt injection patterns detected: %s",
            detected_patterns,
        )

    # Sanitize text if threats detected
    sanitized_text = sanitize_input(text, detected_patterns) if has_threats else text

    return SecurityValidationResult(
        has_threats=has_threats,
        detected_patterns=detected_patterns,
        sanitized_text=sanitized_text,
        original_text=text,
    )


def sanitize_input(text: str, patterns: list[str]) -> str:
    """Remove detected injection patterns from text.

    Args:
        text: Original text
        patterns: List of detected patterns to remove

    Returns:
        Sanitized text with patterns removed and whitespace normalized
    """
    if not patterns:
        return text

    sanitized = text

    # Remove each detected pattern (case-insensitive)
    for pattern in patterns:
        # Escape special regex characters in the pattern
        escaped_pattern = re.escape(pattern)
        sanitized = re.sub(escaped_pattern, "", sanitized, flags=re.IGNORECASE)

    # Normalize whitespace: replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Clean up leading/trailing whitespace and multiple periods/punctuation
    return sanitized.strip()
