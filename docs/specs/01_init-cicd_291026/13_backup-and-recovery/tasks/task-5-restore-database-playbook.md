# Task 5: Restore database playbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Tasks 1, 2 and 4; spec 08 checklist complete |
| Needs | Fresh isolated PostgreSQL target and Staging-only backup credentials |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Provide a guarded Ansible playbook that restores a selected Restic backup's PostgreSQL globals and databases without implicitly modifying a live Environment.

## Relevant files or references

- Create `playbooks/restore-database.yml`
- `roles/backup/`
- Spec 08 `shared-database/spec.md` for the PostgreSQL contract
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-08, BKP-09)
- v5 §§11.1 and 13.3

## Proposed approach

1. Require an explicit restore Environment and destination inventory target. Default to no target; reject missing, mismatched or protected live targets before any database mutation.
2. Open only that Environment's Restic repository, select the requested verified snapshot or the latest verified good snapshot, and restore into a restricted temporary location.
3. Restore global objects before per-database archives so the expected roles and ownership exist. Validate the restored database inventory before allowing application deployment.
4. Keep restore work files root-only and remove them after use. Never print S3 credentials, repository passwords, database contents or connection secrets.
5. Add an isolated Staging restore test; do not use Production S3 credentials, a Production database or an in-place Staging restore for this task.

## Acceptance criteria

- The playbook refuses to run without an explicit valid Environment, selected backup and isolated destination.
- A clean isolated PostgreSQL target receives all backed-up globals and databases and passes inventory/connection checks.
- Corrupt, missing or wrong-Environment snapshots fail before application deployment and do not report success.
- The live Staging and Production databases remain unchanged during tests.
- No restore credential, password or database content appears in logs, artifacts or task summaries.

## Source reference

BKP-08, BKP-09; DB-01 to DB-05; v5 §§11.1 and 13.3.

## Verify

- Run Ansible syntax checks and focused tests for the target/environment guard.
- Restore a synthetic Staging snapshot to a fresh isolated PostgreSQL service; compare database and role inventories and run an application connection check.
- Inject an invalid snapshot and a mismatched Environment; confirm failure occurs before mutation.
- Inspect sanitized output and confirm temporary files are removed.

## Out of scope

Application file restore, schema migrations, restoring to Production, live database overwrite, or changing spec 08's database provisioning contract.
