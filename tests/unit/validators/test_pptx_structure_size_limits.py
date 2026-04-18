"""Unit tests for PPTX structure validation size limits (Task 6)."""

import zipfile
from pathlib import Path

import pytest

from pptx_agent.validators.exceptions import FileSizeLimitError, SecurityValidationError
from pptx_agent.validators.file_validator import validate_pptx_structure


class TestPptxStructureSizeLimits:
    """Test cases for per-entry size limits in validate_pptx_structure.

    These tests verify that validate_pptx_structure() rejects oversized XML
    entries BEFORE calling defusedxml parser, preventing memory exhaustion.

    Requirements: 2.4.1, 2.4.2, 2.4.3, 2.4.4 from spec.md
    """

    def test_rejects_oversized_xml_entry_before_defusedxml(self, tmp_path: Path) -> None:
        """Test that oversized XML entry is rejected before defusedxml parsing.

        Requirement 2.4.1, 2.4.4: Per-entry size limit (10MB) enforced before
        defusedxml parser is called.
        """
        pptx_path = tmp_path / "oversized_entry.pptx"

        # Create PPTX with single 11MB XML entry (exceeds 10MB limit)
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            # Use ZIP_STORED to avoid compression issues
            oversized_content = (
                "<?xml version='1.0'?><root>" + ("x" * (11 * 1024 * 1024)) + "</root>"
            )
            zf.writestr("ppt/slides/slide1.xml", oversized_content)
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')

        # Should raise FileSizeLimitError for entry size, not SecurityValidationError
        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_structure(pptx_path)

        error_msg = str(exc_info.value).lower()
        assert "entry" in error_msg or "size" in error_msg
        assert "10" in str(exc_info.value) or "limit" in error_msg

    def test_rejects_very_large_xml_entry(self, tmp_path: Path) -> None:
        """Test rejection of extremely large XML entry (400MB).

        Requirement 2.4.1: Validates that validation fails efficiently
        without loading full 400MB content into memory.
        """
        pptx_path = tmp_path / "huge_entry.pptx"

        # Create PPTX with 400MB XML entry
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            # Create 400MB entry - this should be rejected by size check
            huge_content = "<?xml version='1.0'?><root>" + ("x" * (400 * 1024 * 1024)) + "</root>"
            zf.writestr("ppt/slides/huge.xml", huge_content)
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')

        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_structure(pptx_path)

        error_msg = str(exc_info.value).lower()
        assert "entry" in error_msg or "size" in error_msg

    def test_detects_compression_anomaly_zero_compressed_size(self, tmp_path: Path) -> None:
        """Test detection of compression anomaly: compress_size=0 but file_size>0.

        Requirement 2.4.2: Detects suspicious compression patterns that may
        indicate zip bomb or corrupted archive.
        """
        pptx_path = tmp_path / "compression_anomaly.pptx"

        # Manually create a ZIP with compression anomaly
        with zipfile.ZipFile(pptx_path, "w") as zf:
            # Add normal entry first
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')

        # Manually modify the ZIP to create anomaly
        # This is tricky - we need to create a ZIP entry with compress_size=0 but file_size>0
        # For now, we'll test with a real scenario if possible
        # Note: This test may need adjustment based on how zipfile handles this

        # Create entry info with anomaly using ZipInfo
        with zipfile.ZipFile(pptx_path, "a") as zf:
            info = zipfile.ZipInfo("ppt/slides/anomaly.xml")
            info.compress_size = 0
            info.file_size = 1024  # 1KB uncompressed but 0 compressed - suspicious!
            info.compress_type = zipfile.ZIP_STORED
            # Note: Writing this might not work as expected, may need alternative approach
            try:
                zf.writestr(info, "x" * 1024)
            except Exception:
                pytest.skip("Cannot create compression anomaly test file with this zipfile API")

        # Should detect the anomaly and raise an error
        with pytest.raises((FileSizeLimitError, SecurityValidationError)) as exc_info:
            validate_pptx_structure(pptx_path)

        error_msg = str(exc_info.value).lower()
        assert "compress" in error_msg or "anomaly" in error_msg or "suspicious" in error_msg

    def test_normal_xml_entry_passes_validation(self, tmp_path: Path) -> None:
        """Test that normal-sized XML entries pass validation.

        Requirement: Verify that legitimate PPTX files are not rejected.
        """
        pptx_path = tmp_path / "normal.pptx"

        # Create PPTX with normal-sized entries (well under 10MB)
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
            zf.writestr("ppt/presentation.xml", '<?xml version="1.0"?><presentation/>')
            # Add a 1MB XML entry (well under 10MB limit)
            zf.writestr(
                "ppt/slides/slide1.xml",
                '<?xml version="1.0"?><slide>' + ("x" * (1024 * 1024)) + "</slide>",
            )

        # Should not raise any exception
        validate_pptx_structure(pptx_path)

    def test_entry_at_size_limit_passes(self, tmp_path: Path) -> None:
        """Test that XML entry exactly at 10MB limit passes validation.

        Requirement: Verify boundary condition - 10MB should pass.
        """
        pptx_path = tmp_path / "at_limit.pptx"

        # Create PPTX with XML entry at exactly 10MB
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
            # Exactly 10MB = 10 * 1024 * 1024 bytes
            content = '<?xml version="1.0"?><root>' + ("x" * (10 * 1024 * 1024 - 40)) + "</root>"
            zf.writestr("ppt/slides/slide1.xml", content)

        # Should not raise exception - exactly at limit should pass
        validate_pptx_structure(pptx_path)

    def test_entry_over_limit_by_one_byte_fails(self, tmp_path: Path) -> None:
        """Test that XML entry over 10MB limit by one byte fails validation.

        Requirement: Verify boundary condition - 10MB + 1 byte should fail.
        """
        pptx_path = tmp_path / "over_limit.pptx"

        # Create PPTX with XML entry at 10MB + 1 byte
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
            # 10MB + 1 byte
            content = '<?xml version="1.0"?><root>' + ("x" * (10 * 1024 * 1024 + 1)) + "</root>"
            zf.writestr("ppt/slides/slide1.xml", content)

        with pytest.raises(FileSizeLimitError) as exc_info:
            validate_pptx_structure(pptx_path)

        error_msg = str(exc_info.value).lower()
        assert "entry" in error_msg or "size" in error_msg

    def test_multiple_entries_under_limit_pass(self, tmp_path: Path) -> None:
        """Test that multiple entries each under 10MB pass validation.

        Requirement: Verify per-entry limit is enforced individually.
        """
        pptx_path = tmp_path / "multiple_entries.pptx"

        # Create PPTX with multiple entries, each under 10MB
        with zipfile.ZipFile(pptx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
            # Add 5 entries of 8MB each (40MB total, but each individual entry under 10MB)
            for i in range(5):
                content = (
                    f'<?xml version="1.0"?><slide>{i}' + ("x" * (8 * 1024 * 1024)) + "</slide>"
                )
                zf.writestr(f"ppt/slides/slide{i}.xml", content)

        # Should pass - each entry is under 10MB even though total is large
        validate_pptx_structure(pptx_path)
