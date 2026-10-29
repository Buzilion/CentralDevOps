# Task 4: App connection contract

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Task 3; spec 06 registry and Compose policy |
| Needs | Registry and runtime-environment fixtures; no production app |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Define and test how deployment supplies the database connection values without allowing app input to override platform-owned fields.

## Relevant files or references

- Database contract in `deployment/scripts/lib/centraldevops_database.py` and its tests
- `deployment/schemas/registry.schema.json`, `deployment/tools/validate-registry.py`, and `deployment/scripts/centraldevops-compose-policy` as needed for the DB-08 endpoint contract
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-05)
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-10)
- `docs/design/infrastructure-contracts-and-invariants.md` §7
- `docs/design/variables-and-secrets.md` §5.2
- v5 design §§7.2, 9.2, 11.1

## Proposed approach

1. For a shared-database-enabled app, derive `DB_HOST` from the selected database host's `db` gateway, `DB_PORT` as `5432`, and `DB_NAME`/`DB_USER` from the validated registry entry.
2. Map only the app's `APP_DB_PASSWORD` Environment secret to runtime `DB_PASSWORD`. Do not source `DB_HOST`, `DB_PORT`, `DB_NAME`, or `DB_USER` from app input.
3. Fail before host changes if the shared database is enabled but the secret, registry fields, target host, or network gateway is missing or invalid.
4. Ensure app-supplied runtime values contain exactly the manifest-declared app-owned keys. For an app using the `DB_*` contract, require manifest key `DB_PASSWORD`; add only the approved centrally owned `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER` values, and do not print or artifact the environment file.
5. Test the deployment-facing interface with fixtures. Keep the full deployment entrypoint and rollback integration for spec 11.
6. For the future app-owned database path, keep `DB_HOST` centrally supplied using a reviewed `database.host` service name when shared provisioning is disabled. Retain `database.name` and `database.user` for the `DB_*` contract, validate that the endpoint matches a service in the app Compose file, and extend spec 06's schema/validator/policy because its current strict schema does not define this field. Never permit the app to set the reserved runtime key.

## Acceptance criteria

- A database-enabled test app receives exactly the expected `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` values from their designated owners; `DB_PASSWORD` is declared in the manifest and sourced only from the app secret.
- A conflicting app-supplied reserved value, missing secret, or invalid registry field is rejected before the host is contacted.
- The central contract does not expose a server-side PostgreSQL administrator credential.
- For a disabled shared database, the shared provisioner and external `db` network are not selected; when the app-owned DB path is used, its name, user, and host remain centrally reviewed and validated.
- Test output and artifacts contain no runtime secret value.

## Source reference

DB-05; DEP-10; REG-02, REG-04, REG-05; SEC-08, SEC-12; v5 §§7.2, 9.2, 11.1–11.2.

## Verify

- Test valid shared-enabled, disabled, missing-secret, invalid-host, and app-override fixtures.
- Inspect only sanitized key names and source ownership in test output; do not print the rendered environment.
- Confirm a test service on `db` can use the generated contract and a service on another network cannot.

## Out of scope

The complete `deploy-app.yml` workflow, live app rollout, route activation, and actual database moves.
