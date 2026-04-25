"""Register default QA rules with the global registry."""

import contextlib

from pptx_agent.qa.rules.content_checks import (
    BulletLengthRule,
    DuplicateTitleRule,
    MissingChartDataRule,
    PathologicalTableDimensionRule,
    SpeakerNotesVerificationRule,
    UnpopulatedImagePlaceholderRule,
)
from pptx_agent.qa.rules.layout_checks import (
    BoundaryOverflowRule,
    EmptyPlaceholderRule,
    MinimumFontSizeRule,
    OverlappingObjectsRule,
    TextOverflowRule,
    UnpopulatedPlaceholderRule,
)
from pptx_agent.qa.rules.registry import get_global_registry
from pptx_agent.qa.rules.style_checks import (
    InvalidBulletIndentRule,
    OffTemplateColorRule,
    OffTemplateFontRule,
    TemplateConformanceRule,
)


def register_default_rules() -> None:
    """Register all default QA rules with the global registry.

    This function registers all built-in QA rules organized by category:
    - Layout checks: Text overflow, empty placeholders, overlapping objects, etc.
    - Content checks: Bullet length, duplicate titles, image placeholders,
      table dimensions, chart data, speaker notes
    - Style checks: Font conformance, color conformance, bullet indentation, template conformance

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

    # Register content check rules
    with contextlib.suppress(ValueError):
        registry.register(BulletLengthRule(), category="content")

    with contextlib.suppress(ValueError):
        registry.register(DuplicateTitleRule(), category="content")

    with contextlib.suppress(ValueError):
        registry.register(UnpopulatedImagePlaceholderRule(), category="content")

    with contextlib.suppress(ValueError):
        registry.register(PathologicalTableDimensionRule(), category="content")

    with contextlib.suppress(ValueError):
        registry.register(MissingChartDataRule(), category="content")

    with contextlib.suppress(ValueError):
        registry.register(SpeakerNotesVerificationRule(), category="content")

    # Register style check rules
    with contextlib.suppress(ValueError):
        registry.register(OffTemplateFontRule(), category="style")

    with contextlib.suppress(ValueError):
        registry.register(OffTemplateColorRule(), category="style")

    with contextlib.suppress(ValueError):
        registry.register(InvalidBulletIndentRule(), category="style")

    with contextlib.suppress(ValueError):
        registry.register(TemplateConformanceRule(), category="style")


# Auto-register rules when module is imported
register_default_rules()


# Made with Bob
