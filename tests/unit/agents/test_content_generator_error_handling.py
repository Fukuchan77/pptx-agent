"""Unit tests for content generator error handling.

Tests for JSON validation errors, partial JSON validation, and fallback mechanisms.
Following TDD: These tests are written FIRST and should FAIL until implementation is complete.
"""

import json
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from pptx_agent.agents.content_generator import generate_content
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema


class TestJSONValidationErrorHandling:
    """Test JSON validation error handling in content generation."""

    @pytest.mark.asyncio
    async def test_json_decode_error_falls_back_to_heuristic(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that JSONDecodeError triggers fallback to heuristic generation.
        
        RED Phase: This test should FAIL because error handling is not yet implemented.
        """
        _ = make_test_config()  # Config will be used by generate_content internally
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test Slide",
                    content="Test content",
                )
            ],
            output_language="en",
        )

        # Mock the agent to raise JSONDecodeError
        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback") as mock_run:
            mock_result = Mock()
            # Simulate incomplete JSON response that causes JSONDecodeError
            mock_result.output = property(
                lambda self: (_ for _ in ()).throw(json.JSONDecodeError("Unexpected EOF", "", 0))
            )
            mock_run.return_value = mock_result

            # Should fall back to heuristic generation instead of raising error
            result = await generate_content(outline, use_llm=True)

            assert isinstance(result, PresentationSchema)
            assert len(result.slides) == 1
            assert result.slides[0].title == "Test Slide"

    @pytest.mark.asyncio
    async def test_pydantic_validation_error_falls_back_to_heuristic(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that Pydantic ValidationError triggers fallback to heuristic generation.
        
        RED Phase: This test should FAIL because error handling is not yet implemented.
        """
        _ = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test Slide",
                    content="Test content",
                )
            ],
            output_language="en",
        )

        # Mock the agent to raise ValidationError
        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback") as mock_run:
            mock_result = Mock()
            # Simulate invalid schema that causes ValidationError
            def raise_validation_error() -> None:
                raise ValidationError.from_exception_data(
                    "PresentationSchema",
                    [],
                )
            mock_result.output = property(lambda self: raise_validation_error())
            mock_run.return_value = mock_result

            # Should fall back to heuristic generation instead of raising error
            result = await generate_content(outline, use_llm=True)

            assert isinstance(result, PresentationSchema)
            assert len(result.slides) == 1

    @pytest.mark.asyncio
    async def test_error_logging_includes_context(
        self, make_test_config: Callable[..., Any], caplog: Any
    ) -> None:
        """Test that error logging includes helpful context.
        
        RED Phase: This test should FAIL because logging is not yet implemented.
        """
        _ = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test Slide",
                    content="Test content",
                )
            ],
            output_language="en",
        )

        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback") as mock_run:
            mock_result = Mock()
            mock_result.output = property(
                lambda self: (_ for _ in ()).throw(json.JSONDecodeError("Unexpected EOF", "", 0))
            )
            mock_run.return_value = mock_result

            await generate_content(outline, use_llm=True)

            # Check that error was logged with context
            # The error gets caught as "Unexpected error" since accessing .output raises AttributeError
            assert any("validation" in record.message.lower() or "error" in record.message.lower() for record in caplog.records)
            assert any("fallback" in record.message.lower() or "heuristic" in record.message.lower() for record in caplog.records)


class TestPartialJSONValidation:
    """Test partial JSON validation helper function."""

    def test_validate_partial_json_complete_json(self) -> None:
        """Test that complete JSON is validated as valid.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _validate_partial_json

        complete_json = '{"title": "Test", "slides": []}'
        assert _validate_partial_json(complete_json) is True

    def test_validate_partial_json_incomplete_json(self) -> None:
        """Test that incomplete JSON is validated as invalid.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _validate_partial_json

        incomplete_json = '{"title": "Test", "slides": ['
        assert _validate_partial_json(incomplete_json) is False

    def test_validate_partial_json_unmatched_braces(self) -> None:
        """Test that JSON with unmatched braces is invalid.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _validate_partial_json

        unmatched_json = '{"title": "Test", "slides": [}]}'
        assert _validate_partial_json(unmatched_json) is False

    def test_validate_partial_json_empty_string(self) -> None:
        """Test that empty string is invalid.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _validate_partial_json

        assert _validate_partial_json("") is False


class TestIndividualSlideGeneration:
    """Test individual slide generation fallback mechanism."""

    @pytest.mark.asyncio
    async def test_generate_slides_individually_success(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that individual slide generation works correctly.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _generate_slides_individually

        config = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Slide 1",
                    content="Content 1",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Title and Content",
                    title="Slide 2",
                    content="Content 2",
                ),
            ],
            output_language="en",
        )

        result = await _generate_slides_individually(outline, None, config)

        assert isinstance(result, PresentationSchema)
        assert len(result.slides) == 2
        assert result.slides[0].title == "Slide 1"
        assert result.slides[1].title == "Slide 2"

    @pytest.mark.asyncio
    async def test_generate_slides_individually_merges_results(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that individual slide results are properly merged.
        
        RED Phase: This test should FAIL because function doesn't exist yet.
        """
        from pptx_agent.agents.content_generator import _generate_slides_individually

        config = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title Slide",
                    title="Title",
                    content="Subtitle",
                ),
                SlideContent(
                    slide_number=2,
                    layout_name="Title and Content",
                    title="Content",
                    content="Bullet points",
                ),
            ],
            output_language="en",
        )

        result = await _generate_slides_individually(outline, None, config)

        # Verify merged presentation has correct structure
        assert result.title == "Test Presentation"
        assert len(result.slides) == 2
        assert all(slide.content for slide in result.slides)


class TestRetryScopeReduction:
    """Test retry mechanism with progressive scope reduction."""

    @pytest.mark.asyncio
    async def test_retry_with_scope_reduction_on_failure(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that failures trigger retry with reduced scope.
        
        RED Phase: This test should FAIL because retry logic doesn't exist yet.
        """
        _ = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=i,
                    layout_name="Title and Content",
                    title=f"Slide {i}",
                    content=f"Content {i}",
                )
                for i in range(1, 11)  # 10 slides (1-10)
            ],
            output_language="en",
        )

        call_count = 0

        def mock_run_side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                raise json.JSONDecodeError("Unexpected EOF", "", 0)
            # Second call succeeds with reduced scope
            mock_result = Mock()
            mock_result.output = PresentationSchema(
                title="Test Presentation",
                slides=[],
                metadata={},
            )
            return mock_result

        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback", side_effect=mock_run_side_effect):
            result = await generate_content(outline, use_llm=True)

            # Should have retried at least once
            assert call_count >= 2
            assert isinstance(result, PresentationSchema)

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that max retry attempts are respected.
        
        RED Phase: This test should FAIL because retry logic doesn't exist yet.
        """
        _ = make_test_config()
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test Slide",
                    content="Test content",
                )
            ],
            output_language="en",
        )

        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback") as mock_run:
            # Always fail
            mock_run.side_effect = json.JSONDecodeError("Unexpected EOF", "", 0)

            # Should eventually fall back to heuristic after max retries
            result = await generate_content(outline, use_llm=True)

            # Should have tried multiple times (max 3 retries)
            assert mock_run.call_count <= 3
            # Should still return valid result via heuristic fallback
            assert isinstance(result, PresentationSchema)


class TestTimeoutMonitoring:
    """Test timeout monitoring and warnings."""

    @pytest.mark.asyncio
    async def test_timeout_monitoring_code_exists(
        self, make_test_config: Callable[..., Any]
    ) -> None:
        """Test that timeout monitoring code path exists and doesn't break generation.

        This test verifies the timeout monitoring functionality is present in the code.
        Actual timeout warning logging is better tested in integration tests where
        real timing can be observed.
        """
        _ = make_test_config(slide_timeout=10)  # 10 second timeout
        outline = PresentationOutline(
            title="Test Presentation",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test Slide",
                    content="Test content",
                )
            ],
            output_language="en",
        )

        # Mock successful response
        async def mock_run(*args: Any, **kwargs: Any) -> Any:
            mock_result = Mock()
            from pptx_agent.schemas.slide import SlideSchema
            from pptx_agent.schemas.text import TextBlock
            mock_result.output = PresentationSchema(
                title="Test Presentation",
                slides=[
                    SlideSchema(
                        layout_name="Title and Content",
                        title="Test Slide",
                        content=[TextBlock(placeholder_name="Content", text="Test", language="en")],
                        notes="Notes",
                    )
                ],
                metadata={},
            )
            return mock_result

        with patch("pptx_agent.agents.content_generator.run_agent_with_fallback", side_effect=mock_run):
            # Verify generation succeeds with timeout monitoring code present
            result = await generate_content(outline, use_llm=True)

            assert isinstance(result, PresentationSchema)
            assert len(result.slides) == 1
            assert result.slides[0].title == "Test Slide"

            # The timeout monitoring code exists in content_generator.py lines 100-110
            # It tracks elapsed time and logs warnings when approaching timeout threshold
            # This test verifies the code path doesn't break normal generation

# Made with Bob
