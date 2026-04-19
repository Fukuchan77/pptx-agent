"""Content generator agent for creating detailed slide content.

This module generates a PresentationSchema from PresentationOutline input.
The content generator:
- Transforms simple outline content into structured ContentBlocks
- Creates TextBlock objects with appropriate placeholder names
- Handles language-appropriate content (en or ja)
- Preserves slide metadata (title, layout, speaker notes)

Uses heuristic-based generation for initial implementation.
Future versions may integrate LLM-based content enrichment.
"""

import logging
import re
from typing import Any, Literal

from pydantic_ai import Agent

from pptx_agent.agents.prompts import (
    CONTENT_GENERATOR_PROMPT,
    SPEAKER_NOTES_EN_CONTENT_SLIDE,
    SPEAKER_NOTES_EN_SECTION_SLIDE,
    SPEAKER_NOTES_EN_TITLE_SLIDE,
    SPEAKER_NOTES_JA_CONTENT_SLIDE,
    SPEAKER_NOTES_JA_SECTION_SLIDE,
    SPEAKER_NOTES_JA_TITLE_SLIDE,
)
from pptx_agent.agents.utils import run_agent_with_fallback
from pptx_agent.config import get_config
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import ContentBlock, SlideSchema
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, SmartArtBlock, TableBlock

logger = logging.getLogger(__name__)

# Module-level pydantic-ai agent for content generation
_content_agent: Agent[None, PresentationSchema] = Agent(  # type: ignore[assignment]
    output_type=PresentationSchema,
    system_prompt=CONTENT_GENERATOR_PROMPT,
)


async def generate_content(
    outline: PresentationOutline,
    manifest: TemplateManifest | None = None,
    *,
    use_llm: bool = True,
) -> PresentationSchema:
    """Generate detailed presentation content from outline.

    Transforms PresentationOutline into PresentationSchema by:
    - Converting simple content strings into structured ContentBlocks
    - Creating TextBlock objects with placeholder names
    - Preserving slide metadata (title, layout, speaker notes)
    - Setting appropriate language on all text blocks

    Args:
        outline: PresentationOutline object with slide structure
        manifest: Optional TemplateManifest for placeholder name resolution
        use_llm: If True, use LLM agent for generation. If False, use heuristic fallback
                 for testing/debugging (default: True).

    Returns:
        PresentationSchema object with detailed content blocks

    Raises:
        ValueError: If outline is invalid or cannot generate valid content
    """
    if use_llm:
        # Serialize outline to text prompt for LLM
        prompt = _serialize_outline_to_prompt(outline, manifest)

        # Create model from config and run agent with fallback
        config = get_config()
        result = await run_agent_with_fallback(_content_agent, prompt, config)
        return result.output
    # Keep existing heuristic path unchanged
    return _heuristic_generate_content(outline, manifest)


def _heuristic_generate_content(
    outline: PresentationOutline, manifest: TemplateManifest | None = None
) -> PresentationSchema:
    """Heuristic-based content generation (fallback for testing/debugging).

    Transforms PresentationOutline into PresentationSchema by:
    - Converting simple content strings into structured ContentBlocks
    - Creating TextBlock objects with placeholder names
    - Preserving slide metadata (title, layout, speaker notes)
    - Setting appropriate language on all text blocks

    Args:
        outline: PresentationOutline object with slide structure
        manifest: Optional TemplateManifest for placeholder name resolution

    Returns:
        PresentationSchema object with detailed content blocks

    Raises:
        ValueError: If outline is invalid or cannot generate valid content
    """
    # Log function entry with input information
    logger.info(
        "Starting content generation: input_slides=%d, language=%s",
        len(outline.slides),
        outline.output_language,
    )

    # Convert slides from outline to detailed content
    slides = []
    for slide_content in outline.slides:
        slide_schema = _convert_slide_to_schema(slide_content, outline.output_language, manifest)
        slides.append(slide_schema)

    # Create and return presentation schema
    result = PresentationSchema(
        title=outline.title,
        slides=slides,
        metadata={},
    )

    # Log function exit with output information
    total_content_blocks = sum(len(slide.content) for slide in result.slides)
    logger.info(
        "Content generation completed: output_slides=%d, total_content_blocks=%d",
        len(result.slides),
        total_content_blocks,
    )

    return result


def _convert_slide_to_schema(
    slide_content: SlideContent,
    language: Literal["en", "ja"],
    manifest: TemplateManifest | None = None,
) -> SlideSchema:
    """Convert SlideContent to SlideSchema with ContentBlocks.

    Args:
        slide_content: SlideContent from outline
        language: Output language ('en' or 'ja')
        manifest: Optional TemplateManifest for placeholder name resolution

    Returns:
        SlideSchema with structured content blocks
    """
    # Generate content blocks from the content string
    content_blocks = _generate_content_blocks(
        slide_content.content,
        slide_content.layout_name,
        language,
        manifest,
        slide_content.title,
    )

    # Generate or preserve speaker notes
    speaker_notes = slide_content.speaker_notes
    if speaker_notes is None:
        # Generate speaker notes if not provided
        speaker_notes = _generate_speaker_notes(
            slide_content.title,
            slide_content.content,
            slide_content.layout_name,
            language,
        )

    # Create slide schema
    return SlideSchema(
        layout_name=slide_content.layout_name,
        title=slide_content.title,
        content=content_blocks,
        notes=speaker_notes,
    )


def _generate_content_blocks(  # noqa: PLR0911
    content: str,
    layout_name: str,
    language: Literal["en", "ja"],
    manifest: TemplateManifest | None = None,
    slide_title: str = "",
) -> list[ContentBlock]:
    """Generate ContentBlock list from content string.

    Supports:
    - Text content (default)
    - Chart data with "chart:" prefix
    - Table data with "table:" prefix
    - Mixed content (text + chart/table)

    Args:
        content: Content string from outline
        layout_name: Layout name for determining placeholder
        language: Output language ('en' or 'ja')
        manifest: Optional TemplateManifest for placeholder name resolution
        slide_title: Slide title (used for chart titles)

    Returns:
        List of ContentBlock objects (TextBlocks, ChartBlocks, TableBlocks)
    """
    # Handle empty content
    if not content or not content.strip():
        return []

    # Determine placeholder name based on layout
    placeholder_name = _determine_placeholder_name(layout_name, manifest)

    # Check for chart data (format: "chart:type|key1=value1,key2=value2")
    if content.startswith("chart:"):
        return [parse_chart_data(content, placeholder_name, slide_title)]

    # Check for table data (format: "table:header1|header2\nrow1|row2")
    if content.startswith("table:"):
        return [_parse_table_data(content, placeholder_name)]

    # Check for SmartArt data (format: "smartart:diagram_type|node1,node2,node3")
    if content.startswith("smartart:"):
        return [_parse_smartart_data(content, placeholder_name)]

    # Check for mixed content (text + chart/table)
    if "chart:" in content:
        return _parse_mixed_content(content, placeholder_name, slide_title, language)

    # For Title Slide layouts, use content as subtitle
    if "title" in layout_name.lower() and "content" not in layout_name.lower():
        # Title Slide - content is subtitle
        return [
            TextBlock(
                placeholder_name=placeholder_name,
                text=content,
                language=language,
            )
        ]

    # For content layouts, create bullet points or text blocks
    # Split content into sentences for bullet points
    sentences = _split_into_sentences(content)

    if len(sentences) > 1:
        # Multiple sentences - create bullet points
        bullet_text = "\n".join(
            f"• {sentence.strip()}" for sentence in sentences if sentence.strip()
        )
        return [
            TextBlock(
                placeholder_name=placeholder_name,
                text=bullet_text,
                language=language,
            )
        ]
    # Single sentence or paragraph - create single text block
    return [
        TextBlock(
            placeholder_name=placeholder_name,
            text=content,
            language=language,
        )
    ]


def _determine_placeholder_name(layout_name: str, manifest: TemplateManifest | None = None) -> str:
    """Determine appropriate placeholder name based on layout type.

    If manifest is provided, looks up actual placeholder names from template.
    Falls back to heuristic-based defaults if manifest is unavailable or
    layout is not found in manifest.

    Args:
        layout_name: Layout name from template
        manifest: Optional TemplateManifest for accurate placeholder lookup

    Returns:
        Placeholder name string
    """
    # Try to get placeholder name from manifest first
    if manifest:
        layout = manifest.get_layout_by_name(layout_name)
        if layout and layout.placeholders:
            # Look for first content placeholder (BODY or OBJECT type)
            for placeholder in layout.placeholders:
                if placeholder.type in ["BODY", "OBJECT"]:
                    return placeholder.name

    # Fallback to heuristic-based defaults
    layout_lower = layout_name.lower()

    if "title" in layout_lower and "content" not in layout_lower:
        return "Subtitle"
    if "section" in layout_lower or "header" in layout_lower:
        return "Text Placeholder"
    # Default to content placeholder for most layouts
    return "Content Placeholder"


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences for bullet point creation.

    Supports both English periods (.) and Japanese full stops (。).

    Args:
        text: Text string to split

    Returns:
        List of sentence strings
    """
    # Split on both English period (.) and Japanese full stop (。)
    return [s.strip() for s in re.split(r"[.。]", text) if s.strip()]


def _generate_speaker_notes(
    title: str,
    content: str,
    layout_name: str,
    language: Literal["en", "ja"],
) -> str:
    """Generate speaker notes based on slide content.

    Generates contextual speaker notes that provide value beyond
    what's visible on the slide. Notes are tailored to slide type
    and language.

    Args:
        title: Slide title
        content: Slide content
        layout_name: Layout type (Title Slide, Title and Content, etc.)
        language: Output language ('en' or 'ja')

    Returns:
        Generated speaker notes (1-3 sentences)
    """
    layout_lower = layout_name.lower()

    # Determine slide type
    is_title_slide = "title" in layout_lower and "content" not in layout_lower
    is_section_slide = "section" in layout_lower or "header" in layout_lower

    # Generate notes based on slide type and language
    if is_title_slide:
        # Title slide - introduce presentation
        if language == "ja":
            notes = SPEAKER_NOTES_JA_TITLE_SLIDE.format(title=title, content=content)
        else:
            notes = SPEAKER_NOTES_EN_TITLE_SLIDE.format(title=title, content=content)
    elif is_section_slide:
        # Section slide - provide transition
        if language == "ja":
            notes = SPEAKER_NOTES_JA_SECTION_SLIDE.format(title=title, content=content)
        else:
            notes = SPEAKER_NOTES_EN_SECTION_SLIDE.format(title=title, content=content)
    # Content slide - elaborate on content
    elif language == "ja":
        notes = SPEAKER_NOTES_JA_CONTENT_SLIDE.format(title=title, content=content)
    else:
        notes = SPEAKER_NOTES_EN_CONTENT_SLIDE.format(title=title, content=content)

    return notes


def parse_chart_data(content: str, placeholder_name: str, title: str) -> ChartBlock:
    """Parse chart data from content string.

    Format: "chart:type|key1=value1,key2=value2,key3=value3"
    Example: "chart:bar|Q1=100,Q2=150,Q3=200"

    Handles invalid numeric values gracefully by logging a warning and using
    0.0 as a fallback value, ensuring chart generation continues even with
    malformed input data.

    Args:
        content: Content string starting with "chart:"
        placeholder_name: Placeholder name for the chart
        title: Chart title (from slide title)

    Returns:
        ChartBlock instance with parsed data
    """
    # Remove "chart:" prefix
    chart_content = content[6:].strip()

    # Split into chart type and data
    parts = chart_content.split("|", 1)
    chart_type = parts[0].strip()
    data_str = parts[1] if len(parts) > 1 else ""

    # Parse data (format: key1=value1,key2=value2)
    categories = []
    values = []
    for pair in data_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            categories.append(key.strip())
            try:
                values.append(float(value.strip()))
            except ValueError:
                # Log warning before fallback for debugging
                logger.warning(
                    "Invalid numeric value '%s' for category '%s' in chart data. "
                    "Using fallback value 0.0",
                    value.strip(),
                    key.strip(),
                )
                values.append(0.0)

    # Create chart data structure
    chart_data = {
        "categories": categories,
        "series": [{"name": "Series 1", "values": values}],
    }

    return ChartBlock(
        placeholder_name=placeholder_name,
        chart_type=chart_type,
        data=chart_data,
        title=title,
    )


def _parse_table_data(content: str, placeholder_name: str) -> TableBlock:
    """Parse table data from content string.

    Format: "table:header1|header2|header3\\nrow1col1|row1col2|row1col3"
    Example: "table:Product|Price|Rating\\nProduct A|$100|4.5"

    Args:
        content: Content string starting with "table:"
        placeholder_name: Placeholder name for the table

    Returns:
        TableBlock instance with parsed data
    """
    # Remove "table:" prefix
    table_content = content[6:].strip()

    # Split into lines
    lines = table_content.split("\n")

    # First line is headers
    headers = [h.strip() for h in lines[0].split("|")] if lines else []

    # Remaining lines are data rows
    rows = []
    for line in lines[1:]:
        if line.strip():
            row = [cell.strip() for cell in line.split("|")]
            rows.append(row)

    return TableBlock(placeholder_name=placeholder_name, rows=rows, headers=headers)


def _parse_mixed_content(
    content: str,
    placeholder_name: str,
    title: str,
    language: Literal["en", "ja"],
) -> list[ContentBlock]:
    """Parse mixed content with both text and charts.

    Example: "Key findings: chart:bar|Jan=100,Feb=120"

    Args:
        content: Content string with mixed text and chart data
        placeholder_name: Placeholder name
        title: Slide title for chart
        language: Output language

    Returns:
        List of ContentBlock objects (TextBlock + ChartBlock)
    """
    blocks: list[ContentBlock] = []

    # Split by "chart:" marker
    parts = content.split("chart:", 1)

    # Add text part if present
    text_part = parts[0].strip()
    if text_part:
        blocks.append(
            TextBlock(
                placeholder_name=placeholder_name,
                text=text_part,
                language=language,
            )
        )

    # Add chart part if present
    if len(parts) > 1:
        chart_content = f"chart:{parts[1]}"
        blocks.append(parse_chart_data(chart_content, placeholder_name, title))

    return blocks


def _parse_smartart_data(content: str, placeholder_name: str) -> SmartArtBlock:
    """Parse SmartArt data from content string.

    Format: "smartart:diagram_type|node1,node2,node3"
    Example: "smartart:process|Planning,Design,Development,Testing"

    Args:
        content: Content string starting with "smartart:"
        placeholder_name: Placeholder name for the SmartArt

    Returns:
        SmartArtBlock instance with parsed data
    """
    # Remove "smartart:" prefix
    smartart_content = content[9:].strip()

    # Split into diagram type and nodes
    parts = smartart_content.split("|", 1)
    diagram_type = parts[0].strip()
    nodes_str = parts[1] if len(parts) > 1 else ""

    # Parse nodes (comma-separated)
    nodes: list[dict[str, Any]] = []
    for raw_node in nodes_str.split(","):
        node_text = raw_node.strip()
        # Skip empty nodes
        if node_text:
            nodes.append({"text": node_text, "level": 0})

    return SmartArtBlock(
        placeholder_name=placeholder_name,
        diagram_type=diagram_type,
        nodes=nodes,
    )


def _serialize_outline_to_prompt(
    outline: PresentationOutline,
    manifest: TemplateManifest | None = None,
) -> str:
    """Serialize outline and manifest into text prompt for LLM.

    Args:
        outline: Presentation outline
        manifest: Optional template manifest

    Returns:
        Formatted text prompt
    """
    prompt_parts = [
        f"Title: {outline.title}",
        f"Language: {outline.output_language}",
        "\nSlides:",
    ]

    for i, slide in enumerate(outline.slides, 1):
        prompt_parts.append(f"\nSlide {i}:")
        prompt_parts.append(f"  Layout: {slide.layout_name}")
        prompt_parts.append(f"  Title: {slide.title}")
        prompt_parts.append(f"  Content: {slide.content}")
        if slide.speaker_notes:
            prompt_parts.append(f"  Speaker Notes: {slide.speaker_notes}")

    # Add layout constraints from manifest if available
    if manifest:
        prompt_parts.append("\nAvailable Layouts:")
        for layout in manifest.layouts:
            placeholder_count = len(layout.placeholders) if layout.placeholders else 0
            prompt_parts.append(f"  - {layout.name}: {placeholder_count} placeholders")
            if layout.placeholders:
                placeholder_names = [
                    p.name for p in layout.placeholders if p.type in ["BODY", "OBJECT"]
                ]
                if placeholder_names:
                    prompt_parts.append(f"    Content placeholders: {', '.join(placeholder_names)}")

    return "\n".join(prompt_parts)
