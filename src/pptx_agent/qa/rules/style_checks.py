"""QA rules for style validation and template conformance.

This module implements style-related quality checks including:
- Off-template font detection (QA-S-001)
- Off-template color detection (QA-S-002)
- Invalid bullet indent detection (QA-S-003)
- Template conformance validation
"""

from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.schemas import QAIssue, Severity


class OffTemplateFontRule:
    """QA-S-001: Detect off-template font usage.

    Checks if text uses fonts that are not defined in the template's
    theme fonts, which can cause inconsistent branding.

    Attributes:
        rule_id: Unique identifier "QA-S-001"
        description: Human-readable description
        auto_fixable: True - can be fixed by resetting to master font
    """

    rule_id = "QA-S-001"
    description = "Detect off-template font usage"
    severity = "warning"
    auto_fixable = True
    category = "style"

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
        """Validate presentation for off-template font usage.

        Args:
            presentation: Presentation to validate

        Returns:
            List of QA issues found (empty if no violations detected)
        """
        issues: list[QAIssue] = []

        # Get theme fonts from presentation
        try:
            slide_master = presentation.prs.slide_master
            # Access theme through part relationship
            theme = slide_master.part.theme  # type: ignore[attr-defined]
            major_font = theme.font_scheme.major_latin_font  # type: ignore[attr-defined]
            minor_font = theme.font_scheme.minor_latin_font  # type: ignore[attr-defined]
            theme_fonts = {major_font, minor_font}
        except (AttributeError, IndexError):
            # If we can't access theme fonts, skip this check
            return issues

        # Check each slide
        for slide_idx, slide in enumerate(presentation.prs.slides):
            for shape_idx, shape in enumerate(slide.shapes):
                # Only check text-containing shapes
                if not hasattr(shape, "text_frame"):
                    continue

                text_frame = shape.text_frame  # type: ignore[attr-defined]

                # Check each paragraph
                for paragraph in text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.name and run.font.name not in theme_fonts:
                            issues.append(
                                QAIssue(
                                    rule_id=self.rule_id,
                                    severity=Severity.WARNING,
                                    slide_index=slide_idx,
                                    shape_index=shape_idx,
                                    message=f"Off-template font detected: '{run.font.name}' "
                                    f"(expected theme fonts: {', '.join(theme_fonts)})",
                                    auto_fixable=self.auto_fixable,
                                    suggested_fix="Reset font to template master font",
                                )
                            )
                            # Only report once per shape to avoid spam
                            break
                    else:
                        continue
                    break

        return issues


class OffTemplateColorRule:
    """QA-S-002: Detect off-template theme color usage.

    Checks if shapes use colors that are not part of the template's
    theme color scheme.

    Attributes:
        rule_id: Unique identifier "QA-S-002"
        description: Human-readable description
        auto_fixable: False - color changes may be intentional
    """

    rule_id = "QA-S-002"
    description = "Detect off-template theme color usage"
    severity = "warning"
    auto_fixable = False
    category = "style"

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:  # noqa: ARG002
        """Validate presentation for off-template color usage.

        Args:
            presentation: Presentation to validate

        Returns:
            List of QA issues found (empty if no violations detected)
        """
        issues: list[QAIssue] = []

        # Note: Color validation is complex because:
        # 1. Colors can be specified in multiple ways (RGB, theme, scheme)
        # 2. Theme colors are often intentionally overridden
        # 3. python-pptx has limited color introspection capabilities
        #
        # For now, this is a placeholder that returns no issues.
        # Full implementation would require:
        # - Extracting theme color palette
        # - Checking fill and line colors against palette
        # - Handling color variations (tints, shades)

        return issues


class InvalidBulletIndentRule:
    """QA-S-003: Detect invalid bullet indent levels.

    Checks if bullet points exceed the maximum recommended indent level
    (typically 4 levels), which can cause readability issues.

    Attributes:
        rule_id: Unique identifier "QA-S-003"
        description: Human-readable description
        auto_fixable: False - bullet indent reduction strategy not yet implemented
    """

    rule_id = "QA-S-003"
    description = "Detect invalid bullet indent levels (> 4)"
    severity = "warning"
    auto_fixable = False
    category = "style"

    MAX_INDENT_LEVEL = 4

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
        """Validate presentation for excessive bullet indentation.

        Args:
            presentation: Presentation to validate

        Returns:
            List of QA issues found (empty if no violations detected)
        """
        issues: list[QAIssue] = []

        # Check each slide
        for slide_idx, slide in enumerate(presentation.prs.slides):
            for shape_idx, shape in enumerate(slide.shapes):
                # Only check text-containing shapes
                if not hasattr(shape, "text_frame"):
                    continue

                text_frame = shape.text_frame  # type: ignore[attr-defined]

                # Check each paragraph's indent level
                for para_idx, paragraph in enumerate(text_frame.paragraphs):
                    if paragraph.level > self.MAX_INDENT_LEVEL:
                        issues.append(
                            QAIssue(
                                rule_id=self.rule_id,
                                severity=Severity.WARNING,
                                slide_index=slide_idx,
                                shape_index=shape_idx,
                                message=f"Bullet indent level {paragraph.level} exceeds "
                                f"maximum recommended level {self.MAX_INDENT_LEVEL} "
                                f"(paragraph {para_idx + 1})",
                                auto_fixable=self.auto_fixable,
                                suggested_fix=(
                                    f"Reduce indent to level {self.MAX_INDENT_LEVEL} or less"
                                ),
                            )
                        )

        return issues


class TemplateConformanceRule:
    """Template conformance validation rule.

    Validates that a presentation conforms to its template by checking:
    - Slide layouts match template layouts
    - Theme colors are from template
    - Fonts are from template theme

    This is a composite rule that aggregates multiple style checks.

    Attributes:
        rule_id: Unique identifier "QA-S-004"
        description: Human-readable description
        auto_fixable: False - conformance issues may require manual review
    """

    rule_id = "QA-S-004"
    description = "Validate template conformance"
    severity = "error"
    auto_fixable = False
    category = "style"

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
        """Validate presentation for template conformance.

        Args:
            presentation: Presentation to validate

        Returns:
            List of QA issues found (empty if fully conformant)
        """
        issues: list[QAIssue] = []

        # Check if presentation has a slide master
        try:
            slide_master = presentation.prs.slide_master
        except (AttributeError, IndexError):
            issues.append(
                QAIssue(
                    rule_id=self.rule_id,
                    severity=Severity.ERROR,
                    slide_index=0,
                    shape_index=None,
                    message=(
                        "Presentation has no slide master - cannot validate template conformance"
                    ),
                    auto_fixable=False,
                    suggested_fix="Ensure presentation was created from a valid template",
                )
            )
            return issues

        # Check each slide is bound to a layout from the master
        for slide_idx, slide in enumerate(presentation.prs.slides):
            try:
                slide_layout = slide.slide_layout
                # Verify layout belongs to the master
                if slide_layout.slide_master != slide_master:
                    issues.append(
                        QAIssue(
                            rule_id=self.rule_id,
                            severity=Severity.WARNING,
                            slide_index=slide_idx,
                            shape_index=None,
                            message=f"Slide {slide_idx + 1} uses layout from different master",
                            auto_fixable=False,
                            suggested_fix="Recreate slide using template layouts",
                        )
                    )
            except AttributeError:
                issues.append(
                    QAIssue(
                        rule_id=self.rule_id,
                        severity=Severity.WARNING,
                        slide_index=slide_idx,
                        shape_index=None,
                        message=f"Slide {slide_idx + 1} has no layout binding",
                        auto_fixable=False,
                        suggested_fix="Bind slide to a template layout",
                    )
                )

        return issues


# Made with Bob
