"""Outline validator for presentation outline validation.

Validates PresentationOutline against business rules and optional template manifest.
"""

from pptx_agent.constants import MAX_SLIDES, MIN_SLIDES
from pptx_agent.schemas.outline import PresentationOutline
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.validators.exceptions import InvalidFileError


def validate_outline(
    outline: PresentationOutline,
    template_manifest: TemplateManifest | None = None,
) -> PresentationOutline:
    """Validate presentation outline against business rules and template.

    Validates:
    - Slide count is between 3 and 30 (inclusive)
    - All layout names exist in template (if template_manifest provided)
    - Required fields are populated (handled by Pydantic)

    Args:
        outline: The presentation outline to validate
        template_manifest: Optional template manifest for layout validation

    Returns:
        The validated outline if all checks pass

    Raises:
        InvalidFileError: If validation fails with clear error message
    """
    # Validate slide count (MIN_SLIDES-MAX_SLIDES inclusive)
    slide_count = len(outline.slides)
    if slide_count < MIN_SLIDES or slide_count > MAX_SLIDES:
        msg = (
            f"Presentation must contain between {MIN_SLIDES} and "
            f"{MAX_SLIDES} slides, got {slide_count}"
        )
        raise InvalidFileError(msg)

    # Validate layout names against template if provided
    if template_manifest:
        # Get all valid layout names from template
        valid_layouts = {layout.name for layout in template_manifest.layouts}

        # Find all invalid layout names using list comprehension
        invalid_layouts = [
            slide.layout_name for slide in outline.slides if slide.layout_name not in valid_layouts
        ]

        # Raise error if any invalid layouts found
        if invalid_layouts:
            # Get unique invalid layouts for error message (preserve order)
            unique_invalid = list(dict.fromkeys(invalid_layouts))
            layouts_str = ", ".join(f"'{layout}'" for layout in unique_invalid)
            msg = f"Layout {layouts_str} not found in template '{template_manifest.template_name}'"
            raise InvalidFileError(msg)

    # All validations passed, return the outline
    return outline
