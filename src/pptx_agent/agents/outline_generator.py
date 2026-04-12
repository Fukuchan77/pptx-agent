"""Outline generator agent for creating presentation structure.

This module generates a PresentationOutline from StoryAnalysis input.
The outline includes:
- Presentation title
- Slide structure with titles, layout types, and content placeholders
- Language-appropriate output (en or ja)
- 3-30 slides per FR-019 requirement

Uses heuristic-based generation for initial implementation.
Future versions may integrate LLM-based generation.
"""

import logging

from pydantic_ai import Agent

from pptx_agent.agents.prompts import OUTLINE_GENERATOR_PROMPT
from pptx_agent.agents.story_analyzer import StoryAnalysis
from pptx_agent.agents.utils import run_agent_with_fallback
from pptx_agent.config import get_config
from pptx_agent.constants import MAX_SLIDES, MIN_SLIDES
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.template_manifest import TemplateManifest

logger = logging.getLogger(__name__)

# Constants for slide generation
DEFAULT_SLIDE_COUNT = 5  # Default number of slides for standard presentation

# Constants for slide count calculation
COMPLEX_TOPIC_WORD_THRESHOLD = 10  # Words in topic indicating complexity
COMPLEX_MESSAGE_WORD_THRESHOLD = 20  # Words in message indicating complexity
SLIDE_INCREMENT_FOR_COMPLEXITY = 2  # Extra slides for complex content

# Constants for layout selection
LONG_PRESENTATION_THRESHOLD = 8  # Slides count for "long" presentation
SECTION_DIVIDER_INTERVAL = 4  # Interval for section dividers
OVERVIEW_SLIDE_NUMBER = 2  # Position of overview slide

# Module-level agent instance (model provided at runtime)
_outline_agent: Agent[None, PresentationOutline] = Agent(
    output_type=PresentationOutline,
    system_prompt=OUTLINE_GENERATOR_PROMPT,
)


async def generate_outline(
    story: StoryAnalysis,
    manifest: TemplateManifest | None = None,
    *,
    use_llm: bool = True,
) -> PresentationOutline:
    """Generate presentation outline from story analysis.

    Creates a structured presentation outline with:
    - Title slide
    - Content slides based on story structure
    - Conclusion slide

    Args:
        story: StoryAnalysis object containing topic, audience, message, tone, language
        manifest: Optional template manifest for providing layout information
        use_llm: If True, use LLM agent for generation. If False, use heuristic fallback
                 for testing/debugging (default: True).

    Returns:
        PresentationOutline object with complete slide structure

    Raises:
        ValueError: If story is invalid or cannot generate valid outline
    """
    if use_llm:
        # Use LLM for outline generation with fallback
        config = get_config()

        # Format story as prompt for LLM
        prompt = _build_outline_prompt(story, manifest)

        # Use centralized fallback mechanism
        result = await run_agent_with_fallback(_outline_agent, prompt, config)
        return result.output
    # Use heuristic fallback for testing/debugging
    return _heuristic_generate_outline(story)


def _build_outline_prompt(
    story: StoryAnalysis,
    manifest: TemplateManifest | None = None,
) -> str:
    """Build prompt for outline generation including layout information from manifest.

    Args:
        story: StoryAnalysis object containing presentation requirements
        manifest: Optional template manifest with layout information

    Returns:
        Formatted prompt string for LLM
    """
    # Base prompt with story information
    prompt = f"""Generate a presentation outline based on this story analysis:

Topic: {story.topic}
Target Audience: {story.target_audience}
Key Message: {story.key_message}
Tone: {story.tone}
Language: {story.language}
Suggested Structure: {story.suggested_structure or "Standard presentation structure"}

The presentation should have between {MIN_SLIDES} and {MAX_SLIDES} slides.
"""

    # Add available layouts information if manifest is provided
    if manifest and manifest.layouts:
        layout_names = [layout.name for layout in manifest.layouts]
        prompt += f"\n\nAvailable slide layouts in template: {', '.join(layout_names)}"

    return prompt


def _heuristic_generate_outline(story: StoryAnalysis) -> PresentationOutline:
    """Heuristic-based outline generation (fallback for testing/debugging).

    Creates a structured presentation outline with:
    - Title slide
    - Content slides based on story structure
    - Conclusion slide

    Args:
        story: StoryAnalysis object containing topic, audience, message, tone, language

    Returns:
        PresentationOutline object with complete slide structure

    Raises:
        ValueError: If story is invalid or cannot generate valid outline
    """
    # Log function entry with input information
    input_text = story.topic + " " + story.key_message
    logger.info(
        "Starting outline generation: input_text_length=%d, language=%s",
        len(input_text),
        story.language,
    )

    # Determine presentation title from story topic
    presentation_title = _generate_presentation_title(story)

    # Determine number of slides based on story complexity
    slide_count = _calculate_slide_count(story)

    # Generate slides
    slides = _generate_slides(story, slide_count)

    # Create and return presentation outline
    result = PresentationOutline(
        title=presentation_title,
        slides=slides,
        output_language=story.language,
    )

    # Log function exit with output information
    logger.info(
        "Outline generation completed: output_slides=%d, title=%s",
        len(result.slides),
        result.title,
    )

    return result


def _generate_presentation_title(story: StoryAnalysis) -> str:
    """Generate presentation title from story topic.

    Args:
        story: StoryAnalysis object

    Returns:
        Presentation title string
    """
    # Use story topic as the presentation title
    return story.topic


def _calculate_slide_count(story: StoryAnalysis) -> int:
    """Calculate appropriate number of slides based on story complexity.

    Uses heuristics based on:
    - Suggested structure (if present)
    - Story complexity indicators
    - FR-019 constraints (3-30 slides)

    Args:
        story: StoryAnalysis object

    Returns:
        Number of slides to generate (3-30)
    """
    # Base slide count
    slide_count = DEFAULT_SLIDE_COUNT

    # Adjust based on suggested structure
    if story.suggested_structure:
        structure_lower = story.suggested_structure.lower()

        # Structured presentations need more slides
        if "multi-section" in structure_lower:
            slide_count = 12
        elif "problem" in structure_lower and "solution" in structure_lower:
            slide_count = 7  # Title + Problem + Solution + Benefits + Conclusion
        elif "introduction" in structure_lower and "conclusion" in structure_lower:
            slide_count = 8  # Title + Intro + Content (multiple) + Conclusion

    # Adjust based on topic complexity (length as a proxy)
    topic_words = len(story.topic.split())
    if topic_words > COMPLEX_TOPIC_WORD_THRESHOLD:
        slide_count += SLIDE_INCREMENT_FOR_COMPLEXITY

    message_words = len(story.key_message.split())
    if message_words > COMPLEX_MESSAGE_WORD_THRESHOLD:
        slide_count += SLIDE_INCREMENT_FOR_COMPLEXITY

    # Ensure within FR-019 constraints and return directly
    return max(MIN_SLIDES, min(MAX_SLIDES, slide_count))


def _generate_slides(story: StoryAnalysis, slide_count: int) -> list[SlideContent]:
    """Generate individual slides based on story and slide count.

    Args:
        story: StoryAnalysis object
        slide_count: Number of slides to generate

    Returns:
        List of SlideContent objects
    """
    slides = []

    for i in range(1, slide_count + 1):
        slide_number = i
        layout_name = _determine_layout_name(i, slide_count)
        title = _generate_slide_title(story, i, slide_count)
        content = _generate_slide_content(story, i, slide_count)

        slide = SlideContent(
            slide_number=slide_number,
            layout_name=layout_name,
            title=title,
            content=content,
        )
        slides.append(slide)

    return slides


def _determine_layout_name(slide_number: int, total_slides: int) -> str:
    """Determine appropriate layout name for a slide.

    Uses position-based heuristics:
    - First slide: title layout
    - Middle slides: content layout
    - Some middle slides: section layout (for transitions)

    Args:
        slide_number: Current slide number (1-indexed)
        total_slides: Total number of slides

    Returns:
        Layout name string
    """
    # First slide is typically a title slide
    if slide_number == 1:
        return "Title Slide"

    # Last slide could be title or content
    if slide_number == total_slides:
        return "Title Slide"

    # Section dividers at regular intervals for longer presentations
    if total_slides > LONG_PRESENTATION_THRESHOLD and slide_number % SECTION_DIVIDER_INTERVAL == 0:
        return "Section Header"

    # Default to content layout
    return "Title and Content"


def _generate_slide_title(story: StoryAnalysis, slide_number: int, total_slides: int) -> str:
    """Generate title for a specific slide.

    Uses position-based heuristics and story information.

    Args:
        story: StoryAnalysis object
        slide_number: Current slide number (1-indexed)
        total_slides: Total number of slides

    Returns:
        Slide title string
    """
    # First slide uses presentation topic
    if slide_number == 1:
        return story.topic

    # Last slide is conclusion
    if slide_number == total_slides:
        return "まとめ" if story.language == "ja" else "Conclusion"

    # Second slide could be introduction/overview
    if slide_number == OVERVIEW_SLIDE_NUMBER:
        return "概要" if story.language == "ja" else "Overview"

    # Generate generic content titles
    return f"トピック {slide_number - 1}" if story.language == "ja" else f"Topic {slide_number - 1}"


def _generate_slide_content(story: StoryAnalysis, slide_number: int, total_slides: int) -> str:
    """Generate content placeholder for a specific slide.

    Args:
        story: StoryAnalysis object
        slide_number: Current slide number (1-indexed)
        total_slides: Total number of slides

    Returns:
        Slide content string (can be empty)
    """
    # First slide: use key message as subtitle
    if slide_number == 1:
        return story.key_message

    # Last slide: summary content
    if slide_number == total_slides:
        return "主要なポイントのまとめ" if story.language == "ja" else "Summary of key points"

    # Second slide: target audience and context
    if slide_number == OVERVIEW_SLIDE_NUMBER:
        return (
            f"対象: {story.target_audience}"
            if story.language == "ja"
            else f"Target: {story.target_audience}"
        )

    # Middle slides: generic content placeholder
    return "内容の詳細" if story.language == "ja" else "Content details"
