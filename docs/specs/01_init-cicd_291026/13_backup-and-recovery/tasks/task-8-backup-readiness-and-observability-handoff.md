# Task 8: Backup readiness and observability handoff

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Tasks 1–7 |
| Needs | Completed Staging drill evidence and the backup status contract defined in this spec |
| Summary | Write `summaries/task-8-summary.md` when this task closes |

## Goal

Close spec 13 with traceable evidence for each BKP/RTE requirement and hand the stable backup-health signal to spec 14 without claiming its alert work is complete.

## Relevant files or references

- `docs/specs/01_init-cicd_291026/13_backup-and-recovery/checklist.md`
- `docs/specs/01_init-cicd_291026/00_spec-roadmap.md`
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md`
- `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md`
- Spec 14 `observability-and-alerting` (consumer of the backup status contract)

## Proposed approach

1. Review evidence for BKP-01 through BKP-15 and RTE-12 against the spec and task acceptance criteria. Leave any unmet requirement unchecked and state the blocker; do not infer completion from a successful code build.
2. Verify that S3 provider capability results, DNS TTL, 14-day/12-month retention and 12-month deployment-record retention are recorded in the runbook/design variables documentation.
3. Hand spec 14 the status-file schema, permissions, per-class last-good timestamps, failure cases and the exact 8-hour stale threshold. Confirm the monitoring consumer has read-only access.
4. Keep the end-to-end alert and notification evidence assigned to spec 14. The production go-live gate stays blocked until that spec proves the alert reaches its configured recipient.
5. Publish only sanitized commands, run links, dates, timings and changed-file lists in the task summary. Never attach database dumps, snapshots, credentials or runtime values.

## Acceptance criteria

- Every applicable BKP/RTE requirement has an evidence reference or is explicitly left incomplete with a blocker.
- The spec 14 handoff identifies the status contract, 8-hour threshold and stale/missing/failure cases without requiring secret access.
- This task does not mark Production go-live complete. It records the timed restore, S3 verification and DNS evidence and leaves the end-to-end alert proof explicitly pending spec 14.
- The final task summary contains no secret value, database content, private key or sensitive host credential.

## Source reference

BKP-01 to BKP-15; RTE-12; OBS-02, OBS-03 and OBS-05; roadmap specs 13–15 and go-live gates 4–5.

## Verify

- Review the completed checklist and trace every checked item to a test, runbook section or accepted provider evidence.
- Review the status-file contract and prove the planned read-only monitoring identity can read status without write or credential access; spec 14 verifies end-to-end consumption.
- Confirm any missing alert, timed drill, DNS or provider evidence remains an explicit Production blocker.

## Out of scope

Implementing spec 14 dashboards/alerts, authoring spec 15's final go-live gate record, or approving Production readiness.
