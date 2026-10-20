---
name: documentation
description: Generate orientation-first codebase documentation — architecture summaries, data flow narratives, domain glossaries, and Mermaid diagrams — for engineers trying to understand a system. Use this skill whenever the user says "document this codebase", "generate docs", "explain the architecture", "create a technical overview", "what does this system do", "write up how this works", "document this service", or when they want any form of written technical documentation that helps someone understand a codebase. Also trigger when the user shares a repo or file tree and asks for an explanation. Do NOT wait for the user to say "documentation skill" explicitly — if they want to understand or document a codebase, use this.
---

# Documentation Skill

`Detect workspace structure → Explore code → Generate docs + diagrams`

Write for **an engineer understanding the system**, not an API integrator. Bias toward prose and Mermaid diagrams. Never enumerate every function or route — explain purpose instead.

---

## Step 1: Detect Workspace Structure

- **Multiple `package.json` / `pyproject.toml` at root** → monorepo; cross-reference actual imports before inferring relationships
- **Single manifest** → single service; infer consumers from public API surface and domain naming
- **IaC (Terraform / Bicep / ARM)** → generate service dependency maps, topology, and network boundaries

Use `list_dir`, `file_search`, `grep_search` to map entry points, modules, and test structure before reading code.

---

## Step 2: Explore the Code

Read enough to understand the *system*, not every file. Focus on:
- Entry points (server bootstrap, CLI)
- Domain modules and data models
- Auth, logging, error handling patterns
- External integrations (DBs, queues, third-party services)
- Git history — commit messages reveal *why* decisions were made; use for legacy constraints and non-obvious design choices

---

## Step 3: Generate the Documentation

Write to `docs/documentation.md`. Use this structure:

```markdown
# [System Name] — Technical Overview

## What This Is
One paragraph: problem solved, domain.

## Architecture Summary
Prose + Mermaid diagram of major components.

## Data Flow
End-to-end narrative of the primary operation + Mermaid sequence or flowchart.

## What This System Owns
Source-of-truth data/state/processes. What it delegates externally.

## Dependencies
External services, DBs, queues this system calls.

## Domain Glossary
Domain-specific terms defined in plain language.

## Potential Consumers
Inferred consumers (see rules below).
```

---

## Consumer Inference Rules

Infer from exported interfaces, event emissions, domain naming, and auth patterns. Only surface domain-specific, non-obvious inferences.

> ❌ *"This REST API could be consumed by a frontend or mobile app."*
> ✅ *"Given the shift management domain and write-heavy mutation pattern, this is likely consumed by an operations dashboard — not a reporting layer."*

Establish the domain first before inferring consumers.

---

## Mermaid Diagram Types

- `graph LR/TD` — service dependencies, module relationships
- `sequenceDiagram` — request/response flows
- `erDiagram` — data models
- `flowchart` — decision logic, state machines

One diagram per concern. IaC workspaces also get a resource ownership table.

---

## Quality Check

- [ ] An unfamiliar engineer understands what it does after reading
- [ ] At least one architecture diagram included
- [ ] At least one data flow written in prose
- [ ] Glossary covers terms a newcomer wouldn't know
- [ ] Consumer inferences are domain-specific, not generic
- [ ] No exhaustive function/endpoint listings
