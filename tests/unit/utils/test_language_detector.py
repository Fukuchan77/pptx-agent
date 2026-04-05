"""Tests for language detection utility."""

from pptx_agent.utils.language_detector import detect_language, is_japanese_char


def test_language_detector_module_exists():
    """Test that language_detector module can be imported."""
    from pptx_agent.utils import language_detector

    assert language_detector is not None


def test_detect_language_function_exists():
    """Test that detect_language function exists."""

    assert callable(detect_language)


def test_detect_english_text():
    """Test detection of English text."""
    english_text = "This is a sample English text for testing language detection."
    result = detect_language(english_text)

    assert result == "en"


def test_detect_japanese_text():
    """Test detection of Japanese text."""
    japanese_text = "これは日本語のテキストです。言語検出のテストに使用します。"
    result = detect_language(japanese_text)

    assert result == "ja"


def test_detect_mixed_text_english_dominant():
    """Test detection of mixed text with English dominant."""
    mixed_text = "This is mostly English text with some 日本語 words."
    result = detect_language(mixed_text)

    assert result == "en"


def test_detect_mixed_text_japanese_dominant():
    """Test detection of mixed text with Japanese dominant."""
    mixed_text = "これは主に日本語のテキストで、some English words が含まれています。"
    result = detect_language(mixed_text)

    assert result == "ja"


def test_detect_empty_string_defaults_to_english():
    """Test that empty string defaults to English."""
    result = detect_language("")

    assert result == "en"


def test_detect_numbers_only_defaults_to_english():
    """Test that numbers-only text defaults to English."""
    result = detect_language("123456 789")

    assert result == "en"


def test_is_japanese_char_function_exists():
    """Test that is_japanese_char helper function exists."""
    assert callable(is_japanese_char)


def test_is_japanese_char_hiragana():
    """Test detection of hiragana characters."""
    assert is_japanese_char("あ") is True
    assert is_japanese_char("ん") is True


def test_is_japanese_char_katakana():
    """Test detection of katakana characters."""
    assert is_japanese_char("ア") is True
    assert is_japanese_char("ン") is True


def test_is_japanese_char_kanji():
    """Test detection of kanji characters."""
    assert is_japanese_char("日") is True
    assert is_japanese_char("本") is True
    assert is_japanese_char("語") is True


def test_is_japanese_char_english():
    """Test that English characters are not Japanese."""
    assert is_japanese_char("a") is False
    assert is_japanese_char("Z") is False
    assert is_japanese_char("1") is False
