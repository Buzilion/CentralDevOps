# Task 4: Central run polling and reporting

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Task 3 |
| Needs | CentralDevOps workflow exposes the verified source run ID and attempt as a sanitized correlation value |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Make the app run wait for, identify, and accurately report the central run created by its own request.

## Relevant files or references

- `.github/actions/request-deploy/action.yml` and its helper code
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-10, REL-11)
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-03, DEP-14, DEP-15)
- v5 design §§7.2, 8.1–8.2, 13.4, 15.3
- Spec 02 source `run_id` and `run_attempt` claim contract

## Proposed approach

1. Use the dispatch App installation token to query Actions runs in CentralDevOps. Match the exact source `run_id` and `run_attempt` correlation emitted by the central workflow; verify the workflow and that its ref is permitted by the requested Environment before associating the run.
2. Refresh the short-lived installation token from the supplied App credentials before it expires if polling continues through a long approval wait. Reuse the same source correlation and never redispatch because a polling token expired.
3. Do not infer identity from creation time, app name, digest, Environment, actor alone, or the newest run. If no unique match exists, fail rather than report another deployment's result.
4. Poll until the matching central run reaches a terminal conclusion, including an approval wait for Production. Respect the app job's configured runtime; a wait timeout is a failure/unknown result, not success.
5. Exit successfully only when the central run concludes successfully. Map results to the finite statuses `success`, `failure`, `cancelled`, `timed_out`, or `unknown`; propagate every non-success as a nonzero action result.
6. Set the sanitized `central_run_url` and `central_run_result` outputs when known and write an app job summary with Environment, digest, central URL, and result. Never include a runtime value, OIDC token, App token, or bundle content.
7. Test concurrent synthetic requests so each app run links to its own central run, plus success, failure, cancellation, token refresh, approval wait, timeout, and ambiguous/missing correlation cases.

## Acceptance criteria

- The action links only the central run whose correlation matches its source run ID and attempt.
- The central workflow identity and `main` ref are checked before the run is accepted as the result.
- An installation token can be refreshed during a long wait without dispatching a duplicate request.
- A Production approval wait does not cause the app run to report premature failure or success.
- A failed, cancelled, timed-out, ambiguous, or missing central run cannot produce a successful app run.
- The app summary and action outputs contain a central run URL and sanitized result when available, and no runtime secret or token.

## Source reference

REL-10, REL-11; DEP-03, DEP-14, DEP-15; v5 §§7.2, 8.1–8.2, 13.4.

## Verify

- Run isolated synthetic requests concurrently and compare each app result to its central run correlation.
- Exercise terminal success and each failure state; confirm exit codes and summary links.
- Review logs, outputs, and job summaries for canary-secret, token, and bundle-content leakage.

## Out of scope

Dispatch authorization, the central deployment decision, app workflow creation, and manual rollback documentation.
