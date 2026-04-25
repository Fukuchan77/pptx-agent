"""Register default QA rules with the global registry."""

import contextlib

from pptx_agent.qa.rules.layout_checks import (
    BoundaryOverflowRule,
    EmptyPlaceholderRule,
    MinimumFontSizeRule,
    OverlappingObjectsRule,
    TextOverflowRule,
    UnpopulatedPlaceholderRule,
)
from pptx_agent.qa.rules.registry import get_global_registry


def register_default_rules() -> None:
    """Register all default QA rules with the global registry.

    This function registers all built-in QA rules organized by category:
    - Layout checks: Text overflow, empty placeholders, overlapping objects, etc.
    - Content checks: (to be added in future phases)
    - Style checks: (to be added in future phases)

    The function is idempotent - calling it multiple times will not
    cause errors (duplicate registrations are prevented by the registry).
    """
    registry = get_global_registry()

    # Register layout check rules
    with contextlib.suppress(ValueError):
        registry.register(TextOverflowRule(), category="layout")

    with contextlib.suppress(ValueError):
        registry.register(EmptyPlaceholderRule(), category="layout")

    with contextlib.suppress(ValueError):
        registry.register(UnpopulatedPlaceholderRule(), category="layout")

    with contextlib.suppress(ValueError):
        registry.register(OverlappingObjectsRule(), category="layout")

    with contextlib.suppress(ValueError):
        registry.register(BoundaryOverflowRule(), category="layout")

    with contextlib.suppress(ValueError):
        registry.register(MinimumFontSizeRule(), category="layout")


# Auto-register rules when module is imported
register_default_rules()


# Made with Bob
