"""Tests for text handler module."""

from pptx_agent.pptx_wrapper.text_handler import TextHandler


class TestTextHandler:
    """Test suite for TextHandler."""

    def test_text_fits_within_capacity(self) -> None:
        """Test detecting when text fits within capacity."""
        # Arrange
        text = "Short text"  # 10 chars
        max_capacity = 50
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is True

    def test_text_exceeds_capacity(self) -> None:
        """Test detecting when text exceeds capacity."""
        # Arrange
        text = "A" * 100  # 100 chars
        max_capacity = 50
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is False

    def test_text_fits_exactly_at_capacity(self) -> None:
        """Test text that exactly matches capacity."""
        # Arrange
        text = "A" * 50  # Exactly 50 chars
        max_capacity = 50
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is True

    def test_detect_overflow_amount(self) -> None:
        """Test calculating overflow amount when text exceeds capacity."""
        # Arrange
        text = "A" * 100  # 100 chars
        max_capacity = 50
        handler = TextHandler()

        # Act
        overflow = handler.calculate_overflow(text, max_capacity)

        # Assert
        assert overflow == 50  # 100 - 50 = 50 chars overflow

    def test_no_overflow_when_text_fits(self) -> None:
        """Test that overflow is 0 when text fits."""
        # Arrange
        text = "Short"  # 5 chars
        max_capacity = 50
        handler = TextHandler()

        # Act
        overflow = handler.calculate_overflow(text, max_capacity)

        # Assert
        assert overflow == 0

    def test_text_fits_with_language_ratio_english(self) -> None:
        """Test text fitting with English language ratio (1.0)."""
        # Arrange
        text = "A" * 50  # 50 chars
        max_capacity = 50
        language = "en"
        language_ratio = 1.0
        handler = TextHandler()

        # Act
        fits = handler.text_fits_with_language(text, max_capacity, language, language_ratio)

        # Assert
        assert fits is True

    def test_text_fits_with_language_ratio_japanese(self) -> None:
        """Test text fitting with Japanese language ratio (0.55)."""
        # Arrange
        text = "あ" * 30  # 30 Japanese chars
        max_capacity = 50  # Effective capacity: 50 * 0.55 = 27.5
        language = "ja"
        language_ratio = 0.55
        handler = TextHandler()

        # Act
        # With ratio 0.55, effective capacity is 27.5, so 30 chars should not fit
        fits = handler.text_fits_with_language(text, max_capacity, language, language_ratio)

        # Assert
        assert fits is False

    def test_calculate_overflow_with_language_ratio(self) -> None:
        """Test overflow calculation with language ratio."""
        # Arrange
        text = "あ" * 30  # 30 Japanese chars
        max_capacity = 50  # Effective capacity: 50 * 0.55 = 27.5 ≈ 27
        language = "ja"
        language_ratio = 0.55
        handler = TextHandler()

        # Act
        overflow = handler.calculate_overflow_with_language(
            text, max_capacity, language, language_ratio
        )

        # Assert
        # Effective capacity is 27, so overflow is 30 - 27 = 3
        assert overflow == 3

    def test_empty_text_always_fits(self) -> None:
        """Test that empty text always fits."""
        # Arrange
        text = ""
        max_capacity = 50
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is True

    def test_zero_capacity_with_text_does_not_fit(self) -> None:
        """Test that any text does not fit in zero capacity."""
        # Arrange
        text = "A"
        max_capacity = 0
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is False

    def test_zero_capacity_with_empty_text_fits(self) -> None:
        """Test that empty text fits even in zero capacity."""
        # Arrange
        text = ""
        max_capacity = 0
        handler = TextHandler()

        # Act
        fits = handler.text_fits(text, max_capacity)

        # Assert
        assert fits is True

    def test_get_overflow_percentage(self) -> None:
        """Test calculating overflow as a percentage."""
        # Arrange
        text = "A" * 150  # 150 chars
        max_capacity = 100
        handler = TextHandler()

        # Act
        percentage = handler.get_overflow_percentage(text, max_capacity)

        # Assert
        # Overflow is 50 chars, which is 50% of capacity
        assert percentage == 50.0

    def test_no_overflow_percentage_when_fits(self) -> None:
        """Test that overflow percentage is 0 when text fits."""
        # Arrange
        text = "A" * 50
        max_capacity = 100
        handler = TextHandler()

        # Act
        percentage = handler.get_overflow_percentage(text, max_capacity)

        # Assert
        assert percentage == 0.0

    def test_truncate_text_to_capacity(self) -> None:
        """Test truncating text to fit capacity."""
        # Arrange
        text = "This is a long text that needs to be truncated"
        max_capacity = 20
        handler = TextHandler()

        # Act
        truncated = handler.truncate_text(text, max_capacity)

        # Assert
        assert len(truncated) <= max_capacity
        assert truncated.endswith("...")  # Should add ellipsis
        assert len(truncated) == 20  # Exactly at capacity including ellipsis

    def test_truncate_text_that_fits_returns_unchanged(self) -> None:
        """Test that text that fits is not truncated."""
        # Arrange
        text = "Short"
        max_capacity = 20
        handler = TextHandler()

        # Act
        truncated = handler.truncate_text(text, max_capacity)

        # Assert
        assert truncated == text  # Unchanged
