# Module PRD: Shared Database (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `DB` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

One shared PostgreSQL instance per Environment serving all apps on the host, with isolation per app, a stable connection contract and a documented path to dedicated databases. Backup of the database is in `backup-and-recovery-v1.md`.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| DB-01 | Each Environment runs one PostgreSQL instance with one database and one login role per app. No app uses a superuser. | An app's role cannot read another app's database. No app configuration contains superuser credentials. | §1 #9, §11.1 |
| DB-02 | PostgreSQL is reachable only by apps over the private `db` network (or a private IP once moved), never publicly. It listens only on localhost and the `db` network gateway, accepts the `db` subnet with password-based authentication using a modern hash, and the firewall admits port 5432 only from that subnet. | An external scan finds 5432 closed. A container not on the `db` network cannot connect. | §11.1, §12.1 |
| DB-03 | After a host reboot, PostgreSQL is listening on the `db` network gateway and apps reconnect. | After a reboot of a test host, verification confirms the listener and an app health check passes. | §11.1 |
| DB-04 | When the registry enables the database for an app, each deployment idempotently ensures the database and role exist and sets the role's password from the app's runtime secrets. | A first deployment creates them. A repeat deployment changes nothing. A changed app secret followed by a deployment rotates the password. | §11.1 |
| DB-05 | The connection contract given to apps is `DB_HOST`, `DB_PORT`, `DB_NAME` and `DB_USER`, injected centrally, plus `DB_PASSWORD`, supplied by the app from its own secrets. | A deployed test app connects using only these variables. | §11.1 |
| DB-06 | Schema migrations are owned by each app and must be backward compatible with the previous release. CentralDevOps never runs migrations itself; an app may use the optional release command or run migrations at start-up. | The onboarding contract states this. A deployment performs no migration other than an app-declared release command. | §11.3 |
| DB-07 | Administrators access the database for GUI-based work only through an SSH tunnel using the admin identity. | A GUI client connects through the tunnel and no public database port exists. | §11.3, §12.1 |
| DB-08 | The migration path to a per-app database container, or to a separate database host, is documented. It keeps the `DB_*` contract and changes only the app's Compose file or `DB_HOST`, and the registry settings. | The path is documented step by step. | §11.2 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| DB-09 | An app is moved to its own database container, or the shared database to a separate host, using the documented path. | The app passes its health check after the move with no change to the `DB_*` contract. | §11.2, §14.2 |
