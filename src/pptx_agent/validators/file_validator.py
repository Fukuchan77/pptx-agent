"""File validation module for PPTX files."""

import re
import zipfile
from pathlib import Path

from pptx_agent.validators.exceptions import (
    CompressionRatioError,
    FileSizeLimitError,
    InvalidFileError,
    SecurityValidationError,
)
from pptx_agent.validators.security import validate_xml_safety

# Constants for validation limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB
MAX_ENTRY_SIZE = 10 * 1024 * 1024  # 10MB per entry (zip bomb protection)
MAX_COMPRESSION_RATIO = 100
CHUNK_SIZE = 8192  # 8KB for streaming reads


def validate_pptx_file(file_path: Path | str) -> None:
    """Validate PPTX file against ZIP bomb and size constraints.

    This function implements multi-layered protection against malicious ZIP files:

    1. **Compressed File Size Check (100MB limit)**:
       - Validates the file size on disk before opening
       - Prevents processing of excessively large files

    2. **Per-Entry Size Check (10MB limit)**:
       - Validates each individual entry's uncompressed size
       - Prevents individual entries from consuming excessive memory
       - Detects zip bombs before decompression occurs

    3. **Total Uncompressed Size Check (500MB limit)**:
       - Validates the total size of all entries when decompressed
       - Provides defense-in-depth against zip bombs

    4. **Compression Ratio Check (max 100x)**:
       - Detects suspiciously high compression ratios (e.g., 1KB → 100MB)
       - Normal PPTX files have ratios of 2x-20x for text, 1x-2x for images
       - Ratios > 100x indicate potential zip bomb attacks

    Args:
        file_path: Path to the PPTX file to validate

    Raises:
        InvalidFileError: If file does not exist or is not a valid ZIP file
        FileSizeLimitError: If file size, per-entry size, or uncompressed size exceeds limits
        CompressionRatioError: If compression ratio is suspicious (potential zip bomb)

    Security Note:
        These checks provide protection against zip bomb attacks and resource exhaustion.
        They are designed for CLI tool usage with locally stored files. For web service
        deployment, consider additional measures such as sandboxing and rate limiting.

    """
    # Convert to Path object if string
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check compressed file size (EAFP pattern - try operation directly)
    try:
        file_size = file_path.stat().st_size
    except FileNotFoundError as e:
        msg = (
            f"File validation failed: file does not exist at '{file_path}'. "
            "Expected: valid path to existing file."
        )
        raise InvalidFileError(msg) from e
    if file_size > MAX_FILE_SIZE:
        msg = (
            f"File size limit exceeded: {file_size} bytes (compressed), "
            f"maximum allowed is {MAX_FILE_SIZE} bytes."
        )
        raise FileSizeLimitError(msg)

    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # ZIP BOMB PROTECTION: Validate each entry in the archive
            # We check both per-entry size limits and compression ratios
            # to detect malicious zip bombs before decompression
            total_uncompressed_size = 0

            for info in zf.infolist():
                # Per-entry size check (10MB limit)
                if info.file_size > MAX_ENTRY_SIZE:
                    msg = (
                        f"Entry size limit exceeded: file '{info.filename}' has "
                        f"uncompressed size of {info.file_size} bytes, "
                        f"maximum allowed is {MAX_ENTRY_SIZE} bytes (10MB). "
                        "Expected: entries under 10MB. If this is a legitimate file, "
                        "consider splitting large entries or reducing file size."
                    )
                    raise FileSizeLimitError(msg)

                total_uncompressed_size += info.file_size

                # Compression ratio check (max 100x)
                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > MAX_COMPRESSION_RATIO:
                        msg = (
                            f"Suspicious compression ratio detected: file '{info.filename}' has "
                            f"compression ratio of {ratio:.1f}x, maximum allowed is "
                            f"{MAX_COMPRESSION_RATIO}x. This may indicate a zip bomb attack. "
                            "Expected: valid compression ratio. Please verify the file is "
                            "legitimate and not corrupted."
                        )
                        raise CompressionRatioError(msg)

            # Check total uncompressed size (after gathering total)
            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                msg = (
                    f"Uncompressed size limit exceeded: {total_uncompressed_size} bytes total, "
                    f"maximum allowed is {MAX_UNCOMPRESSED_SIZE} bytes."
                )
                raise FileSizeLimitError(msg)

    except zipfile.BadZipFile as e:
        msg = f"File format validation failed: file is not a valid ZIP/PPTX file. Details: {e}"
        raise InvalidFileError(msg) from e


def validate_file_extension(file_path: Path | str) -> None:
    """Validate file has allowed extension (.pptx only).

    Args:
        file_path: Path to the file to validate

    Raises:
        InvalidFileError: If file extension is not .pptx

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Get file extension (case-insensitive)
    file_extension = file_path.suffix.lower()

    # Only allow .pptx extension
    if file_extension != ".pptx":
        msg = (
            f"File extension validation failed: '{file_extension}' is not allowed. "
            "Expected: .pptx extension only."
        )
        raise InvalidFileError(msg)


def validate_no_symlinks(file_path: Path | str) -> None:
    """Validate that file path does not contain symlinks.

    This function validates that the file path and its parent directories
    do not contain symlinks. However, it allows the current working directory
    (cwd) itself to be a symlink, as this is a common scenario when users
    run the application from a symlinked directory.

    The validation resolves cwd to its real path first, then checks only
    the path components beyond cwd for symlinks. This prevents false positives
    when running from a symlinked directory while still catching actual
    security issues.

    Args:
        file_path: Path to validate

    Raises:
        SecurityValidationError: If path contains symlinks (excluding cwd)

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check if the file itself is a symlink
    if file_path.is_symlink():
        msg = (
            f"Symlink validation failed: file at '{file_path}' is a symlink. "
            "Expected: regular file without symlinks."
        )
        raise SecurityValidationError(msg)

    # Check if any parent directory is a symlink
    # IMPORTANT: Check for symlinks BEFORE resolving paths, as resolve() follows symlinks
    # Strategy: Walk up the absolute path and check each component for symlinks
    # Allow cwd itself to be a symlink to support common dev scenarios
    # Also allow system-level symlinks (e.g., /var -> /private/var on macOS)
    try:
        # Get resolved cwd (Path.cwd() already resolves symlinks on most systems)
        resolved_cwd = Path.cwd().resolve()

        # System-level symlinks that are safe to allow (common OS patterns)
        # These are typically part of the OS filesystem structure
        system_symlinks = {
            Path("/var"),  # macOS: /var -> /private/var
            Path("/tmp"),  # noqa: S108  # Some systems: /tmp -> /private/tmp
            Path("/etc"),  # Some systems: /etc -> /private/etc
        }

        # Check if the file path (when resolved) is under or related to cwd
        # This determines if we should apply the pragmatic symlink acceptance
        try:
            file_path.resolve().relative_to(resolved_cwd)
            file_under_cwd = True
        except ValueError:
            file_under_cwd = False

        # Convert to absolute path but DON'T resolve yet (we need to check for symlinks first)
        abs_path = file_path.absolute()

        # Walk up parent directories and check for symlinks
        current = abs_path.parent
        while current != current.parent:
            # Check if this directory is a symlink
            if current.is_symlink():
                # Allow system-level symlinks (safe OS patterns)
                if current in system_symlinks:
                    current = current.parent
                    continue

                # Pragmatic approach: Allow ONLY symlinks that are part of the cwd path itself
                # (i.e., cwd or its ancestors). This prevents false positives when running
                # from a symlinked directory while still catching security issues with
                # unrelated symlinked directories.
                if file_under_cwd:
                    try:
                        current_resolved = current.resolve()
                        # Check if the symlink is cwd itself or an ancestor of cwd
                        # by verifying that resolved_cwd is under current_resolved
                        try:
                            resolved_cwd.relative_to(current_resolved)
                            # current is cwd or an ancestor of cwd - acceptable
                            current = current.parent
                            continue
                        except ValueError:
                            # current is NOT in the cwd path - reject it
                            pass
                    except (OSError, RuntimeError):
                        pass

                # This is a symlink that's not part of the cwd path - reject it
                msg = (
                    f"Symlink validation failed: path contains symlink at '{current}'. "
                    "Expected: regular file path without symlinks."
                )
                raise SecurityValidationError(msg)

            current = current.parent

    except (OSError, RuntimeError) as e:
        msg = f"Symlink validation failed: error while validating path. Details: {e}"
        raise SecurityValidationError(msg) from e


def validate_pptx_structure(file_path: Path | str) -> None:
    """Validate PPTX internal XML structure against malicious patterns.

    This function implements a four-layer defense-in-depth approach to validate
    XML content before parsing:

    **Layer 1: Per-Entry Size Check (10MB limit)**
    - Validates each XML/rels entry's uncompressed size before reading content
    - Prevents oversized entries from being loaded into memory
    - Rejects entries exceeding MAX_ENTRY_SIZE (10MB) before any parsing occurs

    **Layer 2: Compression Anomaly Detection**
    - Detects suspicious entries where compress_size==0 but file_size>0
    - Indicates potentially corrupted archives or zip bomb attempts

    **Layer 3: Regex Pre-Check**
    - Fast pattern matching for malicious XML constructs (<!ENTITY>, SYSTEM)
    - Performs initial screening before full XML parsing
    - Sufficient for CLI usage with trusted local files

    **Layer 4: UTF-8 Decode Validation**
    - Ensures all XML content is valid UTF-8 (standard for Office-generated PPTX)
    - Rejects files with suspicious non-UTF-8 encodings

    **Layer 5: Secure XML Parsing**
    - Final validation using secure XML parser (lxml with resolve_entities=False)
    - Automatically prevents XXE and entity expansion attacks
    - Only executes after all previous layers pass

    Protects against:
    - Resource exhaustion (oversized XML entries)
    - Zip bombs (compression anomalies)
    - XML billion laughs attack (entity expansion)
    - XXE (external entity injection)
    - Excessive entity expansion depth

    **Security Design Rationale:**

    The validation order is critical - size checks occur BEFORE reading content
    to prevent memory exhaustion. This defense-in-depth approach is appropriate
    for CLI tool usage with locally specified files.

    Args:
        file_path: Path to the PPTX file

    Raises:
        FileSizeLimitError: If XML entry exceeds size limit or compression anomaly detected
        SecurityValidationError: If malicious XML patterns detected

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Regex-based malicious XML detection (fast pre-check for CLI use).
    # See docstring for security design rationale and future considerations.
    entity_pattern = re.compile(rb"<!ENTITY", re.IGNORECASE)
    doctype_pattern = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
    system_pattern = re.compile(rb"SYSTEM\s+[\"']", re.IGNORECASE)

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Check all XML files in the PPTX
            for file_info in zf.infolist():
                if file_info.filename.endswith(".xml") or file_info.filename.endswith(".rels"):
                    # Per-entry size check (10MB limit)
                    if file_info.file_size > MAX_ENTRY_SIZE:
                        msg = (
                            f"XML entry size limit exceeded: file '{file_info.filename}' has "
                            f"uncompressed size of {file_info.file_size} bytes, "
                            f"maximum allowed is {MAX_ENTRY_SIZE} bytes (10MB). "
                            "Validation failed before XML parsing to prevent memory exhaustion. "
                            "Expected: XML entries under 10MB."
                        )
                        raise FileSizeLimitError(msg)

                    # Compression anomaly detection
                    if file_info.compress_size == 0 and file_info.file_size > 0:
                        msg = (
                            f"Compression anomaly detected: file '{file_info.filename}' has "
                            f"compressed size of 0 bytes but uncompressed size of "
                            f"{file_info.file_size} bytes. "
                            "This may indicate a corrupted archive or malicious content. "
                            "Expected: valid compression metadata."
                        )
                        raise FileSizeLimitError(msg)

                    content = zf.read(file_info.filename)

                    # Detect entity declarations (Billion Laughs attack)
                    if entity_pattern.search(content):
                        msg = (
                            f"XML security validation failed: malicious entity declaration "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without entity declarations."
                        )
                        raise SecurityValidationError(msg)

                    # Detect XXE (external entity references)
                    if doctype_pattern.search(content) and system_pattern.search(content):
                        msg = (
                            f"XML security validation failed: external entity reference (XXE) "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without external entity references."
                        )
                        raise SecurityValidationError(msg)

                    # Defense-in-depth: validate via secure XML parser
                    try:
                        decoded_content = content.decode("utf-8")
                    except UnicodeDecodeError as e:
                        # Non-UTF-8 XML in a PPTX is suspicious
                        msg = (
                            f"XML security validation failed: unable to decode "
                            f"'{file_info.filename}' as UTF-8. "
                            "Expected: UTF-8 encoded XML."
                        )
                        raise SecurityValidationError(msg) from e

                    if not validate_xml_safety(decoded_content):
                        msg = (
                            f"XML security validation failed: secure XML parser detected "
                            f"a potential threat in '{file_info.filename}'. "
                            "Expected: XML without malicious patterns."
                        )
                        raise SecurityValidationError(msg)

    except zipfile.BadZipFile as e:
        msg = (
            f"PPTX structure validation failed: cannot validate structure due to invalid "
            f"ZIP file. Details: {e}"
        )
        raise InvalidFileError(msg) from e


def validate_template_path(template_path: str) -> Path:
    """Validate template path for storage and retrieval.

    Validates that the template path:
    - Has .pptx extension
    - Does not contain symlinks
    - Exists and is a valid PPTX file
    - Has no malicious XML patterns (XXE, Billion Laughs)
    - Is readable

    Args:
        template_path: Path to the template file

    Returns:
        Absolute Path object to the validated template

    Raises:
        InvalidFileError: If file does not exist, has wrong extension, or is not a valid PPTX
        SecurityValidationError: If path contains symlinks or malicious XML patterns
            (XXE, entity expansion)
        FileSizeLimitError: If file size exceeds limits
        CompressionRatioError: If compression ratio is suspicious

    """
    # Convert to Path object
    path = Path(template_path)

    # Validate file extension first (before checking existence)
    # Intentional order for better CLI UX: If user specifies wrong file type
    # (e.g., "template.pdf"), they get immediate, clear error about extension
    # rather than ambiguous "file not found" error that could mean wrong path OR wrong extension.
    validate_file_extension(path)

    # Check if file exists
    if not path.exists():
        msg = (
            f"Template path validation failed: file does not exist at '{template_path}'. "
            "Expected: valid path to existing template file."
        )
        raise InvalidFileError(msg)

    # Validate no symlinks
    # This provides security against symlink attacks without being overly restrictive
    # for CLI usage where users explicitly specify template paths
    validate_no_symlinks(path)

    # Validate PPTX file structure and size
    validate_pptx_file(path)

    # Validate PPTX internal XML structure (XXE, Billion Laughs protection)
    validate_pptx_structure(path)

    # Return absolute path
    return path.resolve()
