"""Visual asset schemas for slides.

Includes:
- ImageBlock: For image placeholders
- ChartBlock: For chart/graph placeholders
- TableBlock: For table placeholders
- SmartArtBlock: For SmartArt diagram placeholders
"""

from typing import Any

from pydantic import BaseModel, Field


class ImageBlock(BaseModel):
    """Image content block.

    Supports both URL and local file path.
    At least one of image_url or image_path must be provided.
    """

    placeholder_name: str = Field(min_length=1)
    image_url: str | None = None
    image_path: str | None = None
    alt_text: str


class ChartBlock(BaseModel):
    """Chart/graph content block.

    Attributes:
        placeholder_name: Target placeholder name
        chart_type: Type of chart (bar, line, pie, etc.)
        data: Chart data structure (dict with series, categories, values)
        title: Chart title
    """

    placeholder_name: str = Field(min_length=1)
    chart_type: str = Field(min_length=1)
    data: dict[str, Any] = Field(min_length=1)
    title: str


class TableBlock(BaseModel):
    """Table content block.

    Attributes:
        placeholder_name: Target placeholder name
        rows: List of rows (each row is list of cell values)
        headers: Column headers
    """

    placeholder_name: str = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)
    headers: list[str]

    @property
    def num_rows(self) -> int:
        """Get number of rows (excluding headers)."""
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        """Get number of columns."""
        return len(self.headers)


class SmartArtBlock(BaseModel):
    """SmartArt diagram content block.

    Attributes:
        placeholder_name: Target placeholder name
        diagram_type: Type of SmartArt diagram (process, hierarchy, etc.)
        nodes: List of nodes with text and level information
    """

    placeholder_name: str = Field(min_length=1)
    diagram_type: str = Field(min_length=1)
    nodes: list[dict[str, Any]] = Field(min_length=1)
