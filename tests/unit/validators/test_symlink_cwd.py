"""Tests for symlink validation when cwd itself is a symlink.

This test file specifically addresses the scenario where the current
working directory is a symlink, which should not trigger false positives
when validating files within that directory.
"""

from pathlib import Path

import pytest

from pptx_agent.validators.exceptions import SecurityValidationError
from pptx_agent.validators.file_validator import validate_no_symlinks


class TestSymlinkCwdValidation:
    """Tests for validate_no_symlinks when cwd is a symlink."""

    def test_accept_file_when_cwd_is_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should accept files in cwd even when cwd itself is a symlink.

        RED PHASE: This test will FAIL until we fix the implementation.

        Scenario:
        - real_dir: /tmp/actual_dir
        - symlink_dir: /tmp/link_dir -> /tmp/actual_dir
        - file: /tmp/link_dir/test.pptx (or relative: test.pptx from link_dir)

        Expected: Should NOT raise SecurityValidationError
        Reason: The file path itself doesn't traverse symlinks - only cwd is a symlink,
                which is acceptable since the user explicitly chose to run from that location.
        """
        # Create real directory and file
        real_dir = tmp_path / "actual_dir"
        real_dir.mkdir()

        test_file = real_dir / "test.pptx"
        test_file.touch()

        # Create symlink to directory
        symlink_dir = tmp_path / "link_dir"
        symlink_dir.symlink_to(real_dir)

        # Change to the symlinked directory
        monkeypatch.chdir(symlink_dir)

        # Validate file using relative path from symlinked cwd
        # This should NOT raise an error - cwd being a symlink is acceptable
        file_via_symlink = symlink_dir / "test.pptx"

        # Should not raise exception (but currently does - that's the bug!)
        validate_no_symlinks(file_via_symlink)

    def test_accept_relative_path_when_cwd_is_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should accept relative paths when running from a symlinked cwd.

        RED PHASE: This test will FAIL until we fix the implementation.
        """
        # Create real directory and file
        real_dir = tmp_path / "actual_dir"
        real_dir.mkdir()

        test_file = real_dir / "test.pptx"
        test_file.touch()

        # Create symlink to directory
        symlink_dir = tmp_path / "link_dir"
        symlink_dir.symlink_to(real_dir)

        # Change to the symlinked directory
        monkeypatch.chdir(symlink_dir)

        # Validate using relative path
        # This should NOT raise an error
        validate_no_symlinks("test.pptx")

    def test_reject_file_symlink_even_when_cwd_is_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should still reject file symlinks even when cwd is a symlink.

        This ensures we're not being too permissive - actual file symlinks
        should still be rejected.
        """
        # Create real directory
        real_dir = tmp_path / "actual_dir"
        real_dir.mkdir()

        # Create real file
        real_file = real_dir / "real.pptx"
        real_file.touch()

        # Create symlink to file
        file_symlink = real_dir / "link.pptx"
        file_symlink.symlink_to(real_file)

        # Create symlink to directory
        symlink_dir = tmp_path / "link_dir"
        symlink_dir.symlink_to(real_dir)

        # Change to the symlinked directory
        monkeypatch.chdir(symlink_dir)

        # Validate the file symlink - should still be rejected!
        file_via_cwd = symlink_dir / "link.pptx"

        with pytest.raises(SecurityValidationError) as exc_info:
            validate_no_symlinks(file_via_cwd)

        assert "symlink" in str(exc_info.value).lower()
