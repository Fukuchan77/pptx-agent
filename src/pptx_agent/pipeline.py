"""Pipeline orchestration for presentation generation.

This module orchestrates the complete workflow from input text to .pptx file:
1. Story Analysis: Input text → StoryAnalysis
2. Outline Generation: StoryAnalysis → PresentationOutline
3. Outline Validation: PresentationOutline → validated outline
4. Content Generation: PresentationOutline → PresentationSchema
5. Content Validation: PresentationSchema → validated content
6. Slide Building: PresentationSchema + template → .pptx file
"""

import logging
import time
from typing import Literal

from pptx_agent.agents.content_generator import generate_content
from pptx_agent.agents.outline_generator import generate_outline
from pptx_agent.agents.overflow_resolver import resolve_overflow
from pptx_agent.agents.story_analyzer import analyze_story
from pptx_agent.pptx_wrapper.slide_builder import build_presentation
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.validators.content_validator import validate_content
from pptx_agent.validators.input_validator import validate_and_sanitize
from pptx_agent.validators.outline_validator import validate_outline

logger = logging.getLogger(__name__)


def generate_presentation(
    input_text: str,
    template_path: str,
    output_path: str,
    template_manifest: TemplateManifest | None = None,
    output_language: Literal["en", "ja"] | None = None,
) -> str:
    """Generate a PowerPoint presentation from input text.

    Orchestrates the complete pipeline:
    - Analyzes the input text to extract story elements
    - Generates a presentation outline structure
    - Validates the outline against template constraints
    - Generates detailed content for each slide
    - Validates the content against business rules
    - Builds the final PowerPoint presentation

    Args:
        input_text: Input text to convert into presentation
        template_path: Path to PowerPoint template file
        output_path: Path where generated presentation should be saved
        template_manifest: Optional template manifest for validation
        output_language: Optional explicit output language ('en' or 'ja').
                        If None, language is auto-detected from input text.

    Returns:
        Path to the generated .pptx file (same as output_path)

    Raises:
        ValueError: If input text is invalid or cannot be analyzed
        InvalidFileError: If validation fails at any stage
        FileNotFoundError: If template file doesn't exist
    """
    pipeline_start = time.time()

    # Stage 0: Validate and sanitize input
    input_text = validate_and_sanitize(input_text)

    # Stage 1: Analyze story
    start = time.time()
    story = analyze_story(input_text)
    duration = time.time() - start
    logger.info("Stage: Story Analysis completed in %.2fs", duration)

    # Stage 2: Generate outline
    start = time.time()
    outline = generate_outline(story)

    # Override output_language if explicitly provided
    if output_language is not None:
        outline.output_language = output_language

    duration = time.time() - start
    logger.info("Stage: Outline Generation completed in %.2fs", duration)

    # Stage 3: Validate outline
    start = time.time()
    validated_outline = validate_outline(outline, template_manifest)
    duration = time.time() - start
    logger.info("Stage: Outline Validation completed in %.2fs", duration)

    # Stage 4: Generate content
    start = time.time()
    content = generate_content(validated_outline)
    duration = time.time() - start
    logger.info("Stage: Content Generation completed in %.2fs", duration)

    # Stage 5: Validate content
    start = time.time()
    validated_content = validate_content(content, validated_outline, template_manifest)
    duration = time.time() - start
    logger.info("Stage: Content Validation completed in %.2fs", duration)

    # Stage 5.5: Check for overflow and apply resolution strategies
    if template_manifest is not None:
        start = time.time()
        for slide in validated_outline.slides:
            resolution = resolve_overflow(
                slide, template_manifest, validated_outline.output_language
            )
            if resolution.overflow_detected:
                logger.info(
                    "Overflow detected in slide %d '%s': %.1f%% overflow, strategy: %s",
                    slide.slide_number,
                    slide.title,
                    resolution.overflow_percentage,
                    resolution.strategy,
                )
        duration = time.time() - start
        logger.info("Stage: Overflow Resolution completed in %.2fs", duration)

    # Stage 6: Build presentation
    start = time.time()
    result = build_presentation(validated_content, template_path, output_path)
    duration = time.time() - start
    logger.info("Stage: Slide Building completed in %.2fs", duration)

    # Log total execution time
    total_time = time.time() - pipeline_start
    logger.info("Total pipeline execution completed in %.2fs", total_time)

    return result
