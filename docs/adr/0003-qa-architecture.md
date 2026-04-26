# ADR 0003: QA Architecture and Auto-Fix Framework

## Status

Accepted

Adoption Date: 2026-04-24

## Context

### Background

The pptx-agent system generates PowerPoint presentations from text input using AI. While the generation pipeline produces functional presentations, several quality issues can occur:

1. **Text Overflow**: Generated content may exceed placeholder capacity
2. **Empty Placeholders**: Some placeholders may remain unpopulated
3. **Style Violations**: Generated content may use off-template fonts or colors
4. **Layout Issues**: Objects may overlap or extend beyond slide boundaries
5. **Content Quality**: Bullet points may be too long, titles may be duplicated

These issues require manual inspection and correction, reducing the value proposition of automated generation. Users need confidence that generated presentations meet professional quality standards without manual cleanup.

### Requirements

The QA framework must satisfy the following requirements:

1. **Automated Inspection**: Detect quality issues without manual review
2. **Comprehensive Coverage**: Check layout, content, and style dimensions
3. **Severity Classification**: Distinguish blocking errors from optional improvements
4. **Actionable Reporting**: Provide specific issue locations and fix suggestions
5. **Automatic Remediation**: Fix common issues through iterative correction
6. **Language Awareness**: Handle multi-language presentations correctly
7. **Extensibility**: Support custom rules and fix strategies
8. **Performance**: Complete QA pass in seconds, not minutes

### Constraints

1. **Constitutional Compliance**: Must follow TDD, maintain ≥80% test coverage
2. **Type Safety**: Full type annotations with pyright strict mode
3. **No Breaking Changes**: Existing generation pipeline must continue working
4. **Optional Features**: QA and auto-fix must be opt-in, not mandatory
5. **Template Preservation**: Fixes must not corrupt template structure

## Decision

We implemented a **rule-based QA engine with iterative auto-fix loop** architecture consisting of three core modules:

### 1. QA Engine (`src/pptx_agent/qa/`)

**Architecture**: Registry pattern with pluggable rules

**Components**:

- **QAEngine**: Orchestrates rule execution and report generation
- **QARule Protocol**: Interface for validation rules
- **Rule Registry**: Dynamic rule registration and discovery
- **QA Schemas**: Type-safe issue and report models

**Rule Categories**:

- **Layout Checks** (`layout_checks.py`): Text overflow, empty placeholders, overlapping objects, boundary violations, minimum font size
- **Content Checks** (`content_checks.py`): Bullet length, duplicate titles, unpopulated images, pathological tables, missing chart data, speaker notes
- **Style Checks** (`style_checks.py`): Off-template fonts, off-template colors, invalid bullet indents

**Design Rationale**:

- **Registry Pattern**: Enables dynamic rule addition without modifying engine code
- **Protocol-Based Rules**: Provides type-safe interface without inheritance overhead
- **Severity Levels**: ERROR (blocking), WARNING (should fix), INFO (optional)
- **Auto-Fixable Flag**: Rules declare whether issues can be automatically corrected

### 2. Fixer Engine (`src/pptx_agent/fixer/`)

**Architecture**: Strategy pattern with bounded iteration loop

**Components**:

- **FixEngine**: Orchestrates fix loop with max iteration limit
- **FixStrategy Protocol**: Interface for fix strategies
- **Strategy Registry**: Dynamic strategy registration
- **Fix Schemas**: Type-safe fix result models

**Fix Strategies**:

- **Text Overflow** (`text_overflow.py`): Font reduction → Layout switching → Content summarization (staged escalation)
- **Placeholder Population** (`placeholder.py`): Fill empty placeholders from outline
- **Style Reset** (`style.py`): Reset fonts/colors to template master

**Fix Loop Algorithm**:

```
1. Run initial QA pass → Generate QA report
2. If no errors OR max iterations reached → Exit
3. For each auto-fixable error:
   a. Select appropriate fix strategy
   b. Apply fix to presentation
   c. Record fix result
4. Run QA pass again → Generate new report
5. Go to step 2
```

**Design Rationale**:

- **Bounded Iterations**: Prevents infinite loops (default: 3 iterations)
- **Strategy Pattern**: Enables multiple fix approaches per issue type
- **Staged Escalation**: Try least invasive fixes first (font reduction before summarization)
- **Idempotency**: Re-running QA after fixes validates corrections

### 3. Cache Module (`src/pptx_agent/cache/`)

**Architecture**: File-based cache with SHA-256 keying and file locking

**Components**:

- **CacheManager**: High-level cache operations
- **CacheStorage**: Low-level file I/O with locking
- **Cache Schemas**: Type-safe cache entry models

**Caching Strategy**:

- **Key Generation**: SHA-256 hash of template file content
- **Storage Location**: Platform-specific cache directory (via `platformdirs`)
- **Concurrency**: File locking prevents race conditions
- **Invalidation**: Automatic on template modification (hash mismatch)
- **Cleanup**: Stale entry removal (default: 30 days)

**Design Rationale**:

- **Content-Based Keying**: Hash ensures cache invalidation on template changes
- **Platform Conventions**: Uses OS-appropriate cache directories
- **File Locking**: Prevents corruption in concurrent scenarios
- **Graceful Degradation**: Falls back to parsing if cache unavailable

### 4. Pipeline Integration

**Integration Points**:

```python
# In pipeline.py
async def generate_presentation(
    ...,
    qa_enabled: bool = True,
    autofix_enabled: bool = False,
) -> tuple[str, QAReport | None]:
    # ... existing generation stages ...

    # Stage 8: QA Pass (optional)
    if qa_enabled:
        qa_engine = QAEngine(language=output_language)
        qa_report = qa_engine.validate(wrapper)

        # Stage 9: Auto-Fix Loop (optional)
        if autofix_enabled and not qa_report.passed:
            fix_engine = FixEngine(max_iterations=3)
            fix_result = fix_engine.fix_loop(wrapper, qa_report)
            qa_report = fix_result.final_qa_report

    return output_path, qa_report
```

**Design Rationale**:

- **Opt-In**: QA and auto-fix are disabled by default (backward compatible)
- **Separate Stages**: QA and fix are distinct pipeline stages
- **Return QA Report**: Enables API/CLI to expose validation results
- **Non-Blocking**: Generation succeeds even if QA fails (report indicates issues)

## Alternatives Considered

### Alternative 1: LLM-Based QA

**Approach**: Use LLM to evaluate presentation quality

**Pros**:

- Could detect semantic issues (unclear messaging, poor flow)
- No need to define explicit rules

**Cons**:

- **Cost**: LLM calls for every QA pass would be expensive
- **Latency**: Significantly slower than rule-based checks
- **Non-Deterministic**: Same presentation might get different results
- **Harder to Fix**: LLM feedback is descriptive, not actionable

**Decision**: Rejected. Rule-based approach is faster, cheaper, and more deterministic.

### Alternative 2: Pre-Generation Validation Only

**Approach**: Validate outline/content before slide building

**Pros**:

- Catch issues earlier in pipeline
- Prevent generation of problematic presentations

**Cons**:

- **Incomplete Coverage**: Can't detect layout issues without actual slides
- **No Overflow Detection**: Text capacity depends on actual rendering
- **No Style Validation**: Can't check template conformance without slides

**Decision**: Rejected. Post-generation QA is necessary for comprehensive validation.

### Alternative 3: Manual Fix Only (No Auto-Fix)

**Approach**: QA reports issues, user fixes manually

**Pros**:

- Simpler implementation
- No risk of incorrect automatic fixes
- User maintains full control

**Cons**:

- **Reduced Value**: Users still need manual cleanup
- **Slower Workflow**: Defeats purpose of automation
- **Inconsistent Quality**: Manual fixes vary by user skill

**Decision**: Partially adopted. Auto-fix is optional; users can choose manual fixes.

### Alternative 4: Monolithic QA Engine

**Approach**: Single class with all validation logic

**Pros**:

- Simpler architecture
- Fewer abstractions

**Cons**:

- **Not Extensible**: Adding rules requires modifying engine
- **Hard to Test**: Monolithic class is harder to unit test
- **Tight Coupling**: Rules coupled to engine implementation

**Decision**: Rejected. Registry pattern provides better extensibility and testability.

## Consequences

### Positive

1. **Automated Quality Assurance**: Users get professional-quality presentations without manual inspection
2. **Actionable Feedback**: Specific issue locations and fix suggestions enable quick corrections
3. **Iterative Improvement**: Auto-fix loop progressively resolves issues
4. **Extensibility**: New rules and strategies can be added without modifying core engine
5. **Performance**: Template caching significantly improves repeated generation
6. **Type Safety**: Full type annotations catch errors at development time
7. **Test Coverage**: ≥80% coverage ensures reliability
8. **Backward Compatible**: Existing workflows continue working (QA/fix are opt-in)

### Negative

1. **Increased Complexity**: Three new modules add ~3000 lines of code
2. **Maintenance Burden**: Rules and strategies need updates as requirements evolve
3. **False Positives**: Rule-based approach may flag valid presentations
4. **Fix Limitations**: Not all issues are auto-fixable (e.g., semantic problems)
5. **Performance Overhead**: QA pass adds 1-3 seconds to generation time
6. **Cache Management**: Users need to manage cache directory size

### Neutral

1. **Learning Curve**: Developers need to understand registry and strategy patterns
2. **Configuration**: Users need to decide when to enable QA/auto-fix
3. **Rule Tuning**: Severity thresholds may need adjustment based on user feedback

## Implementation Notes

### Testing Strategy

Following TDD principles (Constitution Principle 1):

1. **Unit Tests**: Each rule and strategy has isolated tests
2. **Integration Tests**: End-to-end QA → Fix → Re-QA cycles
3. **Performance Tests**: QA pass performance on large presentations
4. **Constitutional Tests**: Verify TDD compliance, type safety, coverage

### Performance Optimization

1. **Template Caching**: Manifest caching reduces parsing overhead by ~80%
2. **Lazy Rule Loading**: Rules loaded only when needed
3. **Early Termination**: QA stops on first critical error (optional)
4. **Parallel Rule Execution**: Future optimization for independent rules

### Extensibility Points

1. **Custom Rules**: Implement `QARule` protocol and register
2. **Custom Strategies**: Implement `FixStrategy` protocol and register
3. **Custom Severity**: Extend `Severity` enum for organization-specific levels
4. **Custom Reports**: Subclass `QAReport` for custom formatting

### Migration Path

For existing users:

1. **Phase 1**: QA disabled by default (no impact)
2. **Phase 2**: Users opt-in to QA via `--qa` flag
3. **Phase 3**: Users opt-in to auto-fix via `--autofix` flag
4. **Phase 4**: Consider making QA default in future major version

## References

- [Feature Specification](../../specs/005-editable-pptx-qa/spec.md)
- [Implementation Plan](../../specs/005-editable-pptx-qa/plan.md)
- [QA Engine Implementation](../../src/pptx_agent/qa/engine.py)
- [Fix Engine Implementation](../../src/pptx_agent/fixer/engine.py)
- [Cache Manager Implementation](../../src/pptx_agent/cache/manager.py)
- [Constitution Principle 1: TDD](../../.bob/rules/bobkit/constitution.md#principle-1-test-driven-development-non-negotiable)

## Revision History

- 2026-04-24: Initial version (Accepted)

<!-- Made with Bob -->
