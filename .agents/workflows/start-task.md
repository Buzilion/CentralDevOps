---
name: start-task
description: "Start a task from a spec: create/switch to spec branch, implement, then run a review loop until all findings are resolved."
user-invocable: true
argument-hint: "<spec-name> [task-name or task-number] — e.g. 'user-auth task 3', 'user-auth implement login endpoint', or just a path to the spec.md file"
---

# Start Task

You are orchestrating a full implement-review cycle for one task from a spec. Work autonomously through all steps below and report at the end.

## Workflow

### 1. Locate the Task

**If the user provided a path to a `spec.md` file** (e.g. `docs/specs/user-auth/spec.md`), derive `<spec-name>` from it and auto-select the task:
- Read `docs/specs/<spec-name>/checklist.md` and find the first unchecked task (`[ ]`).
- That is the task to work on. Report which task was selected.

**If the user provided a spec name and task reference**, find the spec at `docs/specs/<spec-name>/`.

Once `<spec-name>` and task are identified:
- Read `docs/specs/<spec-name>/spec.md` for overall context, decisions, and invariants.
- Read the task file at `docs/specs/<spec-name>/tasks/task-[n]-[task-name].md` for the specific requirements, acceptance criteria, and implementation notes.
- Read `docs/specs/<spec-name>/checklist.md` to confirm the task is not already marked complete. If it is, stop and report.
- Check `docs/specs/<spec-name>/summaries/` for a previous summary file matching `task-[n]-summary.md`. If it exists, read it for prior context (decisions made, deferred findings, known constraints). If it does not exist, continue without it.

### 2. Create or Switch to the Spec Branch

- Use the **branch** skill to create or switch to a branch scoped to the entire spec (not per-task): `<spec-name>-tasks` or `feature/<spec-name>`.
- One branch covers all tasks in the spec. If the branch already exists, switch to it.
- Report the branch name and any uncommitted work already present.

### 3. Implement

- Use the **implement** skill for the identified task.
- Complete all steps: understand, plan, implement, test, verify, report.
- Do not move to review until the implement skill's verification passes.

### 4. Review Loop

Repeat until the review returns zero actionable findings:

**4a.** Use the **review** skill on the changes made since the branch started.
**4b.** If findings exist:
  - Address each actionable finding with targeted edits. Stay within the task's scope.
  - Re-run relevant tests and checks.
  - Go to step 4a.
**4c.** If no actionable findings remain, exit the loop.
**4d.** If the loop exceeds 3 passes without converging, stop and report the remaining findings to the user for guidance.

### 5. Report

- Summarize: what was implemented, how many review cycles ran, and the final clean-review outcome.
- List any deferred findings (out-of-scope issues discovered during review) for later attention.
- Remind the user: when satisfied, run **end task `<spec-name> <task-name>`** to update the checklist and save the session summary.

## Rules

- One task per invocation. Do not batch multiple checklist items. Unless the user explicitly asked to work on multiple tasks in one session.
- When auto-selecting from a spec.md path, always pick the first unchecked task — never skip ahead.
- Do not update the checklist or write session summaries here — that is `end-task`'s job.
- Do not commit any changes here — committing is `end-task.md`'s workflow job.
- Resolve implement-skill scope questions before entering the review loop.
- Do not use review findings as an excuse for unrelated refactors.
