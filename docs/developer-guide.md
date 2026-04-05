# Developer Guide - AI PowerPoint Presentation Generator

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Architecture](#project-architecture)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Adding New Features](#adding-new-features)
7. [Module Documentation](#module-documentation)
8. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
9. [Code Standards](#code-standards)
10. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- [mise](https://mise.jdx.dev/) task runner
- Git
- IDE: VS Code, PyCharm, or any Python-compatible IDE

### Initial Setup

1. **Clone Repository**:

   ```bash
   git clone <repository-url>
   cd pptx-agent
   ```

2. **Install Dependencies**:

   ```bash
   uv sync --all-extras
   ```

3. **Configure Development Environment**:

   ```bash
   cp .env.template .env
   # Edit .env with development settings
   ```

4. **Verify Setup**:
   ```bash
   mise run ci  # Runs lint, typecheck, and tests
   ```

### Recommended IDE Configuration

#### VS Code

Install extensions:

- Python
- Pylance
- Ruff (linter/formatter)
- Test Explorer

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true
}
```

#### PyCharm

1. Configure interpreter: `.venv/bin/python`
2. Enable Ruff in Settings → Tools → External Tools
3. Configure pytest as test runner

## Project Architecture

### High-Level Architecture

```
┌─────────────┐
│   CLI       │  Entry point (main.py)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Pipeline (pipeline.py)          │
│  Orchestrates all generation stages     │
└───┬─────────┬──────────┬───────────┬───┘
    │         │          │           │
    ▼         ▼          ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Story  │ │Outline │ │Content │ │ Slide  │
│Analyzer│ │  Gen   │ │  Gen   │ │Builder │
└────────┘ └────────┘ └────────┘ └────────┘
    │         │          │           │
    └─────────┴──────────┴───────────┘
                  │
    ┌─────────────┴─────────────┐
    ▼                           ▼
┌──────────┐              ┌──────────┐
│Validators│              │  Schemas │
└──────────┘              └──────────┘
```

### Design Principles

1. **Separation of Concerns**:
   - Content generation (LLM) separate from rendering (PowerPoint)
   - Validation as independent layer
   - Template parsing as standalone module

2. **Type Safety**:
   - Pydantic models for all data structures
   - Strict type checking with pyright
   - Type hints throughout codebase

3. **Testability**:
   - Dependency injection for LLM agents
   - Mock-friendly interfaces
   - Clear separation between I/O and logic

4. **Error Resilience**:
   - Validation at multiple stages
   - Automatic retry with backoff
   - Provider fallback in production

## Code Organization

### Directory Structure

```
pptx-agent/
├── src/pptx_agent/           # Main package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # CLI entry point
│   ├── pipeline.py           # Pipeline orchestration
│   ├── config.py             # Configuration management
│   ├── constants.py          # Project-wide constants
│   │
│   ├── agents/               # LLM agents
│   │   ├── story_analyzer.py      # Input text analysis
│   │   ├── outline_generator.py   # Outline generation
│   │   ├── content_generator.py   # Slide content generation
│   │   └── overflow_resolver.py   # Text overflow resolution
│   │
│   ├── schemas/              # Pydantic models
│   │   ├── outline.py        # Outline structures
│   │   ├── presentation.py   # Presentation schema
│   │   ├── slide.py          # Slide schema
│   │   ├── text.py           # Text blocks
│   │   ├── visual_assets.py  # Charts, tables, SmartArt
│   │   ├── template_manifest.py  # Template metadata
│   │   └── validators.py     # Schema validators
│   │
│   ├── pptx_wrapper/         # PowerPoint manipulation
│   │   ├── presentation.py   # Presentation wrapper
│   │   ├── slide.py          # Slide wrapper
│   │   ├── slide_builder.py  # Slide assembly
│   │   ├── text_handler.py   # Text fitting
│   │   ├── chart_builder.py  # Chart creation
│   │   ├── table_builder.py  # Table creation
│   │   ├── smartart_builder.py   # SmartArt manipulation
│   │   ├── shapes.py         # Shape wrappers
│   │   ├── placeholder_ops.py    # Placeholder operations
│   │   ├── xml_utils.py      # XML manipulation utilities
│   │   └── type_helpers.py   # Type annotation helpers
│   │
│   ├── template_parser/      # Template analysis
│   │   ├── parser.py         # Template parsing
│   │   ├── manifest_builder.py   # Manifest generation
│   │   ├── capacity_calculator.py # Text capacity
│   │   └── models.py         # Parser models
│   │
│   ├── validators/           # Validation logic
│   │   ├── input_validator.py    # Input validation
│   │   ├── outline_validator.py  # Outline validation
│   │   ├── content_validator.py  # Content validation
│   │   ├── file_validator.py     # File security
│   │   ├── security.py       # Security checks
│   │   └── exceptions.py     # Custom exceptions
│   │
│   └── utils/                # Utility functions
│       ├── language_detector.py  # Language detection
│       ├── text_capacity.py      # Capacity calculations
│       └── logging_config.py     # Logging setup
│
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   │   ├── agents/
│   │   ├── pptx_wrapper/
│   │   ├── schemas/
│   │   ├── template_parser/
│   │   ├── validators/
│   │   └── utils/
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data
│
├── templates/                # Sample PowerPoint templates
├── docs/                     # Documentation
├── specs/                    # SDD specifications
└── examples/                 # Example inputs and outputs
```

### Module Responsibilities

#### `agents/`

- **LLM interaction**: All AI-powered content generation
- **Pydantic AI agents**: Type-safe LLM interactions
- **Heuristic fallbacks**: Rule-based generation when needed

#### `schemas/`

- **Data models**: Pydantic models for all data structures
- **Validation**: Field validators and constraints
- **Type safety**: Runtime type checking

#### `pptx_wrapper/`

- **PowerPoint abstraction**: Wrapper around python-pptx
- **Safe operations**: Error-handled XML manipulation
- **Type helpers**: Localized type: ignore comments

#### `validators/`

- **Multi-stage validation**: Input, outline, content, file
- **Security**: Injection detection, file validation
- **Business rules**: Slide count, capacity, constraints

## Development Workflow

### TDD Cycle (Mandatory)

Follow the RED-GREEN-REFACTOR cycle:

```
1. RED:    Write failing test
2. GREEN:  Write minimal code to pass
3. REFACTOR: Improve code quality
```

**Example**:

```python
# 1. RED - Write failing test
def test_detect_japanese_text():
    text = "これは日本語です"
    assert detect_language(text) == "ja"

# Run: uv run pytest tests/unit/utils/test_language_detector.py
# Result: FAIL (function doesn't exist)

# 2. GREEN - Minimal implementation
def detect_language(text: str) -> Literal["ja", "en"]:
    # Simple check for Japanese characters
    for char in text:
        if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF':
            return "ja"
    return "en"

# Run: uv run pytest
# Result: PASS

# 3. REFACTOR - Improve implementation
def detect_language(text: str) -> Literal["ja", "en"]:
    """Detect language with improved accuracy."""
    japanese_count = sum(1 for c in text if is_japanese_char(c))
    total_chars = len([c for c in text if c.isalnum()])

    if total_chars == 0:
        return "en"

    japanese_ratio = japanese_count / total_chars
    return "ja" if japanese_ratio > 0.3 else "en"

# Run: uv run pytest
# Result: PASS (tests still pass after refactoring)
```

### Daily Development Flow

```bash
# 1. Start development
git checkout -b feature/new-feature

# 2. Write tests first (TDD)
# Create test file in tests/unit/

# 3. Run tests (RED phase)
mise run test

# 4. Implement feature (GREEN phase)
# Write minimal code to pass tests

# 5. Run tests again
mise run test

# 6. Refactor (REFACTOR phase)
# Improve code while keeping tests green

# 7. Run full CI checks
mise run ci  # Lint + typecheck + test

# 8. Commit changes
git add .
git commit -m "feat: add new feature"

# 9. Push and create PR
git push origin feature/new-feature
```

### Code Review Checklist

Before submitting PR:

- [ ] All tests pass (`mise run test`)
- [ ] No linting errors (`mise run lint`)
- [ ] No type errors (`mise run typecheck`)
- [ ] Test coverage ≥80% for new code
- [ ] Docstrings added (Google style)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No breaking changes (or documented)

## Testing Guidelines

### Test Organization

```
tests/
├── unit/           # Fast, isolated tests
│   └── test_*.py   # One test file per module
├── integration/    # End-to-end tests
│   └── test_*.py   # Feature-level tests
└── fixtures/       # Test data
    ├── *.txt       # Sample inputs
    ├── *.pptx      # Test templates
    └── *.json      # Test manifests
```

### Writing Unit Tests

**Pattern**: Arrange-Act-Assert

```python
def test_calculate_effective_capacity():
    # Arrange
    max_chars = 1000
    language = "ja"

    # Act
    result = calculate_effective_capacity(max_chars, language)

    # Assert
    assert result == 550  # 1000 * 0.55
```

**Use pytest fixtures for common setup**:

```python
@pytest.fixture
def sample_outline():
    return PresentationOutline(
        title="Test Presentation",
        slides=[
            SlideContent(
                slide_number=1,
                layout_name="Title Slide",
                title="Introduction",
                content="Welcome"
            )
        ],
        output_language="en"
    )

def test_outline_validation(sample_outline):
    result = validate_outline(sample_outline, template_manifest=None)
    assert result.title == "Test Presentation"
```

### Writing Integration Tests

**Test complete workflows**:

```python
def test_basic_presentation_generation(tmp_path):
    # Arrange
    input_file = "tests/fixtures/sample_story_en.txt"
    template_file = "templates/basic-template.pptx"
    output_file = tmp_path / "output.pptx"

    # Act
    result = generate_presentation(
        input_text=Path(input_file).read_text(),
        template_path=template_file,
        output_path=str(output_file)
    )

    # Assert
    assert output_file.exists()
    assert output_file.stat().st_size > 0

    # Verify it's a valid PPTX
    prs = Presentation(str(output_file))
    assert len(prs.slides) >= 3
```

### Running Tests

```bash
# Run all tests
mise run test

# Run with coverage
mise run test-cov

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run specific test
uv run pytest tests/unit/test_config.py::test_config_validation

# Run tests matching pattern
uv run pytest -k "language"

# Run with verbose output
uv run pytest -v

# Run with print statements
uv run pytest -s
```

### Test Coverage Requirements

- **Core modules**: ≥80% coverage required
  - `agents/`
  - `schemas/`
  - `pptx_wrapper/`
  - `validators/`

- **Utility modules**: ≥90% coverage recommended
  - `utils/`

- **Integration tests**: Cover all user stories

Check coverage:

```bash
mise run test-cov
# Opens HTML report in browser
```

## Adding New Features

### Feature Development Process

1. **Specification**: Write or update SDD spec in `specs/`
2. **Tests**: Write tests first (TDD)
3. **Implementation**: Write minimal code to pass tests
4. **Validation**: Add validators if needed
5. **Integration**: Wire into pipeline
   6
