---
name: end-task
description: "Close out a completed task: mark the spec checklist and write a session summary."
user-invocable: true
argument-hint: "<spec-name> <task-name or task-number> — e.g. 'user-auth task 3'"
---

# End Task

You are closing out a task after its implement-review cycle is clean. Do not implement or edit code here.

## Workflow

### 1. Confirm Completion

- Verify the task was implemented and the review loop ended with no open findings.
- If there are unresolved review findings, warn the user and stop. Do not close out an unfinished task.

### 2. Update Checklist

- Invoke the **checklist** skill, passing `<spec-name>` and `<task-number-or-name>` as arguments.
- The checklist skill handles locating the file, matching the task, and marking it complete.

### 3. Write Session Summary

- Invoke the **summarize** skill, passing `<spec-name>`, `<task-number>`, and `<task-name>` as arguments.
- The summarize skill handles locating previous summaries, rolling compression, and writing the file to `docs/specs/<spec-name>/summaries/task-<task-number>-summary.md`.

### 4. Commit

- Invoke the **commit** skill to stage and commit all changes made during the task.

### 5. Report

- Confirm the checklist was updated (show the line that changed).
- Confirm the summary path.
- List the remaining unchecked tasks on the checklist so the user knows what comes next.

## Rules

- Do not edit implementation files during end-task.
- Do not close a task with open review findings.
- If the spec folder or checklist does not exist at the expected path, report the exact path checked and stop.
- Create the summaries folder if it does not exist; do not create the entire spec folder structure.
