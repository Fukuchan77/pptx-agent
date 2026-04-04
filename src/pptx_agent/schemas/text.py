"""Text block schemas with language-aware capacity calculation.

Language capacity multipliers:
- English (en): 1.0x
- Japanese (ja): 0.55x (denser character information)
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TextCapacity(BaseModel):
    """Calculate effective text capacity based on language.

    Japanese text requires more visual space per information unit,
    so we apply a 0.55x multiplier to max character capacity.
    """

    language: Literal["en", "ja"]
    max_chars: int = Field(gt=0, description="Maximum character capacity")

    def get_effective_capacity(self) -> int:
        """Get effective capacity after applying language multiplier.

        Returns:
            Effective capacity (int)
        """
        if self.language == "ja":
            return int(self.max_chars * 0.55)
        return self.max_chars


class TextBlock(BaseModel):
    """Text content block for slide placeholders.

    Attributes:
        placeholder_name: Target placeholder name in the template
        text: Text content to insert
        language: Language code ('en' or 'ja')
        max_capacity: Optional maximum character capacity for validation
    """

    placeholder_name: str = Field(min_length=1)
    text: str
    language: Literal["en", "ja"]
    max_capacity: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_text_capacity(self) -> "TextBlock":
        """Validate text length against max_capacity if provided."""
        if self.max_capacity is not None:
            capacity = TextCapacity(language=self.language, max_chars=self.max_capacity)
            effective_capacity = capacity.get_effective_capacity()

            if len(self.text) > effective_capacity:
                msg = (
                    f"Text length ({len(self.text)}) exceeds effective capacity "
                    f"({effective_capacity}) for language '{self.language}'"
                )
                raise ValueError(msg)
        return self
