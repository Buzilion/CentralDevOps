# Task 3: Implement the central proof verifier

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Task 2 |
| Summary | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-3-summary.md` (write when the task closes) |

## Goal

Add a temporary CentralDevOps workflow that validates the dispatch actor and OIDC proof in a no-Environment job, then associates a harmless dependent job with the verified matching Environment.

## Context

Authorization must happen before any Environment or secret is used, so the verifier job cannot declare an Environment or access secrets. The second job demonstrates Environment selection only after verification and must not read secrets or perform deployment work.

## Relevant files or references

- CentralDevOps: `.github/workflows/dispatch-proof.yml`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `.github/rulesets/main.json` and the spec 01 runbook for branch and workflow controls
- `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§8.1–8.2

## Proposed approach

1. Add a separate `workflow_dispatch` proof workflow, with minimal top-level and per-job permissions and no `pull_request_target` trigger.
2. In an `authorize` job with no Environment, reject unless the CentralDevOps run ref is exactly `refs/heads/main`; do not produce an authorized output for any other ref.
3. Validate the OIDC JWT signature against GitHub's published JWKS and check issuer, expiry, audience, required claims, expected repository, `.github/workflows/deploy.yml`, allowed ref, source Environment, and payload-to-audience binding.
4. Recompute the audience from the exact sealed-bundle bytes after decoding the dispatched base64 value once. Reject malformed encoding and any mismatch.
5. Derive the source app from the verified `repository` claim using the spec's inline test fixture; do not accept an app name or repository as a dispatch input.
6. Independently validate the dispatch actor from trusted event context against the expected installed GitHub App identity. Fail closed if either proof is missing or incorrect.
7. Emit only validated non-sensitive values needed by the dependent job. Never emit the JWT, bundle, or bundle contents.
8. Add a dependent job whose Environment is selected only from the verified authorization output and is restricted to `Staging` or `Production`. It performs a harmless assertion and reads no variables or secrets.
9. Keep this proof workflow separate from infrastructure workflows and future production deployment workflows.

## Acceptance criteria

- A valid dispatch from the throwaway repository passes both independent checks.
- The authorization job has no Environment and grants no secret access.
- The Environment-bound job depends on successful authorization and selects only the verified matching Environment.
- The workflow rejects CentralDevOps runs from refs other than `main`.
- No token or bundle content appears in logs, outputs, or artifacts.

## Source reference

DEP-02, DEP-06, DEP-08, DEP-16, DEP-20, SEC-10; spec requirements T-03 to T-06.

## Verify

- Run the positive dispatch and verify the central job's non-sensitive claims match the expected repository, workflow, ref, Environment, run ID, and attempt.
- Confirm GitHub run details show the downstream job associated with the matching CentralDevOps Environment and that no Environment secrets were accessed.
- Confirm the verifier ran on CentralDevOps `main` and that no deployment or infrastructure job was invoked.
- Inspect all run outputs and artifacts for JWT or bundle leakage.

## Out of scope

The production authorizer, registry validation, replay prevention, provenance verification, VPS access, and deployment.
