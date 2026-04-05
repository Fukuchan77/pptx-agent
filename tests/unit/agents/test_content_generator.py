"""Unit tests for content generator agent.

Tests cover:
- PresentationSchema generation from PresentationOutline
- Japanese and English content generation
- Different layout types (title, content, section)
- Content block structure (TextBlocks with placeholder names)
- Language-appropriate content
- Edge cases (minimal outline, complex slides)
"""

from unittest.mock import patch

from pptx_agent.agents.content_generator import _split_into_sentences, generate_content
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.text import TextBlock


def test_generate_content_function_exists():
    """Test that generate_content function can be imported."""
    assert callable(generate_content)


def test_generate_content_with_english_outline():
    """Test generate_content with English PresentationOutline input."""
    outline = PresentationOutline(
        title="Introduction to Machine Learning",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Introduction to Machine Learning",
                content="A beginner's guide to ML concepts",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="What is Machine Learning?",
                content="Machine learning enables computers to learn from data",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title Slide",
                title="Conclusion",
                content="Summary of key points",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert isinstance(result, PresentationSchema)
    assert result.title == "Introduction to Machine Learning"
    assert len(result.slides) == 3
    assert len(result.slides[0].content) > 0  # Should have content blocks


def test_generate_content_with_japanese_outline():
    """Test generate_content with Japanese PresentationOutline input."""
    outline = PresentationOutline(
        title="機械学習入門",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="機械学習入門",
                content="初心者向けMLガイド",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="機械学習とは?",
                content="機械学習はデータから学習するシステムです",
            ),
        ],
        output_language="ja",
    )

    result = generate_content(outline)

    assert isinstance(result, PresentationSchema)
    assert result.title == "機械学習入門"
    assert len(result.slides) == 2


def test_generate_content_creates_text_blocks():
    """Test that content generator creates TextBlock objects."""
    outline = PresentationOutline(
        title="Test Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Slide",
                content="This is test content",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Check that slides have content blocks
    assert len(result.slides) > 0
    assert len(result.slides[0].content) > 0

    # Check that content blocks are TextBlocks
    first_block = result.slides[0].content[0]
    assert isinstance(first_block, TextBlock)


def test_generate_content_preserves_layout_names():
    """Test that layout names are preserved from outline."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Title",
                content="Content",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Section Header",
                title="Section",
                content="Content",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title and Content",
                title="Content Slide",
                content="Content",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert result.slides[0].layout_name == "Title Slide"
    assert result.slides[1].layout_name == "Section Header"
    assert result.slides[2].layout_name == "Title and Content"


def test_generate_content_preserves_slide_titles():
    """Test that slide titles are preserved from outline."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="First Title",
                content="Content",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Second Title",
                content="Content",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert result.slides[0].title == "First Title"
    assert result.slides[1].title == "Second Title"


def test_generate_content_sets_language_on_text_blocks():
    """Test that TextBlocks have correct language set."""
    # Test English
    outline_en = PresentationOutline(
        title="English Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="English content",
            ),
        ],
        output_language="en",
    )

    result_en = generate_content(outline_en)
    text_blocks_en = [b for b in result_en.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks_en) > 0
    assert all(block.language == "en" for block in text_blocks_en)

    # Test Japanese
    outline_ja = PresentationOutline(
        title="日本語テスト",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="テスト",
                content="日本語コンテンツ",
            ),
        ],
        output_language="ja",
    )

    result_ja = generate_content(outline_ja)
    text_blocks_ja = [b for b in result_ja.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks_ja) > 0
    assert all(block.language == "ja" for block in text_blocks_ja)


def test_generate_content_with_speaker_notes():
    """Test that speaker notes are preserved if present."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Slide",
                content="Content",
                speaker_notes="These are speaker notes",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert result.slides[0].notes == "These are speaker notes"


def test_generate_content_without_speaker_notes():
    """Test handling when speaker notes are not present."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Slide",
                content="Content",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Notes should be None or not cause errors
    assert result.slides[0].notes is None or isinstance(result.slides[0].notes, str)


def test_generate_content_with_minimal_outline():
    """Test generate_content with minimal outline (3 slides)."""
    outline = PresentationOutline(
        title="Minimal",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Title",
                content="",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Content",
                content="Brief content",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title Slide",
                title="End",
                content="",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert isinstance(result, PresentationSchema)
    assert len(result.slides) == 3


def test_generate_content_with_complex_outline():
    """Test generate_content with complex outline (many slides)."""
    # Create 15 slides
    slides = [
        SlideContent(
            slide_number=i,
            layout_name="Title and Content" if i > 1 and i < 15 else "Title Slide",
            title=f"Slide {i}",
            content=f"Content for slide {i}",
        )
        for i in range(1, 16)
    ]

    outline = PresentationOutline(
        title="Complex Presentation",
        slides=slides,
        output_language="en",
    )

    result = generate_content(outline)

    assert isinstance(result, PresentationSchema)
    assert len(result.slides) == 15


def test_generate_content_handles_empty_content():
    """Test that empty content strings are handled gracefully."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Title Only",
                content="",  # Empty content
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Should handle empty content gracefully
    assert isinstance(result.slides[0].content, list)


def test_generate_content_handles_long_content():
    """Test handling of long content strings."""
    long_content = " ".join(["This is a long sentence."] * 20)

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Long Content",
                content=long_content,
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Should create content blocks for long content
    assert len(result.slides[0].content) > 0


def test_generate_content_assigns_placeholder_names():
    """Test that TextBlocks have appropriate placeholder names."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content text",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0

    # All text blocks should have placeholder names
    for block in text_blocks:
        assert len(block.placeholder_name) > 0


def test_generate_content_creates_bullet_points_for_title_and_content():
    """Test that Title and Content layouts create bullet-point style content."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Point one. Point two. Point three.",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Should have content (subtitle placeholder)
    assert len(result.slides[0].content) > 0


def test_generate_speaker_notes_for_all_slides():
    """Test that speaker notes are GENERATED for all slides when not provided."""
    outline = PresentationOutline(
        title="Test Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Introduction to AI",
                content="A beginner's guide",
                # NO speaker_notes provided
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="What is AI?",
                content="AI enables machines to learn from data",
                # NO speaker_notes provided
            ),
            SlideContent(
                slide_number=3,
                layout_name="Section Header",
                title="Key Concepts",
                content="Understanding the basics",
                # NO speaker_notes provided
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # All slides should have generated speaker notes (FR-024)
    for slide in result.slides:
        assert slide.notes is not None, f"Slide '{slide.title}' missing speaker notes"
        assert len(slide.notes.strip()) > 0, f"Slide '{slide.title}' has empty speaker notes"


def test_generated_speaker_notes_not_empty():
    """Test that generated speaker notes are not empty strings."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Slide",
                content="Some content here",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    assert result.slides[0].notes is not None
    assert len(result.slides[0].notes.strip()) > 0


def test_speaker_notes_in_english():
    """Test that speaker notes are generated in English for English presentations."""
    outline = PresentationOutline(
        title="English Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Welcome",
                content="Introduction to the topic",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Check for English characteristics (basic check for ASCII characters)
    # More sophisticated language detection could be added
    assert any(c.isascii() for c in notes if c.isalpha())


def test_speaker_notes_in_japanese():
    """Test that speaker notes are generated in Japanese for Japanese presentations."""
    outline = PresentationOutline(
        title="日本語プレゼンテーション",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="ようこそ",
                content="トピックの紹介",
            ),
        ],
        output_language="ja",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Check for Japanese characteristics (hiragana, katakana, or kanji)
    assert any(ord(c) > 0x3000 for c in notes if not c.isspace())


def test_speaker_notes_for_title_slide():
    """Test that title slides get appropriate introductory speaker notes."""
    outline = PresentationOutline(
        title="Machine Learning Basics",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Machine Learning Basics",
                content="A comprehensive guide",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Title slide notes should introduce the presentation
    # Should be 1-3 sentences as per guidelines
    sentence_count = notes.count(".") + notes.count("。")
    assert 1 <= sentence_count <= 3


def test_speaker_notes_for_content_slide():
    """Test that content slides get elaborative speaker notes."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Key Features",
                content="Feature one. Feature two. Feature three.",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Content slide notes should elaborate on bullet points
    assert len(notes) > len("Feature one")  # Should add value beyond slide content


def test_speaker_notes_for_section_slide():
    """Test that section slides get transitional speaker notes."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Section Header",
                title="Part 2: Implementation",
                content="Getting into the details",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Section slide notes should provide transition and context
    assert len(notes.strip()) > 0


def test_speaker_notes_provide_value_added_context():
    """Test that speaker notes provide context beyond what's on the slide."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Benefits",
                content="Increased efficiency",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Notes should be more than just repeating the title or content
    # Should add explanatory context
    assert len(notes) > len("Benefits Increased efficiency")


def test_speaker_notes_length_appropriate():
    """Test that speaker notes are 1-3 sentences as per guidelines."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Topic",
                content="Test content here",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    notes = result.slides[0].notes
    assert notes is not None
    # Count sentences (periods or Japanese periods)
    sentence_count = notes.count(".") + notes.count("。")
    assert 1 <= sentence_count <= 3, f"Expected 1-3 sentences, got {sentence_count}"


def test_speaker_notes_preserved_when_provided():
    """Test that speaker notes from outline are preserved (backward compatibility)."""
    provided_notes = "These are manually provided notes that should be kept."

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content",
                speaker_notes=provided_notes,
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # When speaker notes are provided, they should be preserved (not generated)
    assert result.slides[0].notes == provided_notes

    # Should have at least one content block
    assert len(result.slides[0].content) > 0


def test_generate_content_handles_title_slide_layout():
    """Test special handling for Title Slide layout (subtitle)."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Main Title",
                content="Subtitle content",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Verify Title Slide layout generates content
    assert isinstance(result, PresentationSchema)
    assert len(result.slides) == 1
    assert result.slides[0].layout_name == "Title Slide"


def test_generate_content_logs_entry_with_input_info():
    """Test that generate_content logs input information at function entry."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Test 2",
                content="Content 2",
            ),
        ],
        output_language="en",
    )

    with patch("pptx_agent.agents.content_generator.logger") as mock_logger:
        generate_content(outline)

        # Verify INFO level log at entry with input slide count
        mock_logger.info.assert_any_call(
            "Starting content generation: input_slides=%d, language=%s",
            2,  # number of slides
            "en",
        )


def test_generate_content_logs_exit_with_output_info():
    """Test that generate_content logs output information at function exit."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Test 2",
                content="Content 2",
            ),
        ],
        output_language="en",
    )

    with patch("pptx_agent.agents.content_generator.logger") as mock_logger:
        result = generate_content(outline)

        # Verify INFO level log at exit with output content count
        total_content_blocks = sum(len(slide.content) for slide in result.slides)
        mock_logger.info.assert_any_call(
            "Content generation completed: output_slides=%d, total_content_blocks=%d",
            2,  # number of slides
            total_content_blocks,
        )


# Tests for _split_into_sentences() function


def test_split_into_sentences_with_english_text():
    """Test splitting English text with periods."""
    text = "First sentence. Second sentence. Third sentence."
    result = _split_into_sentences(text)

    assert len(result) == 3
    assert result[0] == "First sentence"
    assert result[1] == "Second sentence"
    assert result[2] == "Third sentence"


def test_split_into_sentences_with_japanese_text():
    """Test splitting Japanese text with 。 (full stop)."""
    text = "最初の文。二番目の文。三番目の文。"
    result = _split_into_sentences(text)

    assert len(result) == 3
    assert result[0] == "最初の文"
    assert result[1] == "二番目の文"
    assert result[2] == "三番目の文"


def test_split_into_sentences_with_mixed_text():
    """Test splitting mixed English and Japanese text."""
    text = "English sentence. 日本語の文。Another English. もう一つの日本語。"
    result = _split_into_sentences(text)

    assert len(result) == 4
    assert result[0] == "English sentence"
    assert result[1] == "日本語の文"
    assert result[2] == "Another English"
    assert result[3] == "もう一つの日本語"


def test_split_into_sentences_with_empty_string():
    """Test splitting empty string."""
    text = ""
    result = _split_into_sentences(text)

    assert len(result) == 0
    assert result == []


def test_split_into_sentences_with_whitespace_only():
    """Test splitting whitespace-only string."""
    text = "   \n\t  "
    result = _split_into_sentences(text)

    assert len(result) == 0
    assert result == []


def test_split_into_sentences_without_trailing_period():
    """Test splitting text without trailing punctuation."""
    text = "First sentence. Second sentence"
    result = _split_into_sentences(text)

    assert len(result) == 2
    assert result[0] == "First sentence"
    assert result[1] == "Second sentence"


def test_split_into_sentences_without_trailing_japanese_period():
    """Test splitting Japanese text without trailing 。."""
    text = "最初の文。二番目の文"
    result = _split_into_sentences(text)

    assert len(result) == 2
    assert result[0] == "最初の文"
    assert result[1] == "二番目の文"


def test_split_into_sentences_with_multiple_consecutive_periods():
    """Test splitting text with multiple consecutive periods."""
    text = "First sentence.. Second sentence..."
    result = _split_into_sentences(text)

    # Should filter out empty strings from consecutive periods
    assert all(sentence for sentence in result)  # No empty strings
    assert "First sentence" in result
    assert "Second sentence" in result


def test_split_into_sentences_with_multiple_consecutive_japanese_periods():
    """Test splitting Japanese text with multiple consecutive 。."""
    text = "最初の文。。二番目の文。。。"
    result = _split_into_sentences(text)

    # Should filter out empty strings from consecutive periods
    assert all(sentence for sentence in result)  # No empty strings
    assert "最初の文" in result
    assert "二番目の文" in result


def test_split_into_sentences_single_sentence_no_punctuation():
    """Test single sentence without any punctuation."""
    text = "Single sentence without punctuation"
    result = _split_into_sentences(text)

    assert len(result) == 1
    assert result[0] == "Single sentence without punctuation"


# Tests for manifest-based placeholder name resolution (M-6)


def test_determine_placeholder_name_from_manifest_body_type():
    """Test that placeholder names are determined from manifest when available."""
    # Create manifest with custom placeholder name
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(
                        name="Custom Content Box", type="BODY", max_chars=500
                    ),  # BODY type
                ],
            ),
        ],
        default_language="en",
    )

    # Create outline that will use this layout
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test Slide",
                content="This is test content",
            ),
        ],
        output_language="en",
    )

    # Generate content with manifest
    result = generate_content(outline, manifest=manifest)

    # Verify placeholder name comes from manifest, not hardcoded default
    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should use "Custom Content Box" from manifest, NOT "Content Placeholder"
    assert text_blocks[0].placeholder_name == "Custom Content Box"


def test_determine_placeholder_name_from_manifest_object_type():
    """Test placeholder name resolution with OBJECT type placeholder."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(
                        name="Content Area", type="OBJECT", max_chars=400
                    ),  # OBJECT type
                ],
            ),
        ],
    )

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content text",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline, manifest=manifest)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should use "Content Area" from manifest (OBJECT type is content placeholder)
    assert text_blocks[0].placeholder_name == "Content Area"


def test_determine_placeholder_name_fallback_when_no_manifest():
    """Test that hardcoded defaults are used when no manifest is provided."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content text",
            ),
        ],
        output_language="en",
    )

    # Call without manifest parameter (backward compatibility)
    result = generate_content(outline)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should fall back to hardcoded default "Content Placeholder"
    assert text_blocks[0].placeholder_name == "Content Placeholder"


def test_determine_placeholder_name_fallback_when_layout_not_in_manifest():
    """Test fallback when layout exists but isn't in manifest."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Different Layout",  # Different layout name
                placeholders=[
                    PlaceholderInfo(name="Content Box", type="BODY", max_chars=500),
                ],
            ),
        ],
    )

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",  # Layout not in manifest
                title="Test",
                content="Content text",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline, manifest=manifest)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should fall back to default since layout not found in manifest
    assert text_blocks[0].placeholder_name == "Content Placeholder"


def test_determine_placeholder_name_title_slide_from_manifest():
    """Test subtitle placeholder name resolution for Title Slide layout."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title Slide",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Custom Subtitle Area", type="BODY", max_chars=200),
                ],
            ),
        ],
    )

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Main Title",
                content="Subtitle text",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline, manifest=manifest)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should use "Custom Subtitle Area" from manifest, NOT hardcoded "Subtitle"
    assert text_blocks[0].placeholder_name == "Custom Subtitle Area"


def test_determine_placeholder_name_no_body_placeholders_in_manifest():
    """Test fallback when manifest has layout but no BODY/OBJECT placeholders."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    # Only TITLE placeholder, no BODY/OBJECT
                ],
            ),
        ],
    )

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="Content text",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline, manifest=manifest)

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    assert len(text_blocks) > 0
    # Should fall back to default since no BODY/OBJECT placeholders in manifest
    assert text_blocks[0].placeholder_name == "Content Placeholder"
