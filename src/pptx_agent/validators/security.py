"""Security validation and prompt injection detection."""

import logging
import re
import urllib.parse
from pathlib import Path

from lxml import etree
from pydantic import BaseModel

# Configure logger
logger = logging.getLogger(__name__)

# Prompt injection patterns to detect (case-insensitive)
# English patterns
INJECTION_PATTERNS_EN = [
    r"ignore\s+(?:previous|all|above|everything)",
    r"disregard\s+(?:previous|all|above)",
    r"forget\s+(?:your\s+)?instructions?",
    r"system\s+prompt",
    r"you\s+are\s+now",
    r"override\s+(?:(?:previous|all|the|your)\s+)?(?:instructions?|rules?|prompts?|settings?)",
    r"new\s+instructions?",
]

# Japanese patterns for prompt injection detection
INJECTION_PATTERNS_JA = [
    r"以前の指示を無視",  # "ignore previous instructions"
    r"新しい指示",  # "new instructions"
    r"システムプロンプト",  # "system prompt"
    r"指示を忘れ",  # "forget instructions"
    r"すべて無視",  # "ignore everything"
]

# Alias for INJECTION_PATTERNS_EN — backward compatibility
INJECTION_PATTERNS = INJECTION_PATTERNS_EN


class SecurityValidationResult(BaseModel):
    """Result of security validation with detected threats and sanitized text."""

    has_threats: bool
    detected_patterns: list[str]
    sanitized_text: str
    original_text: str


def flag_suspicious_phrases(text: str) -> None:
    """Detect suspicious phrases that may indicate prompt injection attempts.

    This is a BEST-EFFORT detection mechanism and NOT a security boundary.
    LLM prompt injection is fundamentally out-of-scope per the CLI trust model,
    where the user already has full filesystem access and controls all inputs.

    This function provides a signal for obviously suspicious patterns but makes
    no guarantee of comprehensive detection. Adversarial users can trivially
    bypass pattern matching.

    The function preserves all whitespace and structure in the input text.
    Multi-line content such as Markdown, code blocks, and bullet lists are
    not modified.

    Args:
        text: Input text to check for suspicious patterns

    Raises:
        ValueError: If suspicious phrases are detected in the input text.
                   The error message includes information about the detected pattern.

    Requirements:
        - 2.3.1: Raise ValueError on detection instead of silent sanitization
        - 2.3.2: Preserve whitespace and multi-line content
        - 2.3.3: Detect both English and Japanese suspicious patterns
        - 2.3.4: Document as best-effort signal, not security boundary

    Note:
        This function does NOT modify the input text. Whitespace, newlines,
        indentation, and all formatting are preserved exactly as provided.
    """
    text_lower = text.lower()

    # Check English patterns
    for pattern in INJECTION_PATTERNS_EN:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            matched_text = text[match.start() : match.end()]
            logger.warning("Suspicious phrase detected (English): %s", matched_text)
            msg = (
                f"Suspicious phrase detected: '{matched_text}'. "
                "Input rejected as potential prompt injection."
            )
            raise ValueError(msg)

    # Check Japanese patterns
    for pattern in INJECTION_PATTERNS_JA:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_text = text[match.start() : match.end()]
            logger.warning("Suspicious phrase detected (Japanese): %s", matched_text)
            msg = (
                f"Suspicious phrase detected: '{matched_text}'. "
                "Input rejected as potential prompt injection."
            )
            raise ValueError(msg)


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

    # Try to parse XML with secure parser (which disables dangerous features)
    try:
        # Secure XML parser prevents:
        # - External entity expansion (resolve_entities=False)
        # - Network access (no_network=True)
        # - DTD processing
        # huge_tree=True allows large XML (safe because size is pre-validated)
        # This will raise an exception if dangerous XML is encountered
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
        etree.fromstring(xml_content.encode("utf-8"), parser=parser)
    except etree.ParseError:
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

    **IMPORTANT - URL Decoding Contract:**
    This function performs URL decoding (urllib.parse.unquote) internally
    on the input path ONCE. Callers MUST NOT double-decode the output or
    apply additional URL decoding, as this could reintroduce security
    vulnerabilities that were validated against.

    Args:
        file_path: File path to validate (may be URL-encoded)
        base_dir: Base directory that file must be within

    Returns:
        True if path is safe, False if path traversal detected

    Requirements:
        - Detect ../ in paths
        - Detect absolute paths (Unix and Windows)
        - Detect symlinks
        - Ensure path is within base directory
        - Allow safe relative paths
        - Perform single URL decode internally

    Examples:
        Correct usage - pass raw path, use validated result directly:

        >>> base = "/home/user/app"
        >>> path = "documents/file.txt"  # Plain path
        >>> if validate_file_path(path, base):
        ...     # Safe to use path directly
        ...     with open(Path(base) / path) as f:
        ...         data = f.read()

        >>> # URL-encoded path is handled automatically
        >>> encoded_path = "images%2Fphoto.jpg"  # URL-encoded
        >>> if validate_file_path(encoded_path, base):
        ...     # Safe to use - function decoded it internally
        ...     # DO NOT decode again!
        ...     image_path = Path(base) / encoded_path  # ✗ WRONG - double decode
        ...     image_path = Path(base) / urllib.parse.unquote(encoded_path)  # ✓ CORRECT

        Incorrect usage - double decoding (security risk):

        >>> # ✗ WRONG - Do not decode before calling
        >>> decoded = urllib.parse.unquote(path)
        >>> validate_file_path(decoded, base)  # Misses URL-encoded attacks

        >>> # ✗ WRONG - Do not decode after validation
        >>> if validate_file_path(path, base):
        ...     # Double decoding could reintroduce traversal
        ...     unsafe = urllib.parse.unquote(path)

    Note:
        For CLI usage where the user has filesystem access, this validation
        provides defense-in-depth but is not a security boundary. The user
        can already access files through other means. This validation prevents
        accidents and catches obviously malicious patterns.
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
