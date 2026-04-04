"""Outline schema models for LLM-generated presentation structure.

These models represent the intermediate output from LLM agents:
- PresentationOutline: High-level structure from outline generator agent
- SlideContent: Detailed slide content from content generator agent

These differ from PresentationSchema/SlideSchema which represent the final
rendered structure for PPTX generation.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SlideContent(BaseModel):
    """Content for a single slide in the presentation outline.

    Attributes:
        slide_number: Sequential slide number (starts at 1)
        layout_name: Name of the slide layout to use from template
        title: Slide title
        content: Main content text for the slide
        speaker_notes: Optional speaker notes for the presenter
    """

    slide_number: int = Field(gt=0, description="Slide number (must be positive)")
    layout_name: str = Field(min_length=1, description="Layout name from template")
    title: str = Field(min_length=1, description="Slide title")
    content: str = Field(description="Main slide content")
    speaker_notes: str | None = Field(default=None, description="Speaker notes")


class PresentationOutline(BaseModel):
    """High-level presentation structure from LLM outline generator.

    Attributes:
        title: Presentation title
        slides: List of slide content specifications
        output_language: Target output language ('en' or 'ja')
    """

    title: str = Field(min_length=1, description="Presentation title")
    slides: list[SlideContent] = Field(min_length=1, description="Slide content list")
    output_language: Literal["en", "ja"] = Field(
        default="en", description="Output language (en=English, ja=Japanese)"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate that title is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            msg = "Presentation title cannot be empty or whitespace-only"
            raise ValueError(msg)
        return v

    @field_validator("slides")
    @classmethod
    def validate_slides(cls, v: list[SlideContent]) -> list[SlideContent]:
        """Validate that at least one slide is present."""
        if len(v) < 1:
            msg = "Presentation must contain at least one slide"
            raise ValueError(msg)
        return v
