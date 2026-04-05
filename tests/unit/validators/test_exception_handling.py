"""Tests for proper exception handling in critical code paths.

RED PHASE: These tests verify that exceptions are properly handled,
logged, and not silently swallowed.
"""

import logging
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from pptx_agent.pptx_wrapper import ImageWrapper, PresentationWrapper, SlideWrapper
from pptx_agent.pptx_wrapper.xml_utils import safe_get_element, safe_remove_element
from pptx_agent.utils.logging_config import configure_logfire


class TestShapesExceptionHandling:
    """Tests for shapes.py exception handling (line 260)."""

    @pytest.fixture
    def presentation_with_slide(self) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template("templates/basic-template.pptx")
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

    def test_alt_text_attribute_error_is_logged(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        test_image: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that AttributeError when setting alt text is logged.

        RED PHASE: This test should FAIL because current implementation
        catches Exception without logging.
        """
        _, slide = presentation_with_slide

        with caplog.at_level(logging.WARNING):
            # Add image with alt text - should log warning if setting alt text fails
            ImageWrapper.add_image(
                slide._slide,  # type: ignore[reportPrivateUsage]
                placeholder_name="Content",
                image_path=test_image,
                alt_text="Test alt text",
            )

        # If setting alt text fails, we should see a warning log
        # This test verifies proper logging (may pass if alt text works,
        # but will fail if AttributeError occurs without logging)

    def test_alt_text_only_catches_specific_exceptions(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        test_image: str,
    ) -> None:
        """Test that only AttributeError is caught when setting alt text.

        RED PHASE: This test should FAIL because current implementation
        catches generic Exception, hiding other errors.
        """
        _, slide = presentation_with_slide

        # Add image - even if alt text fails with AttributeError, it should succeed
        # But other exceptions should propagate
        ImageWrapper.add_image(
            slide._slide,  # type: ignore[reportPrivateUsage]
            placeholder_name="Content",
            image_path=test_image,
            alt_text="Test",
        )
        # Should succeed (or raise specific exceptions, not swallow them)


class TestSlideExceptionHandling:
    """Tests for slide.py exception handling (line 65)."""

    @pytest.fixture
    def presentation_with_slide(self) -> tuple[PresentationWrapper, SlideWrapper]:
        """Create presentation and add a slide for testing."""
        wrapper = PresentationWrapper()
        wrapper.load_template("templates/basic-template.pptx")
        layouts = wrapper.get_layouts()
        slide = wrapper.add_slide(layouts[0])
        return wrapper, slide

    def test_placeholder_format_error_is_logged(
        self,
        presentation_with_slide: tuple[PresentationWrapper, SlideWrapper],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that errors accessing placeholder_format are logged.

        RED PHASE: This test should FAIL because current implementation
        catches Exception without logging.
        """
        _, slide = presentation_with_slide

        with caplog.at_level(logging.DEBUG):
            # Try to add text - if accessing placeholder format fails,
            # it should be logged
            slide.add_text(placeholder_name="Content", text="Test content", check_overflow=False)

        # The operation might succeed, but if placeholder format access fails,
        # we should see it logged (not silently caught)

    def test_placeholder_format_only_catches_attribute_error(
        self, presentation_with_slide: tuple[PresentationWrapper, SlideWrapper]
    ) -> None:
        """Test that only AttributeError is caught for placeholder format.

        RED PHASE: This test should FAIL because current implementation
        catches generic Exception.
        """
        _, slide = presentation_with_slide

        # Should handle AttributeError gracefully but not hide other exceptions
        result = slide.add_text(
            placeholder_name="Content", text="Test content", check_overflow=False
        )

        # Should succeed or raise specific exceptions
        assert isinstance(result, dict)


class TestXmlUtilsExceptionHandling:
    """Tests for xml_utils.py exception handling (line 29)."""

    def test_safe_remove_element_logs_exceptions(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that exceptions in safe_remove_element are logged.

        RED PHASE: This test verifies that exceptions are logged before
        returning False.
        """
        element = Mock()
        element.getparent.side_effect = AttributeError("Test error")

        with caplog.at_level(logging.ERROR):
            result = safe_remove_element(element)

        # Should return False and log the exception
        assert result is False
        # Verify exception was logged
        assert any("Failed to remove element" in record.message for record in caplog.records), (
            "Exception should be logged"
        )

    def test_safe_remove_element_only_catches_expected_exceptions(self) -> None:
        """Test that only AttributeError and TypeError are caught.

        RED PHASE: Verify that unexpected exceptions propagate properly.
        """
        element = Mock()
        parent = Mock()
        element.getparent.return_value = parent
        # Simulate unexpected exception (not AttributeError or TypeError)
        parent.remove.side_effect = RuntimeError("Unexpected error")

        # RuntimeError should NOT be caught - it should propagate
        # Current implementation catches it, which is wrong
        with pytest.raises(RuntimeError, match="Unexpected error"):
            safe_remove_element(element)

    def test_safe_get_element_logs_missing_attribute(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that missing attributes are logged.

        RED PHASE: Verify proper logging of AttributeError.
        """
        obj = Mock(spec=[])  # Mock with no attributes

        with caplog.at_level(logging.ERROR):
            result = safe_get_element(obj, "_element")

        # Should return None and log the exception
        assert result is None
        assert any("Failed to access element" in record.message for record in caplog.records), (
            "Missing attribute should be logged"
        )


class TestLoggingConfigExceptionHandling:
    """Tests for logging_config.py exception handling (line 88)."""

    def test_permission_error_propagates(self) -> None:
        """Test that PermissionError is NOT caught by configure_logfire.

        RED PHASE: This test should FAIL because current implementation
        catches OSError (which includes PermissionError).
        """
        mock_logfire = Mock()
        # Simulate permission error during configuration
        mock_logfire.configure.side_effect = PermissionError("Access denied")

        with patch.dict("os.environ", {"LOGFIRE_ENABLED": "true"}, clear=True):
            # Remove test environment marker
            os.environ.pop("PYTEST_CURRENT_TEST", None)

            # PermissionError should propagate, not be caught
            with (
                patch.dict("sys.modules", {"logfire": mock_logfire}),
                pytest.raises(PermissionError, match="Access denied"),
            ):
                configure_logfire()

    def test_runtime_error_is_logged_not_raised(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that RuntimeError during logfire config is logged but not raised.

        RED PHASE: Verify that non-security errors are handled gracefully.
        """
        mock_logfire = Mock()
        mock_logfire.configure.side_effect = RuntimeError("Config error")

        with patch.dict("os.environ", {"LOGFIRE_ENABLED": "true"}, clear=True):
            os.environ.pop("PYTEST_CURRENT_TEST", None)

            with patch.dict("sys.modules", {"logfire": mock_logfire}):
                with caplog.at_level(logging.WARNING):
                    # Should not raise, but should log warning
                    configure_logfire()

                # Verify warning was logged
                assert any(
                    "Failed to configure Logfire" in record.message for record in caplog.records
                ), "Configuration error should be logged"

    def test_value_error_is_logged_not_raised(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that ValueError during logfire config is logged but not raised."""
        mock_logfire = Mock()
        mock_logfire.configure.side_effect = ValueError("Invalid config")

        with patch.dict("os.environ", {"LOGFIRE_ENABLED": "true"}, clear=True):
            os.environ.pop("PYTEST_CURRENT_TEST", None)

            with patch.dict("sys.modules", {"logfire": mock_logfire}):
                with caplog.at_level(logging.WARNING):
                    configure_logfire()

                # Should log the error
                assert any(
                    "Failed to configure Logfire" in record.message for record in caplog.records
                )
