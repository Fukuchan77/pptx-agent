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
import os
import time
from typing import TYPE_CHECKING, Any, Literal

from pptx_agent.agents.content_generator import generate_content
from pptx_agent.agents.outline_generator import generate_outline
from pptx_agent.agents.overflow_resolver import resolve_overflow
from pptx_agent.agents.story_analyzer import analyze_story
from pptx_agent.fixer.engine import FixEngine, FixStrategyRegistry
from pptx_agent.fixer.strategies import register_default_strategies
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.pptx_wrapper.slide_builder import build_presentation
from pptx_agent.qa.engine import QAEngine
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.validators.content_validator import validate_content
from pptx_agent.validators.input_validator import validate_and_sanitize, validate_text_security
from pptx_agent.validators.outline_validator import validate_outline
from pptx_agent.validators.security import flag_suspicious_phrases

if TYPE_CHECKING:
    from pptx_agent.qa.schemas import QAReport

logger = logging.getLogger(__name__)


async def _run_qa_stage(output_path: str) -> "QAReport":
    """Run QA validation pass on generated presentation.

    Args:
        output_path: Path to the generated presentation file

    Returns:
        QA report with detected issues
    """
    # Open presentation for QA validation
    presentation = PresentationWrapper()
    presentation.load_template(output_path)

    # Run QA engine
    qa_engine = QAEngine()
    return qa_engine.validate(presentation)


async def _run_autofix_stage(
    output_path: str,
    qa_report: "QAReport",
    max_iterations: int,
    outline: Any | None = None,
) -> "QAReport":
    """Run auto-fix loop to remediate detected issues.

    Args:
        output_path: Path to the presentation file
        qa_report: Initial QA report with issues to fix
        max_iterations: Maximum number of fix iterations
        outline: Optional outline data for strategies that need it

    Returns:
        Updated QA report after fix attempts
    """
    logger.debug("Running auto-fix stage for output: %s", output_path)

    # Load presentation for fixing
    try:
        presentation = PresentationWrapper()
        presentation.load_template(output_path)
    except Exception as exc:
        logger.warning("Autofix skipped: failed to load %s: %s", output_path, exc)
        return qa_report  # Return original QA report without fixes

    # Create local registry and register strategies with presentation context
    local_registry = FixStrategyRegistry()
    register_default_strategies(registry=local_registry, presentation=presentation, outline=outline)

    # Create save callback to persist in-memory edits
    def save_callback() -> None:
        """Save presentation changes to disk."""
        presentation.prs.save(output_path)

    # Run fix engine with local registry and save callback
    fix_engine = FixEngine(registry=local_registry, max_iterations=max_iterations)
    fix_result = fix_engine.run_fix_loop(
        qa_report,
        presentation_path=output_path,
        save_callback=save_callback,
    )

    # Return the final QA report from fix loop
    return fix_result.final_qa_report


async def generate_presentation(
    input_text: str,
    template_path: str,
    output_path: str,
    template_manifest: TemplateManifest | None = None,
    output_language: Literal["en", "ja"] | None = None,
    *,
    use_llm: bool = True,
    qa_enabled: bool = True,
    autofix_enabled: bool = False,
    max_fix_iterations: int = 3,
) -> tuple[str, "QAReport | None"]:
    """Generate a PowerPoint presentation from input text.

    Orchestrates the complete pipeline:
    - Analyzes the input text to extract story elements
    - Generates a presentation outline structure
    - Validates the outline against template constraints
    - Generates detailed content for each slide
    - Validates the content against business rules
    - Builds the final PowerPoint presentation
    - Optionally runs QA validation pass
    - Optionally applies automatic fixes

    Args:
        input_text: Input text to convert into presentation
        template_path: Path to PowerPoint template file
        output_path: Path where generated presentation should be saved
        template_manifest: Optional template manifest for validation
        output_language: Optional explicit output language ('en' or 'ja').
                        If None, language is auto-detected from input text.
        use_llm: If True, use LLM agents for generation. If False, use heuristic fallback
                 for testing/debugging (default: True).
        qa_enabled: If True, run QA validation pass after generation (default: True).
        autofix_enabled: If True, automatically fix detected issues (default: False).
        max_fix_iterations: Maximum number of fix loop iterations (default: 3).

    Returns:
        Tuple of (path to generated .pptx file, QA report if qa_enabled else None)

    Raises:
        ValueError: If input text is invalid or cannot be analyzed
        InvalidFileError: If validation fails at any stage
        FileNotFoundError: If template file doesn't exist
    """
    pipeline_start = time.time()

    # Stage 0a: Security validation - reject suspicious input transparently
    # Check for dangerous characters (null bytes, control chars, etc.)
    # This raises ValueError if suspicious characters are detected
    try:
        validate_text_security(input_text)
    except ValueError as e:
        logger.exception("Input validation failed: suspicious characters detected.")
        # Re-raise with more context for the user
        msg = (
            f"Input validation failed: {e}. "
            "Please ensure your input does not contain null bytes, control characters, "
            "or other suspicious patterns."
        )
        raise ValueError(msg) from e

    # Stage 0b: Sanitize and length-check input
    input_text = validate_and_sanitize(input_text)

    # Security: Detect and reject suspicious phrases (best-effort signal)
    # This is NOT a security boundary per CLI trust model, but provides
    # early feedback for obviously suspicious patterns
    try:
        flag_suspicious_phrases(input_text)
    except ValueError as e:
        logger.warning("Suspicious phrase detected in input: %s", e)
        # Re-raise with user-friendly message
        msg = (
            f"Input validation failed: {e}. "
            "The input contains patterns that may indicate prompt injection. "
            "Please review and modify your input text."
        )
        raise ValueError(msg) from e

    # Stage 1: Analyze story
    start = time.time()
    story = await analyze_story(input_text, use_llm=use_llm)
    duration = time.time() - start
    logger.info("Stage: Story Analysis completed in %.2fs", duration)

    # Stage 2: Generate outline
    start = time.time()

    # Override story language if output_language is explicitly provided
    # This ensures the outline generator uses the correct language from the start
    if output_language is not None:
        story.language = output_language

    outline = await generate_outline(story, manifest=template_manifest, use_llm=use_llm)

    duration = time.time() - start
    logger.info("Stage: Outline Generation completed in %.2fs", duration)

    # Stage 3: Validate outline
    start = time.time()
    validated_outline = validate_outline(outline, template_manifest)
    duration = time.time() - start
    logger.info("Stage: Outline Validation completed in %.2fs", duration)

    # Stage 4: Generate content
    start = time.time()
    content = await generate_content(validated_outline, template_manifest, use_llm=use_llm)
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

    # Stage 7: QA Pass (optional, only if output file exists)
    qa_report: QAReport | None = None
    if qa_enabled and os.path.exists(output_path):  # noqa: ASYNC240, PTH110
        start = time.time()
        qa_report = await _run_qa_stage(output_path)
        duration = time.time() - start
        logger.info("Stage: QA Pass completed in %.2fs", duration)
        logger.info(
            "QA Results: %d total issues (%d errors, %d warnings, %d info)",
            qa_report.total_issues,
            qa_report.error_count,
            qa_report.warning_count,
            qa_report.info_count,
        )

    # Stage 8: Auto-Fix Loop (optional, only if QA found errors)
    if autofix_enabled and qa_report and qa_report.error_count > 0:
        start = time.time()
        qa_report = await _run_autofix_stage(
            output_path, qa_report, max_fix_iterations, outline=validated_outline
        )
        duration = time.time() - start
        logger.info("Stage: Auto-Fix Loop completed in %.2fs", duration)
        logger.info(
            "Fix Results: %d iterations, %d remaining errors",
            qa_report.fix_iterations,
            qa_report.error_count,
        )

    # Log total execution time
    total_time = time.time() - pipeline_start
    logger.info("Total pipeline execution completed in %.2fs", total_time)

    return result, qa_report
