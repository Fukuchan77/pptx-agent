"""Custom exceptions for file validation."""


class InvalidFileError(Exception):
    """Raised when file is invalid or cannot be processed."""


class FileSizeLimitError(Exception):
    """Raised when file size exceeds allowed limits."""


class CompressionRatioError(Exception):
    """Raised when compression ratio is suspicious (potential ZIP bomb)."""


class PathTraversalError(Exception):
    """Raised when path traversal attack is detected."""


class SecurityValidationError(Exception):
    """Raised when security validation fails (symlinks, malicious XML, etc.)."""
