# Task 2: Reboot ordering and verification

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/08_shared-database/spec.md` |
| Depends on | Task 1; spec 05's `verify-vps.yml` and read-only baseline |
| Needs | Disposable VPS with the PostgreSQL role applied |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Ensure PostgreSQL starts only after Docker restores the `db` network and extend the existing read-only host verifier with database checks.

## Relevant files or references

- `roles/postgresql/` systemd drop-in and readiness check
- `roles/postgresql/tasks/verify.yml`
- Extend `playbooks/verify.yml` and `.github/workflows/verify-vps.yml` from spec 05
- `docs/design/infrastructure-contracts-and-invariants.md` §§6.3, 8
- v5 design §§6.3, 11.1

## Proposed approach

1. Add `Requires=docker.service` and `After=docker.service` to the PostgreSQL unit, plus a pre-start check for the expected `db` gateway address. A missing gateway must fail visibly; PostgreSQL must not fall back to listening on another interface.
2. Add `roles/postgresql/tasks/verify.yml` and integrate it into the existing verifier with read-only PASS/FAIL checks for the PostgreSQL package and service, exact listener addresses, effective authentication rules, firewall subnet, Docker network gateway, and systemd ordering.
3. Ensure verification neither provisions app databases nor changes service, firewall, or network state.
4. Reboot only a disposable VPS. Confirm Docker restores `db` before PostgreSQL starts, then verify the listener and app reconnection.

## Acceptance criteria

- The PostgreSQL unit requires and is ordered after Docker, and does not start successfully if the expected gateway is absent.
- `verify-vps.yml` reports a clear PASS/FAIL result for the database checks and remains read-only.
- After reboot, PostgreSQL listens on the expected gateway and a database-enabled test app's health check passes.
- No production VPS is rebooted as part of this task.

## Source reference

DB-03; INF-06, INF-18; v5 §§6.3, 11.1.

## Verify

- Inspect the generated systemd drop-in and verifier output on the disposable VPS.
- Remove or alter the expected gateway in a controlled test and confirm the PostgreSQL pre-start check fails rather than binding broadly.
- Reboot the disposable VPS and record service ordering, listener, and test-app health results.

## Out of scope

Database backup/restore, app credential provisioning, and changes to the verifier's unrelated checks.
