"""Unit tests for file validator module."""

import zipfile
from pathlib import Path

import pytest

from pptx_agent.validators.exceptions import (
    CompressionRatioError,
    FileSizeLimitError,
    InvalidFileError,
    PathTraversalError,
)
from pptx_agent.validators.file_validator import (
    validate_output_path,
    validate_pptx_file,
    validate_template_path,
)


class TestValidatePptxFile:
    """Test cases for validate_pptx_file function."""

    def test_validate_pptx_file_normal(self, tmp_path: Path) -> None:
        """Test validation of normal PPTX file."""
        # Create a small valid ZIP file
        pptx_path = tmp_path / "normal.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "x" * 1000)  # 1KB uncompressed
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
        pptx_path = tmp_path / "compressed.pptx"
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            # Create highly compressible data that results in ratio > 100
            # Use 50MB of repeating data that compresses to < 500KB
            data = "a" * (50 * 1024 * 1024)
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


class TestValidateOutputPath:
    """Test cases for validate_output_path function."""

    def test_validate_output_path_normal(self, tmp_path: Path) -> None:
        """Test validation of normal output path."""
        base_dir = tmp_path / "output"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Normal path within base_dir
        output_path = "test.pptx"
        result = validate_output_path(output_path, str(base_dir))

        # Should return resolved path inside base_dir
        assert result.is_absolute()
        assert result.parent == base_dir

    def test_validate_output_path_relative(self, tmp_path: Path) -> None:
        """Test validation with explicit relative path."""
        base_dir = tmp_path / "output"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Relative path with ./
        output_path = "./subfolder/test.pptx"
        result = validate_output_path(output_path, str(base_dir))

        # Should return resolved path inside base_dir
        assert result.is_absolute()
        assert str(base_dir) in str(result)

    def test_validate_output_path_traversal_attack(self, tmp_path: Path) -> None:
        """Test validation blocks path traversal attack."""
        base_dir = tmp_path / "output"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Path traversal attack using ../
        output_path = "../../../etc/passwd"

        with pytest.raises(PathTraversalError) as exc_info:
            validate_output_path(output_path, str(base_dir))

        error_msg = str(exc_info.value).lower()
        assert "traversal detected" in error_msg or "outside" in error_msg

    def test_validate_output_path_outside_base_dir(self, tmp_path: Path) -> None:
        """Test validation blocks paths outside base_dir."""
        base_dir = tmp_path / "output"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Try to write to a completely different location
        other_dir = tmp_path / "other"
        other_dir.mkdir(parents=True, exist_ok=True)

        output_path = str(other_dir / "test.pptx")

        with pytest.raises(PathTraversalError) as exc_info:
            validate_output_path(output_path, str(base_dir))

        assert (
            "outside" in str(exc_info.value).lower() or "traversal" in str(exc_info.value).lower()
        )

    def test_validate_output_path_custom_base_dir(self, tmp_path: Path) -> None:
        """Test validation with custom base_dir."""
        custom_base = tmp_path / "custom" / "output"
        custom_base.mkdir(parents=True, exist_ok=True)

        output_path = "presentation.pptx"
        result = validate_output_path(output_path, str(custom_base))

        # Should be within custom base directory
        assert result.is_absolute()
        assert str(custom_base) in str(result)
        assert result.name == "presentation.pptx"

    def test_validate_output_path_absolute_inside(self, tmp_path: Path) -> None:
        """Test validation allows absolute path if it's inside base_dir."""
        base_dir = tmp_path / "output"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Absolute path but inside base_dir
        subfolder = base_dir / "subfolder"
        output_path = str(subfolder / "test.pptx")

        result = validate_output_path(output_path, str(base_dir))

        # Should return the same path since it's inside base_dir
        assert result.is_absolute()
        assert str(base_dir) in str(result)
        assert result.name == "test.pptx"

    def test_validate_output_path_default_base_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation uses default base_dir when not specified."""
        # Change working directory to tmp_path
        monkeypatch.chdir(tmp_path)

        # Create default output directory
        default_output = tmp_path / "output"
        default_output.mkdir(parents=True, exist_ok=True)

        output_path = "test.pptx"
        result = validate_output_path(output_path)

        # Should use default ./output directory
        assert result.is_absolute()
        assert "output" in str(result)


class TestValidateTemplatePath:
    """Test cases for validate_template_path function."""

    def test_validate_template_path_valid(self, tmp_path: Path) -> None:
        """Test validation of valid template path."""
        # Create a valid PPTX file
        template_path = tmp_path / "valid_template.pptx"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "x" * 1000)
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
            zf.writestr("content.xml", "x" * 1000)

        with pytest.raises(InvalidFileError) as exc_info:
            validate_template_path(str(template_path))

        error_msg = str(exc_info.value).lower()
        assert "extension validation failed" in error_msg

    def test_validate_template_path_symlink(self, tmp_path: Path) -> None:
        """Test validation fails for symlink to template file."""
        # Create a valid PPTX file
        actual_file = tmp_path / "actual_template.pptx"
        with zipfile.ZipFile(actual_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "x" * 1000)

        # Create a symlink to it
        symlink_path = tmp_path / "symlink_template.pptx"
        try:
            symlink_path.symlink_to(actual_file)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        from pptx_agent.validators.exceptions import SecurityValidationError

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
            zf.writestr("content.xml", "x" * 1000)

        # Pass relative path
        import os

        os.chdir(tmp_path.parent)
        relative_path = f"{tmp_path.name}/template.pptx"

        result = validate_template_path(relative_path)

        # Should return absolute path
        assert result.is_absolute()
        assert result.name == "template.pptx"

    def test_validate_template_path_unreadable(self, tmp_path: Path) -> None:
        """Test validation fails for unreadable template file."""
        import sys

        if sys.platform == "win32":
            pytest.skip("Permission testing not reliable on Windows")

        # Create a valid PPTX file
        template_path = tmp_path / "unreadable.pptx"
        with zipfile.ZipFile(template_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", "x" * 1000)

        # Remove read permission
        import stat

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
