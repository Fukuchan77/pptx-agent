# pyright: reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnusedVariable=false
"""Shared fixtures for integration tests.

Provides reusable LLM mock pipeline fixtures to eliminate duplication
across test_smartart.py, test_charts_tables.py, and test_multilanguage.py.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Literal
from unittest.mock import AsyncMock, patch

from pptx_agent.agents.story_analyzer import StoryAnalysis
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema, SlideSchema
from pptx_agent.schemas.text import TextBlock


def make_mock_pipeline_data(
    topic: str = "Test Topic",
    language: Literal["en", "ja"] = "en",
    slides: list[dict[str, Any]] | None = None,
) -> tuple[StoryAnalysis, PresentationOutline, PresentationSchema]:
    """Build minimal StoryAnalysis, PresentationOutline, and PresentationSchema.

    Args:
        topic: Presentation topic
        language: Output language code
        slides: Optional list of slide dicts with keys:
            layout_name, title, content (list of content blocks).
            Defaults to a 3-slide title/content/end structure.

    Returns:
        Tuple of (mock_story, mock_outline, mock_content)
    """
    mock_story = StoryAnalysis(
        topic=topic,
        target_audience="All",
        key_message=topic,
        tone="professional",
        language=language,
    )

    if slides is None:
        slides = [
            {
                "layout_name": "Title Slide",
                "title": "Title",
                "content": [TextBlock(placeholder_name="Subtitle", text="Test", language=language)],
            },
            {
                "layout_name": "Title and Content",
                "title": topic,
                "content": [
                    TextBlock(
                        placeholder_name="Content Placeholder 2",
                        text="Content text",
                        language=language,
                    )
                ],
            },
            {
                "layout_name": "Title Slide",
                "title": "End",
                "content": [TextBlock(placeholder_name="Subtitle", text="Test", language=language)],
            },
        ]

    mock_outline = PresentationOutline(
        title=topic,
        output_language=language,
        slides=[
            SlideContent(
                slide_number=i + 1,
                layout_name=s["layout_name"],
                title=s["title"],
                content=s.get("content_text", s["title"]),
            )
            for i, s in enumerate(slides)
        ],
    )

    mock_content = PresentationSchema(
        title=topic,
        slides=[
            SlideSchema(
                layout_name=s["layout_name"],
                title=s["title"],
                content=s["content"],
                notes=s.get("notes", ""),
            )
            for s in slides
        ],
    )

    return mock_story, mock_outline, mock_content


@contextmanager
def llm_mock_pipeline(
    topic: str = "Test Topic",
    language: Literal["en", "ja"] = "en",
    slides: list[dict[str, Any]] | None = None,
) -> Generator[tuple[AsyncMock, AsyncMock, AsyncMock], None, None]:
    """Context manager that patches the 3 LLM pipeline functions with mock data.

    Args:
        topic: Presentation topic
        language: Output language code
        slides: Optional custom slide definitions

    Yields:
        Tuple of (mock_analyze, mock_outline_gen, mock_content_gen)

    Example:
        >>> with llm_mock_pipeline(topic="Sales") as (analyze, outline, content):
        ...     result = await generate_presentation(..., use_llm=True)
        ...     assert analyze.called
    """
    mock_story, mock_outline, mock_content = make_mock_pipeline_data(
        topic=topic,
        language=language,
        slides=slides,
    )

    with (
        patch("pptx_agent.pipeline.analyze_story", new_callable=AsyncMock) as mock_analyze,
        patch("pptx_agent.pipeline.generate_outline", new_callable=AsyncMock) as mock_outline_gen,
        patch("pptx_agent.pipeline.generate_content", new_callable=AsyncMock) as mock_content_gen,
    ):
        mock_analyze.return_value = mock_story
        mock_outline_gen.return_value = mock_outline
        mock_content_gen.return_value = mock_content

        yield mock_analyze, mock_outline_gen, mock_content_gen
