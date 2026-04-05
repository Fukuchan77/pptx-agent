"""Unit tests for overflow resolver instruction generation.

RED PHASE: Tests for generating LLM instructions for slide split and summarization strategies.
"""

from pptx_agent.agents.overflow_resolver import (
    OverflowResolution,
    OverflowStrategy,
    generate_slide_split_instruction,
    generate_summarization_instruction,
)
from pptx_agent.schemas.outline import SlideContent


class TestSlideSplitInstructions:
    """Tests for slide split instruction generation."""

    def test_generate_slide_split_instruction_exists(self) -> None:
        """Test that generate_slide_split_instruction function exists.

        RED PHASE: This test should FAIL because the function doesn't exist yet.
        """
        assert callable(generate_slide_split_instruction)

    def test_generates_instruction_with_split_point(self) -> None:
        """Test that instruction includes the split point information.

        RED PHASE: This test should FAIL - function not implemented.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SLIDE_SPLIT,
            overflow_detected=True,
            overflow_percentage=75.0,
            split_point=250,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Long Content Slide",
            content="A" * 500,  # 500 characters
        )

        # Act
        instruction = generate_slide_split_instruction(resolution, original_slide)

        # Assert
        assert isinstance(instruction, str)
        assert len(instruction) > 0
        assert "split" in instruction.lower()
        assert "250" in instruction or "around position 250" in instruction.lower()

    def test_instruction_includes_original_title(self) -> None:
        """Test that instruction includes the original slide title.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SLIDE_SPLIT,
            overflow_detected=True,
            overflow_percentage=60.0,
            split_point=300,
        )

        original_slide = SlideContent(
            slide_number=2,
            layout_name="Title and Content",
            title="Important Topic",
            content="X" * 600,
        )

        # Act
        instruction = generate_slide_split_instruction(resolution, original_slide)

        # Assert
        assert "Important Topic" in instruction

    def test_instruction_mentions_two_slides(self) -> None:
        """Test that instruction mentions splitting into two slides.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SLIDE_SPLIT,
            overflow_detected=True,
            overflow_percentage=80.0,
            split_point=200,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="B" * 400,
        )

        # Act
        instruction = generate_slide_split_instruction(resolution, original_slide)

        # Assert
        assert "two slides" in instruction.lower() or "2 slides" in instruction.lower()

    def test_instruction_includes_original_content(self) -> None:
        """Test that instruction includes the original content for context.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        test_content = "This is important content that needs to be split."
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SLIDE_SPLIT,
            overflow_detected=True,
            overflow_percentage=50.0,
            split_point=25,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content=test_content,
        )

        # Act
        instruction = generate_slide_split_instruction(resolution, original_slide)

        # Assert
        assert test_content in instruction


class TestSummarizationInstructions:
    """Tests for content summarization instruction generation."""

    def test_generate_summarization_instruction_exists(self) -> None:
        """Test that generate_summarization_instruction function exists.

        RED PHASE: This test should FAIL because the function doesn't exist yet.
        """
        assert callable(generate_summarization_instruction)

    def test_generates_instruction_with_target_length(self) -> None:
        """Test that instruction includes the target length information.

        RED PHASE: This test should FAIL - function not implemented.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SUMMARIZE,
            overflow_detected=True,
            overflow_percentage=150.0,
            target_length=500,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Detailed Analysis",
            content="Y" * 1250,  # 150% overflow of 500 char limit
        )

        # Act
        instruction = generate_summarization_instruction(resolution, original_slide)

        # Assert
        assert isinstance(instruction, str)
        assert len(instruction) > 0
        assert "summarize" in instruction.lower() or "condense" in instruction.lower()
        assert "500" in instruction or "500 characters" in instruction.lower()

    def test_instruction_preserves_title(self) -> None:
        """Test that instruction mentions keeping the same title.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SUMMARIZE,
            overflow_detected=True,
            overflow_percentage=120.0,
            target_length=400,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Key Points",
            content="Z" * 880,
        )

        # Act
        instruction = generate_summarization_instruction(resolution, original_slide)

        # Assert
        assert "Key Points" in instruction
        assert "title" in instruction.lower() or "same" in instruction.lower()

    def test_instruction_includes_original_content(self) -> None:
        """Test that instruction includes the original content to summarize.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        test_content = (
            "This is very detailed content that needs to be condensed "
            "significantly to fit within the character limit."
        )
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SUMMARIZE,
            overflow_detected=True,
            overflow_percentage=200.0,
            target_length=50,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content=test_content,
        )

        # Act
        instruction = generate_summarization_instruction(resolution, original_slide)

        # Assert
        assert test_content in instruction

    def test_instruction_emphasizes_key_information(self) -> None:
        """Test that instruction mentions preserving key information.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        resolution = OverflowResolution(
            strategy=OverflowStrategy.SUMMARIZE,
            overflow_detected=True,
            overflow_percentage=180.0,
            target_length=300,
        )

        original_slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="C" * 840,
        )

        # Act
        instruction = generate_summarization_instruction(resolution, original_slide)

        # Assert
        assert any(
            keyword in instruction.lower()
            for keyword in ["key", "essential", "important", "main", "core"]
        )
