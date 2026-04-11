# pyright: ignore[reportAttributeAccessIssue, reportUnknownParameterType, reportUnknownMemberType, reportMissingParameterType, reportUnusedVariable]
"""
Unit tests for template validation script.

PLAN B EXECUTION:
python-pptx cannot create custom slide layouts programmatically.
This test file validates the manual creation instruction/validation functionality.

See design.md Section 8.3.4 for Plan B details.
"""

from pathlib import Path

import pytest


class TestTemplateValidationScript:
    """Tests for template validation and manual creation instructions."""

    def test_generate_data_template_detects_missing_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that script detects when data-template.pptx doesn't exist."""
        from scripts.generate_templates import generate_data_template

        output_path = tmp_path / "data-template.pptx"

        generate_data_template(str(output_path))

        # Should log warning about missing file
        assert "data-template.pptx does NOT exist" in caplog.text
        assert "MANUAL ACTION REQUIRED" in caplog.text

    def test_generate_smartart_template_detects_missing_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that script detects when smartart-template.pptx doesn't exist."""
        from scripts.generate_templates import generate_smartart_template

        output_path = tmp_path / "smartart-template.pptx"

        generate_smartart_template(str(output_path))

        # Should log warning about missing file
        assert "smartart-template.pptx does NOT exist" in caplog.text
        assert "MANUAL ACTION REQUIRED" in caplog.text

    def test_validation_uses_existing_templates(self, tmp_path: Path) -> None:
        """Test that script can validate existing templates."""
        # Copy existing basic-template.pptx to test location
        import shutil

        from scripts.generate_templates import generate_data_template

        basic_template = Path("templates/basic-template.pptx")
        if basic_template.exists():
            output_path = tmp_path / "data-template.pptx"
            shutil.copy(basic_template, output_path)

            # Should detect template exists (even if layouts don't match spec)
            generate_data_template(str(output_path))
            # No assertion - just verifying it doesn't crash


class TestManualCreationDocumentation:
    """Tests that verify manual creation instructions are clear."""

    def test_data_template_instructions_include_required_layouts(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that manual creation instructions list all required layouts."""
        from scripts.generate_templates import generate_data_template

        output_path = tmp_path / "nonexistent.pptx"
        generate_data_template(str(output_path))

        # Should mention all 4 required layouts
        assert "Chart" in caplog.text
        assert "Table" in caplog.text
        assert "Data Analysis" in caplog.text
        assert "Two Column Data" in caplog.text

    def test_smartart_template_instructions_include_required_layouts(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that manual creation instructions list all required SmartArt layouts."""
        from scripts.generate_templates import generate_smartart_template

        output_path = tmp_path / "nonexistent.pptx"
        generate_smartart_template(str(output_path))

        # Should mention all 4 required SmartArt layouts
        assert "Process Flow" in caplog.text
        assert "Hierarchy" in caplog.text
        assert "Cycle" in caplog.text
        assert "Relationship" in caplog.text


class TestMainFunction:
    """Tests for main CLI entry point."""

    def test_main_provides_instructions_for_both_templates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that main() provides instructions for both templates."""
        from scripts.generate_templates import main

        # Mock the template path to use tmp_path
        monkeypatch.setattr("scripts.generate_templates.TEMPLATES_DIR", tmp_path)

        main()

        # Should check both templates
        assert "data-template.pptx" in caplog.text
        assert "smartart-template.pptx" in caplog.text

    def test_main_explains_plan_b_execution(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that main() explains Plan B (manual creation)."""
        from scripts.generate_templates import main

        monkeypatch.setattr("scripts.generate_templates.TEMPLATES_DIR", tmp_path)

        main()

        # Should mention manual action requirement (Plan B execution)
        assert "MANUAL ACTION REQUIRED" in caplog.text
        assert "Open Microsoft PowerPoint" in caplog.text


@pytest.mark.skipif(
    not Path("templates/basic-template.pptx").exists(),
    reason="Requires existing template for parser compatibility test",
)
class TestTemplateParserCompatibility:
    """Tests that existing templates can be parsed (Task 3.5)."""

    def test_existing_templates_parseable_by_template_parser(self):
        """Test that existing templates can be parsed by template_parser."""
        from pptx_agent.template_parser import TemplateParser

        # Test with existing basic-template.pptx
        template_path = "templates/basic-template.pptx"

        parser = TemplateParser()
        manifest = parser.parse_template(template_path)

        # Verify manifest has expected structure
        assert manifest is not None
        assert len(manifest.layouts) > 0
        assert manifest.template_path == str(Path(template_path).resolve())
