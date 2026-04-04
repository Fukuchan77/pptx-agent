"""File validation module for PPTX files."""

import os
import re
import zipfile
from pathlib import Path

from pptx_agent.validators.exceptions import (
    CompressionRatioError,
    FileSizeLimitError,
    InvalidFileError,
    PathTraversalError,
    SecurityValidationError,
)

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

    # Check if file exists
    if not file_path.exists():
        msg = (
            f"File validation failed: file does not exist at '{file_path}'. "
            "Expected: valid path to existing file."
        )
        raise InvalidFileError(msg)

    # Check compressed file size
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        msg = (
            f"File size limit exceeded: {file_size} bytes (compressed), "
            f"maximum allowed is {MAX_FILE_SIZE} bytes."
        )
        raise FileSizeLimitError(msg)

    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # First, calculate total uncompressed size
            total_uncompressed_size = 0

            for info in zf.infolist():
                total_uncompressed_size += info.file_size

            # Check total uncompressed size first (before compression ratio check)
            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                msg = (
                    f"Uncompressed size limit exceeded: {total_uncompressed_size} bytes total, "
                    f"maximum allowed is {MAX_UNCOMPRESSED_SIZE} bytes."
                )
                raise FileSizeLimitError(msg)

            # Then check compression ratio for each file
            for info in zf.infolist():
                uncompressed_size = info.file_size
                compressed_size = info.compress_size

                # Check compression ratio for each file (avoid division by zero)
                if compressed_size > 0:
                    ratio = uncompressed_size / compressed_size
                    if ratio > MAX_COMPRESSION_RATIO:
                        msg = (
                            f"Suspicious compression ratio detected: file '{info.filename}' has "
                            f"compression ratio of {ratio:.1f}x, maximum allowed is "
                            f"{MAX_COMPRESSION_RATIO}x. Expected: valid compression ratio."
                        )
                        raise CompressionRatioError(msg)

    except zipfile.BadZipFile as e:
        msg = f"File format validation failed: file is not a valid ZIP/PPTX file. Details: {e}"
        raise InvalidFileError(msg) from e


def validate_output_path(output_path: str, base_dir: str | None = None) -> Path:
    """Validate output path against path traversal attacks.

    Args:
        output_path: Path where file should be saved
        base_dir: Base directory for output files (default: ./output or PPTX_OUTPUT_DIR env var)

    Returns:
        Resolved absolute Path object inside base_dir

    Raises:
        PathTraversalError: If path is outside base_dir or contains path traversal

    """
    # Determine base directory
    if base_dir is None:
        # Check environment variable first, fallback to default ./output
        env_base_dir = os.environ.get("PPTX_OUTPUT_DIR")
        base_dir = env_base_dir or str(Path.cwd() / "output")

    # Convert to Path objects and resolve to absolute paths
    base_path = Path(base_dir).resolve()
    output = Path(output_path)

    # If output is relative, resolve it relative to base_dir
    if not output.is_absolute():
        output = base_path / output

    # Resolve to absolute path
    output = output.resolve()

    # Check if output is inside base_dir using is_relative_to (Python 3.9+) or string comparison
    try:
        # Check if output path is relative to base_path
        output.relative_to(base_path)
    except ValueError:
        msg = (
            f"Path traversal detected: output path '{output}' is outside allowed base "
            f"directory '{base_path}'. Expected: path within base directory."
        )
        raise PathTraversalError(msg) from None

    return output


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

    Args:
        file_path: Path to the PPTX file

    Raises:
        SecurityValidationError: If malicious XML patterns detected

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Patterns that indicate malicious XML
    entity_pattern = re.compile(rb"<!ENTITY", re.IGNORECASE)
    doctype_pattern = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
    system_pattern = re.compile(rb"SYSTEM\s+", re.IGNORECASE)

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Check all XML files in the PPTX
            for file_info in zf.infolist():
                if file_info.filename.endswith(".xml") or file_info.filename.endswith(".rels"):
                    content = zf.read(file_info.filename)

                    # Check for entity declarations (billion laughs, entity expansion)
                    if entity_pattern.search(content):
                        msg = (
                            f"XML security validation failed: malicious entity declaration "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without entity declarations."
                        )
                        raise SecurityValidationError(msg)

                    # Check for DOCTYPE with potential XXE
                    # DOCTYPE is allowed in some cases, but check for SYSTEM (external entities)
                    if doctype_pattern.search(content) and system_pattern.search(content):
                        msg = (
                            f"XML security validation failed: external entity reference (XXE) "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without external entity references."
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
    - Is readable

    Args:
        template_path: Path to the template file

    Returns:
        Absolute Path object to the validated template

    Raises:
        InvalidFileError: If file does not exist, has wrong extension, or is not a valid PPTX
        SecurityValidationError: If path contains symlinks
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
    validate_no_symlinks(path)

    # Validate PPTX file structure and size
    validate_pptx_file(path)

    # Return absolute path
    return path.resolve()
