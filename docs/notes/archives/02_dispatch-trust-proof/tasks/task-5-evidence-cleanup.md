# Task 5: Record evidence and clean up

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Tasks 1 to 4 |

## Goal

Record sanitized evidence for the trust proof and remove or revoke every test-only repository, credential, and workflow resource.

## Context

Spec 02 is an acceptance spike. Its value is a reproducible result and a clean removal of its temporary trust path, not a permanent test repository or an early production implementation.

## Relevant files or references

- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-5-summary.md`
- The temporary resources recorded in Task 1

## Proposed approach

1. Summarize the positive run, negative-case results, validated non-sensitive claims, Environment selection, CentralDevOps commit, and run URLs.
2. Confirm no token, bundle contents, App private key, or other credential appears in the report, logs, artifacts, or committed files.
3. Remove the proof-only CentralDevOps workflow and temporary test code after preserving sanitized evidence.
4. Revoke/remove test-only App credential access, delete the disposable repository, and remove any test-only Environment resources.
5. Verify cleanup by listing the exact recorded resources and confirming no temporary credential access remains.
6. Update the spec 02 checklist only after Tasks 1–4 pass and cleanup is verified. Record any unmet acceptance criterion as blocked rather than marking it complete.

## Acceptance criteria

- A sanitized report exists and contains evidence for all T-01 to T-07 requirements.
- No JWT, installation token, private key, bundle content, or secret value is present in the report or repository.
- Temporary credentials are revoked and the disposable repository and proof-only workflow/resources are removed.
- The checklist reflects only verified task results; unresolved gaps remain unchecked and are reported.

## Source reference

DEP-20, SEC-12; spec requirement T-07.

## Verify

- Review the report and confirm every result links to a relevant run or test without exposing credentials.
- Search the repository and run artifacts for test token markers and secret canaries.
- Confirm the disposable repository is deleted and App credential access is revoked.
- Confirm the proof-only workflow no longer exists on CentralDevOps after evidence capture.

## Out of scope

Production workflow implementation, production App credential rollout, or updating the checklist for spec 01.
