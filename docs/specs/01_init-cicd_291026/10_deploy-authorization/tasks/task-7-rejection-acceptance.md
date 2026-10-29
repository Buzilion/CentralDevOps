# Task 7: Prove rejection boundaries and record evidence

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Tasks 1–6 |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-7-summary.md` (write when the task closes) |

## Goal

Prove the authorization and preflight path accepts only the intended request, rejects each invalid boundary before approval or host access, and leaves sanitized evidence.

## Relevant files or references

- `.github/workflows/deploy-app.yml`
- `deployment/tools/tests/`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/`
- `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/`
- `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/`
- `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-7-summary.md`

## Proposed approach

1. Run the positive synthetic verifier, registry, attestation, replay and bundle-preflight suites. Keep registry records and keys in fixtures, not the production `apps/` path.
2. Exercise negative actor, central ref, signature, issuer, expiry, audience, repository, workflow, source ref, Environment, correlation metadata, digest, provenance, placement, replay, archive, manifest, Compose and runtime-key cases.
3. Prove a duplicate request cannot reach the Environment-bound job, including two concurrent dispatches and a replay while Production is waiting for approval.
4. Prove a changed Environment, image reference or ciphertext fails request binding. Confirm wrong-host and cross-Environment fixtures fail before a host connection.
5. Where a live workflow run is needed, use only a reviewed disposable registry entry and synthetic bundle. If no safe test registration exists, leave live acceptance blocked; do not use a production app or bypass the registry.
6. Scan logs, summaries, artifacts and temporary output for synthetic JWT, bundle and canary markers. Record sanitized run URLs, commit, tool versions, outcomes and remaining limits.
7. Write the final summary only after all acceptance checks pass, then check off the task and update the spec checklist.

## Acceptance criteria

- Every negative case fails at its owning authorization or preflight check, with no Environment job for pre-approval failures.
- A positive synthetic request completes authorization and preflight without a host connection or host mutation.
- Duplicate source tuples have only one successful authorization; a new source run attempt is independently testable.
- The pre-authorization correlation hash lets the app action locate the exact central run, including rejected requests, without guessing from time, Environment or digest.
- No JWT, bundle bytes, runtime value, private key, host address or rendered Compose JSON appears in repository files, logs, artifacts or summary.
- The task summary accurately records any test that could not be run; unresolved acceptance remains unchecked.

## Source reference

DEP-02 to DEP-07, DEP-10, DEP-13, DEP-16, SEC-12; spec 12 D5; requirements A-02 to A-13.

## Verify

- Run the focused unit/integration suites, actionlint, zizmor and repository secret-name checks.
- Review the positive and negative workflow run links and verify no rejected run selected an Environment.
- Search test logs and artifacts for canary markers and review the summary for sensitive values.

## Out of scope

Deploying to Staging or Production, proving health checks/rollback, creating production registry entries or changing GitHub protection rules.
