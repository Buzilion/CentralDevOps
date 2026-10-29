# Task 4: Retention and backup-health contract

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Tasks 2 and 3 |
| Needs | Disposable Restic repository and the spec 05 verification workflow |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Enforce the selected retention policy, expose secret-free per-class backup results and make stale backups fail host verification.

## Relevant files or references

- `roles/backup/`
- `playbooks/verify.yml` and `.github/workflows/verify-vps.yml`
- `docs/design/variables-and-secrets.md` (BACKUP retention variables)
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-06, BKP-07)
- `docs/prd/01_init-cicd_291026/observability-v1.md` (OBS-02, OBS-03, OBS-05)

## Proposed approach

1. Retain the complete 14-day snapshot window and 12 monthly recovery points. Keep `BACKUP_RETENTION_DAYS=14` and add Environment-scoped `BACKUP_RETENTION_MONTHS=12`; update the variable contract.
2. Serialize backup, repository check and prune operations. Prune only the selected Environment's repository after a successful snapshot and repository check; never prune after a failed or incomplete check.
3. Write `/var/lib/centraldevops/backups/status.json` atomically with per-class last attempt, last success, sanitized result/error code and verified snapshot identifier. Do not include file contents, secret values or S3 credentials.
4. Extend `verify-vps.yml` with a read-only backup freshness check. Report `FAIL` when the newest good backup is older than 8 hours or no good backup exists; a later failed run must not erase the previous last-good time.
5. Provide read-only access to the status signal for spec 14. Spec 14 owns the dashboard and end-to-end alert notification test; keep Production blocked until that handoff is proven.

## Acceptance criteria

- The 14-day and 12-month policies preserve the expected snapshots in a disposable repository.
- No prune runs after an upload or repository-check failure, and one Environment's policy cannot prune the other prefix.
- Status is atomic, secret-free, root-owned and has an independently preserved last-success time per backup class.
- `verify-vps.yml` passes for a fresh backup and fails for missing or older-than-8-hour backup data.
- The spec 14 monitoring consumer can read the status without write access or secret access.

## Source reference

BKP-06, BKP-07; OBS-02, OBS-03, OBS-05; parent PRD Q4; v5 §§13.1–13.2.

## Verify

- Exercise retention in a disposable Restic repository with dated synthetic snapshots.
- Inject a failed repository check and confirm pruning is skipped.
- Test fresh, stale, missing and failed-last-attempt status fixtures through `verify-vps.yml`.
- Inspect ownership, permissions and status contents without displaying secret-bearing files.

## Out of scope

Grafana dashboards and alert notification delivery (spec 14), changing the 8-hour freshness threshold, or reducing the 12-month record-retention decision.
