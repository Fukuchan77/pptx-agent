"""Configuration for story analyzer heuristic fallbacks."""

from dataclasses import dataclass


@dataclass
class StoryAnalyzerConfig:
    """Constants and configuration for heuristic story analysis."""

    max_topic_length: int = 100
    max_message_length: int = 150
    min_emphasized_text_length: int = 20
    min_paragraph_length: int = 50
    max_contraction_count_formal: int = 3
    min_contraction_count_casual: int = 5
    max_exclamation_count_professional: int = 2
    min_exclamation_count_casual: int = 3
    min_markdown_headers_for_structured: int = 3


# Global configuration instance
ANALYZER_CONFIG = StoryAnalyzerConfig()
