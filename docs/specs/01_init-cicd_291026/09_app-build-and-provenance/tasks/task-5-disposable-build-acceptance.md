# Task 5: Disposable build acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md` |
| Depends on | Tasks 1-4 |
| Needs | Completed proof workflow, GHCR access through `GITHUB_TOKEN`, and no production credentials |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Prove the full build contract, document the app-side operator steps, and remove all temporary test resources.

## Relevant files or references

- Disposable app repository and test GHCR package
- Create `docs/runbooks/app-build-and-provenance.md`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-02` to `REL-04`, `REL-15`)
- Spec 09: Invariants, Error Behavior, and Testing Strategy

## Proposed approach

1. Run a successful build from `main` and record sanitized evidence for the selected ref, resolved commit, test result, digest, tag, metadata artifact, and attestation verification.
2. Exercise invalid-ref, non-main workflow-ref, failing-test, publication-failure, and attestation-failure behavior where safe; verify no failed path reports a successful release.
3. Confirm the GHCR package is linked to the disposable app repository through `org.opencontainers.image.source`.
4. Write `docs/runbooks/app-build-and-provenance.md` with the build input contract, permissions, summary/artifact fields, digest-only deployment rule, attestation check, and failure handling. Do not document the full deploy-to-Production flow owned by spec 12.
5. Delete the named disposable repository and test GHCR package, then verify they are absent. Record sanitized run URLs, tested commit, dates, outcomes, and cleanup in this task summary.

## Acceptance criteria

- A successful run passes tests, publishes the expected image/tag, emits matching digest metadata, and has a verifiable attestation for the same commit and workflow.
- A failing test, invalid source ref, or attestation failure cannot produce a successful release summary or metadata artifact.
- The package links to the disposable repository and the summary/artifact contain no secret or runtime data.
- The runbook matches the tested workflow contract and keeps build separate from deployment.
- The disposable repository and its test package are removed; no temporary credential or production resource remains.
- `summaries/task-5-summary.md` records dated, sanitized evidence and cleanup confirmation.

## Source reference

REL-02, REL-03, REL-04, REL-15; NFR-12, NFR-15; v5 §§7.1, 16 step 8.

## Verify

- Review positive and negative workflow run results and confirm the runbook accurately describes them.
- Verify the repository and GHCR package are absent after cleanup; check that no test secret or deploy credential was created.
- Review the task summary for dates, run URLs, tested commit, verification results, cleanup evidence, and absence of credentials.

## Out of scope

Production app onboarding, CentralDevOps deployment authorization, real app or production GHCR cleanup, and a reusable app starter template.
