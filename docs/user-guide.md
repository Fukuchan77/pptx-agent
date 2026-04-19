[English](user-guide.md) | [日本語](user-guide_ja.md)

# AI PowerPoint Presentation Generator - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Basic Usage](#basic-usage)
6. [Advanced Features](#advanced-features)
7. [Template Requirements](#template-requirements)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)
10. [Best Practices](#best-practices)

## Introduction

The AI PowerPoint Presentation Generator is a command-line tool that automatically converts text or Markdown documents into professional PowerPoint presentations using Large Language Models (LLMs). The tool analyzes your content, generates a structured outline, creates detailed slide content, and assembles a complete presentation using your template.

### Key Features

- **Automated Content Analysis**: Extracts topics, key messages, and structure from your input
- **Intelligent Slide Generation**: Creates 3-30 slides with appropriate layouts
- **Multi-Language Support**: Full support for Japanese and English
- **Smart Text Fitting**: Automatically adjusts content to fit placeholders
- **Visual Assets**: Generates charts, tables, and SmartArt diagrams
- **Template-Based Design**: Uses your PowerPoint templates for consistent branding
- **Production-Ready**: Robust error handling, retry logic, and provider fallback

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL
- **Python**: Version 3.12 or higher
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (latest version)
- **Task Runner**: [mise](https://mise.jdx.dev/) (optional but recommended)
- **LLM Access**: API access to OpenAI, Anthropic Claude, or IBM watsonx.ai

## Getting Started

### Quick Start (5 minutes)

1. Clone and install:

   ```bash
   git clone <repository-url>
   cd pptx-agent
   uv sync --all-extras
   ```

2. Configure (create `.env` file):

   ```bash
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-sonnet-4-6
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. Generate your first presentation:
   ```bash
   uv run python -m pptx_agent.main \
     --input examples/01-business-quarterly-review.txt \
     --template templates/basic-template.pptx \
     --output my-presentation.pptx
   ```

## Installation

### Prerequisites

#### 1. Install Python 3.12+

**macOS (using Homebrew)**:

```bash
brew install python@3.12
```

**Linux (Ubuntu/Debian)**:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Windows (WSL)**:
Follow Linux instructions after setting up WSL.

#### 2. Install uv Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with pip:

```bash
pip install uv
```

#### 3. Install mise (Optional but Recommended)

```bash
curl https://mise.run | sh
```

### Install the Tool

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd pptx-agent
   ```

2. **Install Dependencies**:

   ```bash
   uv sync --all-extras
   ```

   This installs:
   - Core dependencies (pydantic-ai, python-pptx, litellm)
   - Development tools (ruff, pyright, pytest)
   - Optional extras (logfire for LLM tracing)

3. **Verify Installation**:

   ```bash
   uv run python -m pptx_agent.main --help
   ```

   You should see the help message with available options.

## Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```bash
touch .env
```

### Provider Configuration

#### Option 1: Anthropic Claude (Recommended for Production)

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-api03-...
ENVIRONMENT=production
```

**Get API Key**: [https://console.anthropic.com/](https://console.anthropic.com/)

#### Option 2: OpenAI (via Local Endpoint or API)

**For Local Development (Ollama)**:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_BASE=http://localhost:11434/v1
ENVIRONMENT=development
```

**For OpenAI API**:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
```

#### Option 3: IBM watsonx.ai

```env
LLM_PROVIDER=watsonx
LLM_MODEL=ibm/granite-4-h-small
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_APIKEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-project-id
ENVIRONMENT=production
```

**Get API Key and Browse Models**: [IBM watsonx.ai](https://www.ibm.com/products/watsonx-ai/foundation-models)

### Environment Settings

#### Development Mode (Fast, Less Resilient)

```env
ENVIRONMENT=development
MAX_RETRIES=1
REQUEST_TIMEOUT=60
```

- Faster feedback during development
- Minimal retries to fail fast
- Shorter timeouts

#### Production Mode (Robust, Resilient)

```env
ENVIRONMENT=production
MAX_RETRIES=5
REQUEST_TIMEOUT=120
```

- Automatic retry with exponential backoff
- Provider fallback (watsonx → Claude)
- Comprehensive error logging

### Optional: Provider Fallback

Configure fallback provider for production resilience:

```env
ENABLE_FALLBACK=true
FALLBACK_PROVIDER=anthropic
FALLBACK_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-api03-...
```

If primary provider fails, system automatically switches to fallback.

## Basic Usage

### Command Structure

```bash
uv run python -m pptx_agent.main \
  --input <input-file> \
  --template <template-file> \
  --output <output-file> \
  [--language <en|ja>] \
  [--manifest <manifest-file>] \
  [--verbose]
```

### Required Arguments

- `--input` or `-i`: Path to input text/Markdown file
- `--template` or `-t`: Path to PowerPoint template (.pptx)
- `--output` or `-o`: Path for generated presentation (.pptx)

### Optional Arguments

- `--language` or `-l`: Output language (`en` for English, `ja` for Japanese)
- `--manifest` or `-m`: Path to template manifest JSON file
- `--verbose`: Enable verbose output with full error traces

### Example 1: Basic Generation

```bash
uv run python -m pptx_agent.main \
  --input my-content.txt \
  --template templates/basic-template.pptx \
  --output presentation.pptx
```

### Example 2: Japanese Presentation

```bash
uv run python -m pptx_agent.main \
  --input content-ja.txt \
  --template templates/japanese-template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### Example 3: With Template Manifest

```bash
uv run python -m pptx_agent.main \
  --input business-proposal.md \
  --template templates/corporate-template.pptx \
  --manifest templates/corporate-manifest.json \
  --output proposal.pptx
```

### Example 4: Verbose Mode for Debugging

```bash
uv run python -m pptx_agent.main \
  --input my-content.txt \
  --template templates/basic-template.pptx \
  --output presentation.pptx \
  --verbose
```

## Advanced Features

### Multi-Language Support

The system automatically detects input language and generates slides accordingly:

- **English**: Uses full-width text capacity calculations
- **Japanese**: Applies 0.55x capacity multiplier for full-width characters
- **Mixed Content**: Preserves technical terms in English within Japanese text

**Force Output Language**:

```bash
# Input is English, but generate Japanese slides
uv run python -m pptx_agent.main \
  --input input-en.txt \
  --template templates/template.pptx \
  --output presentation-ja.pptx \
  --language ja
```

### Charts and Tables

The system automatically identifies numerical and tabular data in your input and converts them to visual elements.

**Chart Example Input**:

```markdown
## Sales Performance

Our quarterly sales data shows:

- Q1: $1.2M
- Q2: $1.5M
- Q3: $1.8M
- Q4: $2.1M
```

The system generates a bar chart with this data.

**Table Example Input**:

```markdown
## Product Comparison

| Feature | Basic  | Pro    | Enterprise |
| ------- | ------ | ------ | ---------- |
| Users   | 10     | 100    | Unlimited  |
| Storage | 10GB   | 100GB  | 1TB        |
| Price   | $10/mo | $50/mo | Custom     |
```

The system generates a formatted table.

### SmartArt Diagrams

If your template includes SmartArt layouts, the system can populate them:

**Process Flow Input**:

```markdown
## Implementation Process

1. Requirements Gathering
2. Design & Planning
3. Development
4. Testing & QA
5. Deployment
```

The system populates a process SmartArt with these steps.

### Text Overflow Resolution

The system automatically handles text that doesn't fit:

1. **Font Reduction**: Reduces font size by 10-20%
2. **Layout Change**: Switches to layout with larger placeholder
3. **Content Split**: Divides content across multiple slides
4. **Summarization**: Requests LLM to condense content

You don't need to do anything - the system handles this automatically.

## Template Requirements

### Minimum Requirements

Your PowerPoint template must include:

1. **Title Slide Layout**: For the first and last slides
2. **Title and Content Layout**: For main content slides
3. **Section Header Layout** (optional): For section transitions

### Layout Naming Conventions

The system looks for layouts with these names:

- "Title Slide"
- "Title and Content"
- "Section Header"
- "Two Content" (for two-column layouts)
- "Title Only"
- "Blank"

### Placeholder Requirements

Each layout should have clearly named placeholders:

- **Title**: "Title" or "Title 1"
- **Content**: "Content", "Text Placeholder", or "Body"
- **Chart**: "Chart Placeholder" or "Content"
- **Table**: "Table Placeholder" or "Content"

### Creating Compatible Templates

1. **Start with Microsoft PowerPoint or LibreOffice Impress**
2. **Create Slide Master** with your branding
3. **Add Layouts** with appropriate placeholders
4. **Name Layouts** using standard conventions
5. **Test** with the tool to verify compatibility

### Template Manifest (Optional)

Generate a manifest to optimize generation:

```bash
uv run python -m pptx_agent.template_parser.parser \
  --template templates/my-template.pptx \
  --output templates/my-template-manifest.json
```

The manifest includes:

- Available layouts and placeholders
- Text capacity calculations
- SmartArt configurations
- Color and font themes

## Troubleshooting

### Common Issues

#### Issue: "Template file not found"

**Cause**: Template path is incorrect or file doesn't exist.

**Solution**:

```bash
# Use absolute path
--template /full/path/to/template.pptx

# Or relative from current directory
--template ./templates/template.pptx
```

#### Issue: "Input validation failed: text too short"

**Cause**: Input file is empty or has less than 10 characters.

**Solution**:

- Ensure input file has substantial content (at least 100 characters recommended)
- Check file encoding (must be UTF-8)

#### Issue: "Required configuration for anthropic provider is incomplete"

**Cause**: Missing API key in environment variables.

**Solution**:

```bash
# Add to .env file
ANTHROPIC_API_KEY=your-actual-api-key-here
```

#### Issue: "Layout 'Title and Content' not found in template"

**Cause**: Template doesn't have required layout.

**Solution**:

- Use a compatible template from `templates/` directory
- Or add missing layout to your template in PowerPoint

#### Issue: Text overflow even after resolution

**Cause**: Content is extremely long or template has very small placeholders.

**Solution**:

- Simplify input content
- Use template with larger placeholders
- Enable summarization in manifest

### Error Messages

#### "Validation Error: slide count exceeds maximum"

**Meaning**: Generated outline has more than 30 slides.

**Solution**: Reduce input content or split into multiple presentations.

#### "Provider error: rate limit exceeded"

**Meaning**: Too many API requests to LLM provider.

**Solution**:

- Wait and retry
- Use production mode with retry backoff
- Check your API rate limits

#### "Timeout error: outline generation exceeded 120s"

**Meaning**: LLM took too long to respond.

**Solution**:

- Retry (usually succeeds on second attempt)
- Check LLM provider status
- Reduce input complexity

### Getting Help

1. **Check Logs**: Run with `--verbose` flag for detailed error information
2. **Verify Configuration**: Ensure `.env` file has correct API keys
3. **Test Template**: Try with provided sample templates first
4. **Check API Status**: Verify your LLM provider is operational

## FAQ

### Q: What input formats are supported?

**A**: Plain text (.txt) and Markdown (.md) files. The system handles both English and Japanese text.

### Q: How long should my input text be?

**A**: Between 100 and 30,000 characters for optimal results. Longer text may be rejected or split.

### Q: How many slides will be generated?

**A**: Between 3 and 30 slides, depending on content complexity. The system issues a warning if more than 20 slides are generated.

### Q: Can I use my company's PowerPoint template?

**A**: Yes! As long as it follows standard layout naming conventions. See [Template Requirements](#template-requirements).

### Q: Does this work offline?

**A**: No, it requires internet access to call LLM APIs. However, you can use a local LLM server (like Ollama) for offline operation.

### Q: How accurate is the content generation?

**A**: The system generates content based on your input text. Quality depends on:

- Input text clarity and structure
- LLM model quality (GPT-4 and Claude 3.5 Sonnet recommended)
- Template design and placeholder sizing

### Q: Can I edit the generated presentation?

**A**: Yes! The output is a standard PowerPoint file that can be edited in Microsoft PowerPoint, LibreOffice Impress, or Google Slides.

### Q: What about speaker notes?

**A**: Speaker notes are generated automatically for every slide by default, summarizing the key points of the slide content to assist the presenter.

## Best Practices

1. **Structuring Input**: Organize your input document with clear headings, bullet points, and distinct sections.
2. **Template Validation**: Run your template through the template parser script once to ensure layouts are detected properly.
3. **Review Extracted Stats**: Run in `--verbose` mode to see what the agent extracts before checking the final PPTX.
4. **Iterative Refinement**: Provide the LLM with enough content context so that slide layouts can be correctly determined avoiding heavy overflow reduction.
