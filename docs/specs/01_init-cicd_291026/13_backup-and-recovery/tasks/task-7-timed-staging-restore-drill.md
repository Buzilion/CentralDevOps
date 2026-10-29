# Task 7: Timed Staging restore drill

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Tasks 1–6; specs 08, 11 and 12 checklists complete |
| Needs | Disposable Staging replacement target, current Staging S3 credentials and a controlled test domain |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Prove the S3 endpoint, restore path and disaster-recovery runbook end to end on an isolated Staging target within the 4-hour RTO.

## Relevant files or references

- `docs/runbooks/backup-and-disaster-recovery.md`
- `playbooks/restore-database.yml`
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-08 to BKP-11)
- Parent PRD go-live gate 4
- v5 §§13.2–13.3

## Proposed approach

1. Use a disposable replacement target isolated from the live Staging and Production hosts. Confirm the target and credentials are Staging-only before starting the timer.
2. Execute the runbook from the declared recovery start through database and approved app-data restore, digest-based redeploy, host verification and HTTPS smoke test. Use a controlled test domain and the CA staging endpoint; do not change Production DNS.
3. Record every step's start/end time, restore point, app digest source and sanitized result. Note any production-only DNS or CA difference explicitly; do not omit a required recovery step and still claim the 4-hour target passed.
4. Verify the latest Staging S3 backup can be opened, all expected databases/global objects and durable app data are present, deployment records resolve to the expected digest, and the recovered app passes its health/smoke checks.
5. Preserve live Staging data and clean up only the named disposable resources after evidence is captured.

## Acceptance criteria

- The isolated restore completes from the Sumopod S3 Restic repository and proves the endpoint, repository password and restore procedure.
- The drill restores PostgreSQL and an approved app-data marker, redeploys by an immutable digest and passes host/app verification.
- Total measured elapsed time is at most 4 hours, with step-level timings and no silently excluded mandatory step.
- The live Staging and Production services, credentials and DNS records are not changed by the drill.
- Sanitized evidence records the date, run/commit references, target alias, backup timestamp, digest sources, timings and outcomes without secrets or private host data.

## Source reference

BKP-08 to BKP-11; parent PRD NFR-01, NFR-03 and gate 4; v5 §§13.2–13.3.

## Verify

- Compare the drill evidence against every runbook step and each BKP-08 to BKP-11 acceptance criterion.
- Confirm restored database inventories, durable-data marker, digest and successful smoke-test output.
- Review elapsed-time sum and check the recorded S3 restore came from the expected Staging repository.
- Confirm disposable resource cleanup did not include broad or unresolved paths.

## Out of scope

Restoring onto a live host, exercising Production S3 or credentials, changing Production DNS, or issuing a Production certificate.
