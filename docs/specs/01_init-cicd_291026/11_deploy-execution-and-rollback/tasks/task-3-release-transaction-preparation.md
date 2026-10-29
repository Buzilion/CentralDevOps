# Task 3: Release transaction preparation

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Task 2; specs 06, 08 and 10 checklists complete |
| Needs | Validated registry/manifest/Compose fixtures and a disposable Staging app |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Prepare a release transaction from only validated inputs, preserve the current release before changes and integrate the shared database and optional release-command contracts.

## Relevant files or references

- `deployment/scripts/centraldevops-deploy`
- `deployment/scripts/lib/centraldevops_database.py` from spec 08
- `deployment/tools/tests/`
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-10, DEP-11, DEP-19)
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-04, DB-05)
- v5 design §§8.3, 9.4 and 11.3

## Proposed approach

1. Revalidate the authorized plan, rendered Compose input and runtime-key set at the host boundary. Derive the stable project name and `/opt/apps/<app>/<environment-path>/` location; reject any mismatch.
2. Pull only the requested immutable image digest. Confirm the rendered app service uses that exact digest before replacing any container.
3. Snapshot the previous `compose.env`, `compose.yml` and image reference under `previous/` before modifying the current release. Treat the absence of a previous release as an explicit first-deploy state.
4. If the registry enables shared database provisioning, call the spec 08 module with registry-owned identity values and the validated runtime password. Do not log, echo or pass a password in command arguments.
5. When a validated manifest declares `release_command`, run it exactly once with the new image before replacing the current containers. A failure aborts replacement and route activation; do not retry the command automatically.
6. If database credentials changed and any pre-replacement step fails, restore the previous database password before restoring the previous runtime environment. Do not claim that a database schema migration was rolled back.
7. Keep the runner-side decrypted bundle in a restricted temporary directory, mask its secrets, remove it after the run and never upload it. Host runtime files must remain restricted and must never be printed.

## Acceptance criteria

- The new app service image in rendered Compose matches the authorized digest exactly.
- The complete previous release state is preserved before any app replacement.
- Shared database provisioning uses the spec 08 interface and remains idempotent when values are unchanged.
- A successful optional `release_command` is invoked once before replacement.
- A failing optional `release_command` leaves the previous app running and the route untouched; changed DB credentials are restored before the previous runtime environment.
- No runtime environment contents or canary secret values appear in logs, command arguments or artifacts.

## Source reference

DEP-10, DEP-11, DEP-19; DB-04, DB-05; SEC-12; v5 §§8.3, 9.4, 11.3.

## Verify

- Run focused tests for digest enforcement, path/input validation, previous-state capture and database-module integration.
- Exercise both an absent and a present `release_command`; inject a failing command and verify the current release remains serving.
- Canary-scan logs, artifacts and test output; inspect host runtime-file permissions without displaying file contents.

## Out of scope

Container health waiting and automatic post-replacement rollback (Task 4), route activation (Task 5) or database schema migration ownership.
