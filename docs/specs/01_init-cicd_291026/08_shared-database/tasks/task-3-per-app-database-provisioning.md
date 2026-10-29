# Task 3: Per-app database provisioning

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Task 1; spec 06 registry schema and validation |
| Needs | Disposable PostgreSQL instance and registry fixtures |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Provide a root-owned, idempotent database provisioning interface for registry-enabled apps, including safe password rotation and rollback behavior.

## Relevant files or references

- Create `deployment/scripts/lib/centraldevops_database.py`
- Add focused tests under `deployment/tools/tests/`
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-01, DB-04)
- `docs/design/variables-and-secrets.md` §§5.2, 8
- v5 design §§9.2, 11.1

## Proposed approach

1. Accept only the authenticated app identity and the selected, validated registry entry. Use `database.enabled`, `database.name`, `database.user`, and the selected `placement.database_group`; never accept database or role names from a dispatch payload, manifest, or runtime environment.
2. Validate database and role names against `^[a-z_][a-z0-9_]{0,62}$`. Reject duplicate database names or duplicate role names within the Environment, reserved administrative identities, missing fields, or malformed values before issuing SQL; the same app may use the same name for its database and role.
3. When enabled, create the database and `LOGIN` role if absent, set the database owner to that role, revoke `CONNECT` from `PUBLIC` on managed app databases, and grant access only to the matching app role. Ensure the role has no superuser, `CREATEDB`, `CREATEROLE`, replication, or administrative membership.
4. Quote SQL identifiers with the database library's identifier-quoting API and parameterize values. Apply the app's `DB_PASSWORD` as a SCRAM-SHA-256 credential. Detect whether the desired secret already matches the role without exposing it; do not issue `ALTER ROLE` with a new verifier on every repeat deployment.
5. Return only sanitized status such as `created`, `unchanged`, or `rotated`. Never place a password in command arguments, SQL output, logs, artifacts, or a deploy-readable file. Do not add a direct sudo rule or grant `cdo-deploy` database-socket access.
6. Define and test a rollback operation for the previous `DB_PASSWORD`. A harness simulates a failed replacement and confirms the previous credential works after rollback. Spec 11 wires this interface into the full deployment flow.
7. When `database.enabled` is false, skip shared-object creation and do not drop pre-existing data. Keep the spec 04 deploy entrypoint fail-closed until spec 11.
8. Install the module root-owned and non-deploy-writable under `/usr/local/lib/centraldevops/`; it must not be a standalone privileged entrypoint.

## Acceptance criteria

- First provisioning creates exactly one database and non-superuser login role using the registry names.
- A second run with unchanged registry values and password makes no database or password-verifier change.
- A changed app secret updates only that app role's password; its prior password stops authenticating and the new password works.
- An app role cannot connect to another managed app database and has no administrative attributes or role memberships.
- Disabled registry entries do not create or delete shared database objects.
- Invalid input and missing secrets fail before database mutation; test logs, command arguments, and artifacts contain no secret.
- The rollback operation restores the previous credential so the previous release can reconnect after a simulated failure.

## Source reference

DB-01, DB-04; SEC-08, SEC-12; v5 §§9.2, 11.1.

## Verify

- Use isolated fixture databases and app roles on a disposable PostgreSQL instance.
- Capture role/database state before and after first run, unchanged repeat, rotation, and rollback without printing password verifiers.
- Run malformed-name and missing-secret cases and confirm no SQL mutation and no secret in captured output.

## Out of scope

Full deployment authorization/execution, schema migrations, automatic database deletion, and per-app container provisioning.
