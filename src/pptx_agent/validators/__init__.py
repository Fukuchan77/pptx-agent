"""Validation functions for presentation and slide schemas."""

from pydantic import BaseModel

from pptx_agent.schemas import PresentationSchema, SlideSchema, TextBlock
from pptx_agent.template_parser import TemplateMetadata
from pptx_agent.validators.input_validator import InputValidationError, validate_and_sanitize

__all__ = [
    "InputValidationError",
    "ValidationResult",
    "validate_and_sanitize",
    "validate_presentation_schema",
    "validate_slide_schema",
]


class ValidationResult(BaseModel):
    """Result of validation with errors and warnings."""

    valid: bool
    errors: list[str] = []
    warnings: list[str] = []


def validate_presentation_schema(_schema: PresentationSchema) -> ValidationResult:
    """Validate presentation schema against business rules.

    Note: Basic validations (non-empty title, at least one slide) are already
    handled by Pydantic validators in PresentationSchema. This function can be
    extended with additional business logic validations as needed.

    Args:
        _schema: The presentation schema to validate (currently unused,
            reserved for future validations)

    Returns:
        ValidationResult with any errors or warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Pydantic already validates:
    # - Title is not empty/whitespace
    # - At least one slide exists

    # Additional business logic validations can be added here
    # For now, if the schema passed Pydantic validation, it's valid

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_slide_schema(schema: SlideSchema, template_meta: TemplateMetadata) -> ValidationResult:
    """Validate slide schema against template metadata.

    Args:
        schema: The slide schema to validate
        template_meta: Template metadata containing layout and placeholder info

    Returns:
        ValidationResult with any errors or warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check layout exists in template
    layout = template_meta.get_layout(schema.layout_name)
    if not layout:
        errors.append(f"Layout '{schema.layout_name}' not found in template")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Check each content block's placeholder exists in layout
    for content in schema.content:
        placeholder_name = content.placeholder_name
        placeholder = next(
            (p for p in layout.placeholders if p.name == placeholder_name),
            None,
        )
        if not placeholder:
            errors.append(
                f"Placeholder '{placeholder_name}' not found in layout '{schema.layout_name}'"
            )
            continue

        # Check text capacity for text blocks (have 'text' and 'language' attributes)
        if isinstance(content, TextBlock):
            text_length = len(content.text)
            capacity = placeholder.max_chars

            # Apply language multiplier
            effective_capacity = capacity * 0.55 if content.language == "ja" else capacity

            if text_length > effective_capacity:
                warnings.append(
                    f"Text in '{placeholder_name}' ({text_length} chars) exceeds capacity "
                    f"({int(effective_capacity)} chars for {content.language})"
                )

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
