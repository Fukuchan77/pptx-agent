"""Unit tests for outline generator agent.

Tests cover:
- PresentationOutline generation from StoryAnalysis
- Slide count validation (3-30 slides per FR-019)
- Japanese and English outline generation
- Layout type assignments (title, content, section)
- Edge cases (minimal input, complex structure)
"""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai import AgentRunResult

from pptx_agent.agents.outline_generator import generate_outline
from pptx_agent.agents.story_analyzer import StoryAnalysis
from pptx_agent.schemas.outline import PresentationOutline, SlideContent


def test_generate_outline_function_exists():
    """Test that generate_outline function can be imported."""

    assert callable(generate_outline)


@pytest.mark.asyncio
async def test_generate_outline_with_english_story():
    """Test generate_outline with English StoryAnalysis input."""
    story = StoryAnalysis(
        topic="Introduction to Machine Learning",
        target_audience="Beginner audience",
        key_message="Machine learning enables systems to learn from data",
        tone="professional",
        language="en",
        suggested_structure="Introduction, Main Content, Conclusion",
    )

    result = await generate_outline(story, use_llm=False)

    assert isinstance(result, PresentationOutline)
    assert result.output_language == "en"
    assert len(result.title) > 0
    assert len(result.slides) >= 3  # Minimum 3 slides per FR-019
    assert len(result.slides) <= 30  # Maximum 30 slides per FR-019


@pytest.mark.asyncio
async def test_generate_outline_with_japanese_story():
    """Test generate_outline with Japanese StoryAnalysis input."""
    story = StoryAnalysis(
        topic="機械学習入門",
        target_audience="初心者向け",
        key_message="機械学習はデータから学習するシステム",
        tone="professional",
        language="ja",
        suggested_structure="導入, 本編, まとめ",
    )

    result = await generate_outline(story, use_llm=False)

    assert isinstance(result, PresentationOutline)
    assert result.output_language == "ja"
    assert len(result.title) > 0
    assert len(result.slides) >= 3
    assert len(result.slides) <= 30


@pytest.mark.asyncio
async def test_generate_outline_slide_count_minimum():
    """Test that outline generates at least 3 slides (FR-019)."""
    # Minimal story
    story = StoryAnalysis(
        topic="Quick Topic",
        target_audience="General audience",
        key_message="Brief message",
        tone="neutral",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    assert len(result.slides) >= 3, "Outline must generate at least 3 slides per FR-019"


@pytest.mark.asyncio
async def test_generate_outline_slide_count_maximum():
    """Test that outline does not exceed 30 slides (FR-019)."""
    # Complex story with detailed structure
    story = StoryAnalysis(
        topic="Comprehensive Machine Learning Guide",
        target_audience="Advanced audience",
        key_message="Master machine learning concepts",
        tone="professional",
        language="en",
        suggested_structure="Multi-section structured presentation",
    )

    result = await generate_outline(story, use_llm=False)

    assert len(result.slides) <= 30, "Outline must not exceed 30 slides per FR-019"


@pytest.mark.asyncio
async def test_generate_outline_slide_numbering():
    """Test that slides have sequential numbering starting at 1."""
    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    # Verify sequential numbering
    for i, slide in enumerate(result.slides, start=1):
        assert slide.slide_number == i, "Slide numbering must be sequential starting at 1"


@pytest.mark.asyncio
async def test_generate_outline_layout_types():
    """Test that outline assigns appropriate layout types."""
    story = StoryAnalysis(
        topic="Project Overview",
        target_audience="Business audience",
        key_message="Key insights from project",
        tone="professional",
        language="en",
        suggested_structure="Introduction, Main Content, Conclusion",
    )

    result = await generate_outline(story, use_llm=False)

    # First slide should typically be title slide
    assert len(result.slides[0].layout_name) > 0

    # All slides should have layout names
    for slide in result.slides:
        assert len(slide.layout_name) > 0, "Each slide must have a layout name"


@pytest.mark.asyncio
async def test_generate_outline_slide_titles():
    """Test that all slides have titles."""
    story = StoryAnalysis(
        topic="Data Analysis Fundamentals",
        target_audience="Student audience",
        key_message="Learn data analysis basics",
        tone="friendly",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    # All slides must have titles
    for slide in result.slides:
        assert len(slide.title) > 0, "Each slide must have a non-empty title"


@pytest.mark.asyncio
async def test_generate_outline_uses_story_topic():
    """Test that outline incorporates story topic into presentation title."""
    story = StoryAnalysis(
        topic="Cloud Computing Architecture",
        target_audience="Technical audience",
        key_message="Understanding cloud infrastructure",
        tone="professional",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    # Presentation title should relate to the story topic
    title_lower = result.title.lower()
    assert "cloud" in title_lower or "computing" in title_lower or "architecture" in title_lower, (
        "Outline title should relate to story topic"
    )


@pytest.mark.asyncio
async def test_generate_outline_respects_language():
    """Test that outline output_language matches input story language."""
    # English story
    story_en = StoryAnalysis(
        topic="English Topic",
        target_audience="General audience",
        key_message="English message",
        tone="neutral",
        language="en",
    )

    result_en = await generate_outline(story_en, use_llm=False)
    assert result_en.output_language == "en"

    # Japanese story
    story_ja = StoryAnalysis(
        topic="日本語トピック",
        target_audience="一般向け",
        key_message="日本語メッセージ",
        tone="neutral",
        language="ja",
    )

    result_ja = await generate_outline(story_ja, use_llm=False)
    assert result_ja.output_language == "ja"


@pytest.mark.asyncio
async def test_generate_outline_with_structured_content():
    """Test outline generation with suggested structure."""
    story = StoryAnalysis(
        topic="Business Strategy Review",
        target_audience="Business audience",
        key_message="Strategic insights for growth",
        tone="professional",
        language="en",
        suggested_structure="Problem, Solution, Benefits",
    )

    result = await generate_outline(story, use_llm=False)

    # Should generate appropriate number of slides based on structure
    assert len(result.slides) >= 4  # At least: Title + Problem + Solution + Benefits


@pytest.mark.asyncio
async def test_generate_outline_with_minimal_story():
    """Test outline generation with minimal StoryAnalysis input."""
    story = StoryAnalysis(
        topic="A",
        target_audience="B",
        key_message="C",
        tone="neutral",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    # Should still generate valid outline even with minimal input
    assert isinstance(result, PresentationOutline)
    assert len(result.slides) >= 3
    assert len(result.slides) <= 30


@pytest.mark.asyncio
async def test_generate_outline_with_complex_story():
    """Test outline generation with complex StoryAnalysis input."""
    story = StoryAnalysis(
        topic="Comprehensive Guide to Modern Software Development Practices and Methodologies",
        target_audience="Advanced technical professionals and software architects",
        key_message=(
            "Understanding and implementing modern software development requires "
            "careful attention to testing, deployment, and team collaboration practices"
        ),
        tone="professional",
        language="en",
        suggested_structure="Multi-section structured presentation",
    )

    result = await generate_outline(story, use_llm=False)

    # Should handle complex input gracefully
    assert isinstance(result, PresentationOutline)
    assert len(result.slides) >= 3
    assert len(result.slides) <= 30


@pytest.mark.asyncio
async def test_generate_outline_slide_content_not_empty():
    """Test that slides have content field (even if empty string is allowed)."""
    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    # All slides should have content field defined (content can be empty string)
    for slide in result.slides:
        assert hasattr(slide, "content"), "Each slide must have a content field"


@pytest.mark.asyncio
async def test_generate_outline_presentation_title_not_empty():
    """Test that presentation title is not empty."""
    story = StoryAnalysis(
        topic="Important Topic",
        target_audience="General audience",
        key_message="Important message",
        tone="neutral",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    assert len(result.title.strip()) > 0, "Presentation title must not be empty"


@pytest.mark.asyncio
async def test_generate_outline_with_formal_tone():
    """Test outline generation with formal tone story."""
    story = StoryAnalysis(
        topic="Quarterly Financial Report",
        target_audience="Business audience",
        key_message="Financial performance insights",
        tone="formal",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    assert isinstance(result, PresentationOutline)
    assert len(result.slides) >= 3


@pytest.mark.asyncio
async def test_generate_outline_with_casual_tone():
    """Test outline generation with casual tone story."""
    story = StoryAnalysis(
        topic="Fun Team Building Ideas",
        target_audience="General audience",
        key_message="Great activities for team bonding",
        tone="casual",
        language="en",
    )

    result = await generate_outline(story, use_llm=False)

    assert isinstance(result, PresentationOutline)
    assert len(result.slides) >= 3


@pytest.mark.asyncio
async def test_generate_outline_logs_entry_with_input_info():
    """Test that generate_outline logs input information at function entry."""
    story = StoryAnalysis(
        topic="Test Topic with some words",
        target_audience="General audience",
        key_message="Test message with more words",
        tone="neutral",
        language="en",
    )

    with patch("pptx_agent.agents.outline_generator.logger") as mock_logger:
        await generate_outline(story, use_llm=False)

        # Verify INFO level log at entry with input text length (topic + key_message)
        input_text = story.topic + " " + story.key_message
        mock_logger.info.assert_any_call(
            "Starting outline generation: input_text_length=%d, language=%s",
            len(input_text),
            "en",
        )


@pytest.mark.asyncio
async def test_generate_outline_logs_exit_with_output_info():
    """Test that generate_outline logs output information at function exit."""
    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    with patch("pptx_agent.agents.outline_generator.logger") as mock_logger:
        result = await generate_outline(story, use_llm=False)

        # Verify INFO level log at exit with output slide count
        mock_logger.info.assert_any_call(
            "Outline generation completed: output_slides=%d, title=%s",
            len(result.slides),
            result.title,
        )


# Tests for LLM integration (use_llm=True)


@pytest.mark.asyncio
async def test_generate_outline_with_llm_integration():
    """Test OutlineGenerator with LLM (use_llm=True).

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    story = StoryAnalysis(
        topic="Machine Learning Basics",
        target_audience="Beginner audience",
        key_message="Learn ML fundamentals",
        tone="professional",
        language="en",
    )

    # Expected result from LLM
    expected_outline = PresentationOutline(
        title="Machine Learning Basics",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Machine Learning Basics",
                content="Learn ML fundamentals",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="What is ML?",
                content="ML overview",
            ),
            SlideContent(
                slide_number=3,
                layout_name="Title Slide",
                title="Conclusion",
                content="Summary",
            ),
        ],
        output_language="en",
    )

    # Mock the agent's run method
    with (
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
        patch("pptx_agent.agents.outline_generator.get_config") as mock_get_config,
        patch("pptx_agent.agents.outline_generator.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_outline)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        result = await generate_outline(story, use_llm=True)

        # Assert
        assert result == expected_outline
        mock_agent.run.assert_called_once()


@pytest.mark.asyncio
async def test_generate_outline_llm_calls_create_model():
    """Test that LLM integration creates model from config.

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    story = StoryAnalysis(
        topic="Test",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    expected_outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Test",
                content="Test message",
            ),
        ],
        output_language="en",
    )

    with (
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
        patch("pptx_agent.agents.outline_generator.get_config") as mock_get_config,
        patch("pptx_agent.agents.outline_generator.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_outline)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        await generate_outline(story, use_llm=True)

        # Assert that create_model was called
        mock_create_model.assert_called_once()


@pytest.mark.asyncio
async def test_generate_outline_llm_returns_result_output():
    """Test that LLM integration returns result.output from AgentRunResult.

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    story = StoryAnalysis(
        topic="Business Strategy",
        target_audience="Business audience",
        key_message="Strategic insights",
        tone="formal",
        language="en",
    )

    expected_outline = PresentationOutline(
        title="Business Strategy",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Business Strategy",
                content="Strategic insights",
            ),
        ],
        output_language="en",
    )

    with (
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
        patch("pptx_agent.agents.outline_generator.get_config") as mock_get_config,
        patch("pptx_agent.agents.outline_generator.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_outline)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        result = await generate_outline(story, use_llm=True)

        # Assert we get the output from AgentRunResult
        assert isinstance(result, PresentationOutline)
        assert result.title == "Business Strategy"
        assert len(result.slides) >= 1


@pytest.mark.asyncio
async def test_generate_outline_llm_false_uses_heuristic():
    """Test that use_llm=False still uses heuristic method.

    This ensures backward compatibility.
    """
    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    # Should NOT call the agent when use_llm=False
    with patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent:
        mock_agent.run = AsyncMock()

        # Act
        result = await generate_outline(story, use_llm=False)

        # Assert agent was NOT called
        mock_agent.run.assert_not_called()

        # Should still return valid PresentationOutline
        assert isinstance(result, PresentationOutline)
        assert len(result.slides) >= 3


# Tests for provider fallback logic (Task 6.7)


@pytest.mark.asyncio
async def test_generate_outline_with_fallback_on_primary_failure():
    """Test that fallback model is used when primary fails."""
    from unittest.mock import MagicMock

    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    # Expected result from fallback
    expected_outline = PresentationOutline(
        title="Fallback Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Fallback Test",
                content="Fallback succeeded",
            ),
        ],
        output_language="en",
    )

    primary_model = MagicMock()
    fallback_model = MagicMock()

    with (
        patch("pptx_agent.agents.outline_generator.get_config") as mock_get_config,
        patch(
            "pptx_agent.agents.outline_generator.create_model", return_value=primary_model
        ) as mock_create_model,
        patch(
            "pptx_agent.agents.outline_generator.create_fallback_model", return_value=fallback_model
        ) as mock_create_fallback,
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
    ):
        mock_get_config.return_value = "mock-config"

        # First call fails with primary, second succeeds with fallback
        mock_agent.run = AsyncMock(
            side_effect=[
                Exception("Primary provider failed"),
                AgentRunResult(output=expected_outline),
            ]
        )

        # Act
        result = await generate_outline(story, use_llm=True)

        # Assert
        assert result == expected_outline
        assert mock_agent.run.call_count == 2  # Called twice: primary + fallback
        mock_create_model.assert_called_once()
        mock_create_fallback.assert_called_once()


@pytest.mark.asyncio
async def test_generate_outline_both_providers_fail():
    """Test that exception is raised when both providers fail."""
    from unittest.mock import MagicMock

    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    primary_model = MagicMock()
    fallback_model = MagicMock()

    with (
        patch("pptx_agent.agents.outline_generator.get_config") as mock_get_config,
        patch("pptx_agent.agents.outline_generator.create_model", return_value=primary_model),
        patch(
            "pptx_agent.agents.outline_generator.create_fallback_model", return_value=fallback_model
        ),
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
    ):
        mock_get_config.return_value = "mock-config"

        # Both calls fail
        mock_agent.run = AsyncMock(side_effect=Exception("All providers failed"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await generate_outline(story, use_llm=True)


@pytest.mark.asyncio
async def test_generate_outline_heuristic_no_fallback():
    """Test that fallback is not used in heuristic mode."""
    story = StoryAnalysis(
        topic="Test Topic",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    with (
        patch("pptx_agent.agents.outline_generator._outline_agent") as mock_agent,
        patch("pptx_agent.agents.outline_generator.create_model") as mock_create_model,
        patch("pptx_agent.agents.outline_generator.create_fallback_model") as mock_create_fallback,
    ):
        mock_agent.run = AsyncMock()

        # Act
        result = await generate_outline(story, use_llm=False)

        # Assert
        assert result is not None
        assert isinstance(result, PresentationOutline)
        # No LLM calls should be made
        mock_agent.run.assert_not_called()
        mock_create_model.assert_not_called()
        mock_create_fallback.assert_not_called()
