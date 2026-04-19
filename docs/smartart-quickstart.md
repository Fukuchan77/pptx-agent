[English](smartart-quickstart.md) | [日本語](smartart-quickstart_ja.md)

# SmartArt Template Creation Quickstart

## Table of Contents

1. [Overview](#overview)
2. [Purpose Differences](#purpose-differences)
3. [Current Status](#current-status)
4. [Required Manual Steps (PowerPoint)](#required-manual-steps-powerpoint)
5. [Verification Steps](#verification-steps)
6. [Troubleshooting](#troubleshooting)
7. [Summary](#summary)

## Overview

**This guide is specialized for passing integration tests.**

This explains how to create a SmartArt template for passing integration tests in **10-15 minutes**. For creating a complete production template, see [smartart-manual-setup.md](smartart-manual-setup.md).

## Purpose Differences

| Purpose                        | Method                                 | Target              | Guide                                                |
| ------------------------------ | -------------------------------------- | ------------------- | ---------------------------------------------------- |
| **Pass Integration Tests**     | Insert SmartArt into regular slides    | `prs.slides`        | 👉 This document                                     |
| **Create Production Template** | Place SmartArt in slide master/layouts | `prs.slide_layouts` | [smartart-manual-setup.md](smartart-manual-setup.md) |

### Why Are They Different?

- **Tests**: [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py) iterates over `prs.slides` → requires regular slides
- **Production**: [TemplateParser](../src/pptx_agent/template_parser/parser.py) parses `prs.slide_layouts` → requires slide layouts

## Prerequisites and Expected State

### Prerequisites

- Microsoft PowerPoint application (Microsoft 365 or desktop version)
- Access to the repository's `tests/fixtures/` directory
- Basic familiarity with SmartArt insertion in PowerPoint

### Expected State After Completion

The template file `tests/fixtures/smartart_test_template.pptx` should contain:

- **Slide 1**: Process Flow (Basic Process SmartArt with 3 nodes)
- **Slide 2**: Hierarchy (Organization Chart SmartArt with 3 nodes)
- **Slide 3**: Cycle (Basic Cycle SmartArt with 4 nodes)
- **Slide 4**: Relationship (Basic Venn SmartArt with 3 nodes)

All SmartArt shapes must be properly formatted and contain the specified text content.

## Required Manual Steps (PowerPoint)

### Option A: Edit Existing File (Recommended)

1. **Open in PowerPoint**
   ```bash
   open tests/fixtures/smartart_test_template.pptx
   ```
2. **For each slide** (4 slides total):

   **Slide 1 - Process Flow:**
   - Delete Rectangle 3 (placeholder)
   - Select "Insert" → "SmartArt" → "Process" → "Basic Process"
   - Set node count to **3**
   - Text: "Node 1", "Node 2", "Node 3"

   **Slide 2 - Hierarchy:**
   - Delete Rectangle 3
   - Select "Insert" → "SmartArt" → "Hierarchy" → "Organization Chart"
   - Set node count to **3** (1 top, 2 children)
   - Text: "CEO", "VP Sales", "VP Engineering"

   **Slide 3 - Cycle:**
   - Delete Rectangle 3
   - Select "Insert" → "SmartArt" → "Cycle" → "Basic Cycle"
   - Set node count to **4**
   - Text: "Plan", "Do", "Check", "Act"

   **Slide 4 - Relationship:**
   - Delete Rectangle 3
   - Select "Insert" → "SmartArt" → "Relationship" → "Basic Venn"
   - Set node count to **3**
   - Text: "Group 1", "Group 2", "Group 3"

3. **Save**
   - Ctrl+S / Cmd+S to save

### Option B: Create New (Use Detailed Guide)

See [smartart-manual-setup.md](smartart-manual-setup.md) for detailed instructions

## Verification Steps

### 1. Verify SmartArt Presence

```bash
uv run python -c "
from pptx import Presentation
from pathlib import Path

template_path = 'tests/fixtures/smartart_test_template.pptx'
prs = Presentation(template_path)
smartart_count = 0

for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if hasattr(shape, '_element'):
            if 'graphicFrame' in str(shape._element.tag):
                smartart_count += 1
                print(f'✓ Slide {i+1}: Found SmartArt - {shape.name}')

if smartart_count > 0:
    print(f'\n✓ SUCCESS: Template has {smartart_count} SmartArt shapes')
    print('You can run tests: uv run pytest tests/integration/test_smartart_real_templates.py -v')
else:
    print('\n❌ FAILED: No SmartArt shapes found')
    print('Manual editing with PowerPoint is required')
"
```

**Expected output:**

```
✓ Slide 1: Found SmartArt - Content Placeholder 2
✓ Slide 2: Found SmartArt - Content Placeholder 2
✓ Slide 3: Found SmartArt - Content Placeholder 2
✓ Slide 4: Found SmartArt - Content Placeholder 2

✓ SUCCESS: Template has 4 SmartArt shapes
```

### 2. Run Tests

```bash
uv run pytest tests/integration/test_smartart_real_templates.py -v
```

**Expected results:**

```
test_smartart_with_real_template_process_flow PASSED
test_smartart_all_types_in_real_template PASSED
test_smartart_end_to_end_workflow PASSED
```

## Troubleshooting

### Q: PowerPoint is not available

**A:** LibreOffice Impress has limited SmartArt creation capabilities. Here are your options:

1. **Try Microsoft 365** (1-month free trial available)
2. **Create on another PC** and copy the file
3. **Consider commercial libraries** (Aspose.Slides, etc.)
4. **Skip tests** and operate as-is (SmartArt logic is already verified by unit tests)

### Q: Node count doesn't match

**A:** Adjust SmartArt node counts to match:

- Process: 3 nodes
- Hierarchy: 3 nodes (1 top, 2 children)
- Cycle: 4 nodes
- Relationship: 3 nodes

### Q: Cannot delete existing placeholders

**A:** Edit in normal slide view, not in slide master view.

## Summary

### Current State

- ✅ Test code complete
- ✅ SmartArt processing logic complete
- ✅ File placement and naming complete
- ❌ **Waiting for SmartArt insertion in PowerPoint**

### Next Steps

1. Open `tests/fixtures/smartart_test_template.pptx` in PowerPoint
2. Insert SmartArt into 4 slides (see steps above)
3. Save
4. Run verification script
5. Run tests

**Time Required**: Approximately 10-15 minutes
