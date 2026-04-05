"""Agents for LLM-powered content generation.

This module contains agents that analyze and generate presentation content:
- Story Analyzer: Analyzes input text to extract topic, audience, message, tone
- Outline Generator: Creates presentation structure (to be implemented)
- Content Generator: Generates detailed slide content (to be implemented)
"""

from pptx_agent.agents.story_analyzer import StoryAnalysis, analyze_story

__all__ = ["StoryAnalysis", "analyze_story"]
