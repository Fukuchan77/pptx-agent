"""Unit tests for SmartArt support in content generator agent.

Tests cover:
- SmartArt data parsing from "smartart:" prefix
- SmartArtBlock creation with correct structure
- Node text and level parsing
- Different diagram types (process, hierarchy, cycle, etc.)
- Integration with manifest-based placeholder names
"""

from pptx_agent.agents.content_generator import generate_content
from pptx_agent.schemas.outline import PresentationOutline, SlideContent
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import SmartArtBlock


def test_generate_content_with_smartart_process():
    """Test SmartArt process diagram generation from outline."""
    outline = PresentationOutline(
        title="Process Flow",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Project Workflow",
                content="smartart:process|Planning,Design,Development,Testing,Deployment",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # Should have one slide with SmartArtBlock
    assert len(result.slides) == 1
    assert len(result.slides[0].content) == 1

    # Verify SmartArtBlock structure
    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.diagram_type == "process"
    assert len(block.nodes) == 5
    assert block.nodes[0]["text"] == "Planning"
    assert block.nodes[4]["text"] == "Deployment"


def test_generate_content_with_smartart_hierarchy():
    """Test SmartArt hierarchy diagram generation."""
    outline = PresentationOutline(
        title="Organization",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Company Structure",
                content="smartart:hierarchy|CEO,VP Sales,VP Engineering,Manager,Developer",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.diagram_type == "hierarchy"
    assert len(block.nodes) == 5


def test_generate_content_with_smartart_cycle():
    """Test SmartArt cycle diagram generation."""
    outline = PresentationOutline(
        title="PDCA Cycle",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Continuous Improvement",
                content="smartart:cycle|Plan,Do,Check,Act",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.diagram_type == "cycle"
    assert len(block.nodes) == 4
    assert block.nodes[0]["text"] == "Plan"


def test_generate_content_smartart_placeholder_name():
    """Test that SmartArt uses correct placeholder name."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Step 1,Step 2,Step 3",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    # Should use default placeholder name
    assert block.placeholder_name == "Content Placeholder"


def test_generate_content_smartart_with_manifest():
    """Test SmartArt placeholder name resolution from manifest."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="SmartArt Area", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=5,
            ),
        ],
    )

    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|A,B,C",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline, manifest=manifest)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    # Should use placeholder name from manifest
    assert block.placeholder_name == "SmartArt Area"


def test_generate_content_smartart_node_level_default():
    """Test that SmartArt nodes have level 0 by default."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Node 1,Node 2",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    # All nodes should have level 0 (flat structure)
    for node in block.nodes:
        assert node["level"] == 0


def test_generate_content_smartart_japanese():
    """Test SmartArt generation with Japanese content."""
    outline = PresentationOutline(
        title="プロセス",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="開発プロセス",
                content="smartart:process|計画,設計,実装,テスト,リリース",
            ),
        ],
        output_language="ja",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.diagram_type == "process"
    assert block.nodes[0]["text"] == "計画"
    assert block.nodes[4]["text"] == "リリース"


def test_generate_content_smartart_single_node():
    """Test SmartArt with single node."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Single Step",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert len(block.nodes) == 1
    assert block.nodes[0]["text"] == "Single Step"


def test_generate_content_smartart_many_nodes():
    """Test SmartArt with many nodes."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Step 1,Step 2,Step 3,Step 4,Step 5,Step 6,Step 7,Step 8",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert len(block.nodes) == 8


def test_generate_content_smartart_empty_node_text():
    """Test that empty node text is handled gracefully."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Step 1,,Step 3",  # Empty middle node
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    # Should skip empty nodes
    assert len(block.nodes) == 2
    assert block.nodes[0]["text"] == "Step 1"
    assert block.nodes[1]["text"] == "Step 3"


def test_generate_content_smartart_whitespace_trimming():
    """Test that node text whitespace is trimmed."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|  Step 1  ,  Step 2  ,  Step 3  ",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.nodes[0]["text"] == "Step 1"
    assert block.nodes[1]["text"] == "Step 2"
    assert block.nodes[2]["text"] == "Step 3"


def test_generate_content_smartart_different_diagram_types():
    """Test various SmartArt diagram types."""
    diagram_types = ["process", "hierarchy", "cycle", "relationship", "matrix", "pyramid"]

    for diagram_type in diagram_types:
        outline = PresentationOutline(
            title="Test",
            slides=[
                SlideContent(
                    slide_number=1,
                    layout_name="Title and Content",
                    title="Test",
                    content=f"smartart:{diagram_type}|Item 1,Item 2,Item 3",
                ),
            ],
            output_language="en",
        )

        result = generate_content(outline)
        block = result.slides[0].content[0]
        assert isinstance(block, SmartArtBlock)
        assert block.diagram_type == diagram_type


def test_generate_content_smartart_special_characters():
    """Test SmartArt with special characters in node text."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Test",
                content="smartart:process|Step #1,Step @2,Step $3",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    block = result.slides[0].content[0]
    assert isinstance(block, SmartArtBlock)
    assert block.nodes[0]["text"] == "Step #1"
    assert block.nodes[1]["text"] == "Step @2"
    assert block.nodes[2]["text"] == "Step $3"


def test_generate_content_preserves_non_smartart_content():
    """Test that non-SmartArt content is not affected by SmartArt parsing."""
    outline = PresentationOutline(
        title="Test",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title and Content",
                title="Text Slide",
                content="This is regular text content",
            ),
            SlideContent(
                slide_number=2,
                layout_name="Title and Content",
                title="SmartArt Slide",
                content="smartart:process|Step 1,Step 2",
            ),
        ],
        output_language="en",
    )

    result = generate_content(outline)

    # First slide should have TextBlock
    assert isinstance(result.slides[0].content[0], TextBlock)

    # Second slide should have SmartArtBlock
    assert isinstance(result.slides[1].content[0], SmartArtBlock)
