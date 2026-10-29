# Task 7: Failure runbook and Staging acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Tasks 1–6; specs 04, 07, 08 and 10 checklists complete |
| Needs | Disposable Staging VPS, throwaway app, controlled test domain and sanitized run evidence |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Prove the deploy and rollback contract end to end on Staging, then document the operator response for failed releases without using a Production service host.

## Relevant files or references

- Create `docs/runbooks/deploy-and-rollback.md`
- `deployment/tools/tests/`
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-08, DEP-09, DEP-11, DEP-12, DEP-14, DEP-15, DEP-17 to DEP-19)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-12)
- Spec 07's Q8 decision and spec 08's database credential rollback contract
- Parent PRD §8 go-live gate 3

## Proposed approach

1. Confirm all direct prerequisite checklists are complete. Use a disposable Staging host and test app; do not use Production credentials or issue a Production certificate.
2. Deploy a healthy digest and verify the exact running digest, health check, route, HTTPS smoke test, route confirmation, host record, central summary and source-run audit correlation.
3. Inject a failing `release_command`; verify the old release keeps serving and route state is unchanged.
4. Inject an unhealthy replacement; verify automatic rollback restores the old image and runtime environment, restores a changed database password first and leaves the route unchanged. Also test a failed first deployment and confirm the app is stopped.
5. Inject an external HTTPS smoke-test failure after route activation; verify the run fails, automatic rollback does not occur and route confirmation is skipped, as required by Q8.
6. Run two same-app requests concurrently and verify host serialization or a clean failure. Run different-app requests concurrently and verify proxy edits/reloads remain serialized without one app cancelling the other's pending run.
7. Use a canary secret in a disposable test bundle and scan Actions logs, summaries and artifacts. Confirm the canary, runtime environment and decrypted bundle are absent.
8. Document diagnosis, central/app/container log review, previous-digest redeploy, the health-check rollback guarantee, the Q8 smoke-test exception, record location and cause recording.
9. Keep the record-backup integration listed for spec 13. Do not claim DEP-14's off-host restore criterion until spec 13's restore drill proves it.

## Acceptance criteria

- Required Staging success, rollback, first-deploy, release-command, smoke-test, concurrency, secret-redaction and audit-correlation cases pass with sanitized evidence.
- The runbook gives operators actionable commands/locations and distinguishes health-check rollback from the no-auto-rollback smoke-test decision.
- No Production host, Production credential or Production certificate is used for this acceptance task.
- Evidence records the test date, disposable host alias, test app/domain, commit/run references and outcomes without secrets or private host data.
- The checklist remains unchecked if any prerequisite, required proof or record field is missing.

## Source reference

DEP-08, DEP-09, DEP-11, DEP-12, DEP-14, DEP-15, DEP-17 to DEP-19; RTE-07, RTE-11; SEC-12; parent PRD §8; v5 §§8.2–8.5, 15.6.

## Verify

- Review sanitized evidence against every invariant in `spec.md`.
- Run workflow lint, name checks, focused tests and the available deployment/Compose checks.
- Confirm the Stage 3 go-live evidence includes a rehearsed health-check rollback and that the smoke-test failure is recorded as a failed run without automatic rollback.

## Out of scope

Production rollout, app onboarding, backup/restore-drill implementation or live database-schema rollback.
