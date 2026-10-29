# Task 1: Registry and manifest schemas

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Spec 01 and spec 03 checklists complete |
| Needs | No VPS access or credentials |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Create strict, versioned schema contracts for CentralDevOps registry entries and app-owned route manifests.

## Relevant files or references

- Create `deployment/schemas/registry.schema.json` and `deployment/schemas/app-manifest.schema.json`
- Create schema fixtures under `deployment/tools/tests/fixtures/`
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (`REG-01`, `REG-02`)
- `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md` (`RTE-02`)
- Spec sections: Registry schema, App manifest schema, Decisions D1–D3
- `docs/notes/requirements/02_init-cicd_291026/v3/centraldevops-deployment-contract.md` §§1–3 (illustrative only)

## Proposed approach

1. Use JSON Schema Draft 2020-12 and reject unknown properties at each object level.
2. Define the v5 registry fields and require each file's `app` and `environment` to agree with its canonical `apps/<app>/<environment>.yml` path.
3. Accept exactly `docker_edge` and `private_ip`; require a host port for `private_ip` and constrain any declared host port to the reserved 21000–29999 range.
4. Require production registry entries to require attestation. Keep database names conditional on `database.enabled`.
5. Define the manifest using only the REG-02 fields. Do not carry forward v3-only `app.name`, `edge_alias`, `routing.enabled` or timeout fields.
6. Pin the schema/YAML validation dependencies in `deployment/tools/requirements.txt`. Keep examples under test fixtures; do not create a real app registry entry.

## Acceptance criteria

- A compliant Staging registry, Production registry and manifest fixture pass.
- Missing required properties, wrong types, malformed values and unknown top-level or nested properties fail.
- `private_ip` with a valid host port passes schema validation; `private_ip` without a port fails.
- A Production entry with `require_attestation: false` fails.
- Manifest fixtures contain only the allowed request fields and never include runtime secret values.
- Schema fixtures are not discovered as production registry entries.

## Source reference

REG-01, REG-02, REG-04, REG-06, RTE-02; P-01, P-02, P-08; D1 to D3.

## Verify

- Run the schema validator against every positive and negative fixture.
- Run the repository's existing workflow and name checks after adding any dependency or workflow files.
- Inspect that schema errors identify a file and field without echoing fixture values.

## Out of scope

Global duplicate checks, inventory resolution, capacity sums, Compose rendering, deployment workflows or real app records.
