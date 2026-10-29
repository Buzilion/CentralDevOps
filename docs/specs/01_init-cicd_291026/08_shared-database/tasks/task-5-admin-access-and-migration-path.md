# Task 5: Admin access and migration path

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Task 1; spec 03 admin SSH identity |
| Needs | Disposable VPS and GUI PostgreSQL client for tunnel verification; align backup details with spec 13 when available |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Document safe GUI access and practical, reversible steps for moving an app off the shared PostgreSQL instance without changing its `DB_*` key names.

## Relevant files or references

- Create `docs/runbooks/shared-database.md`
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-06, DB-07, DB-08)
- `docs/design/variables-and-secrets.md` §§4.1, 8
- v5 design §§11.2–11.3, 12.1, 13.2

## Proposed approach

1. Document an SSH local port forward to remote loopback, such as `ssh -N -L 15432:127.0.0.1:5432 <admin-user>@<environment-host>`. Tell operators to connect the GUI to local `127.0.0.1:15432` and use the matching Environment's admin identity.
2. State that any PostgreSQL administrator credential needed by the GUI remains in the approved operator password manager; never put it in GitHub, an app repository, or app runtime secrets. Do not document a direct public connection.
3. Document the app-owned database-container path: take and verify a backup using the accepted restore procedure, add the app's database service on its private Compose project network, restore and validate data, set `database.enabled: false`, configure centrally supplied `DB_HOST` to the reviewed service name, deploy and verify health, retain a rollback window, then seek separate approval before cleanup.
4. Document the separate-host path: prepare a private database host and firewall, restore and validate from an accepted backup, update the reviewed `placement.database_group`, derive `DB_HOST` from the host's private inventory address, deploy and verify reconnection, and retain a rollback path.
5. Keep `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` names unchanged. State that the app owns schema migrations and backward compatibility; CentralDevOps does not run migrations. Spec 15 owns DB-06 onboarding acceptance.
6. Mark actual data migration and decommissioning as future operator work; this runbook is not permission to move a live database or delete shared data.

## Acceptance criteria

- An operator can connect a GUI client to the disposable host through the documented SSH tunnel; a direct public connection fails.
- The runbook gives ordered, reversible steps for both database-move paths and calls for a verified backup/restore before cutover.
- The connection variable names stay unchanged and `DB_HOST` remains centrally owned, including for the app-owned container path.
- The runbook does not claim that spec 08 implements backups, migrations, live cutover, or data deletion.
- No sensitive host credential or database password is included.

## Source reference

DB-06, DB-07, DB-08; v5 §§11.2–11.3, 12.1, 13.2.

## Verify

- Follow the SSH tunnel instructions with the test GUI client and record only the sanitized connection result.
- Confirm each migration path requires a verified backup and rollback before cleanup. Align tool-specific steps with spec 13 when it is written; spec 13 is not a prerequisite for closing this task.
- Check that the runbook contains no real hostnames, secrets, or private credentials.

## Out of scope

Actual migration execution, backup tooling, app schema changes, and production database cleanup.
