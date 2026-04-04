"""Tests for enhanced security validation features."""

import zipfile
from pathlib import Path

import pytest

from pptx_agent.validators.exceptions import InvalidFileError, SecurityValidationError
from pptx_agent.validators.file_validator import (
    validate_file_extension,
    validate_no_symlinks,
    validate_pptx_structure,
)
from pptx_agent.validators.input_validator import sanitize_dangerous_characters


class TestFileExtensionValidation:
    """Tests for file extension whitelist validation."""

    def test_valid_pptx_extension(self, tmp_path: Path) -> None:
        """Should accept valid .pptx extension."""
        file_path = tmp_path / "presentation.pptx"
        file_path.touch()

        # Should not raise exception
        validate_file_extension(file_path)

    def test_valid_pptx_case_insensitive(self, tmp_path: Path) -> None:
        """Should accept .PPTX extension (case-insensitive)."""
        file_path = tmp_path / "presentation.PPTX"
        file_path.touch()

        # Should not raise exception
        validate_file_extension(file_path)

    def test_invalid_extension_exe(self, tmp_path: Path) -> None:
        """Should reject .exe files."""
        file_path = tmp_path / "malware.exe"
        file_path.touch()

        with pytest.raises(InvalidFileError) as exc_info:
            validate_file_extension(file_path)

        assert (
            "extension validation failed" in str(exc_info.value).lower()
            or "not allowed" in str(exc_info.value).lower()
        )

    def test_invalid_extension_double(self, tmp_path: Path) -> None:
        """Should reject double extensions like .pptx.exe."""
        file_path = tmp_path / "fake.pptx.exe"
        file_path.touch()

        with pytest.raises(InvalidFileError) as exc_info:
            validate_file_extension(file_path)

        assert (
            "extension validation failed" in str(exc_info.value).lower()
            or "not allowed" in str(exc_info.value).lower()
        )

    def test_invalid_no_extension(self, tmp_path: Path) -> None:
        """Should reject files without extension."""
        file_path = tmp_path / "noextension"
        file_path.touch()

        with pytest.raises(InvalidFileError) as exc_info:
            validate_file_extension(file_path)

        assert (
            "extension validation failed" in str(exc_info.value).lower()
            or "extension" in str(exc_info.value).lower()
        )


class TestSymlinkValidation:
    """Tests for symlink validation."""

    def test_normal_file_no_symlink(self, tmp_path: Path) -> None:
        """Should accept normal files (not symlinks)."""
        file_path = tmp_path / "normal.pptx"
        file_path.touch()

        # Should not raise exception
        validate_no_symlinks(file_path)

    def test_reject_symlink_file(self, tmp_path: Path) -> None:
        """Should reject symlink files."""
        real_file = tmp_path / "real.pptx"
        real_file.touch()

        symlink = tmp_path / "link.pptx"
        symlink.symlink_to(real_file)

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_no_symlinks(symlink)

        assert (
            "symlink validation failed" in str(exc_info.value).lower()
            or "symlink" in str(exc_info.value).lower()
        )

    def test_reject_symlink_in_path(self, tmp_path: Path) -> None:
        """Should reject files in symlinked directories."""
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()

        symlink_dir = tmp_path / "link_dir"
        symlink_dir.symlink_to(real_dir)

        file_in_symlink = symlink_dir / "file.pptx"
        file_in_symlink.touch()

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_no_symlinks(file_in_symlink)

        assert (
            "symlink validation failed" in str(exc_info.value).lower()
            or "symlink" in str(exc_info.value).lower()
        )


class TestPptxStructureValidation:
    """Tests for PPTX structure validation (XML bomb protection)."""

    def test_normal_pptx_structure(self, tmp_path: Path) -> None:
        """Should accept normal PPTX with standard XML."""
        pptx_path = tmp_path / "normal.pptx"
        with zipfile.ZipFile(pptx_path, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
            zf.writestr("ppt/presentation.xml", '<?xml version="1.0"?><presentation/>')

        # Should not raise exception
        validate_pptx_structure(pptx_path)

    def test_reject_billion_laughs_attack(self, tmp_path: Path) -> None:
        """Should reject XML with billion laughs attack (entity expansion)."""
        pptx_path = tmp_path / "malicious.pptx"

        # Billion laughs attack XML
        malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<lolz>&lol4;</lolz>"""

        with zipfile.ZipFile(pptx_path, "w") as zf:
            zf.writestr("[Content_Types].xml", malicious_xml)

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_pptx_structure(pptx_path)

        assert (
            "xml security validation failed" in str(exc_info.value).lower()
            or "entity" in str(exc_info.value).lower()
        )

    def test_reject_external_entity_reference(self, tmp_path: Path) -> None:
        """Should reject XML with external entity references."""
        pptx_path = tmp_path / "xxe.pptx"

        # XXE attack XML
        xxe_xml = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>"""

        with zipfile.ZipFile(pptx_path, "w") as zf:
            zf.writestr("[Content_Types].xml", xxe_xml)

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_pptx_structure(pptx_path)

        assert (
            "xml security validation failed" in str(exc_info.value).lower()
            or "entity" in str(exc_info.value).lower()
            or "external" in str(exc_info.value).lower()
        )

    def test_reject_excessive_entity_expansion(self, tmp_path: Path) -> None:
        """Should reject XML with excessive entity expansion depth."""
        pptx_path = tmp_path / "expansion.pptx"

        # Deep entity expansion
        deep_expansion = """<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY a "aaaaaaaaaa">
  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
]>
<root>&c;</root>"""

        with zipfile.ZipFile(pptx_path, "w") as zf:
            zf.writestr("ppt/slides/slide1.xml", deep_expansion)

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_pptx_structure(pptx_path)

        assert (
            "xml security validation failed" in str(exc_info.value).lower()
            or "entity" in str(exc_info.value).lower()
        )


class TestDangerousCharacterSanitization:
    """Tests for dangerous character sanitization in input."""

    def test_clean_input_unchanged(self) -> None:
        """Should not modify clean input text."""
        text = "This is a normal presentation about business strategy."
        result = sanitize_dangerous_characters(text)
        assert result == text

    def test_remove_null_bytes(self) -> None:
        """Should remove null bytes from input."""
        text = "Normal text\x00with null byte"
        result = sanitize_dangerous_characters(text)
        assert "\x00" not in result
        assert "Normal text" in result
        assert "with null byte" in result

    def test_remove_control_characters(self) -> None:
        """Should remove dangerous control characters."""
        text = "Text with\x01control\x02characters\x03here"
        result = sanitize_dangerous_characters(text)
        # Control characters should be removed
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result
        assert "Text with" in result

    def test_preserve_common_whitespace(self) -> None:
        """Should preserve common whitespace (space, tab, newline)."""
        text = "Line 1\nLine 2\tTabbed\r\nLine 3"
        result = sanitize_dangerous_characters(text)
        assert "\n" in result
        assert "\t" in result

    def test_remove_unicode_bidi_override(self) -> None:
        """Should remove Unicode bidirectional override characters."""
        # These can be used for spoofing
        text = "Normal\u202etext\u202dhere"
        result = sanitize_dangerous_characters(text)
        assert "\u202e" not in result
        assert "\u202d" not in result

    def test_remove_zero_width_characters(self) -> None:
        """Should remove zero-width characters used for obfuscation."""
        text = "Text\u200bwith\u200czero\u200dwidth"
        result = sanitize_dangerous_characters(text)
        assert "\u200b" not in result  # Zero-width space
        assert "\u200c" not in result  # Zero-width non-joiner
        assert "\u200d" not in result  # Zero-width joiner

    def test_normalize_whitespace(self) -> None:
        """Should normalize excessive whitespace."""
        text = "Text    with     multiple     spaces"
        result = sanitize_dangerous_characters(text)
        # Should not have more than 2 consecutive spaces
        assert "    " not in result

    def test_japanese_text_preserved(self) -> None:
        """Should preserve Japanese text during sanitization."""
        text = "これは日本語のテキストです。"
        result = sanitize_dangerous_characters(text)
        assert result == text

    def test_mixed_content_sanitization(self) -> None:
        """Should sanitize mixed content with various threats."""
        text = "Normal text\x00null\u202ebidi\x01control"
        result = sanitize_dangerous_characters(text)
        assert "\x00" not in result
        assert "\u202e" not in result
        assert "\x01" not in result
        assert "Normal text" in result
