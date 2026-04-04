# AI PowerPoint Presentation Generator

An AI-powered tool that generates professional PowerPoint presentations from text or Markdown input using Large Language Models (LLMs).

## Features

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

**Development (OpenAI/Claude via local endpoint):**

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_BASE=http://localhost:11434/v1
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

## Usage

### Basic Usage

Generate a presentation from a text file:

```bash
uv run python -m pptx_agent.main \
  --input input.txt \
  --template templates/basic-template.pptx \
  --output output.pptx
```

### With Language Specification

```bash
uv run python -m pptx_agent.main \
  --input input.txt \
  --template templates/basic-template.pptx \
  --output output.pptx \
  --language ja
```

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

The system follows a pipeline architecture:

1. **Story Analyzer**: Analyzes and summarizes input text
2. **Outline Generator**: Creates presentation structure with slide types
3. **Content Generator**: Generates detailed content for each slide
4. **Validators**: Validates outline and content against template constraints
5. **Slide Builder**: Populates PowerPoint slides with content
6. **Overflow Resolver**: Handles text overflow through staged strategies

### LLM Integration

- Uses [Pydantic AI](https://ai.pydantic.dev/) for type-safe LLM interactions
- Structured output validation with Pydantic models
- Automatic retry with exponential backoff
- Provider fallback (watsonx.ai → Claude)
- Comprehensive logging with Logfire

## Testing

Run the test suite:

```bash
# Run all tests
mise run test

# Run with coverage
mise run test-cov

# Run specific test file
uv run pytest tests/unit/test_project_structure.py

# Run specific test
uv run pytest tests/unit/test_project_structure.py::test_src_directory_exists
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and contribution process.

## License

[Add license information]

## Acknowledgments

- Built with [python-pptx](https://python-pptx.readthedocs.io/)
- LLM integration via [Pydantic AI](https://ai.pydantic.dev/)
- Uses [LiteLLM](https://litellm.ai/) for multi-provider support
