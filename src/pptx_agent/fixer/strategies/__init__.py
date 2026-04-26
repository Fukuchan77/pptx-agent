"""Fix strategies for automatic issue remediation.

This module provides concrete fix strategies for different types of QA issues:
- Text overflow fixes (font reduction, layout switching, content summarization)
- Placeholder population fixes
- Style violation fixes

Each strategy implements a common interface with an `apply` method that takes
a QAIssue and returns a FixResult.
"""

from typing import Any

from pptx_agent.fixer.engine import FixStrategyRegistry, get_global_registry
from pptx_agent.fixer.schemas import FixResult
from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy
from pptx_agent.fixer.strategies.style import StyleResetStrategy
from pptx_agent.fixer.strategies.text_overflow import (
    ContentSummarizationStrategy,
    FontReductionStrategy,
    LayoutSwitchingStrategy,
)
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.schemas import QAIssue

__all__ = [
    "ContentSummarizationStrategy",
    "FontReductionStrategy",
    "LayoutSwitchingStrategy",
    "PlaceholderPopulationStrategy",
    "StyleResetStrategy",
    "register_default_strategies",
]


def register_default_strategies(
    registry: FixStrategyRegistry | None = None,
    presentation: PresentationWrapper | None = None,
    outline: Any | None = None,
) -> None:
    """Register all default fix strategies with the registry.

    This function registers the following strategies:
    - QA-L-001: Text overflow fixes (font reduction, layout switching, summarization)
    - QA-L-002: Empty placeholder population
    - QA-S-001: Style violation fixes

    Args:
        registry: Registry to register strategies with. If None, uses global registry.
        presentation: Presentation wrapper to bind to strategies. Required for actual fixing.
        outline: Optional outline data to bind to strategies.

    Note:
        If presentation is None, no strategies are registered (early return).
        Tests that need registration without a real presentation should pass a stub
        PresentationWrapper instance.
    """
    if registry is None:
        registry = get_global_registry()

    # Text overflow strategies - QA-L-001
    # Multiple strategies registered for the same rule; engine tries them in order
    if presentation is not None:
        # Create wrappers that bind the presentation context
        font_reduction_wrapper = create_strategy_wrapper(
            FontReductionStrategy, presentation, outline
        )
        layout_switching_wrapper = create_strategy_wrapper(
            LayoutSwitchingStrategy, presentation, outline
        )
        content_summarization_wrapper = create_strategy_wrapper(
            ContentSummarizationStrategy, presentation, outline
        )
        placeholder_population_wrapper = create_strategy_wrapper(
            PlaceholderPopulationStrategy, presentation, outline
        )
        style_reset_wrapper = create_strategy_wrapper(StyleResetStrategy, presentation, outline)

        # Register strategies for each rule
        # Multiple strategies can be registered per rule; engine tries them in order
        registry.register(FontReductionStrategy.rule_id, font_reduction_wrapper)
        registry.register(FontReductionStrategy.rule_id, layout_switching_wrapper)
        registry.register(FontReductionStrategy.rule_id, content_summarization_wrapper)
        registry.register(PlaceholderPopulationStrategy.rule_id, placeholder_population_wrapper)
        registry.register(StyleResetStrategy.rule_id, style_reset_wrapper)


def create_strategy_wrapper(
    strategy_class: type,
    presentation: PresentationWrapper,
    outline: Any | None = None,
) -> Any:
    """Create a wrapper function for a strategy that captures context.

    This helper function creates a closure that captures the presentation
    and outline context, allowing the strategy to be called with just
    the issue parameter as required by the registry.

    Args:
        strategy_class: Strategy class to instantiate
        presentation: Presentation wrapper to pass to strategy
        outline: Optional outline data to pass to strategy

    Returns:
        Callable that takes a QAIssue and returns a FixResult
    """
    strategy = strategy_class()

    def wrapper(issue: QAIssue) -> FixResult:
        return strategy.apply(issue, presentation, outline)

    return wrapper


# Made with Bob
