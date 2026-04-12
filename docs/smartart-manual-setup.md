[English](smartart-manual-setup.md) | [日本語](smartart-manual-setup_ja.md)

# SmartArt Template Manual Setup Guide (Production)

## Table of Contents

1. [Overview](#overview)
2. [Purpose Differences](#purpose-differences)
3. [Background](#background)
4. [Manual Creation Steps](#manual-creation-steps)
5. [Verification Steps](#verification-steps)
6. [Integration with Existing Code](#integration-with-existing-code)
7. [Troubleshooting](#troubleshooting)
8. [References](#references)
9. [Summary](#summary)

## Overview

**This guide is the complete version for creating production templates.**

This document explains how to create a production template with SmartArt placed in slide masters/layouts using Microsoft PowerPoint.

If you just want to pass integration tests, see [smartart-quickstart.md](smartart-quickstart.md) (completed in 10-15 minutes).

## Purpose Differences

| Purpose                        | Method                                 | Target              | Guide                                                            |
| ------------------------------ | -------------------------------------- | ------------------- | ---------------------------------------------------------------- |
| **Pass Integration Tests**     | Insert SmartArt into regular slides    | `prs.slides`        | [smartart-quickstart.md](smartart-quickstart.md) 👈 Quick & Easy |
| **Create Production Template** | Place SmartArt in slide master/layouts | `prs.slide_layouts` | 👉 This document                                                 |

### For Integration Tests Only

**See [smartart-quickstart.md](smartart-quickstart.md) (completed in 10-15 minutes)**

This document is for creating complete templates for production environments.

## Background

### Why Are Tests Skipped?

1. **python-pptx limitation**: The `python-pptx` library **cannot programmatically create SmartArt shapes**
2. **Test requirements**: Integration tests ([test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py)) require templates with real SmartArt shapes
3. **Current situation**: [templates/smartart-test-template.pptx](../templates/smartart-test-template.pptx) contains only placeholder shapes (not real SmartArt)

### Three Skipped Tests

1. [test_smartart_with_real_template_process_flow()](../tests/integration/test_smartart_real_templates.py) - Process flow SmartArt test
2. [test_smartart_all_types_in_real_template()](../tests/integration/test_smartart_real_templates.py) - Four SmartArt types test
3. [test_smartart_end_to_end_workflow()](../tests/integration/test_smartart_real_templates.py) - End-to-end workflow test

## Manual Creation Steps

### Prerequisites

- **Microsoft PowerPoint** (Windows or Mac version) required
  - LibreOffice Impress is not recommended due to limited SmartArt creation capabilities
- PowerPoint 2016 or later recommended

### Step 1: Create New Template File

1. Launch Microsoft PowerPoint
2. Select "New Presentation"
3. Start with blank presentation

### Step 2: Navigate to Slide Master View

1. Select "View" → "Slide Master" from menu bar
2. Enter Slide Master View

### Step 3: Create Custom Layouts (4 types)

#### Layout 1: Process Flow

1. Click "Insert Layout"
2. Rename layout to "Process Flow"
3. Select "Insert" → "SmartArt"
4. **Category**: "Process"
5. **Type**: Select "Basic Process" or "Step Up Process"
6. After inserting SmartArt, configure:
   - Node count: Set to **3** (adjust with Add Shape/Delete Shape)
   - Text for each node: "Node 1", "Node 2", "Node 3"
   - Size: Center on slide, approximately 8 inches wide × 4 inches high
7. Add title placeholder ("Insert Placeholder" → "Title")

#### Layout 2: Hierarchy

1. Insert new layout
2. Rename layout to "Hierarchy"
3. Select "Insert" → "SmartArt"
4. **Category**: "Hierarchy"
5. **Type**: Select "Organization Chart"
6. After inserting SmartArt, configure:
   - Node count: **3-4** (1 top level, 2-3 children)
   - Example text:
     - Level 0: "CEO"
     - Level 1: "VP Sales", "VP Engineering"
   - Size: Center similar to above
7. Add title placeholder

#### Layout 3: Cycle

1. Insert new layout
2. Rename layout to "Cycle"
3. Select "Insert" → "SmartArt"
4. **Category**: "Cycle"
5. **Type**: Select "Basic Cycle"
6. After inserting SmartArt, configure:
   - Node count: **4** (Plan, Do, Check, Act)
   - Text for each node: "Plan", "Do", "Check", "Act"
7. Add title placeholder

#### Layout 4: Relationship

1. Insert new layout
2. Rename layout to "Relationship"
3. Select "Insert" → "SmartArt"
4. **Category**: "Relationship"
5. **Type**: Select "Basic Venn" or "Grouped List"
6. After inserting SmartArt, configure:
   - Node count: **3**
   - Text: "Group 1", "Group 2", "Group 3"
7. Add title placeholder

### Step 4: Exit Slide Master View and Save

1. Click "Close Master View" on the "Slide Master" tab
2. Select "File" → "Save As"
3. **Save location**: `tests/fixtures/smartart_test_template.pptx`
4. **File format**: PowerPoint Presentation (\*.pptx)
5. Save

### Step 5: Copy for Production Template (Optional)

```bash
# Execute in command line
cp tests/fixtures/smartart_test_template.pptx templates/smartart-template.pptx
```

## Verification Steps

### 1. Verify Template with Script

```bash
# Check if template contains SmartArt
uv run python -c "
from pptx import Presentation
from pathlib import Path

template_path = 'tests/fixtures/smartart_test_template.pptx'
if not Path(template_path).exists():
    print(f'❌ Template not found: {template_path}')
    exit(1)

prs = Presentation(template_path)
smartart_count = 0

for slide in prs.slides:
    for shape in slide.shapes:
        if hasattr(shape, '_element'):
            elem = shape._element
            if 'graphicFrame' in str(elem.tag):
                smartart_count += 1
                print(f'✓ Found SmartArt: {shape.name}')

if smartart_count > 0:
    print(f'\n✓ Template has {smartart_count} SmartArt shapes')
else:
    print('\n❌ No SmartArt shapes found')
"
```

### 2. Run Tests

```bash
# Run previously skipped tests
uv run pytest tests/integration/test_smartart_real_templates.py -v

# Expected results:
# test_smartart_with_real_template_process_flow PASSED
# test_smartart_all_types_in_real_template PASSED
# test_smartart_end_to_end_workflow PASSED
```

### 3. Run All Tests

```bash
# Run full test suite to check for regressions
uv run pytest tests/ -v
```

## Integration with Existing Code

### No Integration Required - Just Add Template File

This task **does not require changing existing code** because:

1. **Test code is already complete**: [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py) test logic is complete
2. **SmartArt processing code is complete**: [smartart_builder.py](../src/pptx_agent/pptx_wrapper/smartart_builder.py) and [smartart.py](../src/pptx_agent/pptx_wrapper/smartart.py) are implemented
3. **Only template file needed**: Just place the manually created template file

### File Placement Locations

Place created template file in one of:

```
tests/fixtures/smartart_test_template.pptx  ← For tests (priority)
templates/smartart-template.pptx            ← For production (optional)
```

### Test Fixture Auto-Detection

The [template_with_smartart](../tests/integration/test_smartart_real_templates.py) fixture automatically searches for templates in this order:

```python
possible_paths = [
    "tests/fixtures/smartart_test_template.pptx",  # Highest priority
    "templates/smartart-template.pptx",            # Second
    "tests/fixtures/basic-template.pptx",          # Fallback
]
```

## Troubleshooting

### Issue: SmartArt Not Detected

**Symptom**: Tests still skipped

**Solution**:

1. Open file in PowerPoint and verify SmartArt is actually inserted
2. Confirm it's SmartArt (graphic frame), not regular shapes
3. Verify it was created in Slide Master View (not regular slide)

### Issue: Node Count Mismatch

**Symptom**: `ValueError: Expected X nodes but SmartArt has Y nodes`

**Solution**:

1. Match SmartArt node counts to test data
2. Process Flow: 3 nodes
3. Hierarchy: 3-4 nodes
4. Cycle: 4 nodes
5. Relationship: 3 nodes

### Issue: Created with LibreOffice Impress

**Symptom**: SmartArt not working correctly

**Solution**:

- LibreOffice Impress has limited SmartArt creation capabilities
- **Recommend recreating with Microsoft PowerPoint**

## References

- [SMARTART-TEMPLATE-SPEC.md](../templates/SMARTART-TEMPLATE-SPEC.md) - SmartArt template specification
- [test_smartart_real_templates.py](../tests/integration/test_smartart_real_templates.py) - Integration test code
- [smartart_builder.py](../src/pptx_agent/pptx_wrapper/smartart_builder.py) - SmartArt builder implementation
- [smartart.py](../src/pptx_agent/pptx_wrapper/smartart.py) - SmartArt wrapper implementation

## Summary

### What To Do (Manual Work)

1. ✅ Open Microsoft PowerPoint
2. ✅ Create 4 SmartArt layout types (Process, Hierarchy, Cycle, Relationship)
3. ✅ Save as `tests/fixtures/smartart_test_template.pptx`
4. ✅ Run tests to verify

### What NOT To Do

- ❌ Modify existing code
- ❌ Create new tests
- ❌ Fix build scripts
- ❌ Add dependencies

### Expected Results

```bash
$ uv run pytest tests/integration/test_smartart_real_templates.py -v

tests/integration/test_smartart_real_templates.py::test_smartart_with_real_template_process_flow PASSED
tests/integration/test_smartart_real_templates.py::test_smartart_all_types_in_real_template PASSED
tests/integration/test_smartart_real_templates.py::test_smartart_end_to_end_workflow PASSED

====== 3 passed in 2.45s ======
```
