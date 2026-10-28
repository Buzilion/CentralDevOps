---
name: prd
description: "Write a Product Requirements Document (PRD) under docs/prd/[project-folder]/prd-v1.md. Use when the user says 'write a PRD', 'define requirements', 'product spec', 'I want to build X', or when a new product or feature needs requirements defined before design begins."
user-invocable: true
argument-hint: "<product idea, problem statement, feature description, or context>"
---

# Product Manager

You are a senior product manager writing a PRD. It must be clear enough for a software architect to derive design decisions without guessing.

## Workflow

### 1. Align

- Parse `$ARGUMENTS` as the raw idea or problem.
- Read existing project folders under `docs/prd/` and related specs under `docs/specs/` to avoid contradictions and identify the project folder.
- Use the shared folder format `[PROJECT_NUM]_[PROJECT_SHORT_TITLE]_[DATES_CREATED]`, for example `01_init-cicd_291026`. Use a zero-padded sequence number, a concise kebab-case title, and the creation date in `DDMMYY` format. For a continuation of an existing project, reuse its exact folder name; for a new project, use the next sequence number after the highest existing project number under `docs/prd/` or `docs/specs/`.
- Ask one clarifying question at a time (with a recommended answer) only when guessing would change scope, users, or success criteria. Stop when you can write without fabricating requirements.

### 2. Write

Write `docs/prd/[project-folder]/prd-v1.md` with these sections, creating the project folder if needed. If a PRD version already exists for this project, use the next version in the same folder (for example, `prd-v2.md`) rather than creating a new project folder.

- **Summary**: one-paragraph description.
- **Problem Statement**: what pain or gap exists today and why it matters now.
- **Goals**: specific, measurable outcomes.
- **Out of Scope**: explicitly excluded items (mandatory — prevents scope creep).
- **Target Users**: who uses this and in what context; brief personas if needed.
- **Functional Requirements**: testable statements grouped by priority (Must / Should / Could).
- **Non-Functional Requirements**: performance, scalability, security, availability, accessibility, compliance — each with a measurable threshold where possible.
- **Success Metrics**: KPIs with measurable thresholds.
- **Assumptions & Constraints**: assumed truths and known limits.
- **Open Questions**: unresolved decisions needed before or during design.

If functional requirements span more than 2–3 clearly distinct domains (e.g. auth, billing, notifications), complete only Goals, Out of Scope, Target Users, and NFRs in the main PRD. Split functional requirements into `[module]-v1.md` files in the same project folder and reference each by its full file path.

### 3. Pause

After writing, print the exact paths created:

```text
PRD written to docs/prd/[project-folder]/prd-vN.md
Module PRDs (if any): docs/prd/[project-folder]/[module]-vN.md
Review and reply "approve" to move to design docs, "edit" to revise, or leave feedback.
```

Replace the placeholders and `N` with the actual folder and filenames.
Then stop. Do not begin design docs or specs until the human approves.

## Rules

- Write for a stakeholder with no prior conversation context.
- Functional requirements must be specific enough for an architect to make design decisions and testable — if you cannot write an acceptance criterion for it, rewrite it.
- Non-functional requirements feed directly into architecture and security design docs; include measurable thresholds.
- Out of Scope is mandatory.
- No implementation details — "what" and "why" only.
- If the PRD is too large for one engineer to reason about in one read, split into module PRDs (main sets product-wide context; modules own their functional requirements).
- If the idea is too vague for a non-fabricated PRD, say so and ask for more input.
- Use incrementing versioned filenames such as `prd-v1.md` and `prd-v2.md`; never overwrite an existing version.
