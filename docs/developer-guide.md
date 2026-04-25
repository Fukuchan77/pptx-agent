# Developer Guide - AI PowerPoint Presentation Generator

> **Language**: This document is available in English only.
> **言語**: このドキュメントは英語版のみ提供されています。

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Architecture](#project-architecture)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Adding New Features](#adding-new-features)

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

### Q&A Framework Architecture

The QA (Quality Assurance) framework provides automated inspection and remediation of generated presentations:

```
┌─────────────────────────────────────────────────────────────┐
│                    QA Framework                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ QA Engine   │    │ Fix Engine  │    │ Cache Mgr   │     │
│  │             │    │             │    │             │     │
│  │ • Rule      │    │ • Strategy  │    │ • Template  │     │
│  │   Registry  │    │   Registry  │    │   Manifest  │     │
│  │ • Report    │    │ • Fix Loop  │    │ • SHA-256   │     │
│  │   Generation│    │ • Iteration │    │   Keying    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│  ┌──────────────────────────┼──────────────────────────┐   │
│  │           QA Rules       │        Fix Strategies    │   │
│  │                          │                          │   │
│  │  Layout Checks:          │  Text Overflow:          │   │
│  │  • QA-L-001: Overflow    │  • Font reduction        │   │
│  │  • QA-L-002: Empty title │  • Layout switching      │   │
│  │  • QA-L-003: Unpopulated │  • Content summarization │   │
│  │  • QA-L-004: Overlapping │                          │   │
│  │  • QA-L-005: Boundaries  │  Placeholder:            │   │
│  │  • QA-L-006: Font size   │  • Populate from outline │   │
│  │                          │                          │   │
│  │  Content Checks:         │  Style:                  │   │
│  │  • QA-C-001: Bullet len  │  • Reset to master font  │   │
│  │  • QA-C-002: Dup titles  │  • Fix bullet indents    │   │
│  │  • QA-C-003: Image gaps  │                          │   │
│  │  • QA-C-004: Table dims  │                          │   │
│  │  • QA-C-005: Chart data  │                          │   │
│  │  • QA-C-006: Notes       │                          │   │
│  │                          │                          │   │
│  │  Style Checks:           │                          │   │
│  │  • QA-S-001: Off fonts   │                          │   │
│  │  • QA-S-002: Off colors  │                          │   │
│  │  • QA-S-003: Indent lvl  │                          │   │
│  └──────────────────────────┴──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### QA Engine Design

**Decoupled Architecture**: QA operates independently from generation pipeline:
- Re-opens presentations from disk (no in-memory state dependency)
- Can validate any presentation (not just generated ones)
- Enables QA-only mode for existing files

**Plugin-Based Rules**: Registry pattern enables extensible rule system:
```python
@register_qa_rule("QA-L-001")
class TextOverflowRule(QARule):
    def check(self, presentation: Presentation) -> List[QAIssue]:
        # Detection logic
        pass
```

**Severity Classification**:
- **Error**: Blocks release (text overflow, empty titles, boundary violations)
- **Warning**: Should fix (style violations, overlapping objects, long bullets)
- **Info**: Optional (duplicate titles, off-template colors)

#### Fix Engine Design

**Iterative Fix Loop**: Bounded iterations with progress tracking:
1. Run QA pass → identify fixable issues
2. Apply fix strategies → modify presentation
3. Re-run QA pass → verify fixes
4. Repeat until: zero errors OR max iterations OR no progress

**Staged Fix Strategies**: Multiple approaches per issue type:
- Text overflow: font reduction → layout switch → summarization
- Empty placeholders: populate from outline → default content
- Style violations: reset to master → manual correction needed

**Fix Result Tracking**: Comprehensive reporting:
```python
@dataclass
class FixLoopResult:
    iterations: int
    initial_issues: int
    final_issues: int
    fixes_applied: List[FixResult]
    remaining_issues: List[QAIssue]
```

#### Template Caching Architecture

**Performance Optimization**: SHA-256 keyed manifest caching:
- First parse: analyze template → generate manifest → cache
- Subsequent uses: load cached manifest (50%+ speedup)
- Cache invalidation: automatic on template file changes

**Cache Storage**: Platform-aware directory resolution:
- Linux/Mac: `~/.cache/pptx-agent/`
- Windows: `%LOCALAPPDATA%\pptx-agent\`
- Fallback: system temp directory

**File Locking**: Concurrent access protection:
- Uses `filelock` for atomic cache operations
- Prevents race conditions in multi-process scenarios
- Graceful degradation if locking fails

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
│   ├── templates.py          # Template handling utilities
│   │
│   ├── qa/                   # Quality assurance framework
│   │   ├── engine.py         # QA orchestration
│   │   ├── schemas.py        # QA data models
│   │   ├── report.py         # Report generation
│   │   └── rules/            # QA rule implementations
│   │       ├── base.py       # Rule protocol
│   │       ├── registry.py   # Rule registration
│   │       ├── layout_checks.py    # Layout validation rules
│   │       ├── content_checks.py   # Content validation rules
│   │       ├── style_checks.py     # Style validation rules
│   │       └── register_defaults.py # Default rule registration
│   │
│   ├── fixer/                # Auto-fix framework
│   │   ├── engine.py         # Fix loop orchestration
│   │   ├── schemas.py        # Fix result models
│   │   └── strategies/       # Fix strategy implementations
│   │       ├── __init__.py   # Strategy protocol
│   │       ├── text_overflow.py    # Overflow fixes
│   │       ├── placeholder.py      # Placeholder fixes
│   │       └── style.py      # Style fixes
│   │
│   ├── cache/                # Template manifest caching
│   │   ├── manager.py        # Cache operations
│   │   ├── storage.py        # File-based storage
│   │   └── schemas.py        # Cache entry models
│   │
│   ├── interfaces/           # User interfaces
│   │   ├── cli.py            # Command-line interface
│   │   ├── api.py            # FastAPI REST interface
│   │   └── mcp.py            # MCP server interface
│   │
│   ├── agents/               # LLM agents
│   │   ├── analyzer_config.py     # Analyzer configuration
│   │   ├── llm_config.py          # LLM provider configuration
│   │   ├── utils.py               # Agent utilities
│   │   ├── story_analyzer.py      # Input text analysis
│   │   ├── outline_generator.py   # Outline generation
│   │   ├── content_generator.py   # Slide content generation
│   │   ├── overflow_resolver.py   # Text overflow resolution
│   │   └── prompts/               # Prompt templates
│   │       ├── content_generator.py
│   │       ├── outline_generator.py
│   │       ├── speaker_notes.py
│   │       └── story_analyzer.py
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
│   │   ├── smartart.py       # SmartArt processing
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
└── examples/                 # Example inputs and outputs
```

**Note**: This shows the main modules and directories. Some subdirectories and utility files are omitted for clarity.

### Module Responsibilities

#### `qa/`

- **Quality assurance**: Automated presentation inspection
- **Rule-based checks**: Layout, content, and style validation
- **Report generation**: JSON and Markdown output formats
- **Extensibility**: Plugin-based rule registry

#### `fixer/`

- **Auto-remediation**: Iterative fix loop with bounded iterations
- **Fix strategies**: Text overflow, placeholder, style corrections
- **Progress tracking**: Fix result reporting and metrics
- **Graceful degradation**: Handles unfixable issues

#### `cache/`

- **Template caching**: SHA-256 keyed manifest storage
- **Performance**: 50%+ speedup for repeated template use
- **Platform-aware**: OS-specific cache directory resolution
- **Concurrency**: File locking for multi-process safety

#### `interfaces/`

- **CLI**: Command-line interface with comprehensive flags
- **API**: FastAPI REST endpoints for web integration
- **MCP**: Model Context Protocol server for AI assistants
- **Consistency**: Identical outputs across all interfaces

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

## Testing Configuration

### Unit Tests

Unit tests use the `make_test_config` fixture factory for creating test Config instances:

```python
def test_example(make_test_config):
    # Use default test config
    config = make_test_config()
    assert config.llm_provider == "openai"

    # Override specific fields
    config = make_test_config(
        llm_provider="watsonx",
        watsonx_project_id="test-project"
    )
```

### Integration Tests

Integration tests require real API keys. Set up your test environment:

1. Copy the template:

   ```bash
   cp .env.test.template .env.test
   ```

2. Fill in your test API keys in `.env.test`

3. Run integration tests:
   ```bash
   mise run test-integration
   ```

**Note**: `.env.test` is gitignored and should never be committed.

### Test Isolation

All tests are automatically isolated from your development environment:

- The `isolate_config_from_environment` fixture clears all config-related env vars
- Unit tests don't read `.env` files
- Integration tests explicitly load `.env.test` if present

### Thread Safety

Config access is thread-safe. Tests verify concurrent access patterns.

## Adding New Features

### Feature Development Process

1. **Specification**: Write or update SDD spec in `specs/`
2. **Tests**: Write tests first (TDD)
3. **Implementation**: Write minimal code to pass tests
4. **Validation**: Add validators if needed
5. **Integration**: Wire into pipeline
6. **Documentation**: Update API reference and relevant guides
