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
MAX_COMPRESSION_RATIO = 100


def validate_pptx_file(file_path: Path | str) -> None:
    """Validate PPTX file against ZIP bomb and size constraints.

    Args:
        file_path: Path to the PPTX file to validate

    Raises:
        InvalidFileError: If file does not exist or is not a valid ZIP file
        FileSizeLimitError: If file size or uncompressed size exceeds limits
        CompressionRatioError: If compression ratio is suspicious

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
            # Calculate total uncompressed size and check compression ratio in a single loop
            total_uncompressed_size = 0

            for info in zf.infolist():
                total_uncompressed_size += info.file_size

                # Check compression ratio for each file (avoid division by zero)
                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > MAX_COMPRESSION_RATIO:
                        msg = (
                            f"Suspicious compression ratio detected: file '{info.filename}' has "
                            f"compression ratio of {ratio:.1f}x, maximum allowed is "
                            f"{MAX_COMPRESSION_RATIO}x. Expected: valid compression ratio."
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

    Args:
        file_path: Path to validate

    Raises:
        SecurityValidationError: If path contains symlinks

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
    try:
        # Check each parent in the original path
        current = file_path.absolute()
        while current != current.parent:
            if current.is_symlink():
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

    Protects against:
    - XML billion laughs attack (entity expansion)
    - XXE (external entity injection)
    - Excessive entity expansion depth

    **Security Design Rationale (from Code Review M-5):**

    The current implementation uses regex-based detection instead of an XML parser.
    This is sufficient for CLI tool usage for the following reasons:

    1. **Trusted File Source**: As a CLI tool, it only processes local files explicitly
       specified by users. Uploads from unknown sources are not expected.

    2. **Simple Detection Sufficient**: The <!ENTITY> and SYSTEM patterns detected by
       regex are unnecessary in normal PPTX file structure. If present, they clearly
       indicate abnormal or malicious modifications.

    3. **Encoding Bypass Risk**: <!ENTITY> encoded in UTF-16 or UTF-32 may not be
       detected, but standard PPTX files generated by Office products use UTF-8,
       so this is acceptable for CLI use.

    **Considerations for Future Web Service Deployment:**

    If this tool is deployed as a web service, the following measures are recommended:

    1. **Introduce defusedxml**: Consider using the defusedxml library instead of regex
       to automatically prevent XXE and entity expansion during XML parsing.

    2. **Encoding Protection**: Parser-level validation is needed to prevent bypasses
       using various encodings.

    3. **Sandbox Environment**: Build a mechanism to process untrusted files in an
       isolated environment.

    Args:
        file_path: Path to the PPTX file

    Raises:
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
                    content = zf.read(file_info.filename)

                    # Detect entity declarations (Billion Laughs attack, entity expansion)
                    # Standard PPTX files don't contain <!ENTITY>, so if present,
                    # it indicates malicious modification.
                    # Limitation: Bypasses using non-UTF-8 encoding are not detectable,
                    # but Office products generate PPTX in UTF-8, so this is acceptable for CLI use.
                    if entity_pattern.search(content):
                        msg = (
                            f"XML security validation failed: malicious entity declaration "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without entity declarations."
                        )
                        raise SecurityValidationError(msg)

                    # Detect XXE (external entity references)
                    # <!DOCTYPE> itself is legitimately used in some XML, so we detect
                    # external entity references by the combination with SYSTEM keyword.
                    # This prevents file system access and network requests.
                    if doctype_pattern.search(content) and system_pattern.search(content):
                        msg = (
                            f"XML security validation failed: external entity reference (XXE) "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without external entity references."
                        )
                        raise SecurityValidationError(msg)

                    # Defense-in-depth: validate via defusedxml parser
                    # after regex pre-checks pass.
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
                            f"XML security validation failed: defusedxml detected "
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
