"""Security validation and prompt injection detection."""

import logging
import re
import urllib.parse
from pathlib import Path

from defusedxml import ElementTree
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
    r"override\s+(?:(?:previous|all|the|your)\s+)?(?:instructions?|rules?|prompts?|settings?)",
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
    sanitized = sanitized.strip()

    # Capitalize first letter to maintain sentence structure after removal
    if sanitized and sanitized[0].islower():
        sanitized = sanitized[0].upper() + sanitized[1:]

    return sanitized


def validate_xml_safety(xml_content: str) -> bool:
    """Validate XML content for XXE (XML External Entity) attack patterns.

    This function protects against:
    - External entity declarations (XXE attacks)
    - DTD (Document Type Definition) with entities
    - External resource references (file:// or http://)
    - Parameter entity expansion attacks

    Args:
        xml_content: XML content as string to validate

    Returns:
        True if XML is safe, False if malicious patterns detected

    Requirements:
        - Detect malicious XML external entity declarations
        - Detect DTD with entity definitions
        - Detect external resource references
        - Allow safe XML with namespaces and CDATA
    """
    # Check for dangerous patterns using regex (fast pre-check)
    # These patterns should NOT exist in legitimate PPTX XML files

    # Check for ENTITY declarations (both regular and parameter entities)
    entity_pattern = re.compile(r"<!ENTITY", re.IGNORECASE)
    if entity_pattern.search(xml_content):
        logger.warning("XML security validation: ENTITY declaration detected")
        return False

    # Check for SYSTEM keyword (external resource reference)
    system_pattern = re.compile(r"SYSTEM\s+[\"']", re.IGNORECASE)
    if system_pattern.search(xml_content):
        logger.warning("XML security validation: SYSTEM reference detected")
        return False

    # Try to parse XML with defusedxml (which disables dangerous features)
    try:
        # defusedxml automatically prevents:
        # - External entity expansion
        # - DTD processing
        # - XInclude processing
        # This will raise an exception if dangerous XML is encountered
        ElementTree.fromstring(xml_content)
    except ElementTree.ParseError:
        # If XML is malformed, it's suspicious
        logger.warning("XML security validation: ParseError - malformed or malicious XML")
        return False
    except Exception as e:
        # Any other exception indicates potential security issue
        logger.warning("XML security validation: Exception during parsing - %s", e)
        return False
    else:
        return True


def validate_file_path(file_path: str, base_dir: str) -> bool:
    """Validate file path against directory traversal attacks.

    This function protects against:
    - Parent directory traversal (../)
    - Absolute paths
    - Symlink attacks
    - Access outside base directory
    - URL-encoded traversal attempts

    Args:
        file_path: File path to validate
        base_dir: Base directory that file must be within

    Returns:
        True if path is safe, False if path traversal detected

    Requirements:
        - Detect ../ in paths
        - Detect absolute paths (Unix and Windows)
        - Detect symlinks
        - Ensure path is within base directory
        - Allow safe relative paths
    """
    # URL decode the path to catch encoded traversal attempts
    try:
        decoded_path = urllib.parse.unquote(file_path)
    except Exception:
        # If decoding fails, treat as suspicious
        logger.warning("Path validation: Failed to URL decode path: %s", file_path)
        return False

    # Check for Windows-style absolute paths (C:, D:, \\network\share)
    # These patterns are suspicious even on Unix systems
    windows_absolute_patterns = [
        re.compile(r"^[A-Za-z]:[/\\]"),  # C:\ or D:/
        re.compile(r"^\\\\"),  # \\network\share
    ]
    for pattern in windows_absolute_patterns:
        if pattern.match(decoded_path):
            logger.warning("Path validation: Windows absolute path detected: %s", decoded_path)
            return False

    # Convert to Path objects for robust handling
    try:
        # Resolve base directory to absolute path
        base_path = Path(base_dir).resolve()

        # Check if path is absolute (Unix-style)
        path_obj = Path(decoded_path)

        # Build the unresolved full path first (to check for symlinks)
        unresolved_path = path_obj if path_obj.is_absolute() else base_path / decoded_path

        # Check for symlinks BEFORE resolving (resolve() follows symlinks)
        # NOTE (TOCTOU): There is an inherent time-of-check-to-time-of-use race
        # between the exists()/is_symlink() checks here and the subsequent
        # resolve() call.  An attacker could replace a file with a symlink after
        # this check passes.  For a CLI tool that operates on user-supplied local
        # files this risk is accepted — the user already has filesystem access.
        # If this function is ever used in a server/multi-tenant context, a
        # file-descriptor-based approach (open → fstat) should be adopted instead.
        if unresolved_path.exists():
            # Check if the file itself is a symlink
            if unresolved_path.is_symlink():
                logger.warning("Path validation: Symlink detected at: %s", decoded_path)
                return False

            # Check parent directories for symlinks
            current = unresolved_path.parent
            while current not in (base_path, current.parent):
                if current.is_symlink():
                    logger.warning("Path validation: Symlink detected in path: %s", decoded_path)
                    return False
                current = current.parent

        # Now resolve the path to check if it's within base directory
        # For absolute paths, check if they resolve within base directory
        if path_obj.is_absolute():
            # Resolve the absolute path
            full_path = path_obj.resolve()

            # Check if it's within base directory
            try:
                full_path.relative_to(base_path)
            except ValueError:
                # Absolute path outside base directory
                logger.warning(
                    "Path validation: Absolute path outside base directory: %s", decoded_path
                )
                return False
        else:
            # Relative path - resolve to check if within base
            full_path = (base_path / decoded_path).resolve()

            # Check if resolved path is within base directory
            try:
                full_path.relative_to(base_path)
            except ValueError:
                logger.warning(
                    "Path validation: Path traversal detected - path '%s' "
                    "resolves outside base directory '%s'",
                    decoded_path,
                    base_dir,
                )
                return False

    except (OSError, RuntimeError, ValueError) as e:
        # Any filesystem error is treated as suspicious
        logger.warning("Path validation: Error validating path '%s': %s", file_path, e)
        return False
    else:
        return True
