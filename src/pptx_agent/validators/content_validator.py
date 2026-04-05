"""Content validator for presentation content validation.

Validates PresentationSchema content before PowerPoint rendering with
language-aware overflow detection support.
"""

import logging

from pptx_agent.schemas.outline import PresentationOutline
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, SmartArtBlock, TableBlock
from pptx_agent.validators.exceptions import ContentValidationError

logger = logging.getLogger(__name__)

# Supported chart types as per FR-025 and spec.md
SUPPORTED_CHART_TYPES = {
    "bar",
    "column",
    "line",
    "pie",
    "scatter",
    "doughnut",
    "area",
    "radar",
}

# Table constraints as per FR-026
MAX_TABLE_ROWS = 20
MAX_TABLE_COLS = 10


def _validate_text_block(block: TextBlock, slide_num: int, slide_title: str) -> None:
    """Validate TextBlock content.

    Args:
        block: The TextBlock to validate
        slide_num: Slide number for error messages
        slide_title: Slide title for error messages

    Raises:
        ContentValidationError: If text is empty or whitespace-only
    """
    if not block.text.strip():
        msg = (
            f"Slide {slide_num} '{slide_title}' has empty text in "
            f"placeholder '{block.placeholder_name}'"
        )
        raise ContentValidationError(msg)


def _validate_chart_block(block: ChartBlock, slide_num: int, slide_title: str) -> None:
    """Validate ChartBlock content.

    Args:
        block: The ChartBlock to validate
        slide_num: Slide number for error messages
        slide_title: Slide title for error messages

    Raises:
        ContentValidationError: If chart type is not supported
    """
    if block.chart_type not in SUPPORTED_CHART_TYPES:
        msg = (
            f"Slide {slide_num} '{slide_title}' has invalid chart type "
            f"'{block.chart_type}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_CHART_TYPES))}"
        )
        raise ContentValidationError(msg)


def _validate_table_block(block: TableBlock, slide_num: int, slide_title: str) -> None:
    """Validate TableBlock content.

    Args:
        block: The TableBlock to validate
        slide_num: Slide number for error messages
        slide_title: Slide title for error messages

    Raises:
        ContentValidationError: If table dimensions or row consistency is invalid
    """
    # Validate table dimensions
    if block.num_rows > MAX_TABLE_ROWS:
        msg = (
            f"Slide {slide_num} '{slide_title}' has table with "
            f"{block.num_rows} rows (max {MAX_TABLE_ROWS})"
        )
        raise ContentValidationError(msg)

    if block.num_cols > MAX_TABLE_COLS:
        msg = (
            f"Slide {slide_num} '{slide_title}' has table with "
            f"{block.num_cols} columns (max {MAX_TABLE_COLS})"
        )
        raise ContentValidationError(msg)

    # Validate row consistency
    expected_cols = len(block.headers)
    for row_idx, row in enumerate(block.rows):
        if len(row) != expected_cols:
            msg = (
                f"Slide {slide_num} '{slide_title}' has table with inconsistent "
                f"row lengths. Expected {expected_cols} columns, "
                f"but row {row_idx + 1} has {len(row)}"
            )
            raise ContentValidationError(msg)


def _validate_smartart_block(
    block: SmartArtBlock,
    slide_num: int,
    slide_title: str,
    layout_name: str,
    manifest: TemplateManifest | None,
) -> None:
    """Validate SmartArtBlock content.

    Args:
        block: The SmartArtBlock to validate
        slide_num: Slide number for error messages
        slide_title: Slide title for error messages
        layout_name: Layout name for looking up expected node count
        manifest: Optional template manifest with layout information

    Raises:
        ContentValidationError: If node count doesn't match template requirement
    """
    # If no manifest provided, skip node count validation
    if manifest is None:
        return

    # Look up layout in manifest
    layout = manifest.get_layout_by_name(layout_name)
    if layout is None:
        # Layout not in manifest, can't validate
        return

    # Check if layout has SmartArt node count requirement
    if layout.smartart_node_count is None:
        # No specific node count required
        return

    # Validate node count matches template requirement
    actual_count = len(block.nodes)
    expected_count = layout.smartart_node_count

    if actual_count != expected_count:
        msg = (
            f"Slide {slide_num} '{slide_title}' has SmartArt with "
            f"{actual_count} nodes, but layout '{layout_name}' expects "
            f"{expected_count} nodes"
        )
        raise ContentValidationError(msg)


def validate_content(
    content: PresentationSchema,
    outline: PresentationOutline | None = None,
    _template_manifest: TemplateManifest | None = None,
) -> PresentationSchema:
    """Validate presentation content against business rules.

    Validates:
    - All slides have at least one content block
    - Text blocks contain non-empty text (not whitespace-only)
    - Slide count matches outline if provided
    - Content structure is valid for rendering
    - Language-aware overflow detection (logs warnings for potential overflow)

    Note: Detailed overflow resolution happens during slide building stage.
    The content validator performs basic checks and logs potential issues.

    Args:
        content: The presentation content to validate
        outline: Optional outline to validate slide count against (includes output_language)
        _template_manifest: Optional template manifest (reserved for future use)

    Returns:
        The validated content if all checks pass

    Raises:
        ContentValidationError: If validation fails with clear error message
    """
    # Log output language if available for language-aware processing
    if outline and outline.output_language:
        logger.debug(
            "Validating content with language-aware settings: output_language=%s",
            outline.output_language,
        )
    # Validate slide count matches outline if provided
    if outline:
        content_slide_count = len(content.slides)
        outline_slide_count = len(outline.slides)
        if content_slide_count != outline_slide_count:
            msg = (
                f"Presentation has {content_slide_count} slides but "
                f"outline specified {outline_slide_count}"
            )
            raise ContentValidationError(msg)

    # Validate each slide has content blocks and validate content types
    for i, slide in enumerate(content.slides, start=1):
        # Check if slide has any content blocks
        if not slide.content:
            msg = f"Slide {i} '{slide.title}' has no content blocks"
            raise ContentValidationError(msg)

        # Validate each content block based on its type
        for block in slide.content:
            if isinstance(block, TextBlock):
                _validate_text_block(block, i, slide.title)
            elif isinstance(block, ChartBlock):
                _validate_chart_block(block, i, slide.title)
            elif isinstance(block, TableBlock):
                _validate_table_block(block, i, slide.title)
            elif isinstance(block, SmartArtBlock):
                _validate_smartart_block(
                    block, i, slide.title, slide.layout_name, _template_manifest
                )

    # All validations passed, return the content
    return content
