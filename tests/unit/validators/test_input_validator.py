"""Tests for input validation."""

import pytest

from pptx_agent.validators.input_validator import InputValidationError, validate_input_text


class TestInputValidator:
    """Tests for validate_input_text function."""

    def test_valid_input_text(self):
        """Should accept valid input text within length bounds."""
        text = "This is a valid presentation input with enough content."
        result = validate_input_text(text)
        assert result == text

    def test_empty_input_rejected(self):
        """Should reject empty string with clear error."""
        with pytest.raises(InputValidationError, match="validation failed.*cannot be empty"):
            validate_input_text("")

    def test_whitespace_only_input_rejected(self):
        """Should reject whitespace-only input with clear error."""
        with pytest.raises(InputValidationError, match="validation failed.*cannot be empty"):
            validate_input_text("   \n\t  ")

    def test_input_too_short_rejected(self):
        """Should reject input shorter than 10 characters."""
        with pytest.raises(
            InputValidationError, match="length validation failed.*between 10 and 30,000"
        ):
            validate_input_text("Short")

    def test_input_at_minimum_length_accepted(self):
        """Should accept input at exactly 10 characters."""
        text = "1234567890"  # Exactly 10 chars
        result = validate_input_text(text)
        assert result == text

    def test_input_at_maximum_length_accepted(self):
        """Should accept input at exactly 30,000 characters."""
        text = "x" * 30000
        result = validate_input_text(text)
        assert result == text

    def test_input_too_long_rejected(self):
        """Should reject input longer than 30,000 characters."""
        text = "x" * 30001
        with pytest.raises(
            InputValidationError, match="length validation failed.*between 10 and 30,000"
        ):
            validate_input_text(text)

    def test_input_with_leading_trailing_whitespace(self):
        """Should strip leading and trailing whitespace before validation."""
        text = "  Valid input text content  "
        result = validate_input_text(text)
        assert result == "Valid input text content"

    def test_input_with_unicode_characters(self):
        """Should accept input with Japanese and other Unicode characters."""
        text = "これは日本語のプレゼンテーション入力です。"
        result = validate_input_text(text)
        assert result == text

    def test_input_validation_error_has_context(self):
        """Should include length information in error message."""
        text = "x" * 30001
        with pytest.raises(InputValidationError) as exc_info:
            validate_input_text(text)
        assert "30001" in str(exc_info.value)
        assert "30,000" in str(exc_info.value)
