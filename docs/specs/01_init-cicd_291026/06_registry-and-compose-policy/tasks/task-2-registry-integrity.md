# Task 2: Registry integrity and inventory validation

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Task 1; spec 03 inventories and pinned `ansible-inventory` are complete |
| Needs | Local inventory fixtures only; no VPS access |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Validate registry files as a complete, environment-aware set and expose a strict deployment-preflight mode for a selected registry entry and manifest.

## Relevant files or references

- Create `deployment/tools/validate-registry.py`
- Add tests under `deployment/tools/tests/`
- `inventories/staging/hosts.yml` and `inventories/production/hosts.yml`
- `docs/design/infrastructure-contracts-and-invariants.md` §4
- Spec sections: Registry integrity and inventory resolution, Error Behavior

## Proposed approach

1. Add an `--all` mode that schema-validates every file under `apps/` and checks filename/content agreement. An absent or empty `apps/` directory is a valid pre-onboarding state.
2. Resolve each inventory through the pinned `ansible-inventory` tool. Do not accept an inventory path as an app or workflow input.
3. Require each referenced placement group to resolve to exactly one host in the matching Environment. Reject missing, empty, ambiguous and cross-Environment group matches.
4. Check global domain uniqueness across all apps and Environments. Check private-IP port uniqueness by Environment and resolved app host.
5. Add deployment mode for the verified app, Environment, registry entry, manifest and requested digest. Require the manifest domain to be registered and fail clearly for `private_ip` until its deployment path is implemented.
6. Report only file, field and rule identifiers; never echo runtime values or full manifest/registry content.

## Acceptance criteria

- All registry entries are schema-validated and checked against their canonical paths.
- Duplicate domain claims fail even when the entries are in different Environments.
- Duplicate `private_ip` ports fail on one app host and pass on different hosts.
- A manifest requesting an unregistered domain fails deployment-mode validation.
- A missing or ambiguous group and a group found only in the other inventory fail before any host operation.
- Empty registry state passes without suppressing schema or validator tests.
- Deployment mode rejects unsupported `private_ip` instead of silently falling back to `docker_edge`.

## Source reference

REG-01, REG-03, REG-04, REG-08, RTE-02; P-01, P-03, P-04, P-08.

## Verify

- Run the registry validator against the fixture set and both completed inventories.
- Assert each malformed registry or manifest fixture exits nonzero with the expected rule.
- Use a canary value in a fixture and confirm it is absent from validator output.

## Out of scope

Capacity aggregation, Compose policy, the CI ruleset update or live host access.
