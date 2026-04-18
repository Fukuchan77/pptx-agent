"""Unit tests for file validator module."""

import os
import stat
import sys
import zipfile
from pathlib import Path

import pytest

from pptx_agent.validators.exceptions import (
    CompressionRatioError,
    FileSizeLimitError,
    InvalidFileError,
    SecurityValidationError,
)
from pptx_agent.validators.file_validator import validate_pptx_file, validate_template_path


class TestValidatePptxFile:
    """Test cases for validate_pptx_file function."""

    def test_validate_pptx_file_normal(self, tmp_path: Path) -> None:
        """Test validation of normal PPTX file."""
        # Create a small valid ZIP file
        pptx_path = tmp_path / "normal.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")  # 1KB uncompressed
            zf.writestr("[Content_Types].xml", "<Types/>")

        # Should not raise any exception
        validate_pptx_file(pptx_path)

    def test_validate_pptx_file_too_large(self, tmp_path: Path) -> None:
        """Test validation fails for file exceeding size limit."""
        # Create a file larger than 100MB
        pptx_path = tmp_path / "large.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            # Write 101MB of data
            zf.writestr("large_file.xml", "x" * (101 * 1024 * 1024))

        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_file(pptx_path)

        assert "size limit exceeded" in str(exc_info.value).lower()

    def test_validate_pptx_file_high_compression_ratio(self, tmp_path: Path) -> None:
        """Test validation fails for suspicious compression ratio."""
        # Create a highly compressed file (compression ratio > 100)
        # Must be under 10MB uncompressed to pass per-entry size check
        pptx_path = tmp_path / "compressed.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            # Create highly compressible data that results in ratio > 100
            # Use 9MB of repeating data (under 10MB per-entry limit)
            # This compresses to ~9KB with ratio ~1000x > 100
            data = "a" * (9 * 1024 * 1024)
            zf.writestr("repeating.xml", data)

        with pytest.raises(CompressionRatioError) as exc_info:
            validate_pptx_file(pptx_path)

        assert "compression ratio detected" in str(exc_info.value).lower()

    def test_validate_pptx_file_large_uncompressed(self, tmp_path: Path) -> None:
        """Test validation fails when file has large uncompressed size.

        Note: This test creates files with 540MB uncompressed size.
        Since ZIP_STORED doesn't compress, the file size also exceeds 100MB limit.
        Either the file size check or uncompressed size check will catch this,
        both are valid for detecting oversized files.
        """
        pptx_path = tmp_path / "large_uncompressed.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            # Add 12 files of 45MB each (540MB total uncompressed)
            for i in range(12):
                zf.writestr(f"file_{i}.xml", "x" * (45 * 1024 * 1024))

        # Should raise FileSizeLimitError (either for file size or uncompressed size)
        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_file(pptx_path)

        # Accept either error message as both indicate size limit exceeded
        error_msg = str(exc_info.value).lower()
        assert "size limit exceeded" in error_msg or "limit exceeded" in error_msg

    def test_validate_pptx_file_invalid_format(self, tmp_path: Path) -> None:
        """Test validation fails for invalid ZIP file."""
        # Create an invalid ZIP file
        pptx_path = tmp_path / "invalid.pptx"
        with pptx_path.open("w") as f:
            f.write("This is not a ZIP file")

        with pytest.raises(InvalidFileError) as exc_info:
            validate_pptx_file(pptx_path)

        assert (
            "format validation failed" in str(exc_info.value).lower()
            or "not a valid" in str(exc_info.value).lower()
        )

    def test_validate_pptx_file_not_found(self, tmp_path: Path) -> None:
        """Test validation fails when file does not exist."""
        pptx_path = tmp_path / "nonexistent.pptx"

        with pytest.raises(InvalidFileError) as exc_info:
            validate_pptx_file(pptx_path)

        assert "validation failed" in str(exc_info.value).lower()
        assert "does not exist" in str(exc_info.value).lower()

    def test_validate_pptx_file_entry_exceeds_size_limit(self, tmp_path: Path) -> None:
        """Test validation fails when a single entry exceeds 10MB size limit."""
        pptx_path = tmp_path / "large_entry.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            # Create a single entry with 11MB uncompressed data (exceeds 10MB limit)
            zf.writestr("large_entry.xml", "x" * (11 * 1024 * 1024))

        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_file(pptx_path)

        error_msg = str(exc_info.value).lower()
        assert "entry" in error_msg or "file" in error_msg
        assert "10" in str(exc_info.value) or "limit" in error_msg


class TestValidateTemplatePath:
    """Test cases for validate_template_path function."""

    def test_validate_template_path_valid(self, tmp_path: Path) -> None:
        """Test validation of valid template path."""
        # Create a valid PPTX file
        template_path = tmp_path / "valid_template.pptx"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")
            zf.writestr("[Content_Types].xml", "<Types/>")

        # Should not raise any exception
        result = validate_template_path(str(template_path))
        assert result.is_absolute()
        assert result.exists()

    def test_validate_template_path_nonexistent(self, tmp_path: Path) -> None:
        """Test validation fails for non-existent template file."""
        template_path = tmp_path / "nonexistent.pptx"

        with pytest.raises(InvalidFileError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "validation failed" in error_msg
        assert "does not exist" in error_msg

    def test_validate_template_path_wrong_extension(self, tmp_path: Path) -> None:
        """Test validation fails for file with wrong extension."""
        # Create a file with wrong extension
        template_path = tmp_path / "template.txt"
        template_path.write_text("not a pptx file")

        with pytest.raises(InvalidFileError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "extension validation failed" in error_msg
        assert ".pptx" in error_msg

    def test_validate_template_path_no_extension(self, tmp_path: Path) -> None:
        """Test validation fails for file without extension."""
        template_path = tmp_path / "template"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")

        with pytest.raises(InvalidFileError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "extension validation failed" in error_msg

    def test_validate_template_path_symlink(self, tmp_path: Path) -> None:
        """Test validation fails for symlink to template file."""
        # Create a valid PPTX file
        actual_file = tmp_path / "actual_template.pptx"
        with zipfile.ZipFile(actual_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")

        # Create a symlink to it
        symlink_path = tmp_path / "symlink_template.pptx"
        try:
            symlink_path.symlink_to(actual_file)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_template_path(str(symlink_path))

        error_msg = str(exc_info.value).lower()
        assert "symlink validation failed" in error_msg

    def test_validate_template_path_invalid_zip(self, tmp_path: Path) -> None:
        """Test validation fails for invalid ZIP file with .pptx extension."""
        template_path = tmp_path / "invalid.pptx"
        template_path.write_text("This is not a ZIP file")

        with pytest.raises(InvalidFileError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "not a valid" in error_msg or "format validation failed" in error_msg

    def test_validate_template_path_returns_absolute(self, tmp_path: Path) -> None:
        """Test that validation returns absolute path."""
        # Create a valid PPTX file
        template_path = tmp_path / "template.pptx"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")

        # Pass relative path

        os.chdir(tmp_path.parent)
        relative_path = f"{tmp_path.name}/template.pptx"

        result = validate_template_path(relative_path)

        # Should return absolute path
        assert result.is_absolute()
        assert result.name == "template.pptx"

    def test_validate_template_path_unreadable(self, tmp_path: Path) -> None:
        """Test validation fails for unreadable template file."""

        if sys.platform == "win32":
            pytest.skip("Permission testing not reliable on Windows")

        # Create a valid PPTX file
        template_path = tmp_path / "unreadable.pptx"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "<root>" + "x" * 987 + "</root>")

        # Remove read permission

        template_path.chmod(stat.S_IWUSR)  # Write-only

        try:
            with pytest.raises((InvalidFileError, PermissionError)) as exc_info:
                validate_template_path(str(template_path))

            if isinstance(exc_info.value, InvalidFileError):
                error_msg = str(exc_info.value).lower()
                assert "validation failed" in error_msg or "cannot" in error_msg
        finally:
            # Restore permissions for cleanup
            template_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_validate_template_path_rejects_billion_laughs(self, tmp_path: Path) -> None:
        """Test validation fails for template with billion laughs attack."""
        # Billion laughs attack XML
        malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<lolz>&lol4;</lolz>"""

        template_path = tmp_path / "malicious_template.pptx"
        with zipfile.ZipFile(template_path, "w") as zf:
            zf.writestr("[Content_Types].xml", malicious_xml)
            zf.writestr("ppt/presentation.xml", '<?xml version="1.0"?><presentation/>')

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "xml security validation failed" in error_msg or "entity" in error_msg

    def test_validate_template_path_rejects_xxe_attack(self, tmp_path: Path) -> None:
        """Test validation fails for template with XXE attack."""
        # XXE attack XML
        xxe_xml = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>"""

        template_path = tmp_path / "xxe_template.pptx"
        with zipfile.ZipFile(template_path, "w") as zf:
            zf.writestr("[Content_Types].xml", xxe_xml)
            zf.writestr("ppt/presentation.xml", '<?xml version="1.0"?><presentation/>')

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert (
            "xml security validation failed" in error_msg
            or "entity" in error_msg
            or "external" in error_msg
        )
