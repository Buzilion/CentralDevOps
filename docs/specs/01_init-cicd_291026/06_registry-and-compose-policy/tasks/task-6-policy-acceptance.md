# Task 6: Policy acceptance and evidence

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Tasks 1–5 |
| Needs | Passing required CI check; synthetic fixtures only |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Prove the registry, manifest, capacity and rendered Compose checks work together, then record sanitized evidence for the next dependent spec.

## Relevant files or references

- `deployment/tools/validate-registry.py`
- `deployment/scripts/centraldevops-compose-policy`
- `.github/actions/validate-app-manifest/action.yml`
- `deployment/tools/tests/`
- `docs/runbooks/registry-and-compose-policy.md`
- `docs/specs/01_init-cicd_291026/07_routing-and-tls/` (downstream consumer when created)

## Proposed approach

1. Run the full validator suite on synthetic Staging and Production fixtures without adding them under the production `apps/` path.
2. Exercise the deployment-mode contract with a verified-identity fixture, valid digest, compliant manifest and rendered Compose file.
3. Exercise the app-manifest entry point with a pull-request-style fixture and a pinned CentralDevOps source revision; verify it requires no registry secrets.
4. Confirm invalid schema, duplicate domain, duplicate private port, over-capacity inventory, unsupported `private_ip`, invalid Compose interpolation and unsafe override each fail before any host operation.
5. Confirm the required `registry-policy` status passes for the clean state and fails for an invalid fixture.
6. Confirm logs and test output do not contain runtime canaries, rendered JSON or secret-like values.
7. Record commands, tool versions, pass/fail results and unresolved limitations in `summaries/task-6-summary.md`. Do not include host addresses, credentials or runtime values.

## Acceptance criteria

- Every P-01 through P-08 requirement has a passing positive and/or negative test in its owning test suite.
- App manifest pull-request validation and central deployment-mode validation both reject the same invalid schema fixture.
- The complete local validation command and required CI job both pass.
- Invalid registry, manifest, capacity or Compose input cannot be represented as success or continue to host operations.
- The summary is sanitized and names any required follow-up for spec 10, 12 or 15.
- No real app registry record or host configuration was created as test data.

## Source reference

REG-01 to REG-08; RTE-02; P-01 to P-08.

## Verify

- Run all Python tests and all schema/Compose integration tests.
- Run the repository workflow linters and validate the clean and negative CI fixtures.
- Review the final summary for secrets, host facts and unsupported claims.

## Out of scope

Staging deployment, live host measurements, route activation, onboarding rehearsal or private-IP deployment.
