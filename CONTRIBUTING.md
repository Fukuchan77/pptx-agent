# Contributing to AI PowerPoint Presentation Generator

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to this project.

## Development Philosophy

This project follows **Test-Driven Development (TDD)** principles and emphasizes code quality, type safety, and maintainability.

## TDD Workflow: RED-GREEN-REFACTOR

We strictly follow the TDD cycle for all code changes:

### 1. RED Phase: Write Failing Test

- Write a test that describes the desired behavior
- Run the test and **verify it fails**
- The test failure should be meaningful and indicate what's missing

```bash
# Write test in tests/unit/test_your_feature.py
uv run pytest tests/unit/test_your_feature.py -v
# Test should FAIL with clear error message
```

### 2. GREEN Phase: Make It Pass

- Write the **minimum code** necessary to make the test pass
- Don't add extra features or "nice to haves"
- Focus solely on making the test green

```bash
# Implement minimal code
uv run pytest tests/unit/test_your_feature.py -v
# Test should PASS
```

### 3. REFACTOR Phase: Improve Quality

- Improve code structure while keeping tests green
- Eliminate duplication
- Enhance readability
- Optimize performance if needed
- Run tests after each refactoring step

```bash
# Refactor code
uv run pytest tests/unit/test_your_feature.py -v
# Tests should still PASS
```

### TDD Rules (Non-Negotiable)

1. **Never write implementation before a failing test exists**
2. **Never modify tests to match implementation** (tests define requirements)
3. **Never add functionality not covered by tests**
4. **Never skip running tests between phases**
5. **Tests must assert expected behavior, not implementation details**

## Code Style Guidelines

### Google Python Style Guide

We follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with enforcement via ruff.

#### Docstrings

Use Google-style docstrings for all public modules, classes, and functions:

```python
def generate_outline(input_text: str, language: str = "en") -> PresentationOutline:
    """Generate presentation outline from input text.

    Args:
        input_text: The input text to analyze and structure.
        language: Target language code ("en" or "ja"). Defaults to "en".

    Returns:
        A PresentationOutline containing slide structure and metadata.

    Raises:
        ValidationError: If input_text is empty or invalid.
        LLMError: If outline generation fails after retries.

    Example:
        >>> outline = generate_outline("My presentation content", language="ja")
        >>> print(outline.slide_count)
        10
    """
    pass
```

#### Type Hints

All functions must have complete type hints:

```python
from typing import Optional
from pydantic import BaseModel

def process_slide(
    slide_content: SlideContent,
    template_manifest: TemplateManifest,
    language: Optional[str] = None,
) -> ProcessedSlide:
    """Process slide content with type safety."""
    pass
```

#### Naming Conventions

- **Classes**: `PascalCase` (e.g., `OutlineGenerator`, `SlideContent`)
- **Functions/Methods**: `snake_case` (e.g., `generate_outline`, `validate_content`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_LANGUAGE`)
- **Private**: Prefix with `_` (e.g., `_internal_helper`)

### Linting and Formatting

We use **ruff** for both linting and formatting:

```bash
# Check for issues
mise run lint

# Auto-fix issues
mise run lint-fix

# Format code
mise run format
```

#### Ruff Configuration

- Line length: 100 characters
- Target: Python 3.12+
- Rules: Google Python Style + Bandit security checks
- See `pyproject.toml` for complete configuration

### Type Checking

We use **pyright** in strict mode:

```bash
# Run type checker
mise run typecheck
```

All code must pass strict type checking with zero errors.

## Testing Requirements

### Coverage Requirements

- **Minimum 80% coverage** for core modules (`src/pptx_agent/`)
- **100% coverage** for critical paths (security, validation)
- Exceptions allowed for:
  - `__repr__` and `__str__` methods
  - Defensive `raise NotImplementedError`
  - `if __name__ == "__main__":` blocks
  - Type checking blocks (`if TYPE_CHECKING:`)

### Test Organization

```
tests/
├── unit/              # Unit tests (isolated, fast)
│   ├── test_agents.py
│   ├── test_validators.py
│   └── ...
├── integration/       # Integration tests (multiple components)
│   ├── test_basic_generation.py
│   ├── test_multilanguage.py
│   └── ...
└── fixtures/          # Test data and templates
    ├── sample_inputs/
    └── test_templates/
```

### Writing Good Tests

#### Unit Tests

- Test one thing at a time
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Mock external dependencies

```python
def test_outline_generator_creates_correct_slide_count():
    """Test that outline generator creates expected number of slides."""
    # Arrange
    input_text = "Test content with three sections..."
    expected_slide_count = 4  # Title + 3 content slides

    # Act
    outline = generate_outline(input_text)

    # Assert
    assert outline.slide_count == expected_slide_count
```

#### Integration Tests

- Test realistic workflows
- Use actual dependencies where reasonable
- Test error handling and edge cases

```python
def test_full_presentation_generation_workflow():
    """Test complete workflow from input to PPTX file."""
    # Arrange
    input_file = "tests/fixtures/sample_inputs/basic_input.txt"
    template = "tests/fixtures/test_templates/basic.pptx"
    output = "test_output.pptx"

    # Act
    generate_presentation(input_file, template, output)

    # Assert
    assert Path(output).exists()
    # Verify PPTX is valid and contains expected slides
    prs = Presentation(output)
    assert len(prs.slides) >= 3
```

### Test Execution

```bash
# Run all tests
mise run test

# Run with coverage report
mise run test-cov

# Run specific test file
uv run pytest tests/unit/test_validators.py -v

# Run specific test
uv run pytest tests/unit/test_validators.py::test_input_validator_rejects_empty_input -v

# Run tests matching pattern
uv run pytest -k "validator" -v
```

## Testing Guidelines

### Test Isolation

All tests are automatically isolated from your development environment:

- Environment variables are cleared by [`isolate_config_from_environment`](tests/conftest.py:49) fixture
- Use [`make_test_config()`](tests/conftest.py:103) to create Config instances in tests
- Never rely on environment variables in unit tests

### Writing Tests

Follow TDD (Test-Driven Development):

1. **RED**: Write a failing test that defines the expected behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve the code while keeping tests green

Example:

```python
def test_new_feature(make_test_config):
    """Test description"""
    config = make_test_config(llm_provider="openai")
    result = my_function(config)
    assert result == expected_value
```

### API Keys in Tests

- **Unit tests**: Use [`make_test_config()`](tests/conftest.py:103) which automatically allows test keys
- **Integration tests**: Use real API keys from `.env.test`
- **Never commit**: Real API keys should never be in code or `.env.test`

### Running Specific Tests

```bash
# Single test
uv run pytest tests/unit/test_config.py::test_specific_test -xvs

# Test file
uv run pytest tests/unit/test_config.py -xvs

# With pattern
uv run pytest -k "test_config" -xvs
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:

   ```bash
   mise run ci  # Runs lint, typecheck, and test-cov
   ```

2. **Verify coverage** (≥80% for core modules):

   ```bash
   mise run test-cov
   # Check htmlcov/index.html for detailed report
   ```

3. **Update documentation** if adding features

4. **Add/update tests** for any code changes

### PR Guidelines

1. **Branch Naming**:
   - Feature: `feature/description`
   - Bugfix: `fix/description`
   - Refactor: `refactor/description`

2. **Commit Messages**:
   - Use clear, descriptive messages
   - Start with verb: "Add", "Fix", "Refactor", "Update"
   - Reference issues if applicable: "Fix #123: ..."

   ```
   Add multilanguage support for Japanese presentations

   - Implement language detection in outline generator
   - Add language-aware text capacity calculations
   - Update tests with Japanese fixtures

   Resolves #42
   ```

3. **PR Description**:
   - Describe what changed and why
   - List any breaking changes
   - Include screenshots for UI changes
   - Link to related issues

4. **PR Checklist**:
   - [ ] Tests added/updated
   - [ ] All tests passing (`mise run ci`)
   - [ ] Coverage maintained (≥80%)
   - [ ] Documentation updated
   - [ ] Follows TDD workflow
   - [ ] Code reviewed by self first
   - [ ] No linter warnings
   - [ ] Type checking passes

### Review Process

- At least one approval required
- Address all review comments
- Keep PRs focused and reasonably sized
- Squash commits before merging if needed

## Development Environment Setup

### Prerequisites

1. Install Python 3.12+
2. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Install [mise](https://mise.jdx.dev/):
   ```bash
   curl https://mise.run | sh
   ```

### Setup

```bash
# Clone repository
git clone <repository-url>
cd pptx-agent

# Install dependencies
uv sync --all-extras

# Verify setup
mise run ci
```

## Common Tasks

### Adding a New Feature

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write failing test (RED)
3. Implement minimal code (GREEN)
4. Refactor if needed (REFACTOR)
5. Run CI checks: `mise run ci`
6. Commit and push
7. Create pull request

### Fixing a Bug

1. Write test that reproduces the bug (should fail)
2. Fix the bug (test should pass)
3. Add regression test
4. Run CI checks: `mise run ci`
5. Submit PR with test and fix

### Adding Dependencies

1. Add to `pyproject.toml` dependencies
2. Run `uv sync`
3. Update documentation if needed
4. Test that everything still works

## QA Framework Development

### Overview

The QA (Quality Assurance) framework provides automated validation and remediation of PowerPoint presentations. It consists of:

- **QA Engine**: Rule-based validation system
- **Fix Engine**: Automated issue remediation
- **Rule Registry**: Extensible rule management
- **Fix Strategy Registry**: Pluggable fix strategies

### QA Rule Development

#### Creating a New QA Rule

Follow TDD workflow to create a new QA rule:

1. **RED Phase**: Write failing test

```python
# tests/unit/qa/test_my_new_rule.py
def test_my_new_rule_detects_issue():
    """Test that MyNewRule detects the specific issue."""
    # Arrange
    from pptx_agent.qa.rules.my_category import MyNewRule
    rule = MyNewRule()

    # Create test presentation with the issue
    prs = create_test_presentation_with_issue()

    # Act
    issues = rule.check(prs)

    # Assert
    assert len(issues) == 1
    assert issues[0].rule_id == "QA-X-NNN"
    assert issues[0].severity == "error"
```

2. **GREEN Phase**: Implement minimal rule

```python
# src/pptx_agent/qa/rules/my_category.py
from pptx_agent.qa.rules.base import QARule
from pptx_agent.qa.schemas import QAIssue, Severity

class MyNewRule(QARule):
    """Detects specific issue in presentations."""

    rule_id = "QA-X-NNN"  # X = L/C/S, NNN = 3-digit number
    severity = Severity.ERROR
    auto_fixable = True  # or False

    def check(self, presentation: Presentation) -> list[QAIssue]:
        """Check for the specific issue."""
        issues = []
        # Implement detection logic
        return issues
```

3. **REFACTOR Phase**: Improve implementation

#### QA Rule Naming Convention

- **Format**: `QA-{CATEGORY}-{NUMBER}`
- **Categories**:
  - `L`: Layout rules (text overflow, placeholder usage)
  - `C`: Content rules (missing content, invalid data)
  - `S`: Style rules (font consistency, color compliance)
- **Number**: 3-digit sequential (001, 002, 003...)

Examples:

- `QA-L-001`: Text overflow detection
- `QA-C-001`: Missing required content
- `QA-S-001`: Font consistency check

#### QA Rule Requirements

All QA rules MUST:

1. **Inherit from QARule**: Use `pptx_agent.qa.rules.base.QARule`
2. **Define rule_id**: Unique identifier following naming convention
3. **Define severity**: `Severity.ERROR`, `Severity.WARNING`, or `Severity.INFO`
4. **Define auto_fixable**: Boolean indicating if issue can be auto-fixed
5. **Implement check()**: Return list of `QAIssue` objects
6. **Have docstring**: Explain what the rule checks
7. **Have tests**: Minimum 80% coverage

### Fix Strategy Development

#### Creating a Fix Strategy

1. **RED Phase**: Write failing test

```python
# tests/unit/fixer/test_my_fix_strategy.py
def test_my_fix_strategy_resolves_issue():
    """Test that MyFixStrategy resolves the specific issue."""
    # Arrange
    from pptx_agent.fixer.strategies.my_strategy import MyFixStrategy
    strategy = MyFixStrategy()

    issue = create_test_issue()
    prs = create_test_presentation_with_issue()

    # Act
    result = strategy.apply(issue, prs)

    # Assert
    assert result.status == FixStatus.SUCCESS
    assert result.changes_made == ["specific change description"]
```

2. **GREEN Phase**: Implement minimal strategy

```python
# src/pptx_agent/fixer/strategies/my_strategy.py
from pptx_agent.fixer.strategies.base import FixStrategy
from pptx_agent.fixer.schemas import FixResult, FixStatus

class MyFixStrategy(FixStrategy):
    """Fixes specific issue type."""

    def apply(self, issue: QAIssue, presentation: Presentation) -> FixResult:
        """Apply fix for the issue."""
        try:
            # Implement fix logic
            return FixResult(
                status=FixStatus.SUCCESS,
                message="Issue fixed successfully",
                changes_made=["specific change"],
            )
        except Exception as e:
            return FixResult(
                status=FixStatus.FAILED,
                message=f"Fix failed: {e}",
                changes_made=[],
            )
```

3. **Register strategy**:

```python
# In appropriate module initialization
from pptx_agent.fixer.engine import get_global_registry
from pptx_agent.fixer.strategies.my_strategy import MyFixStrategy

registry = get_global_registry()
registry.register("QA-X-NNN", MyFixStrategy())
```

#### Fix Strategy Requirements

All fix strategies MUST:

1. **Inherit from FixStrategy**: Use `pptx_agent.fixer.strategies.base.FixStrategy`
2. **Implement apply()**: Return `FixResult` with status and changes
3. **Handle errors gracefully**: Return `FixStatus.FAILED` on errors
4. **Be idempotent**: Multiple applications should be safe
5. **Document changes**: List all modifications in `changes_made`
6. **Have tests**: Test success, failure, and edge cases
7. **Register with engine**: Add to global registry

### Testing QA Features

#### Unit Tests

Test individual rules and strategies in isolation:

```python
def test_rule_detects_issue(make_test_presentation):
    """Test rule detection logic."""
    prs = make_test_presentation(with_issue=True)
    rule = MyRule()
    issues = rule.check(prs)
    assert len(issues) > 0

def test_rule_no_false_positives(make_test_presentation):
    """Test rule doesn't flag valid presentations."""
    prs = make_test_presentation(valid=True)
    rule = MyRule()
    issues = rule.check(prs)
    assert len(issues) == 0
```

#### Integration Tests

Test complete QA workflows:

```python
def test_qa_and_fix_workflow():
    """Test end-to-end QA validation and fixing."""
    # Create presentation with known issues
    prs = create_test_presentation()

    # Run QA validation
    qa_engine = QAEngine()
    report = qa_engine.validate(prs)
    assert report.total_issues > 0

    # Run fix loop
    fix_engine = FixEngine()
    result = fix_engine.run_fix_loop(report, prs)
    assert result.final_issue_count < report.total_issues
```

#### Performance Tests

Test QA performance on large presentations:

```python
def test_qa_performance_large_presentation():
    """Test QA validation completes within time limit."""
    prs = create_large_presentation(slide_count=30)

    start_time = time.time()
    qa_engine = QAEngine()
    report = qa_engine.validate(prs)
    elapsed = time.time() - start_time

    # Should complete in reasonable time
    assert elapsed < 10.0  # 10 seconds for 30 slides
```

### Performance Benchmarks

QA framework performance targets:

- **QA Validation**: <5 seconds for 10-slide presentation
- **Fix Loop**: <10 seconds for 5 issues
- **Memory Usage**: <500MB for 30-slide presentation
- **Iteration Limit**: Max 10 iterations per fix loop

### Common Patterns

#### Accessing Slide Elements

```python
def check(self, presentation: Presentation) -> list[QAIssue]:
    """Check all slides for issues."""
    issues = []
    for slide_idx, slide in enumerate(presentation.slides):
        for shape_idx, shape in enumerate(slide.shapes):
            if hasattr(shape, "text_frame"):
                # Check text content
                if self._has_issue(shape.text_frame):
                    issues.append(self._create_issue(slide_idx, shape_idx))
    return issues
```

#### Creating QA Issues

```python
def _create_issue(self, slide_idx: int, shape_idx: int) -> QAIssue:
    """Create QA issue with proper metadata."""
    return QAIssue(
        rule_id=self.rule_id,
        severity=self.severity,
        slide_index=slide_idx,
        shape_index=shape_idx,
        message="Descriptive error message",
        auto_fixable=self.auto_fixable,
        metadata={"additional": "context"},
    )
```

#### Safe Shape Modification

```python
def apply(self, issue: QAIssue, presentation: Presentation) -> FixResult:
    """Apply fix safely with error handling."""
    try:
        slide = presentation.slides[issue.slide_index]
        shape = slide.shapes[issue.shape_index]

        # Verify shape has required attributes
        if not hasattr(shape, "text_frame"):
            return FixResult(
                status=FixStatus.SKIPPED,
                message="Shape has no text frame",
            )

        # Apply modification
        shape.text_frame.text = "Fixed content"

        return FixResult(
            status=FixStatus.SUCCESS,
            message="Content updated",
            changes_made=["Updated text content"],
        )
    except Exception as e:
        return FixResult(
            status=FixStatus.FAILED,
            message=f"Fix failed: {e}",
        )
```

### QA Development Checklist

Before submitting QA-related PRs:

- [ ] Rule follows naming convention (QA-X-NNN)
- [ ] Rule has complete docstring
- [ ] Rule has unit tests (≥80% coverage)
- [ ] Fix strategy registered in global registry
- [ ] Fix strategy handles errors gracefully
- [ ] Fix strategy has unit tests
- [ ] Integration test covers end-to-end workflow
- [ ] Performance test validates benchmarks
- [ ] Documentation updated (if adding new category)
- [ ] All CI checks pass (`mise run ci`)

## Getting Help

- Check existing issues and documentation
- Ask questions in discussions
- Reach out to maintainers

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Help others learn and grow

Thank you for contributing! 🚀
