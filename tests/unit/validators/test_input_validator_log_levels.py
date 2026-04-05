"""Tests for input validator log levels (M-5)."""

import logging

import pytest

from pptx_agent.validators.input_validator import InputValidationError, validate_and_sanitize


class TestInputValidatorLogLevels:
    """Tests to verify correct log levels are used in input_validator.py."""

    def test_validation_start_uses_debug_level(self, caplog):
        """Validation entry should use DEBUG level (internal diagnostic)."""
        caplog.set_level(logging.DEBUG)
        text = "Valid text with enough content for validation."

        validate_and_sanitize(text)

        # Should log validation start at DEBUG level
        debug_logs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("Validating input" in r.message for r in debug_logs), (
            "Validation start should be logged at DEBUG level"
        )

    def test_validation_failure_uses_error_level(self, caplog):
        """Validation failure should use ERROR level (serious problem)."""
        caplog.set_level(logging.DEBUG)
        text = "Short"  # Too short - will fail validation

        with pytest.raises(InputValidationError):
            validate_and_sanitize(text)

        # Should log validation failure at ERROR level
        error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert any("validation failed" in r.message for r in error_logs), (
            "Validation failure should be logged at ERROR level"
        )

    def test_validation_success_uses_debug_level(self, caplog):
        """Validation success should use DEBUG level (internal diagnostic)."""
        caplog.set_level(logging.DEBUG)
        text = "Valid text with enough content for validation."

        validate_and_sanitize(text)

        # Should log validation success at DEBUG level
        debug_logs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("validation successful" in r.message for r in debug_logs), (
            "Validation success should be logged at DEBUG level"
        )

    def test_no_info_level_logs_for_internal_operations(self, caplog):
        """Internal validation operations should not use INFO level."""
        caplog.set_level(logging.INFO)
        text = "Valid text with enough content for validation."

        validate_and_sanitize(text)

        # Should not have INFO level logs for internal operations
        info_logs = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_logs) == 0, "Internal validation operations should use DEBUG, not INFO"

    def test_no_info_level_logs_for_validation_failures(self, caplog):
        """Validation failures should use ERROR, not INFO."""
        caplog.set_level(logging.INFO)
        text = "Short"  # Too short - will fail validation

        with pytest.raises(InputValidationError):
            validate_and_sanitize(text)

        # Should not have INFO level logs for errors
        info_logs = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_logs) == 0, "Validation failures should use ERROR, not INFO"
