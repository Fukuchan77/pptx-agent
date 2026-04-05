"""Unit tests for text handler font reduction strategy.

Tests the font reduction functionality for resolving text overflow.
"""

from pptx_agent.pptx_wrapper.text_handler import TextHandler


class TestFontReductionCalculation:
    """Tests for font reduction calculation."""

    def test_calculates_font_reduction_for_minor_overflow(self) -> None:
        """Test that font reduction is calculated correctly for 10% overflow."""
        handler = TextHandler()
        text = "A" * 550  # 10% over 500 char limit
        max_capacity = 500

        # Calculate required font reduction
        reduction_factor = handler.calculate_font_reduction(text, max_capacity)

        # Should be approximately 0.91 (550/500 = 1.1, so need 1/1.1 ≈ 0.909)
        assert reduction_factor is not None
        assert 0.85 <= reduction_factor <= 0.95

    def test_returns_none_for_fitting_text(self) -> None:
        """Test that no reduction is needed when text fits."""
        handler = TextHandler()
        text = "Short text"
        max_capacity = 500

        reduction_factor = handler.calculate_font_reduction(text, max_capacity)

        assert reduction_factor is None

    def test_calculates_reduction_for_20_percent_overflow(self) -> None:
        """Test font reduction for 20% overflow (maximum for this strategy)."""
        handler = TextHandler()
        text = "A" * 600  # 20% over 500 char limit
        max_capacity = 500

        reduction_factor = handler.calculate_font_reduction(text, max_capacity)

        # Should be approximately 0.83 (600/500 = 1.2, so need 1/1.2 ≈ 0.833)
        assert reduction_factor is not None
        assert 0.80 <= reduction_factor <= 0.85


class TestFontReductionFeasibility:
    """Tests for determining if font reduction is feasible."""

    def test_font_reduction_feasible_for_minor_overflow(self) -> None:
        """Test that font reduction is feasible for 10-20% overflow."""
        handler = TextHandler()
        text = "A" * 550  # 10% overflow
        max_capacity = 500

        is_feasible = handler.is_font_reduction_feasible(text, max_capacity)

        assert is_feasible is True

    def test_font_reduction_not_feasible_for_large_overflow(self) -> None:
        """Test that font reduction is not feasible for >30% overflow."""
        handler = TextHandler()
        text = "A" * 700  # 40% overflow
        max_capacity = 500

        is_feasible = handler.is_font_reduction_feasible(text, max_capacity)

        assert is_feasible is False

    def test_font_reduction_not_needed_for_fitting_text(self) -> None:
        """Test that font reduction is not needed when text fits."""
        handler = TextHandler()
        text = "Short text"
        max_capacity = 500

        is_feasible = handler.is_font_reduction_feasible(text, max_capacity)

        # Text fits, so font reduction is not needed (returns False)
        assert is_feasible is False


class TestFontReductionWithMinimumSize:
    """Tests for font reduction with minimum size constraint."""

    def test_respects_minimum_font_size(self) -> None:
        """Test that font reduction respects minimum font size."""
        handler = TextHandler()
        text = "A" * 650  # 30% overflow
        max_capacity = 500
        current_font_size = 12.0
        min_font_size = 10.0

        reduction_factor = handler.calculate_font_reduction(
            text, max_capacity, current_font_size, min_font_size
        )

        # Should not reduce below minimum
        if reduction_factor is not None:
            reduced_size = current_font_size * reduction_factor
            assert reduced_size >= min_font_size

    def test_rejects_reduction_below_minimum(self) -> None:
        """Test that font reduction is rejected if it would go below minimum."""
        handler = TextHandler()
        text = "A" * 800  # 60% overflow
        max_capacity = 500
        current_font_size = 12.0
        min_font_size = 10.0

        # 60% overflow would require ~0.625x reduction (12 * 0.625 = 7.5 < 10)
        reduction_factor = handler.calculate_font_reduction(
            text, max_capacity, current_font_size, min_font_size
        )

        # Should return None because reduction would violate minimum
        assert reduction_factor is None


class TestLanguageAwareFontReduction:
    """Tests for language-aware font reduction."""

    def test_font_reduction_with_language_ratio(self) -> None:
        """Test that font reduction works with language-specific capacity ratios."""
        handler = TextHandler()
        text = "あ" * 300  # Japanese text
        max_capacity = 500
        language_ratio = 0.55  # Japanese ratio

        # With language ratio 0.55, effective capacity is 275 chars (500 * 0.55)
        # Text length 300 results in ~9% overflow
        reduction_factor = handler.calculate_font_reduction_with_language(
            text, max_capacity, language_ratio=language_ratio
        )

        assert reduction_factor is not None
        assert 0.85 <= reduction_factor <= 0.95
