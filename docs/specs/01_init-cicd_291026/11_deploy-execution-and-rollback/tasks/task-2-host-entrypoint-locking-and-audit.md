# Task 2: Host entrypoint, locking and audit

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Task 1; specs 04, 07, 08 and 10 checklists complete |
| Needs | Disposable Staging VPS with the spec 04 restricted deploy runtime |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Replace the fail-closed deploy stub with a narrowly scoped host execution boundary that serializes app changes and correlates the host audit trail to the authorized source run.

## Relevant files or references

- `deployment/scripts/centraldevops-deploy`
- `deployment/scripts/centraldevops-route` (use the spec 07 implementation and shared proxy lock)
- `roles/deploy_runtime/` and its sudo/SSH audit configuration from spec 04
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-09, DEP-17)
- v5 design §§8.4–8.5

## Proposed approach

1. Preserve the exact entrypoint path, root ownership, non-deploy-writable mode and sudo allow-list from spec 04. Do not add general shell, Docker or additional sudo access.
2. Define a constrained `centraldevops-deploy` operation/input contract for the authorized plan, validated files and safe source-run metadata. Reject unknown fields, malformed IDs, unsafe paths, symlinks, unexpected owners/modes and caller-selected commands.
3. Derive all app, Environment, project and release paths from the validated plan and the naming conventions; never accept arbitrary host paths or Compose project names.
4. Acquire a root-controlled `flock` keyed by app and Environment before changing that app's state. Allow independent apps to proceed concurrently.
5. Call spec 07's route entrypoint for route changes; rely on its shared lock for all proxy edits/reloads, including Certbot renewal. Do not implement a second proxy lock.
6. Add sanitized SSH/sudo and host deployment events that correlate source run ID/attempt and central run identity. Never log bundle contents, runtime values, credentials or private host data.

## Acceptance criteria

- `cdo-deploy` remains outside the Docker group and can invoke only the approved root-owned entrypoints.
- Malformed or path-traversal inputs fail before host state changes.
- Concurrent deployments of the same app and Environment serialize or fail explicitly; different apps can proceed without simultaneous proxy edits/reloads.
- Host SSH/sudo audit events can be matched to the same source app run recorded by the deployment attempt.
- No runtime value or secret appears in command arguments or audit output.

## Source reference

DEP-09, DEP-17; INF-12, INF-13; RTE-11; v5 §§8.4–8.5.

## Verify

- Test valid and invalid entrypoint inputs as `cdo-deploy` on a disposable VPS.
- Run overlapping same-app and different-app deployment attempts and inspect lock behavior and proxy reload events.
- Review sudoers, entrypoint ownership/modes, SSH/sudo logs and direct Docker access as `cdo-deploy`.

## Out of scope

Workflow authorization, app release execution, health checks or route rendering (specs 07, 10 and later tasks in this spec).
