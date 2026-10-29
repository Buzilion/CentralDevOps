# Task 4: Reject replayed deployment requests

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Tasks 1–3 |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-4-summary.md` (write when the task closes) |

## Goal

Allow only one authorization for each verified source repository, `run_id` and `run_attempt`, including concurrent dispatches and Production requests waiting for approval.

## Relevant files or references

- `.github/workflows/deploy-app.yml`
- `deployment/tools/replay-guard.py`
- `deployment/tools/tests/test_replay_guard.py`
- `docs/design/infrastructure-contracts-and-invariants.md` §2
- v5 design §8.1 and §12.3
- `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md`
- `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` D5

## Proposed approach

1. Have the unprivileged `derive-request-key` job calculate only a fixed-length hash from the untrusted token payload and emit it as a correlation locator. In `authorize`, recompute the key from the verified claims and require an exact match; the locator is not a replay claim.
2. Serialize authorization jobs with that key using job-level concurrency, `queue: max` and `cancel-in-progress: false`. Queue overflow is a failed request. Do not treat concurrency by itself as replay protection.
3. Implement `replay-guard.py` with the job's read-only `GITHUB_TOKEN`. Search only prior `workflow_dispatch` attempts for this workflow on `main`; page through every result and scan logs in memory for the exact marker `REPLAY-CLAIM-V1:<hash>`.
4. Exclude only the current central run attempt. Include earlier attempts of the same central run. Do not extract arbitrary archive paths or print/download logs to workflow artifacts.
5. After all other authorization checks pass, emit the replay marker to the current authorize-job log and sanitized summary. A later serialized request must find it and fail before the Environment job. Spec 12 uses the separate pre-authorization correlation marker to locate both successful and rejected runs.
6. Set and audit Actions log retention to at least 90 days. Treat API errors, incomplete pagination, missing eligible logs, rate limits and inadequate retention as authorization failures. Spec 11 also checks and records the tuple in its durable host deployment record before mutation.

## Acceptance criteria

- Two concurrent requests with the same verified tuple cannot both pass authorization; the second never starts the Environment-bound job.
- A later replay is rejected even when its Environment, digest or ciphertext differs; a new source `run_attempt` has a distinct claim.
- A `REQUEST-CORRELATION` marker from a rejected request never counts as a replay claim.
- Earlier attempts of a re-run central workflow are scanned and a previously claimed tuple is rejected.
- Incomplete run history, unavailable logs, rate limiting or short retention fails closed without writing a success-shaped output.
- Only the SHA-256 correlation and replay markers are emitted; the raw repository/run tuple, JWT, bundle and downloaded logs are not printed or uploaded.

## Source reference

DEP-03; requirements A-10.

## Verify

- Run unit tests for key construction, pagination, all-run-attempt scanning, marker matching and fail-closed API cases.
- Exercise two duplicate dispatches concurrently in a controlled test; confirm one reaches authorization and the other fails before Environment selection.
- Review the Actions retention setting and inspect logs/artifacts for token or bundle leakage.

## Out of scope

Host-side locking or the durable deployment record implementation; spec 11 must enforce that downstream check as defense in depth.
