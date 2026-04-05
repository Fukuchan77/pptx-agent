"""Overflow resolver agent for handling text overflow with staged strategies.

This module implements staged overflow resolution:
1. Font reduction (10-20% overflow)
2. Layout change (20-50% overflow)
3. Slide split (50-100% overflow)
4. Content summarization (>100% overflow)
5. Forced truncation (last resort)
"""

import logging
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from pptx_agent.constants import PERCENTAGE_MULTIPLIER
from pptx_agent.schemas.outline import SlideContent
from pptx_agent.schemas.template_manifest import TemplateManifest

logger = logging.getLogger(__name__)

# Overflow percentage thresholds for staged strategies
FONT_REDUCTION_THRESHOLD = 20  # 0-20% overflow
LAYOUT_CHANGE_THRESHOLD = 50  # 20-50% overflow
SLIDE_SPLIT_THRESHOLD = 100  # 50-100% overflow


class OverflowStrategy(StrEnum):
    """Strategy for resolving text overflow."""

    NO_ACTION = "no_action"
    FONT_REDUCTION = "font_reduction"
    LAYOUT_CHANGE = "layout_change"
    SLIDE_SPLIT = "slide_split"
    SUMMARIZE = "summarize"
    FORCED_TRUNCATION = "forced_truncation"


class OverflowResolution(BaseModel):
    """Result of overflow resolution analysis.

    Attributes:
        strategy: Recommended strategy for resolving overflow
        overflow_detected: Whether overflow was detected
        overflow_percentage: Percentage of overflow (0 if no overflow)
        suggested_layout: Layout name to switch to (for LAYOUT_CHANGE strategy)
        split_point: Character position to split content (for SLIDE_SPLIT strategy)
        target_length: Target character length (for SUMMARIZE strategy)
    """

    strategy: OverflowStrategy = Field(description="Recommended overflow resolution strategy")
    overflow_detected: bool = Field(description="Whether overflow was detected")
    overflow_percentage: float = Field(ge=0.0, description="Percentage of overflow")
    suggested_layout: str | None = Field(
        default=None, description="Suggested layout for LAYOUT_CHANGE"
    )
    split_point: int | None = Field(default=None, description="Split position for SLIDE_SPLIT")
    target_length: int | None = Field(default=None, description="Target length for SUMMARIZE")


def resolve_overflow(
    slide: SlideContent,
    manifest: TemplateManifest,
    language: Literal["en", "ja"] | None = None,
) -> OverflowResolution:
    """Analyze slide content and determine overflow resolution strategy.

    Args:
        slide: SlideContent to analyze for overflow
        manifest: TemplateManifest with layout and placeholder information
        language: Optional language code for language-aware capacity calculation

    Returns:
        OverflowResolution with recommended strategy and parameters
    """
    # Get layout from manifest
    layout = manifest.get_layout_by_name(slide.layout_name)
    if layout is None:
        # Layout not found - can't determine capacity
        logger.warning(
            "Layout '%s' not found in manifest, cannot detect overflow",
            slide.layout_name,
        )
        return OverflowResolution(
            strategy=OverflowStrategy.NO_ACTION,
            overflow_detected=False,
            overflow_percentage=0.0,
        )

    # Find content placeholder (BODY or OBJECT type)
    content_placeholder = None
    for placeholder in layout.placeholders:
        if placeholder.type in ["BODY", "OBJECT"]:
            content_placeholder = placeholder
            break

    if content_placeholder is None:
        # No content placeholder found
        logger.warning(
            "No content placeholder found in layout '%s', cannot detect overflow",
            slide.layout_name,
        )
        return OverflowResolution(
            strategy=OverflowStrategy.NO_ACTION,
            overflow_detected=False,
            overflow_percentage=0.0,
        )

    # Calculate effective capacity with language ratio
    max_capacity = content_placeholder.max_chars
    if language == "ja" and content_placeholder.language_ratio is not None:
        # Use language ratio for Japanese content
        max_capacity = int(max_capacity * content_placeholder.language_ratio)
    elif content_placeholder.language_ratio is not None and language is not None:
        # Use language ratio if specified
        max_capacity = int(max_capacity * content_placeholder.language_ratio)

    # Calculate overflow
    content_length = len(slide.content)
    if content_length <= max_capacity:
        # No overflow
        return OverflowResolution(
            strategy=OverflowStrategy.NO_ACTION,
            overflow_detected=False,
            overflow_percentage=0.0,
        )

    # Calculate overflow percentage
    overflow_chars = content_length - max_capacity
    overflow_percentage = (overflow_chars / max_capacity) * PERCENTAGE_MULTIPLIER

    # Determine strategy based on overflow percentage using staged thresholds
    strategy, additional_params = _determine_strategy(
        overflow_percentage, slide.layout_name, manifest, max_capacity
    )

    return OverflowResolution(
        strategy=strategy,
        overflow_detected=True,
        overflow_percentage=overflow_percentage,
        **additional_params,
    )


def _determine_strategy(
    overflow_percentage: float,
    current_layout: str,
    manifest: TemplateManifest,
    max_capacity: int,
) -> tuple[OverflowStrategy, dict[str, Any]]:
    """Determine overflow resolution strategy based on overflow percentage.

    Args:
        overflow_percentage: Percentage of overflow
        current_layout: Current layout name
        manifest: TemplateManifest to search for alternatives
        max_capacity: Current placeholder capacity

    Returns:
        Tuple of (strategy, additional_params_dict)
    """
    if overflow_percentage <= FONT_REDUCTION_THRESHOLD:
        # Minor overflow (0-20%) - try font reduction
        return OverflowStrategy.FONT_REDUCTION, {}

    if overflow_percentage <= LAYOUT_CHANGE_THRESHOLD:
        # Moderate overflow (20-50%) - try layout change
        suggested_layout = _find_larger_layout(current_layout, manifest, max_capacity)
        if suggested_layout is not None:
            return OverflowStrategy.LAYOUT_CHANGE, {"suggested_layout": suggested_layout}
        # No larger layout available, escalate to slide split
        return OverflowStrategy.SLIDE_SPLIT, {"split_point": max_capacity // 2}

    if overflow_percentage <= SLIDE_SPLIT_THRESHOLD:
        # Large overflow (50-100%) - slide split
        return OverflowStrategy.SLIDE_SPLIT, {"split_point": max_capacity // 2}

    # Extreme overflow (>100%) - summarization
    return OverflowStrategy.SUMMARIZE, {"target_length": max_capacity}


def _find_larger_layout(
    current_layout: str,
    manifest: TemplateManifest,
    current_capacity: int,
) -> str | None:
    """Find a layout with larger content placeholder capacity.

    Args:
        current_layout: Current layout name
        manifest: TemplateManifest to search
        current_capacity: Current placeholder capacity

    Returns:
        Layout name with larger capacity, or None if not found
    """
    best_layout = None
    best_capacity = current_capacity

    for layout in manifest.layouts:
        # Skip current layout
        if layout.name == current_layout:
            continue

        # Find content placeholder
        for placeholder in layout.placeholders:
            if placeholder.type in ["BODY", "OBJECT"]:
                if placeholder.max_chars > best_capacity:
                    best_capacity = placeholder.max_chars
                    best_layout = layout.name
                break

    return best_layout


def generate_slide_split_instruction(
    resolution: OverflowResolution,
    original_slide: SlideContent,
) -> str:
    """Generate LLM instruction for splitting content across two slides.

    Args:
        resolution: OverflowResolution with SLIDE_SPLIT strategy
        original_slide: Original SlideContent that needs to be split

    Returns:
        Instruction string for the LLM to split the content

    Example instruction:
        "The slide 'Important Topic' has content that is too long (600 characters).
        Please split this content into two slides with the same layout.
        Split around position 300.

        Original content:
        [content here]

        Generate two slides with logical content division."
    """
    split_point = resolution.split_point or (len(original_slide.content) // 2)
    content_length = len(original_slide.content)

    return f"""The slide '{original_slide.title}' has content that is too long \
({content_length} characters).
Please split this content into two slides with the same layout \
'{original_slide.layout_name}'.
Split around position {split_point} to divide the content logically.

Original content:
{original_slide.content}

Generate two slides:
1. First slide: Use the original title '{original_slide.title}' and the first \
part of the content
2. Second slide: Create an appropriate related title and use the second part \
of the content

Ensure each slide's content is self-contained and flows naturally."""


def generate_summarization_instruction(
    resolution: OverflowResolution,
    original_slide: SlideContent,
) -> str:
    """Generate LLM instruction for summarizing content to fit within target length.

    Args:
        resolution: OverflowResolution with SUMMARIZE strategy
        original_slide: Original SlideContent that needs to be summarized

    Returns:
        Instruction string for the LLM to summarize the content

    Example instruction:
        "The slide 'Detailed Analysis' has content that exceeds the character limit by 150%.
        Please summarize this content to fit within 500 characters while preserving key information.

        Original content (1250 characters):
        [content here]

        Keep the same title and condense the content to the essential points."
    """
    target_length = resolution.target_length or 500
    current_length = len(original_slide.content)
    overflow_pct = resolution.overflow_percentage

    return f"""The slide '{original_slide.title}' has content that exceeds the \
character limit by {overflow_pct:.0f}%.
Please summarize this content to fit within {target_length} characters while \
preserving the most important information.

Original content ({current_length} characters):
{original_slide.content}

Keep the same title '{original_slide.title}' and condense the content to focus on:
- Key points and main ideas
- Essential information only
- Core message without excessive detail

Target: Maximum {target_length} characters."""
