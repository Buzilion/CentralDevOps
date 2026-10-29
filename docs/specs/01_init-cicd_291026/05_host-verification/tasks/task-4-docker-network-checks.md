# Task 4: Docker and network checks

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Tasks 1–3; spec 04 Docker role and inventory are implemented |
| Needs | Disposable VPS with the spec-04 runtime configured |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Verify the Docker runtime and shared network invariants without changing Docker, networks, or containers.

## Relevant files or references

- Add a read-only check to `roles/docker/tasks/verify.yml`
- `inventories/<environment>/host_vars/<host-alias>.yml` for the declared `db` subnet
- `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md`
- Spec 05 check matrix and result contract

## Proposed approach

1. Verify Docker Engine is installed and active and the Compose v2 plugin is usable.
2. Inspect effective daemon listeners and fail if the Docker API has any TCP listener.
3. Inspect `edge` and `db`; confirm both are bridge networks and `db` uses the selected host's exact inventory subnet.
4. Inspect running container port bindings and fail if any container publishes a host port.
5. Use read-only Docker/Ansible inspection commands only; do not create networks, restart services, pull images, or alter containers.
6. Add passing and failing fixtures for missing runtime components, incorrect networks/subnets, exposed API listeners, and prohibited bindings.

## Acceptance criteria

- Docker/Compose availability, daemon exposure, exact shared network names/type/subnet, and any published container port each have an explicit check.
- A wrong or missing `db` subnet, missing network, exposed Docker API, or any published container port reports `FAIL`.
- Checks do not create, update, or restart Docker resources.
- The check is integrated with the verifier for every host to which the configure profile assigns the Docker role.

## Source reference

INF-06, INF-11; D-06, D-07, D-11; HV-04, HV-06, HV-07.

## Verify

- Run Ansible syntax/lint and focused check tests.
- Run read-only checks against the disposable host and confirm Docker/network state is unchanged.
- Confirm each injected failure appears in the report and fails the workflow.

## Out of scope

Installing Docker, creating networks, changing firewall rules, or deploying application containers.
