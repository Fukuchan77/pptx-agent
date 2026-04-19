[English](README.md) | [日本語](README_ja.md)

# AI PowerPoint Presentation Generator

An AI-powered tool that generates professional PowerPoint presentations from text or Markdown input using Large Language Models (LLMs).

## 📚 Documentation

- **[User Guide](docs/user-guide.md)** - Complete installation, configuration, and usage instructions
- **[Developer Guide](docs/developer-guide.md)** - Architecture, development workflow, and contribution guidelines
- **[API Reference](docs/api-reference.md)** - Technical API documentation
- **[Architecture Decision Records (ADR)](docs/adr/)** - Record of important architectural decisions and technical choices
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions _(coming soon)_

## ✨ Features

- **Automated Presentation Generation**: Convert text/Markdown documents into structured PowerPoint presentations
- **Multi-Language Support**: Supports Japanese and English with language-aware text capacity calculations
- **Intelligent Layout Selection**: Automatically selects appropriate slide layouts based on content
- **Smart Content Fitting**: Resolves text overflow through font reduction, layout switching, or content summarization
- **Visual Asset Support**: Generates charts, tables, and populates SmartArt diagrams
- **Template-Based**: Uses customizable PowerPoint templates for consistent branding
- **Production-Ready**: Built-in retry strategies, provider fallback, and comprehensive error handling

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [mise](https://mise.jdx.dev/) task runner

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd pptx-agent
```

2. Install dependencies using uv:

```bash
uv sync --all-extras
```

3. Set up environment variables:

```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

## Configuration

### Environment Variables

The tool supports multiple LLM providers. Configure your preferred provider in `.env`:

**OpenAI (via local endpoint or API):**

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
# For OpenAI API:
OPENAI_API_KEY=your-api-key
# Or for local endpoint (e.g. Ollama):
# LLM_API_BASE=http://localhost:11434/v1
```

**Production (IBM watsonx.ai):**

```bash
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_APIKEY=your-api-key
WATSONX_PROJECT_ID=your-project-id
```

**Production Fallback (Anthropic Claude):**

```bash
ANTHROPIC_API_KEY=your-api-key
```

## 🚀 Quick Start

Generate your first presentation in 3 steps:

```bash
# 1. Install
uv sync --all-extras

# 2. Configure (add your API key to .env)
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# 3. Generate
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output my-presentation.pptx
```

## 📖 Usage Examples

### Basic Presentation Generation

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output.pptx
```

### Japanese Presentation

```bash
uv run python -m pptx_agent.main \
  --input examples/03-python-programming-basics-ja.txt \
  --template templates/japanese-template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### With Template Manifest (Optimized)

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output proposal.pptx \
  --manifest templates/basic-manifest.json
```

### Verbose Mode (Debugging)

```bash
uv run python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output.pptx \
  --verbose
```

For more examples and detailed usage instructions, see the **[User Guide](docs/user-guide.md)**.

## Development

### Using mise Tasks

The project uses mise for task management. Available tasks:

```bash
# Run tests
mise run test

# Run tests with coverage report
mise run test-cov

# Run linter checks
mise run lint

# Auto-fix linter issues
mise run lint-fix

# Format code
mise run format

# Run type checker
mise run typecheck

# Run all CI checks (lint, typecheck, test)
mise run ci
```

### Development Workflow

1. **Write Tests First (TDD)**:
   - Write failing test
   - Implement minimal code to pass
   - Refactor while keeping tests green

2. **Follow Code Style**:
   - Google Python Style Guide
   - Use ruff for linting and formatting
   - Use pyright for type checking

3. **Maintain Test Coverage**:
   - Minimum 80% coverage for core modules
   - Run `mise run test-cov` to check coverage

4. **Commit Standards**:
   - Run `mise run ci` before committing
   - Write clear, descriptive commit messages

### Project Structure

```
pptx-agent/
├── src/
│   └── pptx_agent/           # Main package
│       ├── agents/           # LLM agents (story analyzer, outline generator, etc.)
│       ├── pptx_wrapper/     # PowerPoint manipulation layer
│       ├── template_parser/  # Template analysis and manifest generation
│       ├── validators/       # Input and content validation
│       ├── schemas/          # Pydantic models
│       └── utils/            # Utility functions
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data and templates
├── templates/                # PowerPoint templates
└── docs/                     # Documentation
```

## Architecture

The system follows a pipeline architecture with 7 main stages:

1. **Story Analyzer**: Analyzes and summarizes input text
2. **Outline Generator**: Creates presentation structure with slide types
3. **Outline Validator**: Validates outline against template constraints
4. **Content Generator**: Generates detailed content for each slide
5. **Content Validator**: Validates content against template capacity
6. **Slide Builder**: Populates PowerPoint slides with content
7. **Overflow Resolver**: Handles text overflow through staged strategies

For detailed technical information about each pipeline component, see the [API Reference](docs/api-reference.md).

### LLM Integration

- Uses [Pydantic AI](https://ai.pydantic.dev/) for type-safe LLM interactions
- Structured output validation with Pydantic models
- Automatic retry with exponential backoff
- Provider fallback (watsonx.ai → Claude)
- Comprehensive logging with Logfire

## Testing

### Running Tests

```bash
# Run all tests
mise run test

# Run unit tests only
uv run pytest tests/unit/ -x

# Run integration tests (requires API keys)
uv run pytest tests/integration/ -x

# Run with coverage report
mise run test-cov
```

### Test Configuration

**Unit Tests**: Automatically isolated from environment variables. Use [`make_test_config()`](tests/conftest.py:64) fixture:

```python
def test_something(make_test_config):
    config = make_test_config(llm_provider="openai")
    # Test logic here
```

**Integration Tests**: Require real API keys. Set up your test environment:

1. Copy the template: `cp .env.test.template .env.test`
2. Fill in your test API keys
3. Run integration tests: `uv run pytest tests/integration/ -x`

**Note**: `.env.test` is gitignored and should never be committed.

For more details, see the [Developer Guide](docs/developer-guide.md#testing-configuration).

## 🤝 Contributing

We welcome contributions! Please see:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[Developer Guide](docs/developer-guide.md)** - Development setup and workflow
- **[API Reference](docs/api-reference.md)** - Technical documentation

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow TDD: Write tests first, then implement
4. Run CI checks: `mise run ci`
5. Submit a Pull Request

## License

This project is licensed under the MIT License — see LICENSE for details.

## Acknowledgments

- Built with [python-pptx](https://python-pptx.readthedocs.io/)
- LLM integration via [Pydantic AI](https://ai.pydantic.dev/)
- Multi-provider LLM support via [LiteLLM](https://docs.litellm.ai/) (OpenAI, Anthropic, watsonx, etc.)
