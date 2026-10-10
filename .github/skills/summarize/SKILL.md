---
name: summarize
description: "Produce a rolling task summary at the end of a task session. Applies semantic compression to the previous summary (preserving decisions, constraints, and deferred findings), then appends the current task's full summary. Output is the authoritative context file for the next AI session. Use when the user or a workflow says 'summarize', 'end task', 'write session summary', or when a task session is wrapping up."
user-invocable: true
argument-hint: "<spec-name> <task-number> <task-name>"
---

# Summarize

Produce `task-[n]-summary.md` — the authoritative context file for the next AI session.

## Workflow

### 1. Locate previous summary

Check `docs/specs/<spec-name>/summaries/` for `task-[n-1]-summary.md`.

- If it exists, read it fully. It will be rolled into the new file.
- If it does not exist, this is the first task — skip rolling and write the current summary only.

### 2. Write the current task section (uncompressed)

Compression applies to the past only — write this section in full.

```
## Task [n]: [task-name] — [one-line description]

### What was implemented
Key files created/modified and why. Omit throwaway or scaffolding edits.

### Review findings addressed
*(Omit if no review ran.)*
Each finding and how it was resolved.

### Current state
One paragraph: what modules, endpoints, models, or flows now exist. Supplements the spec — do not restate it.

### Deferred findings
Out-of-scope issues for future tasks. Write "None." if empty.
```

### 3. Compress the previous summary

Preserve: decisions + rationale, unresolved deferred findings, constraints/gotchas, key modules/files established, locked-in tech choices.

Drop: resolved review findings, step-by-step implementation detail (reduce to one line per task), test output (unless it revealed a lasting constraint).

Label the result:
```
## History (tasks 1–[n-1], compressed)
```

### 4. Write the file

`docs/specs/<spec-name>/summaries/task-[n]-summary.md`:
```
## History (tasks 1–[n-1], compressed)   ← omit if task 1

## Task [n]: [task-name] — [one-line description]
### What was implemented
### Review findings addressed             ← omit if no review ran
### Current state
### Deferred findings
```

Never overwrite previous summary files.

## Rules

- Deferred findings survive rolling compression until explicitly resolved.
- Confirm task number against the spec or checklist before writing.
- Capture codebase facts and decisions only — no conversation meta-commentary.