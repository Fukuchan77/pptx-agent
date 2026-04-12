"""Unit tests for story analyzer agent.

Tests cover:
- StoryAnalysis schema validation
- Japanese text analysis
- English text analysis
- Markdown format parsing
- Edge cases (empty input, very long input, etc.)
"""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError
from pydantic_ai import AgentRunResult

from pptx_agent.agents.story_analyzer import StoryAnalysis, analyze_story
from pptx_agent.validators.input_validator import InputValidationError


def test_story_analysis_schema_imports():
    """Test that StoryAnalysis model can be imported."""

    assert StoryAnalysis is not None


def test_story_analysis_schema_fields():
    """Test that StoryAnalysis has required fields."""
    # Create a valid instance
    analysis = StoryAnalysis(
        topic="Sample Topic",
        target_audience="General audience",
        key_message="Main message",
        tone="professional",
        language="en",
    )

    assert analysis.topic == "Sample Topic"
    assert analysis.target_audience == "General audience"
    assert analysis.key_message == "Main message"
    assert analysis.tone == "professional"
    assert analysis.language == "en"


def test_story_analysis_schema_validation_empty_topic():
    """Test that StoryAnalysis validates empty topic."""
    with pytest.raises(ValidationError) as exc_info:
        StoryAnalysis(
            topic="",
            target_audience="General audience",
            key_message="Main message",
            tone="professional",
            language="en",
        )

    assert "topic" in str(exc_info.value).lower()


def test_story_analysis_schema_validation_invalid_language():
    """Test that StoryAnalysis validates language field."""
    with pytest.raises(ValidationError) as exc_info:
        StoryAnalysis(
            topic="Sample Topic",
            target_audience="General audience",
            key_message="Main message",
            tone="professional",
            language="fr",  # type: ignore[arg-type]  # Invalid - only 'en' and 'ja' allowed
        )

    assert "language" in str(exc_info.value).lower()


def test_analyze_story_function_exists():
    """Test that analyze_story function can be imported."""
    assert callable(analyze_story)


@pytest.mark.asyncio
async def test_analyze_story_with_english_text():
    """Test analyze_story with English text input."""
    text = """
    Introduction to Machine Learning

    Machine learning is a subset of artificial intelligence that enables systems
    to learn and improve from experience without being explicitly programmed.
    This presentation will cover the basics of machine learning for beginners
    in the field of data science.

    Key concepts include supervised learning, unsupervised learning, and
    reinforcement learning.
    """

    result = await analyze_story(text, use_llm=False)

    assert isinstance(result, StoryAnalysis)
    assert result.language == "en"
    assert len(result.topic) > 0
    assert len(result.target_audience) > 0
    assert len(result.key_message) > 0
    assert len(result.tone) > 0


@pytest.mark.asyncio
async def test_analyze_story_with_japanese_text():
    """Test analyze_story with Japanese text input."""
    text = """
    機械学習入門

    機械学習は人工知能の一分野であり、明示的にプログラムされることなく
    経験から学習し改善するシステムです。このプレゼンテーションでは、
    データサイエンス分野の初心者向けに機械学習の基礎を説明します。

    重要な概念には、教師あり学習、教師なし学習、強化学習が含まれます。
    """

    result = await analyze_story(text, use_llm=False)

    assert isinstance(result, StoryAnalysis)
    assert result.language == "ja"
    assert len(result.topic) > 0
    assert len(result.target_audience) > 0
    assert len(result.key_message) > 0
    assert len(result.tone) > 0


@pytest.mark.asyncio
async def test_analyze_story_with_markdown_format():
    """Test analyze_story with Markdown formatted text."""
    text = """
    # Project Overview

    ## Background
    This project aims to improve **customer satisfaction** through automation.

    ## Goals
    - Reduce response time
    - Increase accuracy
    - Improve user experience

    ## Target Audience
    *Business stakeholders* and technical teams
    """

    result = await analyze_story(text, use_llm=False)

    assert isinstance(result, StoryAnalysis)
    assert result.language == "en"
    assert "project" in result.topic.lower() or "customer" in result.topic.lower()


@pytest.mark.asyncio
async def test_analyze_story_with_empty_input():
    """Test analyze_story with empty input.

    Note: This tests the defensive validation in analyze_story().
    The pipeline layer (validate_and_sanitize) also validates input,
    but analyze_story() maintains its own check as a defensive measure.
    """
    with pytest.raises(InputValidationError, match=r"(?i)(empty|blank)") as exc_info:
        await analyze_story("", use_llm=False)

    assert "empty" in str(exc_info.value).lower() or "blank" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_analyze_story_with_whitespace_only():
    """Test analyze_story with whitespace-only input.

    Note: This tests the defensive validation in analyze_story().
    The pipeline layer (validate_and_sanitize) also validates input,
    but analyze_story() maintains its own check as a defensive measure.
    """
    with pytest.raises(InputValidationError, match=r"(?i)(empty|blank)") as exc_info:
        await analyze_story("   \n\t  ", use_llm=False)

    assert "empty" in str(exc_info.value).lower() or "blank" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_analyze_story_with_very_short_text():
    """Test analyze_story with very short text (edge case)."""
    text = "Sales report"

    result = await analyze_story(text, use_llm=False)

    assert isinstance(result, StoryAnalysis)
    assert len(result.topic) > 0


@pytest.mark.asyncio
async def test_analyze_story_with_very_long_text():
    """Test analyze_story with very long text (>10000 chars)."""
    # Create a long text by repeating content
    base_text = """
    Chapter on Machine Learning Fundamentals. Machine learning algorithms
    can be categorized into supervised, unsupervised, and reinforcement learning.
    Each category has its own use cases and applications.
    """
    long_text = base_text * 100  # Creates text > 10000 chars

    result = await analyze_story(long_text, use_llm=False)

    assert isinstance(result, StoryAnalysis)
    assert result.language == "en"


@pytest.mark.asyncio
async def test_analyze_story_detects_tone_formal():
    """Test that analyze_story can detect formal tone."""
    text = """
    Quarterly Financial Report

    This document presents the financial performance metrics for Q4 2025.
    The analysis demonstrates significant growth across all key performance indicators.
    Stakeholders are advised to review the detailed findings presented herein.
    """

    result = await analyze_story(text, use_llm=False)

    # Tone should be detected as formal/professional
    assert "formal" in result.tone.lower() or "professional" in result.tone.lower()


@pytest.mark.asyncio
async def test_analyze_story_detects_tone_casual():
    """Test that analyze_story can detect casual tone."""
    text = """
    Hey Team! Let's Talk About Our Awesome Project

    So, we've been working on this cool new feature that's gonna make our users super happy!
    It's pretty straightforward - we're basically making everything easier and more fun to use.
    Can't wait to show you what we've built!
    """

    result = await analyze_story(text, use_llm=False)

    # Tone should be detected as casual/informal
    assert (
        "casual" in result.tone.lower()
        or "informal" in result.tone.lower()
        or "friendly" in result.tone.lower()
    )


@pytest.mark.asyncio
async def test_analyze_story_with_mixed_language_defaults_to_dominant():
    """Test analyze_story with mixed English and Japanese text."""
    # Text with both English and Japanese, but mostly English
    text = """
    Introduction to AI and Machine Learning

    Artificial Intelligence (AI) is transforming industries worldwide.
    人工知能 is the Japanese term for AI.
    This presentation covers the fundamentals of AI technology.
    """

    result = await analyze_story(text, use_llm=False)

    # Should detect dominant language (English in this case)
    assert result.language == "en"


@pytest.mark.asyncio
async def test_analyze_story_extracts_target_audience():
    """Test that analyze_story extracts target audience from context."""
    text = """
    Beginner's Guide to Python Programming

    This tutorial is designed for complete beginners with no prior programming experience.
    We'll start with the basics and gradually build up your skills.
    Perfect for students and career changers looking to enter tech.
    """

    result = await analyze_story(text, use_llm=False)

    # Should identify beginners/students as target audience
    assert (
        "beginner" in result.target_audience.lower() or "student" in result.target_audience.lower()
    )


@pytest.mark.asyncio
async def test_analyze_story_extracts_key_message():
    """Test that analyze_story extracts the key message."""
    text = """
    Digital Transformation Success Story

    Our company successfully migrated to cloud infrastructure, resulting in
    40% cost reduction and 60% improvement in system performance.
    The key takeaway: investing in modern technology pays off.
    """

    result = await analyze_story(text, use_llm=False)

    # Key message should relate to cost reduction, performance, or technology investment
    key_msg_lower = result.key_message.lower()
    assert any(
        word in key_msg_lower for word in ["cost", "performance", "cloud", "technology", "success"]
    )


def test_story_analysis_schema_has_optional_suggested_structure():
    """Test that StoryAnalysis can include optional suggested structure."""
    analysis = StoryAnalysis(
        topic="Test Topic",
        target_audience="General",
        key_message="Message",
        tone="neutral",
        language="en",
        suggested_structure="Introduction, Main Content, Conclusion",
    )

    assert analysis.suggested_structure == "Introduction, Main Content, Conclusion"


def test_story_analysis_schema_suggested_structure_optional():
    """Test that suggested_structure field is optional."""
    # Should work without suggested_structure
    analysis = StoryAnalysis(
        topic="Test Topic",
        target_audience="General",
        key_message="Message",
        tone="neutral",
        language="en",
    )

    assert analysis.suggested_structure is None or analysis.suggested_structure == ""


@pytest.mark.asyncio
async def test_analyze_story_preserves_uppercase_in_key_message():
    """Test that uppercase letters (AI, API, CEO, etc.) are preserved in key message extraction.

    Regression test for bug where sentence_lower.split() loses original case information.
    Example: "The AI API" should remain "The AI API", not become "The ai api"
    """
    text = """
    Technology Overview

    Key message: The AI API enables seamless integration. The CEO announced the new SDK release.
    """

    result = await analyze_story(text, use_llm=False)

    # The key message should preserve uppercase acronyms
    expected = "AI API"
    assert expected in result.key_message, (
        f"Expected '{expected}' in message, got: {result.key_message}"
    )


@pytest.mark.asyncio
async def test_analyze_story_preserves_multiple_uppercase_words():
    """Test that multiple uppercase words are preserved in indicator-based extraction."""
    text = """
    Product Launch

    The key takeaway: Our new REST API supports JSON and XML formats for IoT devices.
    """

    result = await analyze_story(text, use_llm=False)

    # Should preserve REST, API, JSON, XML, IoT
    key_msg = result.key_message
    assert "REST" in key_msg or "rest" not in key_msg.lower() or "Rest" in key_msg
    assert "API" in key_msg, f"Expected 'API' preserved, got: {key_msg}"
    assert "JSON" in key_msg, f"Expected 'JSON' preserved, got: {key_msg}"
    assert "XML" in key_msg, f"Expected 'XML' preserved, got: {key_msg}"
    assert "IoT" in key_msg, f"Expected 'IoT' preserved, got: {key_msg}"


@pytest.mark.asyncio
async def test_analyze_story_preserves_case_with_conclusion_indicator():
    """Test case preservation with 'conclusion' indicator."""
    text = """
    Research Summary

    Conclusion: The ML model achieved 95% accuracy on the MNIST dataset using CNN architecture.
    """

    result = await analyze_story(text, use_llm=False)

    # Should preserve ML, MNIST, CNN
    key_msg = result.key_message
    assert "ML" in key_msg, f"Expected 'ML' preserved, got: {key_msg}"
    assert "MNIST" in key_msg, f"Expected 'MNIST' preserved, got: {key_msg}"
    assert "CNN" in key_msg, f"Expected 'CNN' preserved, got: {key_msg}"


@pytest.mark.asyncio
async def test_target_audience_no_false_positive_for_all_substring():
    """Test 'all' substring in words like 'install', 'wall' doesn't trigger false match.

    RED Phase: This test documents the false positive behavior.
    Since "all" is in the "general" category (checked last) and the default is
    also "General audience", we can't easily test the difference. However, we
    document expected behavior for completeness. The "intro" test below
    demonstrates the false positive issue more clearly.
    """
    # These should all return "General audience" as default (not via false match)
    # After fix: Will still return "General audience" but via default path, not keyword match
    text_install = "Please install the software on your computer."
    result = await analyze_story(text_install, use_llm=False)
    assert result.target_audience.lower() == "general audience"

    text_wall = "The wall needs repainting this month."
    result2 = await analyze_story(text_wall, use_llm=False)
    assert result2.target_audience.lower() == "general audience"

    text_finally = "Finally we conclude this report."
    result3 = await analyze_story(text_finally, use_llm=False)
    assert result3.target_audience.lower() == "general audience"


@pytest.mark.asyncio
async def test_target_audience_no_false_positive_for_intro_substring():
    """Test 'intro' substring in 'introduce', 'introducing' doesn't trigger false match.

    RED Phase: This test exposes the bug where "intro" in text_lower causes
    false positives. The test asserts the DESIRED behavior (after fix) and
    should FAIL with current buggy code.
    """
    # "intro" is in the "beginner" keyword list, which is checked FIRST
    # If "introduce" matches "intro", it will return "Beginner audience"
    # But "introduce" should NOT match "intro" - they're different words
    # After fix: should return "General audience" as default
    # Currently: returns "Beginner audience" because "intro" in "introduce" matches

    text_introduce = "We introduce the new feature today."
    result = await analyze_story(text_introduce, use_llm=False)
    # Should NOT be "Beginner audience" after fix
    assert "beginner" not in result.target_audience.lower(), (
        f"FALSE POSITIVE BUG: 'introduce' incorrectly matched 'intro', "
        f"got: {result.target_audience}"
    )

    text_introducing = "Introducing our new platform this week."
    result2 = await analyze_story(text_introducing, use_llm=False)
    # Should NOT be "Beginner audience" after fix
    assert "beginner" not in result2.target_audience.lower(), (
        f"FALSE POSITIVE BUG: 'introducing' incorrectly matched 'intro', "
        f"got: {result2.target_audience}"
    )


@pytest.mark.asyncio
async def test_target_audience_correct_match_for_all():
    """Test that legitimate 'all' and 'everyone' keywords are correctly detected.

    This ensures our fix doesn't break valid matches.
    """
    text_all = "This presentation is for all users in the organization."
    result_all = await analyze_story(text_all, use_llm=False)
    assert "general" in result_all.target_audience.lower(), (
        f"'for all users' should match general audience, got: {result_all.target_audience}"
    )

    text_everyone = "Everyone can benefit from this training."
    result_everyone = await analyze_story(text_everyone, use_llm=False)
    assert "general" in result_everyone.target_audience.lower(), (
        f"'everyone' should match general audience, got: {result_everyone.target_audience}"
    )


@pytest.mark.asyncio
async def test_target_audience_correct_match_for_intro():
    """Test that legitimate 'intro' keyword is correctly detected.

    This ensures our fix doesn't break valid matches.
    """
    text_intro = "This is an intro level course."
    result = await analyze_story(text_intro, use_llm=False)
    # Should match "beginner" because "intro" is a valid keyword in the beginner list
    assert "beginner" in result.target_audience.lower(), (
        f"'intro level' should match beginner audience, got: {result.target_audience}"
    )

    text_introduction = "This introduction covers the basics."
    result2 = await analyze_story(text_introduction, use_llm=False)
    # "introduction" is a valid keyword in the beginner list
    assert "beginner" in result2.target_audience.lower(), (
        f"'introduction' should match beginner audience, got: {result2.target_audience}"
    )


@pytest.mark.asyncio
async def test_target_audience_no_false_positive_for_expert_substring():
    """Test 'expert' substring in 'experiment' doesn't trigger false match.

    RED Phase: This test exposes the bug where "expert" in text causes
    false positives with words like "experiment", "expertise", etc.
    Current code uses substring matching for "expert", so "experiment"
    incorrectly returns "Advanced audience".
    After fix: should return "General audience" as default.
    """
    text_experiment = "We conducted an experiment to test the hypothesis."
    result = await analyze_story(text_experiment, use_llm=False)
    # Should NOT be "Advanced audience" after fix
    assert "advanced" not in result.target_audience.lower(), (
        f"FALSE POSITIVE BUG: 'experiment' incorrectly matched 'expert', "
        f"got: {result.target_audience}"
    )
    assert result.target_audience.lower() == "general audience", (
        f"Expected 'General audience', got: {result.target_audience}"
    )


@pytest.mark.asyncio
async def test_target_audience_correct_match_for_expert():
    """Test that legitimate 'expert' keyword is correctly detected.

    This ensures our fix doesn't break valid matches.
    """
    text_expert = "This course is designed for expert developers."
    result = await analyze_story(text_expert, use_llm=False)
    # Should match "advanced" because "expert" is a valid keyword
    assert "advanced" in result.target_audience.lower(), (
        f"'expert' should match advanced audience, got: {result.target_audience}"
    )

    text_experienced = "For experienced professionals in the field."
    result2 = await analyze_story(text_experienced, use_llm=False)
    # "experienced" is also in the advanced keyword list
    assert "advanced" in result2.target_audience.lower(), (
        f"'experienced' should match advanced audience, got: {result2.target_audience}"
    )


# Tests for LLM integration (use_llm=True)


@pytest.mark.asyncio
async def test_analyze_story_with_llm_integration():
    """Test StoryAnalyzer with LLM (use_llm=True).

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    text = "Introduction to Machine Learning for beginners"

    # Expected result from LLM
    expected_analysis = StoryAnalysis(
        topic="Introduction to Machine Learning",
        target_audience="Beginner audience",
        key_message="Learn ML fundamentals",
        tone="professional",
        language="en",
    )

    # Mock the agent's run method
    with (
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
        patch("pptx_agent.agents.story_analyzer.get_config") as mock_get_config,
        patch("pptx_agent.agents.story_analyzer.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_analysis)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        result = await analyze_story(text, use_llm=True)

        # Assert
        assert result == expected_analysis
        mock_agent.run.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_story_llm_calls_create_model():
    """Test that LLM integration creates model from config.

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    text = "Test story text"

    expected_analysis = StoryAnalysis(
        topic="Test",
        target_audience="General audience",
        key_message="Test message",
        tone="neutral",
        language="en",
    )

    with (
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
        patch("pptx_agent.agents.story_analyzer.get_config") as mock_get_config,
        patch("pptx_agent.agents.story_analyzer.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_analysis)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        await analyze_story(text, use_llm=True)

        # Assert that create_model was called
        mock_create_model.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_story_llm_returns_result_data():
    """Test that LLM integration returns result.output from AgentRunResult.

    RED PHASE: This test should FAIL until we implement LLM integration.
    """
    text = "Business presentation for executives"

    expected_analysis = StoryAnalysis(
        topic="Business Strategy",
        target_audience="Business audience",
        key_message="Strategic insights",
        tone="formal",
        language="en",
    )

    with (
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
        patch("pptx_agent.agents.story_analyzer.get_config") as mock_get_config,
        patch("pptx_agent.agents.story_analyzer.create_model") as mock_create_model,
    ):
        mock_result = AgentRunResult(output=expected_analysis)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_config.return_value = "mock-config"
        mock_create_model.return_value = "mock-model"

        # Act
        result = await analyze_story(text, use_llm=True)

        # Assert we get the output from AgentRunResult
        assert isinstance(result, StoryAnalysis)
        assert result.topic == "Business Strategy"
        assert result.target_audience == "Business audience"


@pytest.mark.asyncio
async def test_analyze_story_llm_false_uses_heuristic():
    """Test that use_llm=False still uses heuristic method.

    This ensures backward compatibility.
    """
    text = "Machine learning introduction"

    # Should NOT call the agent when use_llm=False
    with patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent:
        mock_agent.run = AsyncMock()

        # Act
        result = await analyze_story(text, use_llm=False)

        # Assert agent was NOT called
        mock_agent.run.assert_not_called()

        # Should still return valid StoryAnalysis
        assert isinstance(result, StoryAnalysis)
        assert len(result.topic) > 0


# Tests for provider fallback logic (Task 6.7)


@pytest.mark.asyncio
async def test_analyze_story_with_fallback_on_primary_failure():
    """Test that fallback model is used when primary fails."""
    from unittest.mock import MagicMock

    text = "Test story for fallback"

    # Expected result from fallback
    expected_analysis = StoryAnalysis(
        topic="Fallback Test",
        target_audience="General audience",
        key_message="Fallback succeeded",
        tone="neutral",
        language="en",
    )

    primary_model = MagicMock()
    fallback_model = MagicMock()

    with (
        patch("pptx_agent.agents.story_analyzer.get_config") as mock_get_config,
        patch(
            "pptx_agent.agents.story_analyzer.create_model", return_value=primary_model
        ) as mock_create_model,
        patch(
            "pptx_agent.agents.story_analyzer.create_fallback_model", return_value=fallback_model
        ) as mock_create_fallback,
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
    ):
        mock_get_config.return_value = "mock-config"

        # First call fails with primary, second succeeds with fallback
        mock_agent.run = AsyncMock(
            side_effect=[
                Exception("Primary provider failed"),
                AgentRunResult(output=expected_analysis),
            ]
        )

        # Act
        result = await analyze_story(text, use_llm=True)

        # Assert
        assert result == expected_analysis
        assert mock_agent.run.call_count == 2  # Called twice: primary + fallback
        mock_create_model.assert_called_once()
        mock_create_fallback.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_story_both_providers_fail():
    """Test that exception is raised when both providers fail."""
    from unittest.mock import MagicMock

    text = "Test story for double failure"

    primary_model = MagicMock()
    fallback_model = MagicMock()

    with (
        patch("pptx_agent.agents.story_analyzer.get_config") as mock_get_config,
        patch("pptx_agent.agents.story_analyzer.create_model", return_value=primary_model),
        patch(
            "pptx_agent.agents.story_analyzer.create_fallback_model", return_value=fallback_model
        ),
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
    ):
        mock_get_config.return_value = "mock-config"

        # Both calls fail
        mock_agent.run = AsyncMock(side_effect=Exception("All providers failed"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await analyze_story(text, use_llm=True)


@pytest.mark.asyncio
async def test_analyze_story_heuristic_no_fallback():
    """Test that fallback is not used in heuristic mode."""
    text = "Test story for heuristic mode"

    with (
        patch("pptx_agent.agents.story_analyzer._story_agent") as mock_agent,
        patch("pptx_agent.agents.story_analyzer.create_model") as mock_create_model,
        patch("pptx_agent.agents.story_analyzer.create_fallback_model") as mock_create_fallback,
    ):
        mock_agent.run = AsyncMock()

        # Act
        result = await analyze_story(text, use_llm=False)

        # Assert
        assert result is not None
        assert isinstance(result, StoryAnalysis)
        # No LLM calls should be made
        mock_agent.run.assert_not_called()
        mock_create_model.assert_not_called()
        mock_create_fallback.assert_not_called()
