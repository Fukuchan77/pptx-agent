"""System prompts for LLM agents.

This package contains system prompt definitions for each LLM agent:
- story_analyzer: Prompt for analyzing input text and extracting story elements
- outline_generator: Prompt for generating presentation outline
- content_generator: Prompt for generating detailed slide content
"""

from pptx_agent.agents.prompts.content_generator import CONTENT_GENERATOR_PROMPT
from pptx_agent.agents.prompts.outline_generator import OUTLINE_GENERATOR_PROMPT
from pptx_agent.agents.prompts.story_analyzer import STORY_ANALYZER_PROMPT

__all__ = [
    "CONTENT_GENERATOR_PROMPT",
    "OUTLINE_GENERATOR_PROMPT",
    "STORY_ANALYZER_PROMPT",
]
