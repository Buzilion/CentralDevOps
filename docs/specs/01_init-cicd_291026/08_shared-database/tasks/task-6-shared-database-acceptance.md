# Task 6: Shared database acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Tasks 1–5; specs 04, 05 and 06 checklists complete |
| Needs | Disposable VPS, throwaway test app, and external scan vantage point |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Prove the database security, per-app isolation, connection contract, reboot behavior, and rotation/rollback path end to end on a disposable host.

## Relevant files or references

- `roles/postgresql/`
- `playbooks/configure.yml` and `playbooks/verify.yml`
- `deployment/scripts/lib/centraldevops_database.py` and focused tests
- `docs/runbooks/shared-database.md`
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-01 to DB-05, DB-07, DB-08)

## Proposed approach

1. Apply the database profile on a disposable host only. Record the PostgreSQL, Docker network, firewall, and verifier results without recording secrets.
2. Run a throwaway app container on `db` through a disposable test harness using only the `DB_*` contract. Do not enable or bypass spec 04's fail-closed deploy stub. Confirm connection and health; attempt connections from a container not on `db`.
3. Create two isolated app fixtures and confirm each role can use only its own database. Test first provisioning, unchanged repeat, changed password, and the rollback interface after a simulated failed replacement.
4. Scan the VPS externally and confirm TCP 5432 is closed. Verify the GUI client connects only through the SSH tunnel.
5. Reboot the disposable VPS and confirm PostgreSQL binds to the restored `db` gateway and the test app reconnects.
6. Run the existing `verify-vps.yml` and verify all PostgreSQL checks are read-only and pass.

## Acceptance criteria

- External TCP 5432 is closed; PostgreSQL listens only on loopback and the expected `db` gateway.
- A test app on `db` connects using the platform connection contract; a non-`db` container cannot connect.
- Two app roles cannot connect to one another's managed databases, and neither role is privileged.
- Provisioning is unchanged on repeat, rotates only the intended app password, and restores the previous credential through its rollback interface after a simulated failed replacement. Spec 11 verifies the full deployment rollback.
- After reboot, the listener and app health check recover; verification reports PASS without mutation.
- The GUI test succeeds through the admin SSH tunnel and no public database path exists.
- Evidence is sanitized and recorded in `summaries/task-6-summary.md`; no task is marked complete while a prerequisite remains incomplete.

## Source reference

DB-01 to DB-05, DB-07; INF-06, INF-18; SEC-12; v5 §§6.3, 11.1, 12.1.

## Verify

- Record commands, dates, and PASS/FAIL outcomes for each acceptance criterion.
- Review workflow logs, host logs, process arguments, and artifacts for absence of canary secrets.
- Confirm the verifier reports failure for a deliberately incorrect listener or network condition on the disposable host.

## Out of scope

Production rollout, data migration, backup/restore implementation, and live database decommissioning.
