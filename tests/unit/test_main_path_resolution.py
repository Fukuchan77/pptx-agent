"""Tests for output path resolution in CLI main.py.

RED PHASE: These tests verify that main.py resolves output paths to absolute
before passing them to the pipeline.
"""

import sys
from pathlib import Path
from unittest.mock import patch

from pptx_agent import main


class TestOutputPathResolution:
    """Test suite for verifying output path resolution in main.py.

    RED PHASE: These tests should FAIL because current implementation
    doesn't resolve paths to absolute.
    """

    def test_main_resolves_relative_output_path_to_absolute(self, tmp_path: Path) -> None:
        """Test that relative output path is resolved to absolute in main().

        RED PHASE: This test should FAIL because current implementation
        passes relative paths directly without resolving.
        """
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()

        # Use relative path for output
        relative_output = "relative/output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            relative_output,  # Relative path
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = relative_output
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0
        mock_generate.assert_called_once()

        # The critical assertion: output_path should be absolute
        call_kwargs = mock_generate.call_args.kwargs
        output_path_arg = call_kwargs.get("output_path")

        # Verify it's an absolute path
        assert Path(output_path_arg).is_absolute(), (
            f"Expected absolute path, but got relative: {output_path_arg}"
        )

    def test_main_resolves_absolute_output_path_correctly(self, tmp_path: Path) -> None:
        """Test that absolute output path remains absolute after resolution.

        RED PHASE: This test should PASS even before changes, serving as regression check.
        """
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
            str(output_file),  # Already absolute
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = str(output_file)
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0
        mock_generate.assert_called_once()

        # Verify it's absolute and matches expected path
        call_kwargs = mock_generate.call_args.kwargs
        output_path_arg = call_kwargs.get("output_path")

        assert Path(output_path_arg).is_absolute()
        # Should resolve to the same absolute path
        assert Path(output_path_arg).resolve() == output_file.resolve()

    def test_main_resolves_dotted_relative_paths(self, tmp_path: Path) -> None:
        """Test that paths with . and .. are properly resolved.

        RED PHASE: This test should FAIL because current implementation
        doesn't resolve relative components.
        """
        # Arrange
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test content")
        template_file = tmp_path / "template.pptx"
        template_file.touch()

        # Use path with ./ prefix
        relative_output = "./output.pptx"

        test_args = [
            "main.py",
            "-i",
            str(input_file),
            "-t",
            str(template_file),
            "-o",
            relative_output,
        ]

        with patch("pptx_agent.main.generate_presentation") as mock_generate:
            mock_generate.return_value = relative_output
            with patch.object(sys, "argv", test_args):
                # Act
                exit_code = main.main()

        # Assert
        assert exit_code == 0

        # Verify path is absolute and doesn't contain . or ..
        call_kwargs = mock_generate.call_args.kwargs
        output_path_arg = call_kwargs.get("output_path")

        assert Path(output_path_arg).is_absolute()
        # Resolved path should not contain relative components
        assert "./" not in output_path_arg
        assert "../" not in output_path_arg
