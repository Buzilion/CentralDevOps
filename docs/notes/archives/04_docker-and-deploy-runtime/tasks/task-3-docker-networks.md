# Task 3: Docker Engine, Compose and shared networks

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Task 2; spec 03 has pinned the supported Ubuntu release and Ansible toolchain |
| Needs | A disposable VPS that has passed spec 03's bootstrap/hardening acceptance |

## Goal

Install the reviewed Docker runtime reproducibly and provide the two shared networks required by subsequent roles and deployments.

## Relevant files or references

- Create `roles/docker/`
- Update `requirements.yml` only if a Docker collection is required
- `inventories/<environment>/group_vars/all.yml` for reviewed package and network facts
- `docs/design/infrastructure-contracts-and-invariants.md` §§5–6
- v5 design §§9.4, 11.1, 12.1

## Proposed approach

1. Select and record explicit Docker Engine and Compose plugin versions after testing against the OS release from spec 03. Use Docker's signed Ubuntu apt repository and Ansible package/service/network modules; do not use floating versions or a convenience installer.
2. Ensure Docker listens only on its Unix socket. Confirm the socket is not mounted into app containers and is not accessible to `cdo-deploy`.
3. Create `edge` as an external bridge network and `db` as an external bridge network with the selected Environment's explicit inventory CIDR.
4. Validate the `db` CIDR against system routes, VPS private routes, Docker address pools, and any other declared network before creating it.
5. Make network and package tasks idempotent and check-mode safe. Do not create host-published ports.

## Acceptance criteria

- Docker Engine and Compose are at the explicitly configured versions and the daemon is enabled/running.
- The daemon has no TCP listener; only authorized host administrators can access its socket.
- `edge` and `db` exist with expected driver/scope; `db` subnet matches inventory and passed overlap validation.
- Invalid/missing/overlapping subnet inputs fail before network mutation.
- Second configure run reports zero changes; check mode does not mutate package, daemon, or network state.

## Source reference

INF-11; NFR-13, NFR-18; D-06, D-07.

## Verify

- On the disposable VPS, inspect package versions, daemon configuration, socket permissions and `docker network inspect edge db`.
- Test a deliberately overlapping subnet and confirm the role fails before network creation.
- Run configure twice and compare Ansible changed counts.

## Out of scope

Installing Nginx, PostgreSQL or app containers; publishing ports; configuring private-IP routing.
