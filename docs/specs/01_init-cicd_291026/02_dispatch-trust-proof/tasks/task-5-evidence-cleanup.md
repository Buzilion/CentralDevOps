# Task 5: Record evidence and clean up

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Tasks 1 to 4 |
| Summary | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-5-summary.md` (write when the task closes; this is also the sanitized proof report) |

## Goal

Record sanitized evidence for the trust proof and remove or revoke every test-only repository, credential, and workflow resource.

## Context

Spec 02 is an acceptance spike. Its value is a reproducible result and a clean removal of its temporary trust path, not a permanent test repository or an early production implementation.

## Relevant files or references

- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-5-summary.md`
- The temporary resources recorded in Task 1

## Proposed approach

1. Capture the sanitized evidence needed for the final report before deleting its sources: positive and negative run URLs, non-sensitive claims, check results, Environment selection, and the CentralDevOps commit. Do not copy tokens or bundle contents.
2. Remove the proof-only CentralDevOps workflow and temporary test code after capturing that evidence.
3. Revoke or remove test-only App credential access, delete the disposable repository, and remove any test-only Environment resources.
4. Verify cleanup by listing only the exact resources recorded in Task 1 and confirming no temporary credential access remains.
5. Confirm no token, bundle contents, App private key, or other credential appears in the final report, logs, artifacts, or committed files.
6. After cleanup is verified, write the sanitized final report in this task's summary file. Close each task only after its acceptance criteria are verified, write its sanitized summary, and update its checklist item. Leave any unmet criterion unchecked and report it as blocked.

## Acceptance criteria

- A sanitized report exists and contains evidence for all T-01 to T-08 requirements.
- No JWT, installation token, private key, bundle content, or secret value is present in the report or repository.
- Temporary credentials are revoked and the disposable repository and proof-only workflow/resources are removed.
- The checklist reflects only verified task results; unresolved gaps remain unchecked and are reported.

## Source reference

DEP-20, SEC-12, SEC-15; spec requirements T-07 and T-08.

## Verify

- Review the report and confirm every result links to a relevant run or test without exposing credentials.
- Search the repository and run artifacts for test token markers and secret canaries.
- Confirm the disposable repository is deleted and App credential access is revoked.
- Confirm the proof-only workflow no longer exists on CentralDevOps after evidence capture.

## Out of scope

Production workflow implementation, production App credential rollout, or updating the checklist for spec 01.
