# Task 6: Deployment records and run summaries

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Tasks 2–5 |
| Needs | Staging deployment attempts with success, health failure and smoke-test failure outcomes |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Write a durable secret-free host record for each authorized host attempt and expose the same sanitized outcome in the central run and the spec 12 caller handoff.

## Relevant files or references

- `deployment/scripts/centraldevops-deploy`
- `.github/workflows/deploy-app.yml`
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-14, DEP-15, DEP-17)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-12)
- v5 design §§8.3, 13.4
- Spec 12's planned `request-deploy` result consumer; spec 13's planned backup inclusion

## Proposed approach

1. Write one root-owned JSON record at `/var/lib/centraldevops/deployments/<app>/<environment-path>/<source-run-id>-<attempt>.json` for each authorized attempt that invokes the host entrypoint.
2. Include app, Environment, requested and previous digest, source commit, source run ID/attempt, central run URL, UTC timestamp, result and a sanitized failure phase. Use `null` for the previous digest on a first deployment.
3. Start the record in a non-success state before host mutation and promote it to success only after the runner-side smoke test and any required route confirmation succeed. A failed stage, failed smoke test or interrupted finalization must never leave a success result.
4. Allow finalization only for the matching run/attempt and only through the existing root-owned entrypoint. Do not permit arbitrary record rewrites or secret-bearing fields.
5. Keep pre-authorization rejections and local preflight failures that never connect to a host in the central Actions history; do not open a host-write path for them.
6. Write a central Actions run summary and a separate `deployment-summary.json` handoff with the full sanitized DEP-14 field set. Spec 12 consumes the handoff to render the app-run summary.
7. Canary-scan logs, summaries and artifacts. Keep sealed/decrypted bundle data, `.env`, runtime values, credentials and private host data out of every summary and artifact.
8. Register the record directory with spec 13 as deployment data that must be backed up after each deployment and restored during the restore drill.

## Acceptance criteria

- Successful, failed-health, failed-smoke and interrupted host attempts have a durable record with the required fields and no secret values.
- The final record result is `success` only when the whole deployment, including HTTPS smoke test and route confirmation, succeeds.
- The central Actions summary and `deployment-summary.json` agree with the host record and identify the same source app run/attempt.
- The app-side summary handoff contains the full DEP-14 field set without runtime environment contents; spec 12 renders it in the app run.
- A pre-authorization rejection does not contact the host or create a host record.
- The record path, owner/mode and backup handoff are documented for spec 13. Off-host restore is not claimed complete until spec 13's drill passes.

## Source reference

DEP-14, DEP-15, DEP-17; SEC-12; v5 §§8.3, 8.5, 13.4.

## Verify

- Compare record, central summary and handoff fields for healthy and failing Staging attempts.
- Confirm the record is root-owned, atomically written, not deploy-writable and contains no credentials.
- Canary-scan workflow logs and all generated artifacts; verify the sealed bundle and runtime environment are absent.

## Out of scope

App-side summary rendering (spec 12), backup implementation or record restoration (spec 13), and records for requests rejected before host execution.
