# Task 4: Health check and automatic rollback

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Task 3 |
| Needs | Disposable Staging host, healthy previous-release fixture and unhealthy image fixture |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Replace the current containers only after transaction preparation succeeds, enforce the health timeout and restore the previous release when the new container does not become healthy.

## Relevant files or references

- `deployment/scripts/centraldevops-deploy`
- `docs/design/variables-and-secrets.md` §3.2 (`DEPLOY_HEALTHCHECK_TIMEOUT`)
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-11, DEP-12)
- `docs/prd/01_init-cicd_291026/prd-v1.md` (NFR-05, NFR-06)
- v5 design §8.4

## Proposed approach

1. Apply the prepared Compose release and wait for the routed service's container health check using `DEPLOY_HEALTHCHECK_TIMEOUT`, default `90` seconds.
2. Confirm that the running service uses the requested digest and report the health result without printing environment contents.
3. On timeout or unhealthy status, fail the deployment. If the database password changed, restore its previous value first; then restore the previous runtime files and image and bring the previous release back.
4. Do not call the route entrypoint on a health-check failure. The route must remain unchanged because route activation happens only after health passes.
5. If there was no previous release, stop the failed app and leave it stopped. Do not report a rollback to a nonexistent version.
6. Surface rollback errors and preserve the previous-state snapshot for diagnosis. A failed rollback remains a failed deployment.

## Acceptance criteria

- A healthy release runs the exact requested digest and records the health-check outcome.
- A forced health-check failure restores the prior digest and runtime configuration, restores any rotated database password before the prior app environment, and leaves the route unchanged.
- A forced first-deployment health failure leaves the app stopped.
- Timeout configuration defaults to 90 seconds and can be overridden only through the selected Environment's approved variable.
- A failed rollback is explicit in the workflow result and is never reported as success.

## Source reference

DEP-11, DEP-12; parent PRD NFR-05, NFR-06; DB-04; v5 §8.4.

## Verify

- Exercise health success, timeout, rollback success and rollback failure using disposable fixtures.
- Compare the before/after digest, runtime files, DB credential contract and route fingerprint.
- Confirm workflow output contains no `.env` values and typical Staging deployment duration remains within the five-minute target, excluding approval wait.

## Out of scope

Route activation and external HTTPS smoke testing (Task 5), backup restoration (spec 13) or application schema rollback.
