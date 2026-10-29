# Task 7: Production go-live gate record

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Tasks 1-6; evidence from specs 02, 03, 11-14 |
| Needs | Accepted evidence for each parent PRD §8 gate |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Create the durable Production readiness record and verify every parent PRD go-live gate from its owning spec's evidence.

## Relevant files or references

- Create `docs/runbooks/production-go-live-record.md`
- `docs/prd/01_init-cicd_291026/prd-v1.md` §8
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-20, DEP-12)
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-13)
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-08, BKP-10, BKP-13)
- `docs/prd/01_init-cicd_291026/infrastructure-v1.md` (INF-16)
- `docs/prd/01_init-cicd_291026/observability-v1.md` (OBS-05)

## Proposed approach

1. Create a record with one row per gate, the exact pass criterion, `PASS`/`FAIL`/`BLOCKED` status, evidence reference, date, and decision owner.
2. Link Gate 1 to the accepted throwaway-app test; Gate 2 to the disposable-VPS hardening proof; Gate 3 to the successful Staging deployment and rehearsed rollback; Gate 4 to the verified S3 endpoint and timed restore; Gate 5 to active host-down/backup-age alerts and the decided DNS TTL handling.
3. Verify that each link points to sanitized, accepted evidence from the owning spec. Do not infer a pass from a task being marked done if its evidence does not establish the gate.
4. Record the capacity-review state separately: actual review complete at four apps, or `not yet triggered` if fewer than four apps exist. It is not a substitute for or an extra parent PRD gate.
5. If any gate is missing, failed, or inconclusive, leave the record `BLOCKED`/`FAIL` and stop. Update it only when the owning issue is resolved and verified.

## Acceptance criteria

- The record contains all five gates from parent PRD §8 with dated, sanitized evidence references and an accountable decision owner.
- Every gate is `PASS` before the Production readiness decision is recorded as ready.
- No missing or inconclusive evidence is represented as `PASS`.
- The capacity-review state is recorded independently from the five go-live gates.
- The record contains no credentials, secrets, private logs, or plaintext runtime values.

## Source reference

Parent PRD §8; DEP-20, INF-16, REL-13, DEP-12, BKP-08, BKP-10, BKP-13, OBS-05.

## Verify

- Independently follow each evidence reference to its accepted result and confirm it satisfies the exact gate wording.
- Confirm the timed restore result is at most four hours and the required alerts and DNS TTL decision are evidenced.
- Confirm all five statuses are `PASS` before marking this task complete; otherwise keep the task and Production readiness blocked.

## Out of scope

Changing a gate's acceptance criteria, waiving a gate, or implementing the deployment/backup/monitoring controls owned by earlier specs.
