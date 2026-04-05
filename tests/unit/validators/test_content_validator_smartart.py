"""Unit tests for SmartArt validation in content validator.

Tests cover:
- SmartArtBlock node count validation against template manifest
- Validation with and without manifest
- Error messages for node count mismatches
- Multiple SmartArt blocks in a presentation
"""

import pytest

from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import SlideSchema
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.schemas.visual_assets import SmartArtBlock
from pptx_agent.validators.content_validator import validate_content
from pptx_agent.validators.exceptions import ContentValidationError


def test_validate_smartart_without_manifest():
    """Test that SmartArt validation passes when no manifest is provided."""
    # Create presentation with SmartArt
    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Test Slide",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},
                            {"text": "Step 3", "level": 0},
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should pass validation without manifest (no node count to check)
    result = validate_content(content)
    assert result == content


def test_validate_smartart_with_matching_node_count():
    """Test SmartArt validation passes when node count matches manifest."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Content Placeholder", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=3,  # Expect 3 nodes
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Test Slide",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},
                            {"text": "Step 3", "level": 0},  # 3 nodes - matches
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should pass validation
    result = validate_content(content, _template_manifest=manifest)
    assert result == content


def test_validate_smartart_with_mismatched_node_count():
    """Test SmartArt validation fails when node count doesn't match manifest."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Content Placeholder", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=5,  # Expect 5 nodes
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Test Slide",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},
                            {"text": "Step 3", "level": 0},  # 3 nodes - doesn't match 5
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should raise ContentValidationError
    with pytest.raises(ContentValidationError) as exc_info:
        validate_content(content, _template_manifest=manifest)

    # Error message should mention node count mismatch
    assert "nodes" in str(exc_info.value).lower()
    assert "3" in str(exc_info.value)
    assert "5" in str(exc_info.value)


def test_validate_smartart_layout_without_node_count():
    """Test SmartArt validation when layout doesn't specify node count."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Content Placeholder", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=None,  # No specific count required
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Test Slide",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should pass validation (no specific count to check)
    result = validate_content(content, _template_manifest=manifest)
    assert result == content


def test_validate_smartart_layout_not_in_manifest():
    """Test SmartArt validation when layout is not in manifest."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Different Layout",  # Different layout
                placeholders=[
                    PlaceholderInfo(name="Content", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=5,
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",  # Layout not in manifest
                title="Test Slide",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},
                            {"text": "Step 3", "level": 0},
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should pass validation (layout not found, can't validate node count)
    result = validate_content(content, _template_manifest=manifest)
    assert result == content


def test_validate_multiple_smartart_blocks():
    """Test validation with multiple SmartArt blocks in different slides."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title 1", type="TITLE", max_chars=100),
                    PlaceholderInfo(name="Content Placeholder", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=3,
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Slide 1",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="process",
                        nodes=[
                            {"text": "A", "level": 0},
                            {"text": "B", "level": 0},
                            {"text": "C", "level": 0},  # 3 nodes - OK
                        ],
                    ),
                ],
                notes="Notes",
            ),
            SlideSchema(
                layout_name="Title and Content",
                title="Slide 2",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content Placeholder",
                        diagram_type="hierarchy",
                        nodes=[
                            {"text": "X", "level": 0},
                            {"text": "Y", "level": 0},
                            {"text": "Z", "level": 0},  # 3 nodes - OK
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Should pass validation for all SmartArt blocks
    result = validate_content(content, _template_manifest=manifest)
    assert result == content


def test_validate_smartart_error_message_includes_slide_info():
    """Test that validation error includes slide number and title."""
    manifest = TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Content", type="OBJECT", max_chars=500),
                ],
                supports_smartart=True,
                smartart_node_count=4,
            ),
        ],
    )

    content = PresentationSchema(
        title="Test",
        slides=[
            SlideSchema(
                layout_name="Title and Content",
                title="Process Flow",
                content=[
                    SmartArtBlock(
                        placeholder_name="Content",
                        diagram_type="process",
                        nodes=[
                            {"text": "Step 1", "level": 0},
                            {"text": "Step 2", "level": 0},  # Only 2 nodes
                        ],
                    ),
                ],
                notes="Notes",
            ),
        ],
        metadata={},
    )

    # Error should include slide number and title
    with pytest.raises(ContentValidationError) as exc_info:
        validate_content(content, _template_manifest=manifest)

    error_msg = str(exc_info.value)
    assert "Slide 1" in error_msg or "slide 1" in error_msg
    assert "Process Flow" in error_msg
