"""Tests for template generation script exception logging."""

import logging
from pathlib import Path

import pytest

from scripts.generate_templates import generate_data_template, generate_smartart_template


class TestDuplicateExceptionLogging:
    """Test that exception logging is not duplicated."""

    def test_data_template_logs_exception_once_on_validation_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify only one exception log when data template validation fails."""
        # Create invalid template file
        template_path = tmp_path / "data-template.pptx"
        template_path.write_bytes(b"invalid pptx content")

        with caplog.at_level(logging.ERROR):
            generate_data_template(str(template_path))

        # Count how many times the exception was logged with traceback
        exception_logs = [record for record in caplog.records if record.exc_info is not None]

        # Should have exactly 1 exception log (not 2)
        assert len(exception_logs) == 1, f"Expected 1 exception log but found {len(exception_logs)}"

        # Verify the exception message
        assert "Failed to validate template" in caplog.text

    def test_smartart_template_logs_exception_once_on_validation_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify only one exception log when smartart template validation fails."""
        # Create invalid template file
        template_path = tmp_path / "smartart-template.pptx"
        template_path.write_bytes(b"invalid pptx content")

        with caplog.at_level(logging.ERROR):
            generate_smartart_template(str(template_path))

        # Count how many times the exception was logged with traceback
        exception_logs = [record for record in caplog.records if record.exc_info is not None]

        # Should have exactly 1 exception log (not 2)
        assert len(exception_logs) == 1, f"Expected 1 exception log but found {len(exception_logs)}"

        # Verify the exception message
        assert "Failed to validate template" in caplog.text

    def test_data_template_includes_remediation_message(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify remediation message is still logged after exception."""
        template_path = tmp_path / "data-template.pptx"
        template_path.write_bytes(b"invalid pptx content")

        with caplog.at_level(logging.WARNING):
            generate_data_template(str(template_path))

        # Remediation message should be present
        assert "Please recreate template following DATA-TEMPLATE-SPEC.md" in caplog.text

    def test_smartart_template_includes_remediation_message(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify remediation message is still logged after exception."""
        template_path = tmp_path / "smartart-template.pptx"
        template_path.write_bytes(b"invalid pptx content")

        with caplog.at_level(logging.WARNING):
            generate_smartart_template(str(template_path))

        # Remediation message should be present
        assert "Please recreate template following SMARTART-TEMPLATE-SPEC.md" in caplog.text
