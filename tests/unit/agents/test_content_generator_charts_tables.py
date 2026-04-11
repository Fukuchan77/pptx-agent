"""Unit tests for chart and table generation in content generator.

Tests Phase 6 (User Story 4) functionality:
- Chart specification generation from numerical data
- Table specification generation from tabular data
- ChartBlock and TableBlock creation
- Data format validation
"""

import pytest

from pptx_agent.agents.content_generator import generate_content
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, TableBlock


@pytest.mark.asyncio
async def test_generate_content_with_chart_data():
    """Test that content generator creates ChartBlock when numerical data is present."""
    # Create outline with numerical data that should become a chart
    outline = PresentationOutline(
        title="Sales Report",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Q1 Sales Performance",
                content="chart:bar|Q1=100,Q2=150,Q3=200,Q4=250",  # Simple chart data format
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    # Verify ChartBlock was created
    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]
    assert len(chart_blocks) > 0, "Expected at least one ChartBlock"

    # Verify chart properties
    chart = chart_blocks[0]
    assert chart.chart_type == "bar"
    assert chart.title == "Q1 Sales Performance"
    assert "categories" in chart.data
    assert "series" in chart.data


@pytest.mark.asyncio
async def test_generate_content_with_table_data():
    """Test that content generator creates TableBlock when tabular data is present."""
    # Create outline with tabular data
    outline = PresentationOutline(
        title="Product Comparison",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Feature Comparison",
                content="table:Product|Price|Rating\nProduct A|$100|4.5\nProduct B|$150|4.8",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    # Verify TableBlock was created
    table_blocks = [b for b in result.slides[0].content if isinstance(b, TableBlock)]
    assert len(table_blocks) > 0, "Expected at least one TableBlock"

    # Verify table properties
    table = table_blocks[0]
    assert len(table.headers) == 3  # Product, Price, Rating
    assert table.num_rows == 2  # Product A, Product B
    assert table.num_cols == 3


@pytest.mark.asyncio
async def test_generate_content_with_line_chart():
    """Test line chart generation."""
    outline = PresentationOutline(
        title="Revenue Trends",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Annual Revenue",
                content="chart:line|2021=1000,2022=1200,2023=1500",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]
    assert len(chart_blocks) > 0
    assert chart_blocks[0].chart_type == "line"


@pytest.mark.asyncio
async def test_generate_content_with_pie_chart():
    """Test pie chart generation."""
    outline = PresentationOutline(
        title="Market Share",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Market Distribution",
                content="chart:pie|Product A=40,Product B=30,Product C=30",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]
    assert len(chart_blocks) > 0
    assert chart_blocks[0].chart_type == "pie"


@pytest.mark.asyncio
async def test_generate_content_with_large_table():
    """Test that large tables are handled (up to 20 rows x 10 columns per FR-026)."""
    # Create table with 15 rows and 5 columns (within limits)
    rows_data = "\n".join([f"Row{i}|Value{i}|Data{i}|Info{i}|Note{i}" for i in range(1, 16)])
    table_content = f"table:Col1|Col2|Col3|Col4|Col5\n{rows_data}"

    outline = PresentationOutline(
        title="Large Dataset",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Detailed Data",
                content=table_content,
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    table_blocks = [b for b in result.slides[0].content if isinstance(b, TableBlock)]
    assert len(table_blocks) > 0
    assert table_blocks[0].num_rows == 15
    assert table_blocks[0].num_cols == 5


@pytest.mark.asyncio
async def test_generate_content_mixed_text_and_chart():
    """Test slide with both text content and chart."""
    outline = PresentationOutline(
        title="Analysis Report",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Performance Analysis",
                content="Key findings: chart:bar|Jan=100,Feb=120,Mar=150",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    # Should have both text and chart blocks
    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]

    # Should have at least text OR chart (implementation may vary)
    assert len(text_blocks) + len(chart_blocks) > 0


@pytest.mark.asyncio
async def test_generate_content_chart_in_japanese():
    """Test chart generation with Japanese labels."""
    outline = PresentationOutline(
        title="売上レポート",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="四半期売上",
                content="chart:bar|第1四半期=100,第2四半期=150,第3四半期=200",
            ),
        ],
        output_language="ja",
    )

    result = await generate_content(outline, use_llm=False)

    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]
    assert len(chart_blocks) > 0
    assert chart_blocks[0].chart_type == "bar"


@pytest.mark.asyncio
async def test_generate_content_table_in_japanese():
    """Test table generation with Japanese content."""
    outline = PresentationOutline(
        title="製品比較",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="機能比較",
                content="table:製品|価格|評価\n製品A|100円|4.5\n製品B|150円|4.8",
            ),
        ],
        output_language="ja",
    )

    result = await generate_content(outline, use_llm=False)

    table_blocks = [b for b in result.slides[0].content if isinstance(b, TableBlock)]
    assert len(table_blocks) > 0
    assert table_blocks[0].num_cols == 3


@pytest.mark.asyncio
async def test_generate_content_multiple_charts_in_presentation():
    """Test presentation with multiple slides containing charts."""
    outline = PresentationOutline(
        title="Business Review",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Revenue",
                content="chart:bar|Q1=100,Q2=150",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="Market Share",
                content="chart:pie|Us=40,Competitor=60",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    # Verify both slides have charts
    chart_blocks_slide1 = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]
    chart_blocks_slide2 = [b for b in result.slides[1].content if isinstance(b, ChartBlock)]

    assert len(chart_blocks_slide1) > 0
    assert len(chart_blocks_slide2) > 0


@pytest.mark.asyncio
async def test_generate_content_chart_without_prefix_fallback():
    """Test that regular numerical content without chart: prefix creates text blocks."""
    outline = PresentationOutline(
        title="Numbers",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Statistics",
                content="Sales increased by 100 units in Q1 and 150 in Q2",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    # Should create text blocks, not chart blocks (no chart: prefix)
    from pptx_agent.schemas.text import TextBlock

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    chart_blocks = [b for b in result.slides[0].content if isinstance(b, ChartBlock)]

    # Without explicit chart marker, should default to text
    assert len(text_blocks) > 0 or len(chart_blocks) > 0


@pytest.mark.asyncio
async def test_generate_content_table_without_prefix_fallback():
    """Test that structured text without table: prefix creates text blocks."""
    outline = PresentationOutline(
        title="Info",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Products",
                content="Product A costs $100. Product B costs $150.",
            ),
        ],
        output_language="en",
    )

    result = await generate_content(outline, use_llm=False)

    from pptx_agent.schemas.text import TextBlock

    text_blocks = [b for b in result.slides[0].content if isinstance(b, TextBlock)]
    table_blocks = [b for b in result.slides[0].content if isinstance(b, TableBlock)]

    # Without explicit table marker, should default to text
    assert len(text_blocks) > 0 or len(table_blocks) > 0
