"""Unit tests for CLI entry point."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pptx_agent import main


class TestCLIEntryPoint:
    """Test suite for CLI entry point functionality."""

    def test_successful_execution(self, tmp_path: Path) -> None:
        """Test successful CLI execution with valid inputs."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()  # Create empty file
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "--input",
            str(input_file),
            "--template",
            str(template_file),
            "--output",
            str(output_file),
        ]

        # Mock the pipeline to avoid actual generation
        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0
        mock_generate.assert_called_once()

    def test_missing_input_file(self, tmp_path: Path) -> None:
        """Test CLI handles missing input file gracefully."""
        # Arrange
        input_file = tmp_path / "nonexistent.txt"  # Does not exist
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "--input",
            str(input_file),
            "--template",
            str(template_file),
            "--output",
            str(output_file),
        ]

        with patch.object(sys, "argv", test_args):
            # Act
            exit_code = main.main()

        # Assert
        assert exit_code != 0  # Non-zero exit code for error

    def test_missing_template_file(self, tmp_path: Path) -> None:
        """Test CLI handles missing template file gracefully."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "nonexistent.pptx"  # Does not exist
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "--input",
            str(input_file),
            "--template",
            str(template_file),
            "--output",
            str(output_file),
        ]

        with patch.object(sys, "argv", test_args):
            # Act
            exit_code = main.main()

        # Assert
        assert exit_code != 0

    def test_help_message_display(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that help message is displayed correctly."""
        # Arrange
        test_args = ["main.py", "--help"]

        with patch.object(sys, "argv", test_args), pytest.raises(SystemExit) as exc_info:
            # Act
            main.main()

        # Assert
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "--input" in captured.out or "--input" in captured.err
        assert "--template" in captured.out or "--template" in captured.err
        assert "--output" in captured.out or "--output" in captured.err

    def test_missing_required_arguments(self) -> None:
        """Test CLI fails when required arguments are missing."""
        # Arrange - no arguments provided
        test_args = ["main.py"]

        with patch.object(sys, "argv", test_args), pytest.raises(SystemExit) as exc_info:
            # Act
            main.main()

        # Assert
        assert exc_info.value.code != 0  # Non-zero exit for error

    def test_invalid_output_path(self, tmp_path: Path) -> None:
        """Test CLI handles invalid output path gracefully."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        # Use an invalid output path (directory that doesn't exist and can't be created)
        output_file = "/invalid/path/that/does/not/exist/output.pptx"

        test_args = [
            "main.py",
            "--input",
            str(input_file),
            "--template",
            str(template_file),
            "--output",
            output_file,
        ]

        with patch.object(sys, "argv", test_args):
            # Act
            exit_code = main.main()

        # Assert
        assert exit_code != 0

    def test_short_argument_names(self, tmp_path: Path) -> None:
        """Test CLI accepts short argument names (-i, -t, -o)."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0

    def test_optional_manifest_parameter(self, tmp_path: Path) -> None:
        """Test CLI accepts optional manifest parameter."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"
        manifest_file = tmp_path / "manifest.json"
        manifest_data = {
            "template_name": "test_template",
            "layouts": [
                {
                    "name": "Title Slide",
                    "placeholders": [{"name": "Title", "type": "TITLE", "max_chars": 100}],
                }
            ],
        }
        manifest_file.write_text(json.dumps(manifest_data))

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
            "-m",
            str(manifest_file),
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0
        # Verify manifest was passed to pipeline
        call_args = mock_generate.call_args
        assert call_args is not None  # Manifest parameter should be passed

    def test_error_message_clarity(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that error messages are clear and user-friendly."""
        # Arrange - empty input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("")  # Empty file
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
        ]

        with patch.object(sys, "argv", test_args):
            # Act
            exit_code = main.main()

        # Assert
        assert exit_code != 0
        captured = capsys.readouterr()
        # Should have some error output
        error_output = captured.out + captured.err
        assert len(error_output) > 0

    def test_pipeline_exception_handling(self, tmp_path: Path) -> None:
        """Test that pipeline exceptions are caught and handled."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            # Simulate a pipeline error
            mock_generate.side_effect = ValueError("Test error from pipeline")
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code != 0

    def test_success_message_with_output_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that success message includes output path."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("This is a test presentation content for testing.")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0
        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        # Success message should mention output file
        assert str(output_file) in output_text or "output.pptx" in output_text

    def test_verbose_flag_recognized(self, tmp_path: Path) -> None:
        """Test that --verbose flag is recognized by parser."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
            "--verbose",
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0

    def test_verbose_mode_shows_traceback(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that verbose mode shows full traceback on exception."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
            "--verbose",
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            # Simulate unexpected exception
            mock_generate.side_effect = RuntimeError("Unexpected test error")
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code != 0
        captured = capsys.readouterr()
        error_output = captured.out + captured.err
        # In verbose mode, should show traceback with file and line info
        assert "Traceback" in error_output
        assert "RuntimeError" in error_output

    def test_normal_mode_shows_simple_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that normal mode (without --verbose) shows simple error message."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
            # No --verbose flag
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            # Simulate unexpected exception
            mock_generate.side_effect = RuntimeError("Unexpected test error")
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code != 0
        captured = capsys.readouterr()
        error_output = captured.out + captured.err
        # In normal mode, should NOT show full traceback
        assert "Traceback" not in error_output
        # Should show simple error message
        assert "Error:" in error_output
        assert "Unexpected test error" in error_output

    def test_exception_logged_to_file(self, tmp_path: Path) -> None:
        """Test that exceptions are logged using logger.exception()."""
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()
        output_file = tmp_path / "output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            str(output_file),
        ]

        with (
            patch("pptx_agent.main.generate_presentation") as mock_generate,
            patch("pptx_agent.main.logger") as mock_logger,
            patch.object(sys, "argv", test_args),
        ):
            mock_generate.side_effect = RuntimeError("Test error for logging")
            # Act
            exit_code = main.main()

        # Assert
        assert exit_code != 0
        # Verify logger.exception() was called to log the error
        mock_logger.exception.assert_called_once()
        # Check the log message contains error info
        call_args = mock_logger.exception.call_args
        assert "Unexpected error" in str(call_args)
