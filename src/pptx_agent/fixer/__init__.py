"""Auto-fix module for automatic issue remediation.

This module provides automatic correction strategies for fixable quality issues
detected by the QA engine.

Note: Default strategies are NOT automatically registered at import time because
they require a PresentationWrapper context. Call register_default_strategies()
with the presentation context when setting up the fix engine.
"""

from pptx_agent.fixer.engine import FixEngine, FixStrategyRegistry, get_global_registry
from pptx_agent.fixer.schemas import FixLoopResult, FixResult, FixStatus
from pptx_agent.fixer.strategies import register_default_strategies

__all__ = [
    "FixEngine",
    "FixLoopResult",
    "FixResult",
    "FixStatus",
    "FixStrategyRegistry",
    "get_global_registry",
    "register_default_strategies",
]

# Note: Unlike QA rules, fix strategies are NOT registered automatically at import
# because they require presentation context. Users must call the function
# register_default_strategies with presentation and outline parameters
# before running the fix engine.

# Made with Bob
