"""Content validator for presentation content validation.

Validates PresentationSchema content before PowerPoint rendering.
"""

from pptx_agent.schemas.outline import PresentationOutline
from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.schemas.text import TextBlock
from pptx_agent.validators.exceptions import ContentValidationError


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

    Args:
        content: The presentation content to validate
        outline: Optional outline to validate slide count against
        _template_manifest: Optional template manifest (reserved for future use)

    Returns:
        The validated content if all checks pass

    Raises:
        ContentValidationError: If validation fails with clear error message
    """
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

    # Validate each slide has content blocks and text is not empty
    for i, slide in enumerate(content.slides, start=1):
        # Check if slide has any content blocks
        if not slide.content:
            msg = f"Slide {i} '{slide.title}' has no content blocks"
            raise ContentValidationError(msg)

        # Check each text block for empty text
        for block in slide.content:
            if isinstance(block, TextBlock) and not block.text.strip():
                # Check if text is empty or whitespace-only
                msg = (
                    f"Slide {i} '{slide.title}' has empty text in "
                    f"placeholder '{block.placeholder_name}'"
                )
                raise ContentValidationError(msg)

    # All validations passed, return the content
    return content
