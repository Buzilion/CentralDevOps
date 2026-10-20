---
name: start-task-tdd
description: "Start a task from a spec using TDD: create/switch to spec branch, implement test-first, then run a review loop until all findings are resolved."
user-invocable: true
argument-hint: "<spec-name> [task-name or task-number] — e.g. 'user-auth task 3', 'user-auth implement login endpoint', or just a path to the spec.md file"
---

# Start Task (TDD)

Orchestrate a full TDD implement-review cycle for one spec task. Work autonomously through all steps and report at the end.

## Workflow

### 1. Locate the Task

- **Path to `spec.md`** (e.g. `docs/specs/user-auth/spec.md`) → `<spec-name>` is the parent directory name (e.g. `user-auth`). Read `docs/specs/<spec-name>/checklist.md`, find the first unchecked task (`[ ]`), and report which task was selected.
- **Spec name + task reference** → find spec at `docs/specs/<spec-name>/`.

Then:
- Read `docs/specs/<spec-name>/spec.md` (context, invariants), `docs/specs/<spec-name>/tasks/task-[n]-[task-name].md` (requirements, acceptance criteria), and `docs/specs/<spec-name>/checklist.md` (confirm not already complete — stop if it is).
- If `docs/specs/<spec-name>/summaries/task-[n]-summary.md` exists, read it for prior decisions and constraints.

### 2. Branch

Use the **branch** skill: create or switch to `feature/<spec-name>`. One branch covers all spec tasks. Report branch name and any existing uncommitted work.

### 3. Implement (TDD)

**3a. Plan** (`implement` Steps 1–2) — map affected files, contracts, and acceptance criteria; choose the smallest complete change; call out contract changes before writing code.

**3b. Red → Green → Refine** (`tdd` Steps 2–4):
- **Red** — write the smallest failing test for the desired behavior; run it; confirm it fails for the right reason. No implementation code before this.
- **Green** — minimum implementation to pass the test; add failure-path tests where they matter.
- **Refine** — simplify while green; run the full relevant test suite.

**3c. Verify + Report** (`implement` Steps 5–6) — run full project checks (lint, type, integration); fix issues within scope; update issue tracker to ready-for-review when available.

Do not enter review until all tests are green and 3c passes.

### 4. Review Loop

Repeat until zero actionable findings:
- **4a.** Run the **review** skill on all changes since branch start.
- **4b.** Address each finding with targeted edits; re-run full test suite (must stay green); repeat 4a.
- **4c.** Zero findings → exit loop.
- **4d.** After 3 passes without convergence → stop and report remaining findings for user guidance.

### 5. Report

- What was implemented, Red → Green → Refine outcome, review cycle count, final clean-review status.
- Deferred findings (out-of-scope issues) for later attention.
- Remind user: run **end task `<spec-name> <task-name>`** to update checklist and save summary.

## Rules

- One task per invocation; never batch checklist items.
- Auto-select always picks the first unchecked task — never skip ahead.
- No implementation code before a failing test exists for the behavior.
- Do not update the checklist or write summaries — that is `end-task`'s job.
- Do not use review findings as an excuse for unrelated refactors.
- For docs, formatting, or non-behavioral scaffolding: skip TDD, use **implement**, note the exception in the report.
