# Spec 08: Shared Database

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 08 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked until specs 04, 05 and 06 are complete |
| Depends on | `04_docker-and-deploy-runtime`, `05_host-verification` and `06_registry-and-compose-policy` (each checklist must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/database-v1.md` (`DB`), `infrastructure-v1.md` (`INF`), `registry-and-policy-v1.md` (`REG`), `central-deployment-v1.md` (`DEP`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§1, 4, 7–8; `docs/design/naming-and-repository-conventions.md` §§3, 5, 7; `docs/design/variables-and-secrets.md` §§5.2, 8–9; v5 design §§6.2–6.3, 9.2, 11.1–11.3, 12.1 and 16 step 7 |

## What

Configure one PostgreSQL instance per Environment on its database host, reachable by enabled apps only through the private `db` network. Provision one isolated database and login role per enabled app, provide the stable `DB_*` runtime contract, make PostgreSQL start after its Docker network is ready, and document administrator access and the supported database-move paths. Extend the existing host-verification operation and prove the behavior on a disposable VPS.

## Context

- Staging and Production have separate VPS hosts and separate PostgreSQL instances. The initial topology is all-in-one; PostgreSQL is a host service, not a publicly published container.
- Spec 04 owns creation of the external Docker `db` network and its inventory subnet. This spec consumes that network and must not redefine its name or subnet. Determine its gateway from the network state and fail closed if the network is absent or inconsistent.
- Spec 05 owns `verify-vps.yml` and its read-only baseline. Add PostgreSQL checks to that verifier; do not introduce a second verifier.
- Spec 06 owns registry and Compose schemas. Use the reviewed registry app identity, `database.enabled`, `database.name`, `database.user`, and `placement.database_group`; do not accept these values from deployment input or an app manifest.
- Spec 06's current strict schema has no `database.host` field and requires `name`/`user` only when shared provisioning is enabled. Task 4 extends that contract for the documented app-owned database path while keeping `DB_HOST` platform-owned.
- The app supplies `APP_DB_PASSWORD` as a secret. The app-side workflow maps it to runtime `DB_PASSWORD` in the sealed bundle. The platform supplies `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER`.
- Spec 11 owns the complete deployment and rollback flow. This spec defines and tests the database-provisioning interface that the root-owned `centraldevops-deploy` entrypoint will call. Do not replace spec 04's fail-closed stub or add another sudo entrypoint.
- Implementation must not start until the checklists for specs 04, 05 and 06 are complete. If a prerequisite spec or checklist is absent, treat this spec as blocked rather than bypassing the roadmap.

## Requirements

| ID | Statement | Source |
|---|---|---|
| DB-01 | Each Environment has one shared PostgreSQL instance and one database and login role per enabled app. App roles are not superusers and cannot connect to another app's database. | Database PRD DB-01; v5 §11.1 |
| DB-02 | PostgreSQL listens only on loopback and the `db` network gateway. The `db` subnet uses SCRAM-SHA-256 password authentication, and the firewall admits TCP 5432 only from that subnet. Port 5432 is never public. | Database PRD DB-02; v5 §§11.1, 12.1 |
| DB-03 | PostgreSQL starts only after Docker has restored the `db` network and its gateway. After a host reboot, the database listener and an enabled app's health check recover. | Database PRD DB-03; v5 §11.1 |
| DB-04 | When the registry enables the shared database, deployment idempotently ensures the registry-owned database and login role and applies the app's runtime `DB_PASSWORD`. An unchanged deployment makes no database change; a changed app secret rotates the role password. | Database PRD DB-04; v5 §11.1 |
| DB-05 | For an app using the shared database, CentralDevOps injects `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER`; the app supplies `DB_PASSWORD` from its own secret. A test app connects using only this contract. | Database PRD DB-05; v5 §§7.2, 11.1 |
| DB-07 | GUI administration reaches PostgreSQL only through an SSH tunnel using the matching Environment's admin identity. No public database port is opened. | Database PRD DB-07; v5 §§11.3, 12.1 |
| DB-08 | Document step-by-step moves to an app-owned database container or a separate database host while preserving the `DB_*` names and changing only the app Compose configuration, centrally supplied `DB_HOST`, and reviewed registry settings. | Database PRD DB-08; v5 §11.2 |

DB-06 (app-owned, backward-compatible migrations) remains a cross-cutting invariant and is completed with the onboarding contract in spec 15 per the roadmap. It is not a deliverable of this spec.

## Design

### PostgreSQL instance and network

- Install the reviewed PostgreSQL package version through Ansible on `database_nodes`. Record and test the selected major version for the Ubuntu release pinned by spec 03; do not use a floating package selection.
- Bind PostgreSQL only to `localhost` and the gateway address of the existing Docker `db` bridge. Discover the gateway from the network created by spec 04; do not hard-code an example subnet or bind to `*`/`0.0.0.0`.
- Set `password_encryption` to `scram-sha-256`. Permit password-authenticated database traffic from the `db` subnet only with `scram-sha-256`. Keep local PostgreSQL administration on the host's local socket; any loopback TCP rule for GUI access must remain loopback-only and use password authentication. Do not add `trust` or broad network rules.
- Extend the existing firewall role so TCP 5432 is admitted only from the selected Environment's `db` subnet. Do not publish a container port or open 5432 to the public interface.
- Revoke `CONNECT` on managed app databases from `PUBLIC` and grant it only to that database's app role. Each app role has `LOGIN` only, no superuser, `CREATEDB`, `CREATEROLE`, replication, or inherited administrative membership.

### Registry and per-app provisioning

- Use the reviewed `database.name` and `database.user` values from the selected app/Environment registry file. Validate both against `^[a-z_][a-z0-9_]{0,62}$`; reject reserved administrative identities and duplicate database names or duplicate role names within the same Environment before any SQL mutation. The same app's database and role may have the same name, as in the v5 example.
- For an app-owned database that keeps the `DB_*` contract, keep `database.name` and `database.user` in the reviewed registry even though shared provisioning is disabled. The spec 06 schema must allow those values with a centrally reviewed `database.host` service name for this path, and the Compose policy must confirm that service exists.
- Quote SQL identifiers with the database library's identifier-quoting API and pass values as parameters; never construct SQL by concatenating registry values or passwords.
- Use the authenticated app identity and validated registry entry, never dispatch input, manifest text, or app-provided `DB_NAME`/`DB_USER`, to select the database and role.
- A database-enabled deployment creates missing objects and reconciles ownership and privileges. It must not drop a database or role when an app is disabled or removed from the registry; destructive deprovisioning is out of scope.
- Set the app role password from the sealed runtime `DB_PASSWORD` using SCRAM-SHA-256. Do not issue a password change on every deployment: detect an unchanged credential without logging or exposing it, and change the role only when the desired secret changes. Never put a password in command arguments, SQL output, logs, artifacts, or a deploy-readable file.
- The provisioner is a root-owned internal module called only by `centraldevops-deploy`; it is not a new sudo allow-list command and does not give `cdo-deploy` direct PostgreSQL socket access. Spec 11 integrates the provision and rollback operations with deployment execution.
- Install the module root-owned and non-deploy-writable under `/usr/local/lib/centraldevops/`; it is not a standalone privileged entrypoint.
- If a deployment rotates `DB_PASSWORD` and the replacement release fails, restore the previous database password before restoring the previous app environment. Do not leave the previous app running with credentials that no longer work.

### App connection contract

| Runtime key | Owner and value |
|---|---|
| `DB_HOST` | CentralDevOps. In the initial shared topology, the `db` network gateway on the host selected by `placement.database_group`; for a later split database host, that host's inventory private IP; for an app-owned database container, the reviewed Compose service name in `database.host`. |
| `DB_PORT` | CentralDevOps; `5432` for the supported PostgreSQL topologies. |
| `DB_NAME` | CentralDevOps; the registry's `database.name`. |
| `DB_USER` | CentralDevOps; the registry's `database.user`. |
| `DB_PASSWORD` | App; `APP_DB_PASSWORD` mapped from the matching GitHub Environment secret. |

- Only a registry-enabled shared database attaches the app service to the external `db` network and invokes shared-database provisioning. A disabled entry does not create shared objects or grant access to the shared network.
- The app-supplied runtime values contain exactly the manifest-declared app-owned keys. For an app using the `DB_*` contract, the manifest requires `DB_PASSWORD`; CentralDevOps adds only the approved platform-owned `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER` values. App input cannot override those fields. Missing `APP_DB_PASSWORD`, invalid registry values, or a collision with reserved keys fails before changing the host or app.
- For the documented app-owned database-container path, keep `DB_HOST` platform-owned. When shared provisioning is disabled but the app still uses `DB_*`, the registry retains `database.name` and `database.user` and provides `database.host` as the service name (for example `db`). Extend spec 06's strict schema/validator and Compose policy to allow only this reviewed endpoint and verify the service exists. The app must not supply the reserved key; the database service stays on the app's project network with no published port.
- Do not print the rendered environment file or any value from it. Tests should assert the resulting contract without exposing credentials.

### Reboot ordering and verification

- Add a systemd drop-in for PostgreSQL with `Requires=docker.service`, `After=docker.service`, and a pre-start readiness check that the expected `db` gateway is present. If the network or gateway is missing, PostgreSQL must fail visibly rather than bind to a different address.
- Extend the spec 05 verifier with read-only checks for the PostgreSQL package/service, exact listener addresses, effective authentication rules, `db` subnet/firewall, database-service ordering, and absence of public 5432 exposure.
- The verifier must not create databases, roles, credentials, or firewall rules. A reboot acceptance run is required on a disposable host.

### Administrator access and migration path

- Document a local SSH port forward to remote loopback, for example `ssh -N -L 15432:127.0.0.1:5432 <admin-user>@<environment-host>`. The GUI client connects to `127.0.0.1:15432`; use the admin SSH identity for the same Environment. Do not connect a GUI client directly to the host's public address.
- If a GUI client needs a PostgreSQL administrator credential, keep it in the approved operator password manager, not GitHub, the app repository, or app runtime secrets. The host-local provisioning path uses local PostgreSQL administration and does not distribute a superuser password to apps.
- For an app-owned database container, the runbook must cover a verified backup, private app-project network, restore and validation, reviewed registry update (`database.enabled: false` and centrally owned `DB_HOST`), health check, rollback window, and only then any separately approved cleanup.
- For a separate database host, the runbook must cover a verified backup/restore, private inventory address and firewall policy, reviewed `placement.database_group`, centrally supplied `DB_HOST`, app reconnection and rollback. Never expose 5432 publicly.
- Both paths retain the `DB_*` names. Database backup implementation is owned by spec 13; use its accepted backup and restore procedure when available. CentralDevOps never runs app schema migrations.

## Deliverables

```text
roles/postgresql/
roles/postgresql/tasks/verify.yml      # role-scoped read-only checks
playbooks/configure.yml                 # database profile uses the postgresql role
playbooks/verify.yml                    # extend spec 05's read-only checks
deployment/scripts/lib/centraldevops_database.py
deployment/schemas/registry.schema.json # allow the reviewed app-owned DB endpoint
deployment/tools/validate-registry.py   # validate database.host and name/user rules
deployment/scripts/centraldevops-compose-policy
deployment/tools/tests/                  # focused provisioning and contract tests
docs/runbooks/shared-database.md
```

The database module defines the tested interface consumed by `centraldevops-deploy`; the complete deploy and rollback execution remains in spec 11. Add only the PostgreSQL inventory values needed by the role, reusing spec 04's `db` subnet rather than defining a second network source of truth.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Use registry-owned `database.name` and `database.user`; reject unsafe, duplicate, or overlength identifiers before host mutation. | Derive names from app input or accept names in a deployment request | The v5 registry example already owns these values; registry review is the authority for per-app database identity. | Yes |
| D2 | Bind to the gateway of the existing `db` network and discover it from Docker network state. | Bind to all interfaces or duplicate the subnet/gateway as unrelated settings | Keeps the database private and the network facts owned by spec 04. | Yes |
| D3 | Treat password rotation as part of the deployment transaction and restore the old password before an app rollback. | Change the role password without coordinating rollback | The previous release must remain able to reconnect after a failed replacement. | Yes |
| D4 | Keep GUI access on a loopback SSH tunnel using the admin identity; any database admin credential stays outside GitHub. | Open 5432 publicly or store an admin password in an Environment secret | Satisfies DB-07 without adding a public database path or app-accessible credential. | Yes |
| D5 | Keep `DB_HOST` centrally supplied for a future app-owned database container; extend the registry schema with a reviewed `database.host` service name and retain `database.name`/`database.user` when shared provisioning is disabled. | Let the app set the reserved `DB_HOST` runtime key | Preserves the runtime ownership boundary while keeping the documented move path usable. | Yes |
| D6 | Disabling shared-database provisioning never automatically drops an existing database or role. | Delete data when a registry flag changes | Prevents a registry edit from becoming an unreviewed destructive data operation. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| PostgreSQL has no public listener or published port. | Inspect effective listener addresses, firewall rules and container port bindings; scan the disposable host externally. |
| Only the `db` subnet can reach the shared PostgreSQL listener. | Connect from an enabled app on `db`; attempt from a container on another network and from outside the host. |
| Each app's role is non-superuser and cannot connect to another app database. | Inspect role attributes and attempt cross-database connections with disposable app roles. |
| An unchanged deployment does not rewrite the app role password. | Compare the stored role verifier before and after a repeat with the same secret; never print either value. |
| The platform owns `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER`; the app owns only `DB_PASSWORD`. | Test valid/invalid runtime bundles and confirm no app-supplied reserved value is accepted. |
| The database provisioner's rollback operation restores the previous credential. | Simulate a failed replacement in a disposable harness, invoke the rollback operation, and verify the previous app credential connects. Spec 11 verifies the full deployment rollback. |
| PostgreSQL is ready after reboot only when the `db` gateway is ready. | Reboot the disposable host and inspect service ordering, listener, and app health. |
| GUI access uses the matching admin SSH identity and a local tunnel. | Connect through the documented tunnel; confirm direct public access fails. |
| CentralDevOps does not run schema migrations. | Review the deploy integration and verify that only an app-declared release command can run migrations. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Any spec 04, 05 or 06 checklist is incomplete or absent. | Do not configure a service host; report the missing prerequisite and keep this spec blocked. |
| The Docker `db` network, subnet, or gateway is missing or inconsistent. | Fail before PostgreSQL configuration or firewall mutation; do not guess an address or bind broadly. |
| PostgreSQL package source/version is unavailable or untrusted. | Stop without falling back to an unpinned package source or convenience installer. |
| Registry database identity is missing, malformed, duplicated, or reserved. | Reject before SQL mutation and identify the invalid registry field without printing secrets. |
| `database.enabled` is true but `DB_PASSWORD` is missing or invalid. | Fail before provisioning or app replacement; do not generate or substitute a password. |
| Provisioning or credential rotation fails. | Return a nonzero sanitized error and do not report deployment success; preserve enough state for safe retry or rollback. |
| PostgreSQL cannot bind to the expected gateway after boot. | Keep the service failed and visible to verification; do not fall back to `0.0.0.0`. |
| A GUI connection is attempted without the SSH tunnel. | The connection fails; do not open a public port as a workaround. |

## Testing Strategy

- **Role tests:** supported package/version, private listener, SCRAM settings, exact `pg_hba` scope, firewall source restriction, check-mode safety, and zero changes on a second unchanged Ansible run.
- **Provisioning tests:** first creation, repeat with unchanged registry and password, password rotation, database/role isolation, invalid identifiers, missing secret, and failure without secret leakage.
- **Contract tests:** shared-enabled and disabled registry cases, exact platform/app ownership of `DB_*`, `DB_HOST` selection, and rejection of app overrides.
- **Host acceptance:** disposable VPS only; verify external port 5432 is closed, non-`db` containers cannot connect, a test app connects using only `DB_*`, and different app roles cannot reach one another's databases.
- **Recovery and access tests:** reboot and app reconnect; GUI client through an SSH tunnel; simulated replacement failure after password rotation followed by successful provisioner rollback. Spec 11 verifies the full deployment rollback.
- Record sanitized commands, results, and dated evidence in each task summary. Never record database passwords, SSH private keys, or sensitive host credentials.

## Out of scope

- Actual database moves; DB-09 is deferred and the migration path is documentation only.
- App schema migrations or CentralDevOps-owned migration commands. DB-06 onboarding acceptance is owned by spec 15.
- Backup scheduling, off-host storage, and restore-drill implementation (spec 13).
- The full deployment authorization, replacement, health-check, and rollback workflow (specs 10–11); this spec provides its tested database interface and rollback contract.
- Public database access, Docker-published PostgreSQL ports, or a database per app in the initial topology.
