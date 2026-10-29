# Task 4: Rendered Compose policy

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Tasks 1 and 2; spec 03 Python toolchain is complete |
| Needs | Pinned Docker Compose v2 on the CI runner; fixtures only, no VPS access |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Implement a central, fail-closed policy check on the fully rendered Compose configuration.

## Relevant files or references

- Create `deployment/scripts/centraldevops-compose-policy`
- Add policy fixtures and tests under `deployment/tools/tests/`
- `docs/design/infrastructure-contracts-and-invariants.md` §6
- `docs/design/naming-and-repository-conventions.md` §5.2
- v5 design §9.4 and v3 deployment contract §3 (illustrative)
- Spec sections: Compose rendering and policy, Error Behavior

## Proposed approach

1. Render with Docker Compose v2 `config --format json`, the derived project name and project directory, an explicit trusted interpolation file and explicitly enumerated Compose files.
2. Clear ambient `COMPOSE_*` variables and disable implicit override discovery. Evaluate every explicit override in the final rendered result.
3. Enforce all rules in the spec policy table: privilege and confinement, devices/capabilities, host namespaces, socket and bind mounts, published ports, networks, project-scoped volumes, image identity/pinning, health check, project name, `env_file`, CPU and memory limits.
4. Require resource limits on every service and compare their sums with the registry CPU and memory ceilings. Reject `build` and floating image tags.
5. Require the routed `docker_edge` service to join external `edge`; reject every app-supplied `ports` entry and any external or cross-project named volume. Do not add a private-IP publish path in this task.
6. Permit only the recognized strengthening `security_opt` value `no-new-privileges:true`; fail closed for weakening or unknown options.
7. Capture rendered output internally and emit only sanitized rule IDs, service names and field paths. Never print the JSON or runtime values.
8. Cover every prohibited rule with negative fixtures, including violations introduced only through interpolation and explicit override files.

## Acceptance criteria

- A compliant baseline fixture passes after rendering.
- Every prohibited setting in the spec policy table fails.
- `no-new-privileges:true` passes and weakening or unknown `security_opt` values fail.
- A forbidden value supplied by interpolation or an override is rejected based on the final rendered configuration.
- `db` is allowed only when enabled in the matching registry entry; `edge` must remain external with its fixed name.
- In `docker_edge` mode, the routed service is attached to `edge`; external or cross-project named volumes fail.
- The manifest's routed service must exist, use the requested digest and have an enabled health check.
- The sum of rendered limits cannot exceed either registry ceiling.
- A runtime canary value does not appear in standard output, standard error or test failure messages.
- A missing or unsupported Docker Compose executable fails; there is no source-YAML fallback.

## Source reference

REG-02, REG-05, REG-06; P-02, P-05, P-06; v5 design §9.4.

## Verify

- Run the focused policy unit tests and integration tests using the pinned Compose CLI.
- Review every rule's positive and negative fixture.
- Confirm that rendering does not modify the source bundle or contact a VPS.

## Out of scope

Installing Docker on a host, private-IP port publishing, app deployment or route activation.
