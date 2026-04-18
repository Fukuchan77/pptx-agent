"""Slide builder for rendering PresentationSchema to PowerPoint.

This module provides the core functionality to convert validated content
into actual PowerPoint slides using a template-first architecture.
"""

import hashlib
import logging
import tempfile
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from pptx_agent.pptx_wrapper.chart_builder import add_chart_to_slide
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.pptx_wrapper.shapes import ImageWrapper
from pptx_agent.pptx_wrapper.smartart_builder import add_smartart_to_slide
from pptx_agent.pptx_wrapper.table_builder import add_table_to_slide
from pptx_agent.schemas import PresentationSchema, SlideSchema
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, ImageBlock, SmartArtBlock, TableBlock
from pptx_agent.validators.exceptions import InvalidFileError


def _get_version() -> str:
    """Get package version from importlib.metadata.

    Returns:
        Package version string, or "unknown" if package not found.
    """
    try:
        return version("pptx-agent")
    except PackageNotFoundError:
        return "unknown"


# Logger for this module
logger = logging.getLogger(__name__)


# Supported image formats (FR-CG-072)
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"}


def _validate_image_path(image_path: str) -> None:
    """Validate that image path is within current working directory or system temp directory.

    This prevents path traversal attacks where malicious paths like
    '../../../etc/passwd' could access files outside the working directory.

    Allows paths within:
    - Current working directory (for production use)
    - System temporary directory (for test environments)

    Args:
        image_path: Path to image file

    Raises:
        ValueError: If path is outside allowed directories
    """
    try:
        # Convert to Path and resolve to absolute path
        path = Path(image_path).resolve()
        cwd = Path.cwd()
        temp_dir = Path(tempfile.gettempdir()).resolve()

        # Check if resolved path is within current working directory or temp directory
        is_in_cwd = path.is_relative_to(cwd)
        is_in_temp = path.is_relative_to(temp_dir)

        if not (is_in_cwd or is_in_temp):
            msg = (
                f"Image path '{image_path}' resolves to a location outside the "
                f"current working directory. For security reasons, only paths within '{cwd}' "
                f"are allowed. Please use a relative path within the current working directory "
                f"or an absolute path that resolves to a location within the current working "
                "directory."
            )
            raise ValueError(msg)
    except (OSError, ValueError) as e:
        # Handle invalid paths or path resolution errors
        if "outside" in str(e):
            # Re-raise our security error
            raise
        msg = (
            f"Invalid image path '{image_path}': {e}. "
            f"Please provide a valid path within the current working directory '{Path.cwd()}'."
        )
        raise ValueError(msg) from e


def _validate_image_format(image_path: str) -> None:
    """Validate that image file has a supported format.

    Args:
        image_path: Path to image file

    Raises:
        ValueError: If image format is not supported
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_FORMATS:
        msg = (
            f"Unsupported image format: '{suffix}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
        )
        raise ValueError(msg)


def _embed_metadata(
    prs: PresentationWrapper,
    content: PresentationSchema,
    template_path: str,
) -> None:
    """Embed generation metadata into presentation core properties.

    Args:
        prs: Presentation wrapper containing the presentation
        content: PresentationSchema used to generate the presentation
        template_path: Path to the template file used

    Metadata embedded:
        - Generator name and version
        - Generation timestamp
        - Template filename
        - Content hash (SHA256, first 16 chars)
    """
    # Access presentation core properties via public property
    core_props = prs.core_properties

    # Get current timestamp once for consistency
    now = datetime.now(UTC)

    # Set generation timestamp
    core_props.created = now
    core_props.modified = now

    # Calculate content hash for tracking
    content_json = content.model_dump_json()
    content_hash = hashlib.sha256(content_json.encode()).hexdigest()[:16]

    # Extract template filename
    template_name = Path(template_path).name

    # Get version at runtime for proper testing/mocking
    pkg_version = _get_version()

    # Build metadata comment string
    metadata_parts = [
        f"Generated by: pptx-agent v{pkg_version}",
        f"Template: {template_name}",
        f"Generated: {now.isoformat()}",
        f"Content Hash: {content_hash}",
    ]

    core_props.comments = " | ".join(metadata_parts)
    core_props.subject = f"Generated using pptx-agent v{pkg_version} with template {template_name}"


def build_presentation(
    content: PresentationSchema,
    template_path: str,
    output_path: str,
) -> str:
    """Build PowerPoint presentation from validated content schema.

    Args:
        content: Validated PresentationSchema with slides and content blocks
        template_path: Path to PowerPoint template file
        output_path: Path where generated presentation should be saved

    Returns:
        Path to the generated .pptx file (same as output_path)

    Raises:
        FileNotFoundError: If template file doesn't exist
        ValueError: If template is invalid or layout not found
    """
    # Initialize presentation wrapper
    prs = PresentationWrapper()

    # Load template - convert InvalidFileError to ValueError for cleaner API
    try:
        prs.load_template(template_path)
    except InvalidFileError as e:
        raise ValueError(str(e)) from e

    # Build each slide
    for slide_schema in content.slides:
        # Create slide with specified layout
        slide = prs.add_slide(slide_schema.layout_name)

        # Set title (log warning if layout has no title placeholder)
        try:
            slide.set_title(slide_schema.title)
        except ValueError as e:
            logger.warning(
                "Failed to set title for slide with layout '%s': %s (title: '%s')",
                slide_schema.layout_name,
                str(e),
                slide_schema.title,
            )

        # Populate content blocks
        for block in slide_schema.content:
            # Handle TextBlock
            if isinstance(block, TextBlock):
                slide.add_text(
                    placeholder_name=block.placeholder_name,
                    text=block.text,
                    check_overflow=False,  # Minimal implementation
                )
            # Handle ChartBlock
            elif isinstance(block, ChartBlock):
                add_chart_to_slide(slide, block)
            # Handle TableBlock
            elif isinstance(block, TableBlock):
                add_table_to_slide(slide, block)
            # Handle SmartArtBlock
            elif isinstance(block, SmartArtBlock):
                add_smartart_to_slide(slide, block)
            # Handle ImageBlock
            elif isinstance(block, ImageBlock):  # type: ignore[reportUnnecessaryIsInstance]
                image_path = block.image_path
                _validate_image_path(image_path)  # Security: Check for path traversal first
                _validate_image_format(image_path)  # Then check format
                ImageWrapper.add_image(
                    slide.slide,
                    block.placeholder_name,
                    image_path,
                    block.alt_text,
                )

    # Embed metadata before saving
    _embed_metadata(prs, content, template_path)

    # Save presentation
    prs.save(output_path)

    # Return output path
    return output_path


def rebuild_slide_with_layout(
    pptx_path: str,
    slide_index: int,
    new_layout: str,
    slide_data: SlideSchema,
) -> None:
    """Rebuild a slide with a different layout.

    This function is used for overflow resolution when a slide's content
    doesn't fit in the current layout. It removes the existing slide and
    creates a new one with the specified layout, preserving title and content.

    Args:
        pptx_path: Path to the PowerPoint file to modify
        slide_index: Index of the slide to rebuild (0-based)
        new_layout: Name of the new layout to use
        slide_data: SlideSchema containing title and content to preserve

    Raises:
        IndexError: If slide_index is out of range
        ValueError: If new_layout doesn't exist in the template
        FileNotFoundError: If pptx_path doesn't exist
    """
    # Load the existing presentation
    prs = PresentationWrapper()

    try:
        prs.load_template(pptx_path)
    except InvalidFileError as e:
        raise FileNotFoundError(str(e)) from e

    # Validate slide index
    slide_count = prs.slide_count()
    if slide_index < 0 or slide_index >= slide_count:
        msg = f"Slide index {slide_index} out of range (presentation has {slide_count} slides)"
        raise IndexError(msg)

    # Remove the old slide
    prs.delete_slide(slide_index)

    # Insert new slide at the same position
    slide = prs.insert_slide(new_layout, slide_index)

    # Restore title
    try:
        slide.set_title(slide_data.title)
    except ValueError as e:
        logger.warning(
            "Failed to set title for rebuilt slide with layout '%s': %s (title: '%s')",
            new_layout,
            str(e),
            slide_data.title,
        )

    # Restore content blocks
    for block in slide_data.content:
        if isinstance(block, TextBlock):
            slide.add_text(
                placeholder_name=block.placeholder_name,
                text=block.text,
                check_overflow=False,
            )
        elif isinstance(block, ChartBlock):
            add_chart_to_slide(slide, block)
        elif isinstance(block, TableBlock):
            add_table_to_slide(slide, block)
        elif isinstance(block, SmartArtBlock):
            add_smartart_to_slide(slide, block)
        elif isinstance(block, ImageBlock):  # type: ignore[reportUnnecessaryIsInstance]
            image_path = block.image_path
            _validate_image_path(image_path)  # Security: Check for path traversal first
            _validate_image_format(image_path)  # Then check format
            ImageWrapper.add_image(
                slide.slide,
                block.placeholder_name,
                image_path,
                block.alt_text,
            )

    # Save the modified presentation
    prs.save(pptx_path)
