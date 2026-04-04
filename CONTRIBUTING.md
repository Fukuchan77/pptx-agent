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
