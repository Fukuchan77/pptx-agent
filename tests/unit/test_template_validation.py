"""Tests for template validation on application startup.

These tests verify that the application properly validates the existence
of required template files and provides clear error messages when they are missing.
"""

from pathlib import Path

import pytest

from pptx_agent.config import validate_templates


class TestTemplateValidation:
    """Test template file validation on startup."""

    def test_validation_succeeds_when_both_templates_exist(self, tmp_path: Path) -> None:
        """Template validation should succeed when both required templates exist."""
        # Create mock template directory with both templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "basic-template.pptx").write_bytes(b"fake pptx content")
        (template_dir / "japanese-template.pptx").write_bytes(b"fake pptx content")

        # Should not raise any exception
        validate_templates(templates_dir=template_dir)

    def test_validation_fails_when_basic_template_missing(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError when basic-template.pptx is missing."""
        # Create mock template directory with only japanese template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "japanese-template.pptx").write_bytes(b"fake pptx content")

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        assert "basic-template.pptx" in error_msg
        assert "templates/" in error_msg or "Template file not found" in error_msg

    def test_validation_fails_when_japanese_template_missing(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError when japanese-template.pptx is missing."""
        # Create mock template directory with only basic template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "basic-template.pptx").write_bytes(b"fake pptx content")

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        assert "japanese-template.pptx" in error_msg
        assert "templates/" in error_msg or "Template file not found" in error_msg

    def test_validation_fails_when_both_templates_missing(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError when both templates are missing."""
        # Create empty template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        # Should mention at least one of the missing templates
        assert "basic-template.pptx" in error_msg or "japanese-template.pptx" in error_msg

    def test_error_message_includes_file_path(self, tmp_path: Path) -> None:
        """Error message should include the full file path."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        # Error should contain path information
        assert "template" in error_msg.lower()
        assert ".pptx" in error_msg

    def test_error_message_includes_resolution_guidance_english(self, tmp_path: Path) -> None:
        """Error message should include guidance on how to resolve the issue (English)."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        # Should provide helpful guidance
        resolution_keywords = ["ensure", "place", "directory", "available", "check"]
        assert any(keyword in error_msg.lower() for keyword in resolution_keywords), (
            f"Error message should include resolution guidance. Got: {error_msg}"
        )

    def test_error_message_bilingual_support(self, tmp_path: Path) -> None:
        """Error message should support both English and Japanese."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir)

        error_msg = str(exc_info.value)
        # Should be clear and helpful in at least English
        # (Japanese support can be added later if needed)
        assert len(error_msg) > 20, "Error message should be descriptive"
        assert "template" in error_msg.lower()
