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
from typing import Literal

from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import ContentBlock, SlideSchema
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.schemas.text import TextBlock

logger = logging.getLogger(__name__)


def generate_content(
    outline: PresentationOutline, manifest: TemplateManifest | None = None
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


def _generate_content_blocks(
    content: str,
    layout_name: str,
    language: Literal["en", "ja"],
    manifest: TemplateManifest | None = None,
) -> list[ContentBlock]:
    """Generate ContentBlock list from content string.

    Args:
        content: Content string from outline
        layout_name: Layout name for determining placeholder
        language: Output language ('en' or 'ja')
        manifest: Optional TemplateManifest for placeholder name resolution

    Returns:
        List of ContentBlock objects (TextBlocks)
    """
    # Handle empty content
    if not content or not content.strip():
        return []

    # Determine placeholder name based on layout
    placeholder_name = _determine_placeholder_name(layout_name, manifest)

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
            notes = (
                f"このプレゼンテーションでは「{title}」について説明します。"
                f"{content}について詳しく見ていきます。"
            )
        else:
            notes = f"This presentation covers {title}. We will explore {content} in detail."
    elif is_section_slide:
        # Section slide - provide transition
        if language == "ja":
            notes = f"次のセクションでは「{title}」について説明します。{content}に焦点を当てます。"
        else:
            notes = f"In this section, we will discuss {title}. The focus will be on {content}."
    # Content slide - elaborate on content
    elif language == "ja":
        notes = (
            f"「{title}」に関して、{content}という点が重要です。これらの詳細について説明します。"
        )
    else:
        notes = (
            f"Regarding {title}, the key points are: {content}. Let me elaborate on these details."
        )

    return notes
