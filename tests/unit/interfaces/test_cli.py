"""Unit tests for CLI argument parsing.

Tests verify that CLI parsers correctly handle arguments, flags, and validation
for analyze-template and qa commands.
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pptx_agent.interfaces.cli import (
    analyze_template_command,
    create_analyze_template_parser,
    create_qa_parser,
    qa_command,
)


class TestAnalyzeTemplateParser:
    """Test suite for analyze-template command parser."""

    def test_parser_creation(self) -> None:
        """Test that parser is created with correct configuration."""
        parser = create_analyze_template_parser()
        assert parser.prog == "pptx-agent analyze-template"
        assert parser.description is not None
        assert "Analyze PowerPoint template" in parser.description

    def test_required_template_argument(self) -> None:
        """Test that template argument is required."""
        parser = create_analyze_template_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_template_argument_parsing(self) -> None:
        """Test parsing of template argument."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx"])
        assert args.template == "template.pptx"

    def test_output_argument_parsing(self) -> None:
        """Test parsing of output argument."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "-o", "manifest.json"])
        assert args.output == "manifest.json"

    def test_language_argument_parsing(self) -> None:
        """Test parsing of language argument."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "-l", "ja"])
        assert args.language == "ja"

    def test_language_default_value(self) -> None:
        """Test that language defaults to 'en'."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx"])
        assert args.language == "en"

    def test_language_choices_validation(self) -> None:
        """Test that invalid language choices are rejected."""
        parser = create_analyze_template_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-t", "template.pptx", "-l", "invalid"])

    def test_cache_stats_flag(self) -> None:
        """Test parsing of cache-stats flag."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "--cache-stats"])
        assert args.cache_stats is True

    def test_no_cache_flag(self) -> None:
        """Test parsing of no-cache flag."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "--no-cache"])
        assert args.no_cache is True

    def test_invalidate_cache_flag(self) -> None:
        """Test parsing of invalidate-cache flag."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "--invalidate-cache"])
        assert args.invalidate_cache is True

    def test_verbose_flag(self) -> None:
        """Test parsing of verbose flag."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(["-t", "template.pptx", "--verbose"])
        assert args.verbose is True

    def test_all_arguments_together(self) -> None:
        """Test parsing all arguments together."""
        parser = create_analyze_template_parser()
        args = parser.parse_args(
            [
                "-t",
                "template.pptx",
                "-o",
                "manifest.json",
                "-l",
                "ja",
                "--cache-stats",
                "--verbose",
            ]
        )
        assert args.template == "template.pptx"
        assert args.output == "manifest.json"
        assert args.language == "ja"
        assert args.cache_stats is True
        assert args.verbose is True


class TestQAParser:
    """Test suite for qa command parser."""

    def test_parser_creation(self) -> None:
        """Test that parser is created with correct configuration."""
        parser = create_qa_parser()
        assert parser.prog == "pptx-agent qa"
        assert parser.description is not None
        assert "quality assurance" in parser.description.lower()

    def test_required_input_argument(self) -> None:
        """Test that input argument is required."""
        parser = create_qa_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_input_argument_parsing(self) -> None:
        """Test parsing of input argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx"])
        assert args.input == "presentation.pptx"

    def test_template_argument_parsing(self) -> None:
        """Test parsing of template argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "-t", "template.pptx"])
        assert args.template == "template.pptx"

    def test_report_argument_parsing(self) -> None:
        """Test parsing of report argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "-r", "report.json"])
        assert args.report == "report.json"

    def test_format_argument_parsing(self) -> None:
        """Test parsing of format argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "-f", "markdown"])
        assert args.format == "markdown"

    def test_format_default_value(self) -> None:
        """Test that format defaults to 'json'."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx"])
        assert args.format == "json"

    def test_format_choices_validation(self) -> None:
        """Test that invalid format choices are rejected."""
        parser = create_qa_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "presentation.pptx", "-f", "invalid"])

    def test_language_argument_parsing(self) -> None:
        """Test parsing of language argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "-l", "ja"])
        assert args.language == "ja"

    def test_language_choices_validation(self) -> None:
        """Test that invalid language choices are rejected."""
        parser = create_qa_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-i", "presentation.pptx", "-l", "invalid"])

    def test_autofix_flag(self) -> None:
        """Test parsing of autofix flag."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "--autofix"])
        assert args.autofix is True

    def test_output_argument_parsing(self) -> None:
        """Test parsing of output argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "-o", "fixed.pptx"])
        assert args.output == "fixed.pptx"

    def test_max_fix_iterations_parsing(self) -> None:
        """Test parsing of max-fix-iterations argument."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "--max-fix-iterations", "5"])
        assert args.max_fix_iterations == 5

    def test_max_fix_iterations_default_value(self) -> None:
        """Test that max-fix-iterations defaults to 3."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx"])
        assert args.max_fix_iterations == 3

    def test_verbose_flag(self) -> None:
        """Test parsing of verbose flag."""
        parser = create_qa_parser()
        args = parser.parse_args(["-i", "presentation.pptx", "--verbose"])
        assert args.verbose is True

    def test_all_arguments_together(self) -> None:
        """Test parsing all arguments together."""
        parser = create_qa_parser()
        args = parser.parse_args(
            [
                "-i",
                "presentation.pptx",
                "-t",
                "template.pptx",
                "-r",
                "report.json",
                "-f",
                "markdown",
                "-l",
                "ja",
                "--autofix",
                "-o",
                "fixed.pptx",
                "--max-fix-iterations",
                "5",
                "--verbose",
            ]
        )
        assert args.input == "presentation.pptx"
        assert args.template == "template.pptx"
        assert args.report == "report.json"
        assert args.format == "markdown"
        assert args.language == "ja"
        assert args.autofix is True
        assert args.output == "fixed.pptx"
        assert args.max_fix_iterations == 5
        assert args.verbose is True


class TestAnalyzeTemplateCommand:
    """Test suite for analyze-template command execution."""

    def test_missing_template_file(self, tmp_path: Path) -> None:
        """Test error handling when template file doesn't exist."""
        args = argparse.Namespace(
            template="nonexistent.pptx",
            output=None,
            language="en",
            cache_stats=False,
            no_cache=False,
            invalidate_cache=False,
            verbose=False,
        )
        exit_code = analyze_template_command(args)
        assert exit_code == 1

    @patch("pptx_agent.interfaces.cli.TemplateParser")
    @patch("pptx_agent.interfaces.cli.ManifestBuilder")
    @patch("pptx_agent.interfaces.cli.CacheManager")
    def test_successful_analysis_without_cache(
        self,
        mock_cache_manager: MagicMock,
        mock_manifest_builder: MagicMock,
        mock_template_parser: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful template analysis without caching."""
        # Create a dummy template file
        template_file = tmp_path / "template.pptx"
        template_file.write_bytes(b"dummy content")

        # Mock the cache manager to return None (cache miss)
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_manifest.return_value = None
        mock_cache_manager.return_value = mock_cache_instance

        # Mock the template parser
        mock_parser_instance = MagicMock()
        mock_template_parser.return_value = mock_parser_instance

        # Mock the manifest builder
        mock_builder_instance = MagicMock()
        mock_manifest = MagicMock()
        mock_manifest.model_dump.return_value = {"template_name": "test"}
        mock_builder_instance.build_manifest.return_value = mock_manifest
        mock_manifest_builder.return_value = mock_builder_instance

        args = argparse.Namespace(
            template=str(template_file),
            output=None,
            language="en",
            cache_stats=False,
            no_cache=False,
            invalidate_cache=False,
            verbose=False,
        )

        exit_code = analyze_template_command(args)
        assert exit_code == 0
        mock_parser_instance.parse_template.assert_called_once()
        mock_builder_instance.build_manifest.assert_called_once()


class TestQACommand:
    """Test suite for qa command execution."""

    def test_missing_input_file(self, tmp_path: Path) -> None:
        """Test error handling when input file doesn't exist."""
        args = argparse.Namespace(
            input="nonexistent.pptx",
            template=None,
            report=None,
            format="json",
            language=None,
            autofix=False,
            output=None,
            max_fix_iterations=3,
            verbose=False,
        )
        exit_code = qa_command(args)
        assert exit_code == 1

    @patch("pptx_agent.interfaces.cli.QAEngine")
    @patch("pptx_agent.interfaces.cli.PresentationWrapper")
    def test_successful_qa_with_no_errors(
        self,
        mock_wrapper: MagicMock,
        mock_qa_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful QA execution with no errors found."""
        # Create a dummy presentation file
        input_file = tmp_path / "presentation.pptx"
        input_file.write_bytes(b"dummy content")

        # Mock the presentation wrapper
        mock_wrapper_instance = MagicMock()
        mock_wrapper.return_value = mock_wrapper_instance

        # Mock the QA engine to return a passing report
        mock_engine_instance = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = True
        mock_report.total_issues = 0
        mock_report.error_count = 0
        mock_report.warning_count = 0
        mock_report.info_count = 0
        mock_report.to_json.return_value = '{"passed": true}'
        mock_engine_instance.validate.return_value = mock_report
        mock_qa_engine.return_value = mock_engine_instance

        args = argparse.Namespace(
            input=str(input_file),
            template=None,
            report=None,
            format="json",
            language=None,
            autofix=False,
            output=None,
            max_fix_iterations=3,
            verbose=False,
        )

        exit_code = qa_command(args)
        assert exit_code == 0
        mock_wrapper_instance.load_template.assert_called_once()
        mock_engine_instance.validate.assert_called_once()

    @patch("pptx_agent.interfaces.cli.QAEngine")
    @patch("pptx_agent.interfaces.cli.PresentationWrapper")
    def test_qa_with_errors_returns_failure_code(
        self,
        mock_wrapper: MagicMock,
        mock_qa_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that QA returns exit code 1 when errors are found."""
        # Create a dummy presentation file
        input_file = tmp_path / "presentation.pptx"
        input_file.write_bytes(b"dummy content")

        # Mock the presentation wrapper
        mock_wrapper_instance = MagicMock()
        mock_wrapper.return_value = mock_wrapper_instance

        # Mock the QA engine to return a failing report
        mock_engine_instance = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = False
        mock_report.total_issues = 3
        mock_report.error_count = 2
        mock_report.warning_count = 1
        mock_report.info_count = 0
        mock_report.to_json.return_value = '{"passed": false}'
        mock_engine_instance.validate.return_value = mock_report
        mock_qa_engine.return_value = mock_engine_instance

        args = argparse.Namespace(
            input=str(input_file),
            template=None,
            report=None,
            format="json",
            language=None,
            autofix=False,
            output=None,
            max_fix_iterations=3,
            verbose=False,
        )

        exit_code = qa_command(args)
        assert exit_code == 1


# Made with Bob
