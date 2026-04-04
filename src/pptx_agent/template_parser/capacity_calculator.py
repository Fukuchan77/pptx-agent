"""Capacity calculator for template placeholders with language awareness.

Calculates effective text capacities for template placeholders based on
language-specific character density ratios.

Language ratios are imported from text_capacity module to avoid duplication.
"""

from typing import Literal

from pptx_agent.schemas.template_manifest import LayoutInfo, TemplateManifest
from pptx_agent.utils.text_capacity import get_language_multiplier


def calculate_effective_capacity(max_chars: int, language: Literal["en", "ja"]) -> int:
    """Calculate effective capacity for a placeholder based on language.

    Args:
        max_chars: Maximum character capacity of the placeholder
        language: Target language code ('en' or 'ja')

    Returns:
        Effective capacity after applying language ratio
    """
    multiplier = get_language_multiplier(language)
    return int(max_chars * multiplier)


def calculate_layout_capacities(
    layout: LayoutInfo, language: Literal["en", "ja"]
) -> dict[str, int]:
    """Calculate effective capacities for all placeholders in a layout.

    Args:
        layout: Layout containing placeholders
        language: Target language code ('en' or 'ja')

    Returns:
        Dictionary mapping placeholder name to effective capacity
    """
    capacities = {}
    for placeholder in layout.placeholders:
        effective_capacity = calculate_effective_capacity(placeholder.max_chars, language)
        capacities[placeholder.name] = effective_capacity
    return capacities


def calculate_manifest_capacities(
    manifest: TemplateManifest, language: Literal["en", "ja"] | None = None
) -> dict[str, dict[str, int]]:
    """Calculate effective capacities for all placeholders in all layouts.

    Args:
        manifest: Template manifest containing layouts
        language: Target language code ('en' or 'ja').
                 If None, uses manifest's default_language.

    Returns:
        Dictionary mapping layout name to placeholder capacities dict
        Structure: {layout_name: {placeholder_name: effective_capacity}}
    """
    # Use manifest's default language if not specified
    target_language = language if language is not None else manifest.default_language

    capacities = {}
    for layout in manifest.layouts:
        layout_capacities = calculate_layout_capacities(layout, target_language)
        capacities[layout.name] = layout_capacities
    return capacities
