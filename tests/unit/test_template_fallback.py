"""Tests for template fallback and auto-generation functionality.

These tests verify that the application can automatically generate missing
templates when the auto_generate option is enabled.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from pptx_agent.templates import validate_templates


class TestTemplateFallback:
    """Test template auto-generation fallback mechanism."""

    def test_auto_generate_disabled_by_default(self, tmp_path: Path) -> None:
        """Auto-generation should be disabled by default when templates are missing."""
        # Create empty template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Should raise FileNotFoundError without auto-generation
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_templates(templates_dir=template_dir, auto_generate=False)

        error_msg = str(exc_info.value)
        assert "basic-template.pptx" in error_msg or "japanese-template.pptx" in error_msg

    def test_auto_generate_creates_missing_basic_template(self, tmp_path: Path) -> None:
        """Should auto-generate basic-template.pptx when missing and auto_generate=True."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        # Only create japanese template
        (template_dir / "japanese-template.pptx").write_bytes(b"fake pptx")

        # Mock the template generation function
        with patch("pptx_agent.templates.generate_basic_template") as mock_gen:
            mock_gen.return_value = None  # Success

            # Should succeed by generating the missing template
            validate_templates(templates_dir=template_dir, auto_generate=True)

            # Verify generation was called for basic template
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args[0]
            assert "basic-template.pptx" in str(call_args[0])

    def test_auto_generate_creates_missing_japanese_template(self, tmp_path: Path) -> None:
        """Should auto-generate japanese-template.pptx when missing and auto_generate=True."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        # Only create basic template
        (template_dir / "basic-template.pptx").write_bytes(b"fake pptx")

        # Mock the template generation function
        with patch("pptx_agent.templates.generate_japanese_template") as mock_gen:
            mock_gen.return_value = None  # Success

            # Should succeed by generating the missing template
            validate_templates(templates_dir=template_dir, auto_generate=True)

            # Verify generation was called for japanese template
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args[0]
            assert "japanese-template.pptx" in str(call_args[0])

    def test_auto_generate_creates_both_missing_templates(self, tmp_path: Path) -> None:
        """Should auto-generate both templates when both are missing."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Mock both generation functions
        with (
            patch("pptx_agent.templates.generate_basic_template") as mock_basic,
            patch("pptx_agent.templates.generate_japanese_template") as mock_japanese,
        ):
            mock_basic.return_value = None
            mock_japanese.return_value = None

            # Should succeed by generating both templates
            validate_templates(templates_dir=template_dir, auto_generate=True)

            # Verify both were called
            assert mock_basic.call_count == 1
            assert mock_japanese.call_count == 1

    def test_auto_generate_fails_with_clear_error_message(self, tmp_path: Path) -> None:
        """Should provide clear error message when auto-generation fails."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Mock generation function to raise an exception
        with patch("pptx_agent.templates.generate_basic_template") as mock_gen:
            mock_gen.side_effect = OSError("Disk full")

            # Should raise an error with helpful message
            with pytest.raises(RuntimeError) as exc_info:
                validate_templates(templates_dir=template_dir, auto_generate=True)

            error_msg = str(exc_info.value)
            assert "Failed to generate" in error_msg or "generation failed" in error_msg.lower()
            assert "basic-template.pptx" in error_msg

    def test_no_generation_when_all_templates_exist(self, tmp_path: Path) -> None:
        """Should not attempt generation when all templates already exist."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "basic-template.pptx").write_bytes(b"fake pptx")
        (template_dir / "japanese-template.pptx").write_bytes(b"fake pptx")

        # Mock generation functions - they should not be called
        with (
            patch("pptx_agent.templates.generate_basic_template") as mock_basic,
            patch("pptx_agent.templates.generate_japanese_template") as mock_japanese,
        ):
            # Should succeed without calling generation
            validate_templates(templates_dir=template_dir, auto_generate=True)

            # Verify no generation was attempted
            mock_basic.assert_not_called()
            mock_japanese.assert_not_called()

    def test_auto_generate_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """Should create template directory if it doesn't exist when auto_generate=True."""
        template_dir = tmp_path / "templates"
        # Don't create the directory

        # Mock generation functions
        with (
            patch("pptx_agent.templates.generate_basic_template") as mock_basic,
            patch("pptx_agent.templates.generate_japanese_template") as mock_japanese,
        ):
            mock_basic.return_value = None
            mock_japanese.return_value = None

            # Should succeed by creating directory and generating templates
            validate_templates(templates_dir=template_dir, auto_generate=True)

            # Verify directory was created
            assert template_dir.exists()
            assert template_dir.is_dir()
