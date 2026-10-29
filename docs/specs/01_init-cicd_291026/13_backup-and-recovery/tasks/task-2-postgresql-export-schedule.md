# Task 2: PostgreSQL export schedule

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Task 1; spec 08 checklist complete |
| Needs | Spec 08 PostgreSQL role and a disposable database fixture |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Capture every PostgreSQL database and global object at least every 6 hours and store each complete export set in the matching Environment's Restic repository.

## Relevant files or references

- `roles/backup/`
- `playbooks/configure.yml`
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-01 to DB-04)
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-01)
- v5 design §§11.1, 13.2

## Proposed approach

1. Enumerate all non-template databases from the configured PostgreSQL instance; export each database in a format that `pg_restore` can consume, and export global objects with `pg_dumpall --globals-only`.
2. Schedule the complete export and Restic upload at least every 6 hours using the repository's Ansible/systemd conventions. Ensure missed schedules are handled on host return and jobs cannot overlap.
3. Write exports only to a root-owned temporary directory with restrictive permissions and a restrictive umask. Do not place database contents in workflow logs, command arguments, CI artifacts or the persistent plaintext backup area.
4. Mark the run successful only after the expected database inventory, globals export, Restic snapshot and repository-write verification all succeed. Remove temporary plaintext on success and failure; preserve the prior last-good status after any failure.
5. Keep Staging and Production schedules and credentials Environment-bound. A backup failure must not trigger a write to the other Environment's repository.

## Acceptance criteria

- Every non-template database and global role/object definition is present in a verified snapshot.
- Successful PostgreSQL snapshots are scheduled no more than 6 hours apart.
- Concurrent backup attempts cannot corrupt or overlap the Restic repository.
- An omitted database, failed dump, failed upload or failed verification never advances the last-good timestamp.
- Temporary plaintext exports are root-only and removed after the attempt; no dump contents or credentials appear in logs or artifacts.

## Source reference

BKP-01; DB-01 to DB-04; v5 §§11.1 and 13.2.

## Verify

- Run the schedule against fixtures containing multiple databases and global roles.
- Restore the exported set into a fresh isolated PostgreSQL instance and compare database and role inventories.
- Inject a dump failure and an S3 upload failure; confirm sanitized failure status, cleanup and unchanged last-good timestamp.
- Inspect the timer/service definition for the six-hour cadence, missed-run behavior and non-overlap.

## Out of scope

PostgreSQL host installation, per-app database provisioning, continuous replication, point-in-time recovery and application schema migrations.
