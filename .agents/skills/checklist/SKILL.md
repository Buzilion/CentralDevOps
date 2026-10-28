---
name: checklist
description: "Mark a task as complete on a spec checklist. Can be called directly or by workflows like end-task. Use when closing out a task: 'mark task done', 'check off task 3', 'update checklist'."
user-invocable: true
argument-hint: "<spec-name> <task-number-or-name>"
---

# Checklist

Mark one task complete on a spec checklist. Do not implement, review, or summarize.

## Steps

1. **Resolve args** — Get `<spec-name>` and `<task-number-or-name>` from `$ARGUMENTS` or the calling workflow. If missing, check `/memories/session/` before asking the user.
2. **Validate session** — Confirm the task matches the active session. If it doesn't, warn and ask for confirmation; proceed if the user overrides.
3. **Locate checklist** — Path: `docs/specs/<spec-name>/checklist.md`. If missing, report the exact path and stop.
4. **Mark complete** — Find `- [ ] Task <N>:` by number, or by name substring. If no match, report the search term and full checklist contents, then stop. Replace `[ ]` with `[x]` on that line only.
5. **Confirm** — Save and report the changed line (before → after).

## Rules

- Only mark tasks complete. Never revert `[x]` to `[ ]`.
- Never edit any line other than the matched task entry.