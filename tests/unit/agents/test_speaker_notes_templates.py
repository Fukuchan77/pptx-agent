"""Unit tests for speaker notes template strings extraction.

Tests that Japanese speaker notes template strings are properly extracted
from content_generator.py to a dedicated constants module for better
maintainability and multilingual support.
"""

import pytest


def test_speaker_notes_templates_exist():
    """Test that speaker notes template strings are defined as importable constants.

    RED PHASE: This test will FAIL until we extract the strings.
    """
    # Import should succeed
    from pptx_agent.agents.prompts.speaker_notes import (
        SPEAKER_NOTES_JA_CONTENT_SLIDE,
        SPEAKER_NOTES_JA_SECTION_SLIDE,
        SPEAKER_NOTES_JA_TITLE_SLIDE,
    )

    # Verify they are non-empty strings
    assert isinstance(SPEAKER_NOTES_JA_TITLE_SLIDE, str)
    assert len(SPEAKER_NOTES_JA_TITLE_SLIDE) > 0

    assert isinstance(SPEAKER_NOTES_JA_SECTION_SLIDE, str)
    assert len(SPEAKER_NOTES_JA_SECTION_SLIDE) > 0

    assert isinstance(SPEAKER_NOTES_JA_CONTENT_SLIDE, str)
    assert len(SPEAKER_NOTES_JA_CONTENT_SLIDE) > 0


def test_speaker_notes_templates_contain_placeholders():
    """Test that template strings contain expected placeholders for formatting."""
    from pptx_agent.agents.prompts.speaker_notes import (
        SPEAKER_NOTES_JA_CONTENT_SLIDE,
        SPEAKER_NOTES_JA_SECTION_SLIDE,
        SPEAKER_NOTES_JA_TITLE_SLIDE,
    )

    # Title slide template should have placeholders for title and content
    assert "{title}" in SPEAKER_NOTES_JA_TITLE_SLIDE
    assert "{content}" in SPEAKER_NOTES_JA_TITLE_SLIDE

    # Section slide template should have placeholders
    assert "{title}" in SPEAKER_NOTES_JA_SECTION_SLIDE
    assert "{content}" in SPEAKER_NOTES_JA_SECTION_SLIDE

    # Content slide template should have placeholders
    assert "{title}" in SPEAKER_NOTES_JA_CONTENT_SLIDE
    assert "{content}" in SPEAKER_NOTES_JA_CONTENT_SLIDE


def test_no_hardcoded_japanese_strings_in_content_generator():
    """Test that content_generator.py does not contain hardcoded Japanese strings.

    This ensures that Japanese text has been properly extracted to template constants.
    """
    import inspect

    from pptx_agent.agents import content_generator

    # Get the source code of the entire content_generator module
    source = inspect.getsource(content_generator)

    # These are the hardcoded Japanese strings that should be extracted
    hardcoded_strings = [
        "このプレゼンテーションでは",
        "について説明します",
        "次のセクションでは",
        "に焦点を当てます",
        "に関して",
        "という点が重要です",
    ]

    # Verify none of these hardcoded strings appear in the function
    for japanese_str in hardcoded_strings:
        assert japanese_str not in source, (
            f"Found hardcoded Japanese string '{japanese_str}' in _generate_speaker_notes(). "
            "Japanese strings should be extracted to speaker_notes.py constants."
        )


@pytest.mark.asyncio
async def test_speaker_notes_generation_still_works_after_extraction():
    """Test that speaker notes generation still works correctly after extraction.

    This is a regression test to ensure the refactoring doesn't break functionality.
    """
    from pptx_agent.agents.content_generator import generate_content
    from pptx_agent.schemas.outline import PresentationOutline, SlideContent

    outline = PresentationOutline(
        title="テストプレゼンテーション",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="機械学習入門",
                content="初心者向けガイド",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Section Header",
                title="基本概念",
                content="重要なポイント",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title and Content",
                title="アルゴリズム",
                content="様々な手法",
            ),
        ],
        output_language="ja",
    )

    result = await generate_content(outline, use_llm=False)

    # Verify all slides have generated Japanese speaker notes
    for i, slide in enumerate(result.slides):
        assert slide.notes is not None, f"Slide {i + 1} missing speaker notes"
        assert len(slide.notes.strip()) > 0, f"Slide {i + 1} has empty speaker notes"
        # Verify notes contain Japanese characters
        assert any(ord(c) > 0x3000 for c in slide.notes if not c.isspace()), (
            f"Slide {i + 1} notes don't contain Japanese characters"
        )
