"""Custom Pydantic validators for template compatibility.

These validators check compatibility between presentation content and
template capabilities, used within Pydantic model validation.
"""

from typing import Literal

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest


def validate_layout_exists(layout_name: str, template: TemplateManifest) -> str:
    """Validate that a layout exists in the template.

    Args:
        layout_name: Name of the layout to validate
        template: Template manifest to check against

    Returns:
        The layout_name if valid

    Raises:
        ValueError: If layout doesn't exist in template
    """
    layout = template.get_layout_by_name(layout_name)
    if layout is None:
        msg = (
            f"Layout validation failed: layout '{layout_name}' not found in template "
            f"'{template.template_name}'. Expected: valid layout name from template."
        )
        raise ValueError(msg)
    return layout_name


def validate_placeholder_exists(placeholder_name: str, layout: LayoutInfo) -> str:
    """Validate that a placeholder exists in the layout.

    Args:
        placeholder_name: Name of the placeholder to validate
        layout: Layout to check for the placeholder

    Returns:
        The placeholder_name if valid

    Raises:
        ValueError: If placeholder doesn't exist in layout
    """
    for placeholder in layout.placeholders:
        if placeholder.name == placeholder_name:
            return placeholder_name

    msg = (
        f"Placeholder validation failed: placeholder '{placeholder_name}' "
        f"not found in layout '{layout.name}'. "
        f"Expected: valid placeholder name from layout."
    )
    raise ValueError(msg)


def validate_content_capacity(
    content: str, placeholder: PlaceholderInfo, language: Literal["en", "ja"]
) -> str:
    """Validate that content fits within placeholder capacity.

    Applies language-specific capacity ratios:
    - English (en): 1.0x (no adjustment)
    - Japanese (ja): 0.55x (denser characters)

    Args:
        content: Content text to validate
        placeholder: Placeholder with max_chars capacity
        language: Language code for capacity calculation

    Returns:
        The content if valid

    Raises:
        ValueError: If content exceeds placeholder capacity
    """
    content_length = len(content)
    max_capacity = placeholder.max_chars

    # Apply language ratio
    effective_capacity = int(max_capacity * 0.55) if language == "ja" else max_capacity

    if content_length > effective_capacity:
        msg = (
            f"Content capacity validation failed: content length {content_length} characters "
            f"exceeds maximum capacity {effective_capacity} characters for placeholder "
            f"'{placeholder.name}' with language '{language}'. "
            "Expected: content within capacity limit."
        )
        raise ValueError(msg)

    return content


def validate_layout_supports_charts(layout: LayoutInfo) -> LayoutInfo:
    """Validate that layout supports chart insertion.

    Args:
        layout: Layout to validate

    Returns:
        The layout if valid

    Raises:
        ValueError: If layout doesn't support charts
    """
    if not layout.supports_charts:
        msg = (
            f"Layout capability validation failed: layout '{layout.name}' does not support charts. "
            "Expected: layout with chart support."
        )
        raise ValueError(msg)
    return layout


def validate_layout_supports_tables(layout: LayoutInfo) -> LayoutInfo:
    """Validate that layout supports table insertion.

    Args:
        layout: Layout to validate

    Returns:
        The layout if valid

    Raises:
        ValueError: If layout doesn't support tables
    """
    if not layout.supports_tables:
        msg = (
            f"Layout capability validation failed: layout '{layout.name}' does not support tables. "
            "Expected: layout with table support."
        )
        raise ValueError(msg)
    return layout


def validate_layout_supports_smartart(layout: LayoutInfo) -> LayoutInfo:
    """Validate that layout supports SmartArt insertion.

    Args:
        layout: Layout to validate

    Returns:
        The layout if valid

    Raises:
        ValueError: If layout doesn't support SmartArt
    """
    if not layout.supports_smartart:
        msg = (
            f"Layout capability validation failed: layout '{layout.name}' does not support "
            "SmartArt. Expected: layout with SmartArt support."
        )
        raise ValueError(msg)
    return layout
