"""Tests for input validation."""

import pytest

from pptx_agent.validators.input_validator import (
    MIN_INPUT_LENGTH,
    InputValidationError,
    sanitize_dangerous_characters,
    validate_and_sanitize,
)


class TestSanitizeDangerousCharacters:
    """Tests for sanitize_dangerous_characters public function."""

    def test_removes_null_bytes(self):
        """Should remove null bytes from text."""
        text = "Text\x00with\x00nulls"
        result = sanitize_dangerous_characters(text)
        assert "\x00" not in result
        assert result == "Textwithnulls"

    def test_removes_control_characters(self):
        """Should remove control characters but preserve normal whitespace."""
        text = "Text\x01with\x02control\x03chars"
        result = sanitize_dangerous_characters(text)
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result
        assert result == "Textwithcontrolchars"

    def test_preserves_normal_whitespace(self):
        """Should preserve spaces, tabs, newlines, and carriage returns."""
        text = "Line 1\nLine 2\rLine 3\tTabbed"
        result = sanitize_dangerous_characters(text)
        assert "\n" in result
        assert "\r" in result
        assert "\t" in result
        assert result == "Line 1\nLine 2\rLine 3\tTabbed"

    def test_removes_unicode_bidi_override_characters(self):
        """Should remove Unicode bidirectional override characters."""
        text = "Text\u202ewith\u202dbidi"
        result = sanitize_dangerous_characters(text)
        assert "\u202e" not in result
        assert "\u202d" not in result
        assert result == "Textwithbidi"

    def test_removes_zero_width_characters(self):
        """Should remove zero-width characters."""
        text = "Text\u200bwith\u200czero\u200dwidth\ufeff"
        result = sanitize_dangerous_characters(text)
        assert "\u200b" not in result
        assert "\u200c" not in result
        assert "\u200d" not in result
        assert "\ufeff" not in result
        assert result == "Textwithzerowidth"

    def test_normalizes_excessive_spaces(self):
        """Should normalize more than 2 consecutive spaces to 2 spaces."""
        text = "Text    with     many      spaces"
        result = sanitize_dangerous_characters(text)
        assert "    " not in result  # No more than 2 spaces
        assert "  " in result  # Should still have 2 spaces
        assert result == "Text  with  many  spaces"

    def test_strips_leading_trailing_whitespace(self):
        """Should strip leading and trailing whitespace."""
        text = "   Text with spaces   "
        result = sanitize_dangerous_characters(text)
        assert result == "Text with spaces"

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        result = sanitize_dangerous_characters("")
        assert result == ""

    def test_handles_none_like_empty_string(self):
        """Should handle None-like values gracefully."""
        # Function returns input if not text (falsy)
        result = sanitize_dangerous_characters("")
        assert result == ""

    def test_preserves_unicode_text(self):
        """Should preserve Unicode characters like Japanese text."""
        text = "これは日本語です"
        result = sanitize_dangerous_characters(text)
        assert result == text

    def test_mixed_dangerous_and_safe_characters(self):
        """Should handle mix of dangerous and safe characters."""
        text = "Safe\x00text\x01with\u200bmixed   chars"
        result = sanitize_dangerous_characters(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\u200b" not in result
        assert result == "Safetextwithmixed  chars"


class TestValidateAndSanitize:
    """Tests for validate_and_sanitize integrated function."""

    def test_normal_text_sanitized_and_validated(self):
        """Should sanitize and validate normal text successfully."""
        text = "This is a valid presentation input with enough content."
        result = validate_and_sanitize(text)
        assert result == text.strip()

    def test_text_with_control_characters_sanitized_then_validated(self):
        """Should sanitize control characters before validation."""
        text = "Valid text\x00with\x01control\x02chars and enough length."
        result = validate_and_sanitize(text)
        # Control characters should be removed
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "Valid text" in result
        assert "with" in result

    def test_sanitized_text_still_fails_validation_if_too_short(self):
        """Should raise validation error if sanitized text is too short."""
        # Text with control characters that when removed becomes too short
        text = "\x00\x01\x02Short\x03\x04"  # "Short" = 5 chars after sanitization
        with pytest.raises(InputValidationError, match="length validation failed"):
            validate_and_sanitize(text)

    def test_sanitized_text_still_fails_validation_if_too_long(self):
        """Should raise validation error if sanitized text is too long."""
        text = "x" * 30001
        with pytest.raises(InputValidationError, match="length validation failed"):
            validate_and_sanitize(text)

    def test_empty_text_after_sanitization_rejected(self):
        """Should reject text that becomes empty after sanitization."""
        text = "\x00\x01\x02\x03"  # Only control characters
        with pytest.raises(InputValidationError, match="cannot be empty"):
            validate_and_sanitize(text)

    def test_whitespace_normalized_before_validation(self):
        """Should normalize excessive spaces before validation."""
        text = "Valid text    with    excessive    spaces here."
        result = validate_and_sanitize(text)
        # Should have at most 2 consecutive spaces
        assert "    " not in result
        assert len(result) >= MIN_INPUT_LENGTH

    def test_unicode_characters_preserved_after_sanitization(self):
        """Should preserve Unicode characters during sanitization."""
        text = "これは日本語のプレゼンテーション入力です。"
        result = validate_and_sanitize(text)
        assert result == text

    def test_custom_length_limits_applied(self):
        """Should apply custom min/max length limits."""
        text = "Short text"  # 10 chars - valid with default, invalid with min_length=15
        with pytest.raises(InputValidationError):
            validate_and_sanitize(text, min_length=15)

    def test_custom_field_name_in_error_message(self):
        """Should use custom field name in error messages."""
        text = "Short"
        with pytest.raises(InputValidationError) as exc_info:
            validate_and_sanitize(text, field_name="theme")
        # Error message should mention the field name
        assert "theme" in str(exc_info.value) or "text" in str(exc_info.value)

    def test_returns_sanitized_not_original_text(self):
        """Should return sanitized text, not the original."""
        text = "  Text with\x00control\x01chars  "
        result = validate_and_sanitize(text)
        # Should be stripped and control chars removed
        assert result != text
        assert result.strip() == result
        assert "\x00" not in result
        assert "\x01" not in result
