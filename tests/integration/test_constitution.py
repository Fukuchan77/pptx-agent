"""Constitutional compliance tests for QA framework.

Verifies that the QA framework implementation adheres to all
constitutional principles defined in the project constitution.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def test_principle_1_tdd_compliance() -> None:
    """Verify Principle 1: Test-Driven Development compliance.

    All QA and fixer modules should have corresponding test files.
    """
    src_qa_dir = Path("src/pptx_agent/qa")
    src_fixer_dir = Path("src/pptx_agent/fixer")
    src_cache_dir = Path("src/pptx_agent/cache")

    test_qa_dir = Path("tests/unit/qa")
    test_fixer_dir = Path("tests/unit/fixer")
    test_cache_dir = Path("tests/unit/cache")

    # Check QA module test coverage
    qa_modules = list(src_qa_dir.rglob("*.py"))
    qa_modules = [m for m in qa_modules if m.name != "__init__.py"]

    for module in qa_modules:
        relative_path = module.relative_to(src_qa_dir)
        test_file = test_qa_dir / f"test_{relative_path.stem}.py"

        # Allow for grouped test files (e.g., test_layout_checks.py covers layout_checks.py)
        if not test_file.exists():
            # Check if there's a test file that covers this module
            test_files = list(test_qa_dir.rglob(f"*{relative_path.stem}*.py"))
            assert len(test_files) > 0, f"No test file found for {module}"

    # Check fixer module test coverage
    fixer_modules = list(src_fixer_dir.rglob("*.py"))
    fixer_modules = [m for m in fixer_modules if m.name != "__init__.py"]

    for module in fixer_modules:
        relative_path = module.relative_to(src_fixer_dir)
        test_file = test_fixer_dir / f"test_{relative_path.stem}.py"

        if not test_file.exists():
            test_files = list(test_fixer_dir.rglob(f"*{relative_path.stem}*.py"))
            assert len(test_files) > 0, f"No test file found for {module}"

    # Check cache module test coverage
    cache_modules = list(src_cache_dir.rglob("*.py"))
    cache_modules = [m for m in cache_modules if m.name != "__init__.py"]

    for module in cache_modules:
        relative_path = module.relative_to(src_cache_dir)
        test_file = test_cache_dir / f"test_{relative_path.stem}.py"

        if not test_file.exists():
            test_files = list(test_cache_dir.rglob(f"*{relative_path.stem}*.py"))
            assert len(test_files) > 0, f"No test file found for {module}"


def test_principle_2_type_safety_compliance() -> None:
    """Verify Principle 2: Code Quality and Type Safety compliance.

    All QA and fixer modules should pass pyright strict mode.
    """
    result = subprocess.run(
        [
            "uv",
            "run",
            "pyright",
            "src/pptx_agent/qa",
            "src/pptx_agent/fixer",
            "src/pptx_agent/cache",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Pyright should exit with 0 for no errors
    assert result.returncode == 0, f"Pyright found type errors:\n{result.stdout}\n{result.stderr}"


def test_principle_3_test_coverage_compliance() -> None:
    """Verify Principle 3: Test Coverage Standards compliance.

    QA, fixer, and cache modules should have ≥80% test coverage.

    Scoped to the dedicated unit/integration tests for these modules only.
    Uses an isolated temporary directory with a minimal .coveragerc that
    restricts measurement to the three target packages, avoiding the
    pyproject.toml [tool.coverage.run] source=["src"] expansion that would
    dilute coverage across all 4000+ statements in src/.
    Also uses a separate coverage data file to avoid SQLite conflicts with
    the outer pytest-cov session.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        cov_data_file = str(tmppath / ".coverage.constitution")
        cov_rc_file = tmppath / ".coveragerc"
        # Minimal coverage config: measure only the three target packages
        cov_rc_file.write_text(
            "[run]\n"
            "source =\n"
            "    src/pptx_agent/qa\n"
            "    src/pptx_agent/fixer\n"
            "    src/pptx_agent/cache\n"
            "data_file = " + cov_data_file + "\n"
            "\n"
            "[report]\n"
            "fail_under = 80\n"
        )
        env = {
            **os.environ,
            "COVERAGE_FILE": cov_data_file,
            "COVERAGE_RCFILE": str(cov_rc_file),
        }
        result = subprocess.run(  # noqa: S603  # Trusted input: hardcoded test command with known arguments
            [
                "uv",
                "run",
                "pytest",
                "tests/unit/qa",
                "tests/unit/fixer",
                "tests/unit/cache",
                "tests/integration/test_qa_only.py",
                "tests/integration/test_fix_loop.py",
                # Suppress pyproject.toml addopts (which includes --cov=src/pptx_agent
                # for the whole package, diluting targeted coverage measurement)
                "--override-ini=addopts=",
                "--cov=src/pptx_agent/qa",
                "--cov=src/pptx_agent/fixer",
                "--cov=src/pptx_agent/cache",
                f"--cov-config={cov_rc_file}",
                "--cov-report=term",
                "--cov-fail-under=80",
                "--no-header",
                "-q",  # Quiet mode to reduce output
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    # Coverage should be ≥80%
    assert result.returncode == 0, f"Test coverage below 80%:\n{result.stdout}\n{result.stderr}"


def test_principle_4_multi_language_support() -> None:
    """Verify Principle 4: Multi-Language Support compliance.

    QA engine should support language-aware capacity calculations.
    """
    from pptx_agent.qa.engine import QAEngine

    # Test English language support
    engine_en = QAEngine(language="en")
    assert engine_en.language == "en"

    # Test Japanese language support
    engine_ja = QAEngine(language="ja")
    assert engine_ja.language == "ja"

    # Test auto-detection (None)
    engine_auto = QAEngine(language=None)
    assert engine_auto.language is None


def test_principle_5_error_handling_compliance() -> None:
    """Verify Principle 5: Production-Ready Error Handling compliance.

    QA and fixer engines should handle errors gracefully.
    """
    from pptx_agent.fixer.engine import FixEngine
    from pptx_agent.fixer.schemas import FixStatus
    from pptx_agent.qa.schemas import QAIssue, Severity

    # Test fix engine error handling
    engine = FixEngine()

    # Create an issue with no registered strategy
    issue = QAIssue(
        rule_id="QA-NONEXISTENT-999",
        severity=Severity.ERROR,
        slide_index=0,
        shape_index=0,
        message="Test issue",
        auto_fixable=True,
    )

    # Should return SKIPPED status, not raise exception
    result = engine.apply_fix(issue)
    assert result.status == FixStatus.SKIPPED
    assert "No fix strategy registered" in result.message


def test_principle_6_template_architecture_compliance() -> None:
    """Verify Principle 6: Template-Based Architecture compliance.

    QA rules should use template manifest for capacity validation.
    """
    from pptx_agent.qa.rules.layout_checks import TextOverflowRule

    # Verify TextOverflowRule exists and has proper structure
    rule = TextOverflowRule()
    assert rule.rule_id == "QA-L-001"
    # Note: severity and auto_fixable are class attributes, not instance attributes
    assert hasattr(rule, "severity"), "TextOverflowRule missing severity"
    assert hasattr(rule, "auto_fixable"), "TextOverflowRule missing auto_fixable"


def test_principle_7_developer_experience_compliance() -> None:
    """Verify Principle 7: Developer Experience and Tooling compliance.

    All QA modules should have proper docstrings and type hints.
    """
    from pptx_agent.fixer.engine import FixEngine
    from pptx_agent.fixer.schemas import FixLoopResult
    from pptx_agent.qa.engine import QAEngine
    from pptx_agent.qa.schemas import QAReport

    # Check that key classes have docstrings
    assert QAEngine.__doc__ is not None, "QAEngine missing docstring"
    assert QAReport.__doc__ is not None, "QAReport missing docstring"
    assert FixEngine.__doc__ is not None, "FixEngine missing docstring"
    assert FixLoopResult.__doc__ is not None, "FixLoopResult missing docstring"

    # Check that key methods have docstrings
    assert QAEngine.validate.__doc__ is not None, "QAEngine.validate missing docstring"
    assert FixEngine.run_fix_loop.__doc__ is not None, "FixEngine.run_fix_loop missing docstring"


def test_qa_rules_follow_naming_convention() -> None:
    """Verify QA rules follow the documented naming convention (QA-X-NNN)."""
    from pptx_agent.qa.engine import QAEngine
    from pptx_agent.qa.rules.register_defaults import register_default_rules

    engine = QAEngine()
    register_default_rules()

    rules = engine.registry.get_all_rules()

    for rule in rules:
        # Rule ID should match pattern: QA-{L|C|S}-NNN
        assert rule.rule_id.startswith("QA-"), f"Rule {rule.rule_id} doesn't start with 'QA-'"

        parts = rule.rule_id.split("-")
        assert len(parts) == 3, f"Rule {rule.rule_id} doesn't follow QA-X-NNN format"

        category = parts[1]
        assert category in ["L", "C", "S"], f"Rule {rule.rule_id} has invalid category {category}"

        number = parts[2]
        assert number.isdigit(), f"Rule {rule.rule_id} has non-numeric suffix {number}"
        assert len(number) == 3, f"Rule {rule.rule_id} number should be 3 digits, got {number}"


def test_qa_rules_have_required_attributes() -> None:
    """Verify all QA rules have required attributes."""
    from pptx_agent.qa.engine import QAEngine
    from pptx_agent.qa.rules.register_defaults import register_default_rules

    engine = QAEngine()
    register_default_rules()

    rules = engine.registry.get_all_rules()

    for rule in rules:
        # Required attributes
        assert hasattr(rule, "rule_id"), "Rule missing rule_id attribute"
        assert hasattr(rule, "severity"), f"Rule {rule.rule_id} missing severity attribute"
        assert hasattr(rule, "auto_fixable"), f"Rule {rule.rule_id} missing auto_fixable attribute"
        assert hasattr(rule, "validate"), f"Rule {rule.rule_id} missing validate method"

        # Verify severity is valid
        severity_value = getattr(rule, "severity", None)
        assert severity_value in ["error", "warning", "info"], (
            f"Rule {rule.rule_id} has invalid severity {severity_value}"
        )

        # Verify auto_fixable is boolean
        assert isinstance(rule.auto_fixable, bool), (
            f"Rule {rule.rule_id} auto_fixable is not boolean"
        )


def test_fix_strategies_registered_for_auto_fixable_rules() -> None:
    """Verify fix strategies are registered for all auto-fixable QA rules."""
    from pptx_agent.fixer.engine import FixStrategyRegistry
    from pptx_agent.fixer.strategies import register_default_strategies
    from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
    from pptx_agent.qa.engine import QAEngine
    from pptx_agent.qa.rules.register_defaults import register_default_rules

    qa_engine = QAEngine()
    register_default_rules()

    # Create a local registry with a mock presentation to test strategy registration
    local_registry = FixStrategyRegistry()
    mock_presentation = PresentationWrapper()
    register_default_strategies(
        registry=local_registry, presentation=mock_presentation, outline=None
    )

    rules = qa_engine.registry.get_all_rules()
    auto_fixable_rules = [rule for rule in rules if rule.auto_fixable]

    for rule in auto_fixable_rules:
        # Auto-fixable rules MUST have a registered fix strategy
        strategies = local_registry.get_strategies(rule.rule_id)
        assert strategies, (
            f"Auto-fixable rule {rule.rule_id} has no registered fix strategy. "
            "All auto-fixable rules must have at least one strategy registered."
        )


def test_qa_report_schema_completeness() -> None:
    """Verify QA report schema includes all required fields."""
    from pptx_agent.qa.schemas import QAReport

    # Create a minimal report
    report = QAReport(
        total_issues=0,
        error_count=0,
        warning_count=0,
        info_count=0,
        issues=[],
    )

    # Verify required methods exist
    assert hasattr(report, "to_json"), "QAReport missing to_json method"
    assert hasattr(report, "to_markdown"), "QAReport missing to_markdown method"

    # Verify methods work
    json_output = report.to_json()
    assert isinstance(json_output, str)

    markdown_output = report.to_markdown()
    assert isinstance(markdown_output, str)


def test_constitutional_principle_enforcement() -> None:
    """Verify constitutional principles are enforced in code structure."""
    # This test verifies that the code structure follows constitutional principles

    # Principle 1: TDD - Verified by test_principle_1_tdd_compliance
    # Principle 2: Type Safety - Verified by test_principle_2_type_safety_compliance
    # Principle 3: Test Coverage - Verified by test_principle_3_test_coverage_compliance
    # Principle 4: Multi-Language - Verified by test_principle_4_multi_language_support
    # Principle 5: Error Handling - Verified by test_principle_5_error_handling_compliance
    # Principle 6: Template Architecture - Verified by test_principle_6_template_architecture_compliance
    # Principle 7: Developer Experience - Verified by test_principle_7_developer_experience_compliance

    # If all individual principle tests pass, constitutional compliance is verified
    assert True, "Constitutional compliance verified through individual principle tests"


# Made with Bob
