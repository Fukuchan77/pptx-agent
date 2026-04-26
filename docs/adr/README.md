# Architecture Decision Records (ADR)

## Overview

This directory contains Architecture Decision Records (ADRs) for the AI PowerPoint Presentation Generator project.

ADRs are a lightweight method for documenting technical decisions, their context, rationale, and consequences. Each ADR provides complete information about a specific decision, enabling future developers and stakeholders to understand the background of past decisions.

## What are ADRs?

Architecture Decision Records are documents that record important decisions related to software architecture. Each ADR includes:

- **Title**: A concise description of the decision
- **Status**: Proposed, Accepted, Rejected, Deprecated, etc.
- **Context**: Background and circumstances that necessitated the decision
- **Decision**: Details of the adopted solution
- **Consequences**: Results of the decision (positive, negative, mitigations)
- **Alternatives**: Options considered but not adopted, and their reasons

## Format

ADRs in this project are based on [Michael Nygard's ADR template](https://github.com/joelparkerhenderson/architecture-decision-record).

## ADR List

| Number                                               | Title                                           | Status   | Date       |
| ---------------------------------------------------- | ----------------------------------------------- | -------- | ---------- |
| [0001](0001-template-generation-plan-b.md)           | Template Generation Strategy - Plan B (Manual)  | Accepted | 2026-04-05 |
| [0002](0002-config-test-isolation-and-validation.md) | Config Test Isolation and Validation            | Accepted | 2026-04-14 |
| [0003](0003-qa-architecture.md)                      | QA Framework Architecture                       | Accepted | 2026-04-15 |
| [0004](0004-template-caching.md)                     | Template Manifest Caching Strategy              | Accepted | 2026-04-16 |

## ADR Creation Guidelines

When creating a new ADR, follow these guidelines:

### 1. File Naming Convention

```
XXXX-brief-title.md
```

- `XXXX`: 4-digit sequential number (e.g., 0001, 0002)
- `brief-title`: Brief English title in kebab-case
- Example: `0002-llm-provider-selection.md`

### 2. Required Sections

Each ADR must include the following sections:

```markdown
# ADR XXXX: Title

## Status

[Proposed | Accepted | Rejected | Deprecated | Superseded]

## Context

Background, problem, and constraints that necessitated the decision

## Decision

Details of the adopted solution

## Consequences

### Positive Consequences

### Negative Consequences

### Mitigations

## Alternatives Considered

### Alternative 1: ...

### Alternative 2: ...

## References

Links to related documents, code, and external resources
```

### 3. When to Create ADRs

Create ADRs in the following situations:

- **Technology Stack Selection**: Choosing libraries, frameworks, platforms
- **Architecture Pattern Adoption**: Microservices, monolith, layered architecture, etc.
- **Important Design Decisions**: Data models, API design, security strategy, etc.
- **Trade-off Decisions**: Performance vs. maintainability, etc.
- **Policy Changes**: Overriding or modifying existing decisions

### 4. Creation Process

1. **Determine Number**: Check the latest ADR number and use the next sequential number
2. **Create Draft**: Create a draft following the template
3. **Review**: Team member review
4. **Approval**: Change status to "Accepted"
5. **Update README**: Add the new ADR to the ADR list in this README

### 5. Best Practices

- **Conciseness**: Write each section clearly and concisely
- **Objectivity**: Base decisions on technical facts and trade-offs, not emotions or subjective opinions
- **Completeness**: Provide sufficient information for future readers to understand the decision background
- **Timeliness**: Record immediately after the decision is made (while memory is fresh)
- **Immutability**: Do not modify ADRs after approval (supersede with new ADRs instead)

## ADR Status Transitions

```
Proposed → Accepted → [Deprecated | Superseded]
         ↓
       Rejected
```

- **Proposed**: Under proposal, under discussion
- **Accepted**: Approved and used in implementation
- **Rejected**: Rejected (with reasons documented)
- **Deprecated**: Deprecated (better method found but still in use)
- **Superseded**: Replaced by a new ADR (specify the replacement ADR)

## Frequently Asked Questions (FAQ)

### Q: Do all technical decisions need to be ADRs?

A: No. ADRs are for **important** architecture decisions. The following are worth recording:

- Decisions that affect project direction
- Decisions that are difficult to change
- Decisions involving trade-offs
- Decisions that require team-wide understanding

Daily implementation details (variable names, file placement, etc.) do not need to be ADRs.

### Q: Can ADRs be modified later?

A: Approved ADRs **should not be modified**. ADRs are historical records. If you need to change a decision, create a new ADR and mark the old ADR as "Superseded".

Minor corrections (typos, link fixes, etc.) are permitted, but changes to the decision content itself should be made in a new ADR.

### Q: Should I write in Japanese or English?

A: In this project, ADRs are written in **English**. This follows the project standard. However, the following elements can use Japanese:

- Comments in code examples (if needed for clarity)
- Technical terms (with English explanations as needed)

### Q: Should rejected alternatives also be recorded?

A: Yes, **they must be recorded**. Recording rejected alternatives and their reasons:

- Prevents repeating the same discussions
- Allows re-evaluation when circumstances change in the future
- Enables complete understanding of the decision background

## Reference Resources

- [Architecture Decision Records (ADR) by Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [Joel Parker Henderson's ADR Templates](https://github.com/joelparkerhenderson/architecture-decision-record)
- [Documenting Architecture Decisions - ThoughtWorks](https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records)

## Contributing

Project members are encouraged to create ADRs when making important architecture decisions. For questions or suggestions, please refer to the project's main README.

---

**Last Updated**: 2026-04-26
**Maintainer**: AI PowerPoint Generator Project Team