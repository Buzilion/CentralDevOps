# Task 4: Verify rejection paths

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Tasks 2 and 3 |

## Goal

Demonstrate that invalid dispatch identity, OIDC claims, and request binding are rejected before the Environment-bound job starts.

## Context

The proof is not accepted based on a successful dispatch alone. Rejection tests must cover the trust boundaries in the spec while keeping all values synthetic and all test tokens out of logs and fixtures.

## Relevant files or references

- Disposable repository: `.github/workflows/deploy.yml`
- CentralDevOps: `.github/workflows/dispatch-proof.yml`
- CentralDevOps proof verifier tests, if added
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`

## Proposed approach

1. Add focused verifier tests for invalid signature, issuer, expiry, missing required claims, and malformed audience using generated test keys and synthetic claims; do not store live GitHub tokens in fixtures.
2. Exercise controlled live dispatches for a changed image reference, changed bundle, wrong repository/workflow/ref/Environment claim, and unexpected dispatch actor where GitHub permits safe test execution.
3. For each case, capture the failing check identifier and confirm the Environment-bound job did not start.
4. If a live claim cannot be safely forged, prove the rejection using a deterministic verifier test and document why a live dispatch was not applicable.
5. Do not weaken branch rules, Environment protections, or action permissions to make a negative case pass.

## Acceptance criteria

- Tests cover each rejection class in spec T-06, using deterministic tests for unforgeable GitHub-issued claims when needed.
- Changed request data never passes the audience binding.
- Every rejection occurs before the Environment-bound job and emits no JWT or bundle data.
- The tests make no network connection to a VPS and use no deployment credentials.

## Source reference

DEP-02, DEP-16, SEC-10, SEC-12; spec requirement T-06.

## Verify

- Run the verifier's focused test suite and confirm each invalid fixture fails with the expected non-sensitive check identifier.
- Review the GitHub run graph for each live rejection and confirm the Environment-bound job was skipped or not created.
- Inspect test fixtures and logs to ensure no live JWT, private key, App token, or bundle contents are present.

## Out of scope

Exhaustive negative testing of the production deployment authorizer, replay storage, registry policy, or deploy workflow.
