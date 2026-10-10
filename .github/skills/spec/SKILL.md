---
name: spec
description: "Write an implementation spec to docs/<feature-slug>/spec.md and pause for human review. Use when the user says \"write a spec\", \"spec this out\", \"technical design\", \"design doc\", or when a task has decisions, invariants, or contracts that should be reviewed before code is written."
user-invocable: true
argument-hint: "<feature description, context, or constraints>"
---

# Spec

You are a principal engineer writing a technical spec for an AI agent to execute. Cover what we are building, why it matters, and how to build it safely. The spec combines requirements and technical design: one document, one read.

## Workflow

### 1. Align

- Treat the full argument as the request unless the user names a feature.
- Derive a kebab-case feature slug if no name is given.
- Confirm the project root and create `docs/` if needed; ask where specs should live only if the repo uses a different docs convention.
- Read referenced files and relevant code so the spec fits the project as it exists.
- Identify decisions, dependencies, invariants, contracts, and error behavior that need review before coding.
- When the spec introduces or pins external runtimes, services, frameworks, or dependencies, check the current stable or LTS version from official sources when possible.
- If code can answer a question, inspect the code instead of asking.
- Ask only when a missing decision would materially change the spec.
- Ask one question at a time, with your recommended answer.
- Continue only when the spec can be written without guessing.

### 2. Write

Write `docs/<feature-slug>/spec.md` using the sections below. Tailor detail to the task: keep simple specs short, expand only where decisions, invariants, or interfaces need review.

- **What**: one-paragraph summary.
- **Context**: why this matters, what exists today, links to relevant code.
- **Requirements**: specific, testable statements of what the system must do.
- **Design**: the chosen approach: components, data flow, interfaces, file changes. Describe logic as plain-English algorithmic steps ("1. Validate input, 2. Look up record, 3. ..."), not code. A short code block is allowed only to pin an exact contract (e.g. a function signature, type, or schema) that must not be paraphrased — never for illustrating logic or flow.
- **Decisions**: choices the agent would otherwise make alone. For each, state the choice, alternatives considered, why this one, and whether it is reversible. Mark assumptions as `Assumption:`.
- **Versions** *(when relevant)*: runtimes, services, frameworks, and dependencies the implementation relies on, with the current stable/LTS choice and source.
- **Invariants** *(when relevant)*: what must not break, and how to check it.
- **Error Behavior** *(when relevant)*: failure paths, error shapes, recovery.
- **Testing Strategy**: what proves the change works.
- **Out of Scope**: what this spec deliberately does not cover.

### 3. Pause

After writing, print:

```text
Spec written to docs/<feature-slug>/spec.md
Review and reply "approve" to proceed, "edit" to revise, or leave feedback.
```

Then stop. Do not plan, implement, or run further tools until the human responds.

## Rules

- Smallest safe change that fully solves the problem.
- If two implementations would behave differently, specify the default.
- Match existing patterns in the codebase. If the spec proposes a new pattern, justify it explicitly.
- Write for a human who will read this in six months and has forgotten the thread.
- Default to one spec for the requested scope, even if it touches several files or steps. Only create more than one spec.md when the request itself spans multiple independently shippable features or unrelated domains (e.g. two separate PRDs) — never simply because the work has multiple parts, layers, or steps.
- Keep it as tight as possible: include only what an implementing agent needs to act without guessing. Omit sections that don't materially change the implementation, and don't restate context the codebase already makes obvious.
- If the spec is getting long because it covers many steps of one feature, that belongs in **plan** (task breakdown), not in a second spec. Split into tasks, not into more specs.
