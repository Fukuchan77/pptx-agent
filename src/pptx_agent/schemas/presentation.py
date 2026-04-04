"""Presentation schema - top-level structure."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from pptx_agent.schemas.slide import SlideSchema


class PresentationSchema(BaseModel):
    """Schema for a complete presentation.

    Attributes:
        title: Presentation title (required, non-empty)
        slides: List of slides (at least one required)
        metadata: Additional metadata (author, date, etc.)
    """

    title: str = Field(min_length=1)
    slides: list[SlideSchema] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

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
    def validate_slides(cls, v: list[SlideSchema]) -> list[SlideSchema]:
        """Validate that at least one slide is present."""
        if len(v) < 1:
            msg = "Presentation must contain at least one slide"
            raise ValueError(msg)
        return v
