"""Story analyzer agent for parsing and summarizing input text.

This module provides functionality to analyze input text and extract:
- Topic: Main subject of the content
- Target Audience: Intended audience for the presentation
- Key Message: Primary message or takeaway
- Tone: Communication style (formal, casual, professional, etc.)
- Language: Detected language (en or ja)
- Suggested Structure: Optional high-level content structure

The analyzer uses heuristic-based text analysis for initial implementation.
Future versions may integrate LLM-based analysis for improved accuracy.
"""

import logging
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent

from pptx_agent.agents.analyzer_config import ANALYZER_CONFIG
from pptx_agent.agents.prompts import STORY_ANALYZER_PROMPT
from pptx_agent.config import get_config
from pptx_agent.utils.language_detector import detect_language
from pptx_agent.validators.input_validator import InputValidationError

logger = logging.getLogger(__name__)


class StoryAnalysis(BaseModel):
    """Analysis result from story analyzer.

    Attributes:
        topic: Main topic or subject of the input text
        target_audience: Identified target audience for the content
        key_message: Primary message or key takeaway
        tone: Communication tone (e.g., formal, casual, professional)
        language: Detected language code ('en' or 'ja')
        suggested_structure: Optional suggested presentation structure
    """

    topic: str = Field(min_length=1, description="Main topic or subject")
    target_audience: str = Field(min_length=1, description="Target audience")
    key_message: str = Field(min_length=1, description="Primary message or takeaway")
    tone: str = Field(min_length=1, description="Communication tone")
    language: Literal["en", "ja"] = Field(description="Detected language (en=English, ja=Japanese)")
    suggested_structure: str | None = Field(default=None, description="Optional content structure")

    @field_validator("topic", "target_audience", "key_message", "tone")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required string fields are not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            msg = "Field cannot be empty or whitespace-only"
            raise ValueError(msg)
        return v


# Module-level agent instance (model provided at runtime)
_story_agent: Agent[None, StoryAnalysis] = Agent(
    output_type=StoryAnalysis,
    system_prompt=STORY_ANALYZER_PROMPT,
)


async def analyze_story(text: str, *, use_llm: bool = True) -> StoryAnalysis:
    """Analyze input text to extract story elements.

    This function performs analysis to extract:
    - Topic (from first lines or headers)
    - Target audience (from contextual clues)
    - Key message (from content analysis)
    - Tone (from linguistic patterns)
    - Language (using language detector utility)

    Args:
        text: Input text to analyze (plain text or Markdown)
        use_llm: If True, use LLM agent for analysis. If False, use heuristic fallback
                 for testing/debugging (default: True).

    Returns:
        StoryAnalysis object containing extracted elements

    Raises:
        InputValidationError: If text is empty or whitespace-only. This is a defensive
            validation that runs even after pipeline-layer validation
            (validate_and_sanitize) to ensure robustness when the function
            is called directly or if pipeline validation is bypassed.

    Note:
        The pipeline layer (validate_and_sanitize) performs primary input
        validation and raises InputValidationError. This function maintains
        its own validation as a defensive measure.
    """
    # Validate input
    if not text or not text.strip():
        msg = "Input text cannot be empty or blank"
        raise InputValidationError(msg)

    if use_llm:
        # Use LLM for analysis with fallback
        config = get_config()
        from pptx_agent.agents.utils import run_agent_with_fallback  # noqa: PLC0415

        result = await run_agent_with_fallback(_story_agent, text, config)
        return result.output
    # Use heuristic fallback for testing/debugging
    return _heuristic_analyze_story(text)


def _heuristic_analyze_story(text: str) -> StoryAnalysis:
    """Heuristic-based story analysis (fallback for testing/debugging).

    This function performs heuristic-based analysis to extract:
    - Topic (from first lines or headers)
    - Target audience (from contextual clues)
    - Key message (from content analysis)
    - Tone (from linguistic patterns)
    - Language (using language detector utility)

    Args:
        text: Input text to analyze (plain text or Markdown)

    Returns:
        StoryAnalysis object containing extracted elements
    """
    # Detect language
    language = detect_language(text)

    # Extract topic from first lines or headers
    topic = _extract_topic(text)

    # Identify target audience from context
    target_audience = _extract_target_audience(text)

    # Extract key message
    key_message = _extract_key_message(text)

    # Detect tone
    tone = _detect_tone(text)

    # Generate suggested structure (optional, based on content)
    suggested_structure = _generate_suggested_structure(text)

    return StoryAnalysis(
        topic=topic,
        target_audience=target_audience,
        key_message=key_message,
        tone=tone,
        language=language,
        suggested_structure=suggested_structure,
    )


def _extract_topic(text: str) -> str:
    """Extract topic from text using heuristic analysis.

    Looks for:
    - Markdown headers (# Title)
    - First non-empty line
    - Keywords in early content

    Args:
        text: Input text

    Returns:
        Extracted topic string
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if not lines:
        return "General Presentation"

    # Check for Markdown headers
    for line in lines[:5]:  # Check first 5 lines
        if line.startswith("#"):
            # Extract header text, removing # symbols
            topic = line.lstrip("#").strip()
            if topic:
                return topic

    # Use first non-empty line as topic
    first_line = lines[0]

    # Limit length for topic
    if len(first_line) > ANALYZER_CONFIG.max_topic_length:
        return first_line[: ANALYZER_CONFIG.max_topic_length - 3] + "..."

    return first_line


def _extract_target_audience(text: str) -> str:
    """Extract target audience from text context.

    Looks for audience-related keywords:
    - beginner, advanced, expert, student, professional
    - business, technical, general, stakeholder

    Uses word boundaries to avoid false positives (e.g., "intro" shouldn't match "introduce",
    "all" shouldn't match "install").

    Args:
        text: Input text

    Returns:
        Identified target audience
    """
    text_lower = text.lower()

    # Define audience keywords and their variations
    # Some keywords need word boundary matching to avoid false positives
    audience_keywords = {
        "beginner": ["beginner", "beginners", "novice", "starter", "intro", "introduction"],
        "advanced": ["advanced", "expert", "experienced", "professional"],
        "student": ["student", "students", "learner", "learners"],
        "business": ["business", "stakeholder", "stakeholders", "executive", "management"],
        "technical": ["technical", "developer", "developers", "engineer", "engineers"],
        "general": ["general", "everyone", "all", "public"],
    }

    # Check for audience keywords using word boundary regex for all keywords
    # to avoid false positives (e.g., "intro" in "introduce", "all" in "install")
    for audience_type, keywords in audience_keywords.items():
        for keyword in keywords:
            # Use word boundary regex for all keywords consistently
            if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                return f"{audience_type.capitalize()} audience"

    # Default to general audience
    return "General audience"


def _truncate_message(msg: str) -> str:
    """Truncate message to maximum length with ellipsis if needed.

    Args:
        msg: Message to truncate

    Returns:
        Truncated message
    """
    if len(msg) > ANALYZER_CONFIG.max_message_length:
        return msg[: ANALYZER_CONFIG.max_message_length - 3] + "..."
    return msg


def _find_message_with_indicators(text: str) -> str | None:
    """Find message using explicit indicators like 'key takeaway', 'conclusion'.

    Args:
        text: Input text

    Returns:
        Extracted message or None if not found
    """
    indicators = [
        "key takeaway",
        "key message",
        "main point",
        "conclusion",
        "summary",
        "in summary",
        "to summarize",
        "the point is",
        "most important",
    ]

    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

    for sentence in sentences:
        sentence_lower = sentence.lower()
        for indicator in indicators:
            if indicator in sentence_lower:
                # Find indicator position in lowercased string for case-insensitive search
                idx = sentence_lower.find(indicator)
                if idx != -1:
                    # Extract from original sentence to preserve case
                    start_idx = idx + len(indicator)
                    msg = sentence[start_idx:].strip()
                    if msg:
                        # Capitalize first character
                        msg = msg[0].upper() + msg[1:]
                        return _truncate_message(msg)
    return None


def _find_emphasized_message(text: str) -> str | None:
    """Find message from Markdown emphasized text (bold/italic).

    Args:
        text: Input text

    Returns:
        Extracted emphasized message or None if not found
    """
    for line in text.split("\n"):
        if "**" in line or "*" in line or "_" in line:
            clean_line = line.replace("**", "").replace("*", "").replace("_", "").strip()
            min_len = ANALYZER_CONFIG.min_emphasized_text_length
            max_len = ANALYZER_CONFIG.max_message_length
            if min_len < len(clean_line) < max_len:
                return clean_line
    return None


def _extract_from_first_paragraph(text: str) -> str | None:
    """Extract message from first substantial paragraph.

    Args:
        text: Input text

    Returns:
        Extracted message from paragraph or None if not found
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return None

    first_para = paragraphs[0]
    if len(first_para) <= ANALYZER_CONFIG.min_paragraph_length:
        return None

    sentences = [s.strip() for s in first_para.split(".") if s.strip()]
    if sentences:
        return _truncate_message(sentences[0])
    return None


def _extract_key_message(text: str) -> str:
    """Extract key message from text.

    Looks for:
    - Explicit key message indicators (key takeaway, conclusion, summary)
    - Important phrases with emphasis markers
    - First substantial sentence

    Args:
        text: Input text

    Returns:
        Extracted key message
    """
    # Try finding message with indicators
    msg = _find_message_with_indicators(text)
    if msg:
        return msg

    # Try finding emphasized text
    msg = _find_emphasized_message(text)
    if msg:
        return msg

    # Try extracting from first paragraph
    msg = _extract_from_first_paragraph(text)
    if msg:
        return msg

    # Fallback: use first sentence from anywhere
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if sentences:
        return _truncate_message(sentences[0])

    return "Content overview and key insights"


def _detect_tone(text: str) -> str:
    """Detect communication tone from text.

    Analyzes:
    - Formality indicators (formal language, jargon)
    - Casual indicators (contractions, informal language)
    - Emotional indicators (exclamations, enthusiasm)

    Args:
        text: Input text

    Returns:
        Detected tone (e.g., formal, casual, professional, friendly)
    """
    text_lower = text.lower()

    # Formal indicators
    formal_keywords = [
        "hereby",
        "pursuant",
        "aforementioned",
        "stakeholder",
        "executive",
        "quarterly",
        "fiscal",
        "strategic",
        "enterprise",
        "herein",
        "advised",
        "demonstrate",
        "performance metrics",
    ]

    # Casual/informal indicators
    casual_keywords = [
        "hey",
        "awesome",
        "cool",
        "gonna",
        "wanna",
        "can't wait",
        "super",
        "pretty much",
        "basically",
    ]

    # Count indicators
    formal_count = sum(1 for keyword in formal_keywords if keyword in text_lower)
    casual_count = sum(1 for keyword in casual_keywords if keyword in text_lower)

    # Check for contractions (casual indicator)
    contractions = ["'ll", "'ve", "'re", "'s", "'t", "'d"]
    contraction_count = sum(text_lower.count(c) for c in contractions)

    # Check for exclamation marks (enthusiastic/casual)
    exclamation_count = text.count("!")

    # Determine tone
    max_contraction_formal = ANALYZER_CONFIG.max_contraction_count_formal
    if formal_count > casual_count and contraction_count < max_contraction_formal:
        return "formal"
    if (
        casual_count > formal_count
        or contraction_count > ANALYZER_CONFIG.min_contraction_count_casual
        or exclamation_count > ANALYZER_CONFIG.min_exclamation_count_casual
    ):
        return "casual"
    if formal_count > 0 and exclamation_count < ANALYZER_CONFIG.max_exclamation_count_professional:
        return "professional"
    if exclamation_count > ANALYZER_CONFIG.max_exclamation_count_professional or casual_count > 0:
        return "friendly"
    return "neutral"


def _generate_suggested_structure(text: str) -> str | None:
    """Generate suggested presentation structure based on content.

    Analyzes text organization to suggest structure like:
    - Introduction, Main Content, Conclusion
    - Problem, Solution, Benefits
    - Overview, Details, Summary

    Args:
        text: Input text

    Returns:
        Suggested structure string or None
    """
    text_lower = text.lower()

    # Check for common structural patterns
    has_intro = any(
        word in text_lower for word in ["introduction", "overview", "background", "intro"]
    )
    has_conclusion = any(
        word in text_lower for word in ["conclusion", "summary", "in summary", "to conclude"]
    )
    has_problem = any(word in text_lower for word in ["problem", "challenge", "issue"])
    has_solution = any(word in text_lower for word in ["solution", "approach", "resolve"])

    # Determine structure pattern
    if has_problem and has_solution:
        return "Problem, Solution, Benefits"
    if has_intro and has_conclusion:
        return "Introduction, Main Content, Conclusion"
    if text.count("#") >= ANALYZER_CONFIG.min_markdown_headers_for_structured:
        # Multiple Markdown headers suggest structured content
        return "Multi-section structured presentation"
    # Default structure
    return "Overview, Key Points, Summary"
