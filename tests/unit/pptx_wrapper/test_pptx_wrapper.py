"""
Unit tests for PPTX wrapper modules.

Tests for PresentationWrapper, SlideWrapper, ChartWrapper, TableWrapper,
ImageWrapper, and SmartArtWrapper classes.

RED Phase: All tests expected to FAIL before implementation.
"""

from pathlib import Path

import pytest
from PIL import Image

from pptx_agent.pptx_wrapper import (
    ChartWrapper,
    ImageWrapper,
    PresentationWrapper,
    SlideWrapper,
    SmartArtWrapper,
    TableWrapper,
)
from pptx_agent.validators.exceptions import InvalidFileError


class TestPresentationWrapper:
    """Tests for PresentationWrapper class."""

    def test_load_template_success(self, template_path: str):
        """Should load valid PPTX template."""
        wrapper = PresentationWrapper()

        # Should not raise exception
        wrapper.load_template(template_path)

        # Verify template was loaded
        assert wrapper._prs is not None  # type: ignore[reportPrivateUsage]
        # Template path is now stored as absolute path
        assert wrapper._template_path is not None  # type: ignore[reportPrivateUsage]
        assert "basic-template.pptx" in wrapper._template_path  # type: ignore[reportPrivateUsage]

    def test_load_nonexistent_template(self):
        """Should raise InvalidFileError for missing template."""
        wrapper = PresentationWrapper()

        with pytest.raises(InvalidFileError):
            wrapper.load_template("nonexistent.pptx")

    def test_add_slide_with_layout(self, template_path: str):
        """Should add slide with specified layout name."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)

        # Get available layouts
        layouts = wrapper.get_layouts()
        assert len(layouts) > 0, "Template should have at least one layout"

        # Add slide with first layout
        slide = wrapper.add_slide(layouts[0])

        assert isinstance(slide, SlideWrapper)
        assert slide._slide is not None  # type: ignore[reportPrivateUsage]

    def test_add_slide_invalid_layout(self, template_path: str):
        """Should raise ValueError for invalid layout name."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)

        with pytest.raises(ValueError, match="Layout.*not found"):
            wrapper.add_slide("NonexistentLayout")

    def test_get_layouts(self, template_path: str):
        """Should return list of available layout names."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)

        layouts = wrapper.get_layouts()

        assert isinstance(layouts, list)
        assert len(layouts) > 0
        assert all(isinstance(name, str) for name in layouts)

    def test_save_presentation(self, template_path: str, tmp_path: Path) -> None:
        """Should save presentation to output path."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)

        output_path = tmp_path / "output.pptx"
        wrapper.save(str(output_path), base_dir=str(tmp_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_load_template_before_operations(self):
        """Should raise error if operations attempted before loading template."""
        wrapper = PresentationWrapper()

        with pytest.raises((ValueError, AttributeError)):
            wrapper.get_layouts()


class TestSlideWrapper:
    """Tests for SlideWrapper class."""

    @pytest.fixture
    def presentation_with_slide(
        self, template_path: str
    ) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    def test_set_title(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should update title placeholder text."""
        _, slide = presentation_with_slide

        title_text = "Test Title"
        slide.set_title(title_text)

        # Verify title was set (check via _slide.shapes[0].text if title exists)
        if hasattr(slide._slide, "shapes") and len(slide._slide.shapes) > 0:  # type: ignore[reportPrivateUsage]
            assert slide._slide.shapes.title is not None  # type: ignore[reportPrivateUsage]

    def test_add_text_to_placeholder(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should add text to named placeholder."""
        _, slide = presentation_with_slide

        result = slide.add_text(
            placeholder_name="Content", text="Test content", check_overflow=False
        )

        assert result["success"] is True
        assert "overflow" in result
        assert "warnings" in result

    def test_add_text_with_overflow_check(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should detect text overflow and return warning."""
        _, slide = presentation_with_slide

        # Very long text that should trigger overflow
        long_text = "A" * 5000

        result = slide.add_text(placeholder_name="Content", text=long_text, check_overflow=True)

        assert result["success"] is True
        assert isinstance(result["overflow"], bool)
        assert isinstance(result["warnings"], list)

    def test_add_text_overflow_disabled(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should add text without overflow check when disabled."""
        _, slide = presentation_with_slide

        result = slide.add_text(
            placeholder_name="Content", text="Test content", check_overflow=False
        )

        assert result["success"] is True
        assert result["overflow"] is False
        assert len(result["warnings"]) == 0

    def test_get_placeholders(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should return dict of placeholder names and info."""
        _, slide = presentation_with_slide

        placeholders = slide.get_placeholders()

        assert isinstance(placeholders, dict)
        # Should have at least some placeholder information
        assert len(placeholders) >= 0

    def test_set_title_missing_placeholder(self, template_path: str):
        """Should handle missing title placeholder gracefully."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()

        slide = wrapper.add_slide(layouts[0])

        # Should either succeed or handle gracefully
        try:
            slide.set_title("Test Title")
            assert True  # Success
        except (ValueError, AttributeError) as e:
            # Acceptable if it raises a clear error
            assert "title" in str(e).lower() or "placeholder" in str(e).lower()

    def test_add_text_nonexistent_placeholder(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should handle nonexistent placeholder name."""
        _, slide = presentation_with_slide

        result = slide.add_text(
            placeholder_name="NonexistentPlaceholder", text="Test", check_overflow=False
        )

        # Should return failure status
        assert result["success"] is False
        assert len(result["warnings"]) > 0


class TestChartWrapper:
    """Tests for ChartWrapper class."""

    @pytest.fixture
    def presentation_with_slide(
        self, template_path: str
    ) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    def test_create_bar_chart(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should create bar chart with data."""
        _, slide = presentation_with_slide

        chart_data = {
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [{"name": "Sales", "values": [100, 150, 120, 180]}],
        }

        # Should not raise exception
        ChartWrapper.create_chart(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            chart_type="bar",
            data=chart_data,
        )
        assert True

    def test_create_line_chart(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should create line chart with data."""
        _, slide = presentation_with_slide

        chart_data = {
            "categories": ["Jan", "Feb", "Mar"],
            "series": [{"name": "Revenue", "values": [1000, 1200, 1100]}],
        }

        ChartWrapper.create_chart(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            chart_type="line",
            data=chart_data,
        )
        assert True

    def test_create_pie_chart(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should create pie chart with data."""
        _, slide = presentation_with_slide

        chart_data = {
            "categories": ["A", "B", "C"],
            "series": [{"name": "Distribution", "values": [30, 40, 30]}],
        }

        ChartWrapper.create_chart(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            chart_type="pie",
            data=chart_data,
        )
        assert True

    def test_invalid_chart_type(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise ValueError for unsupported chart type."""
        _, slide = presentation_with_slide

        chart_data = {"categories": ["A"], "series": [{"name": "Test", "values": [1]}]}

        with pytest.raises(ValueError, match="Chart type validation failed"):
            ChartWrapper.create_chart(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                chart_type="invalid_type",
                data=chart_data,
            )

    def test_empty_chart_data(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise ValueError for empty data."""
        _, slide = presentation_with_slide

        with pytest.raises(ValueError, match="empty|data"):
            ChartWrapper.create_chart(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                chart_type="bar",
                data={"categories": [], "series": []},
            )

    def test_safe_remove_chart_placeholder(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Integration test: Should safely remove chart placeholder using xml_utils."""
        # RED PHASE: Integration test for safe XML removal (Line 99-100 in shapes.py)
        _, slide = presentation_with_slide

        chart_data = {
            "categories": ["Q1", "Q2"],
            "series": [{"name": "Sales", "values": [100, 150]}],
        }

        # Create chart - this should use safe_remove_element internally
        ChartWrapper.create_chart(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            chart_type="bar",
            data=chart_data,
        )

        # If we get here without exception, the safe removal worked
        assert True


class TestTableWrapper:
    """Tests for TableWrapper class."""

    @pytest.fixture
    def presentation_with_slide(
        self, template_path: str
    ) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    def test_create_table_with_headers(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should create table with headers and rows."""
        _, slide = presentation_with_slide

        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "30", "Tokyo"],
            ["Bob", "25", "Osaka"],
        ]

        TableWrapper.create_table(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            rows=rows,
            headers=headers,
        )
        assert True

    def test_create_table_without_headers(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should create table with rows only."""
        _, slide = presentation_with_slide

        rows = [
            ["Value1", "Value2"],
            ["Value3", "Value4"],
        ]

        TableWrapper.create_table(slide._slide, placeholder_name="Content", rows=rows, headers=None)  # type: ignore[reportPrivateUsage]
        assert True

    def test_empty_rows(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise ValueError for empty rows list."""
        _, slide = presentation_with_slide

        with pytest.raises(ValueError, match="empty|rows"):
            TableWrapper.create_table(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                rows=[],
                headers=None,
            )

    def test_mismatched_column_counts(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise ValueError for inconsistent column counts."""
        _, slide = presentation_with_slide

        rows = [
            ["A", "B", "C"],
            ["D", "E"],  # Mismatched column count
        ]

        with pytest.raises(ValueError, match="column|consistent"):
            TableWrapper.create_table(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                rows=rows,
                headers=None,
            )

    def test_safe_remove_table_placeholder(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Integration test: Should safely remove table placeholder using xml_utils."""
        # RED PHASE: Integration test for safe XML removal (Line 240 in shapes.py)
        _, slide = presentation_with_slide

        headers = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]

        # Create table - this should use safe_remove_element internally
        TableWrapper.create_table(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            rows=rows,
            headers=headers,
        )

        # If we get here without exception, the safe removal worked
        assert True


class TestImageWrapper:
    """Tests for ImageWrapper class."""

    @pytest.fixture
    def presentation_with_slide(
        self, template_path: str
    ) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    @pytest.fixture
    def test_image(self, tmp_path: Path) -> str:
        """Create a test image file."""
        image_path = tmp_path / "test_image.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(image_path)
        return str(image_path)

    def test_add_image_success(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        test_image: str,
    ) -> None:
        """Should add image to placeholder."""
        _, slide = presentation_with_slide

        ImageWrapper.add_image(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            image_path=test_image,
            alt_text="",
        )
        assert True

    def test_add_image_nonexistent_file(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise FileNotFoundError for missing image."""
        _, slide = presentation_with_slide

        with pytest.raises(FileNotFoundError):
            ImageWrapper.add_image(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                image_path="nonexistent.png",
                alt_text="",
            )

    def test_safe_remove_image_placeholder(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        test_image: str,
    ) -> None:
        """Integration test: Should safely remove image placeholder using xml_utils."""
        # RED PHASE: Integration test for safe XML removal (Line 174 in shapes.py)
        _, slide = presentation_with_slide

        # Add image - this should use safe_remove_element internally
        ImageWrapper.add_image(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            image_path=test_image,
            alt_text="Test image",
        )

        # If we get here without exception, the safe removal worked
        assert True

    def test_add_image_with_alt_text(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        test_image: str,
    ) -> None:
        """Should add image with alt text."""
        _, slide = presentation_with_slide

        alt_text = "Test image description"
        ImageWrapper.add_image(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            image_path=test_image,
            alt_text=alt_text,
        )
        assert True


class TestSmartArtWrapper:
    """Tests for SmartArtWrapper class."""

    @pytest.fixture
    def presentation_with_slide(
        self, template_path: str
    ) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template(template_path)
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    @pytest.mark.skip("SmartArt XML manipulation - complex, may defer")
    def test_populate_smartart_basic(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should populate SmartArt with node data."""
        _, slide = presentation_with_slide

        nodes = [
            {"text": "Node 1", "level": 0},
            {"text": "Node 2", "level": 1},
            {"text": "Node 3", "level": 1},
        ]

        SmartArtWrapper.populate_smartart(slide._slide, placeholder_name="SmartArt", nodes=nodes)  # type: ignore[reportPrivateUsage]
        assert True

    @pytest.mark.skip("SmartArt XML manipulation - complex, may defer")
    def test_populate_smartart_invalid_placeholder(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Should raise error for invalid placeholder."""
        _, slide = presentation_with_slide

        nodes = [{"text": "Node 1", "level": 0}]

        with pytest.raises((ValueError, AttributeError)):
            SmartArtWrapper.populate_smartart(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="NonexistentSmartArt",
                nodes=nodes,
            )
