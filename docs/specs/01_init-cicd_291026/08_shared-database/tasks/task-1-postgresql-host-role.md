# Task 1: PostgreSQL host role

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Spec-level gate: specs 04, 05 and 06 checklists complete |
| Needs | A disposable Ubuntu VPS with the spec 04 `db` Docker network |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Install and configure one private PostgreSQL instance on each Environment's database host without exposing port 5432 or granting app roles administrative privileges.

## Relevant files or references

- Create `roles/postgresql/`
- Update `playbooks/configure.yml` for the `database` profile
- Reuse the `db` subnet and existing firewall role from specs 03–04
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-01, DB-02)
- `docs/design/infrastructure-contracts-and-invariants.md` §§7–8
- v5 design §§6.2, 11.1 and 12.1

## Proposed approach

1. Select and record an explicit PostgreSQL major/package version tested against the Ubuntu release pinned by spec 03. Use the reviewed package source; do not install `latest` or use an unreviewed installer.
2. Read the existing Docker `db` network state, verify its subnet against the inventory value from spec 04, and obtain its gateway. Fail before changing PostgreSQL or firewall state if either value is absent or inconsistent.
3. Configure PostgreSQL to listen only on loopback and that gateway. Set `password_encryption` to `scram-sha-256`; configure host authentication for the `db` subnet with `scram-sha-256`, and keep local administration on the local socket. Any TCP GUI rule must be limited to loopback and use password authentication.
4. Reuse the existing firewall role to admit TCP 5432 only from the Environment's `db` subnet. Do not publish a container port or add a public-interface rule.
5. Make the role idempotent and check-mode safe. Keep secret-bearing operations out of diffs and logs.

## Acceptance criteria

- PostgreSQL is installed at the recorded version and is enabled/running on the database host.
- Effective listener addresses are exactly loopback and the `db` network gateway; there is no wildcard or public listener.
- `pg_hba.conf` uses SCRAM-SHA-256 for the `db` subnet and has no broad network or `trust` rule.
- The firewall admits TCP 5432 only from the `db` subnet, and no PostgreSQL container port is published.
- Invalid/missing network facts fail before the role changes PostgreSQL or firewall state.
- Check mode does not mutate the host and a second unchanged role run reports zero changes.

## Source reference

DB-01, DB-02; INF-11; NFR-13; v5 §§9.4, 11.1, 12.1.

## Verify

- Inspect the effective PostgreSQL configuration, service status, listener addresses, and firewall rules on the disposable VPS.
- Confirm the `db` subnet matches the spec 04 Docker network and attempt a connection from an external host.
- Run the role twice with unchanged inputs and compare Ansible changed counts; run check mode and compare host state.

## Out of scope

Per-app databases and roles, boot ordering, database backups, and actual app deployment.
