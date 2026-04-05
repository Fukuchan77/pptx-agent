"""Tests for language-aware text capacity calculator."""

from pptx_agent.utils.text_capacity import (
    calculate_effective_capacity,
    calculate_required_capacity,
    get_language_multiplier,
    text_fits_within_capacity,
)


def test_text_capacity_module_exists():
    """Test that text_capacity module can be imported."""
    from pptx_agent.utils import text_capacity

    assert text_capacity is not None


def test_calculate_effective_capacity_function_exists():
    """Test that calculate_effective_capacity function exists."""

    assert callable(calculate_effective_capacity)


def test_calculate_effective_capacity_english():
    """Test effective capacity calculation for English."""
    # English has 1.0x multiplier
    result = calculate_effective_capacity(max_chars=100, language="en")
    assert result == 100


def test_calculate_effective_capacity_japanese():
    """Test effective capacity calculation for Japanese."""
    # Japanese has 0.55x multiplier
    result = calculate_effective_capacity(max_chars=100, language="ja")
    assert result == 55


def test_text_fits_within_capacity_function_exists():
    """Test that text_fits_within_capacity function exists."""
    assert callable(text_fits_within_capacity)


def test_text_fits_within_capacity_english_fits():
    """Test that English text fits within capacity."""
    text = "This is a test"  # 14 characters
    result = text_fits_within_capacity(text=text, max_chars=20, language="en")
    assert result is True


def test_text_fits_within_capacity_english_exceeds():
    """Test that English text exceeds capacity."""
    text = "This is a much longer test text"  # 31 characters
    result = text_fits_within_capacity(text=text, max_chars=20, language="en")
    assert result is False


def test_text_fits_within_capacity_japanese_fits():
    """Test that Japanese text fits within capacity."""
    text = "これはテスト"  # 7 characters
    # With 0.55x multiplier, max_chars=20 -> effective=11, so 7 chars should fit
    result = text_fits_within_capacity(text=text, max_chars=20, language="ja")
    assert result is True


def test_text_fits_within_capacity_japanese_exceeds():
    """Test that Japanese text exceeds capacity."""
    text = "これは非常に長いテストテキストです"  # 17 characters
    # With 0.55x multiplier, max_chars=20 -> effective=11, so 17 chars should NOT fit
    result = text_fits_within_capacity(text=text, max_chars=20, language="ja")
    assert result is False


def test_calculate_required_capacity_function_exists():
    """Test that calculate_required_capacity function exists."""
    assert callable(calculate_required_capacity)


def test_calculate_required_capacity_english():
    """Test required capacity calculation for English text."""
    text = "This is a test"  # 14 characters
    # English has 1.0x multiplier, so required capacity = 14
    result = calculate_required_capacity(text=text, language="en")
    assert result == 14


def test_calculate_required_capacity_japanese():
    """Test required capacity calculation for Japanese text."""
    text = "これはテスト"  # 6 characters
    # Japanese has 0.55x multiplier, so required capacity = 6 / 0.55 ≈ 11
    result = calculate_required_capacity(text=text, language="ja")
    assert result == 11  # ceil(6 / 0.55) = 11


def test_get_language_multiplier_function_exists():
    """Test that get_language_multiplier function exists."""
    assert callable(get_language_multiplier)


def test_get_language_multiplier_english():
    """Test language multiplier for English."""
    result = get_language_multiplier("en")
    assert result == 1.0


def test_get_language_multiplier_japanese():
    """Test language multiplier for Japanese."""
    result = get_language_multiplier("ja")
    assert result == 0.55
