# Task 5: Route activation and HTTPS smoke test

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Task 4; spec 07 checklist complete |
| Needs | Disposable Staging app, controlled test domain and CA staging configuration |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Activate routes only after app health passes, then prove the external HTTPS endpoint from the runner and apply spec 07's Q8 decision consistently.

## Relevant files or references

- `deployment/scripts/centraldevops-route` (spec 07 `apply` and `confirm` contract)
- `.github/workflows/deploy-app.yml`
- `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` (RTE-04 to RTE-07, RTE-11 and Q8 decision)
- `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md`
- v5 design §§8.3, 10.3

## Proposed approach

1. After internal health passes, invoke the idempotent route `apply` operation using only the registry/manifest values already validated by spec 10. Do not edit Nginx files from the workflow.
2. Keep route operations on spec 07's shared proxy lock, including operations shared with other apps and certificate renewal.
3. Run a bounded external HTTPS smoke test from the central runner and include its result in the sanitized deployment summary.
4. Call route `confirm` only after the smoke test succeeds. Do not confirm a new or changed route after failure.
5. If the smoke test fails, fail the deployment but do not automatically roll back the app or route. Tell the operator to diagnose the endpoint and manually redeploy the previous known-good digest if needed.
6. Preserve spec 07's independent rollback behavior for route-plan or Nginx validation failures; do not conflate those errors with a post-activation smoke-test failure.

## Acceptance criteria

- The route entrypoint is never called before the container health check passes.
- An unchanged route causes no rewrite or proxy reload.
- A passing HTTPS smoke test is visible in the run summary and is followed by route confirmation.
- A failing HTTPS smoke test fails the run, does not call `confirm`, and does not automatically roll back the app or route.
- A failed container health check still leaves the prior route unchanged.

## Source reference

RTE-04 to RTE-07, RTE-11; DEP-09, DEP-12; parent PRD Q8; v5 §§8.3, 8.4, 10.3.

## Verify

- Use only a disposable Staging host and a controlled test domain; issue test certificates through the CA staging endpoint.
- Test healthy route activation, unchanged route activation, a controlled smoke-test failure and a health failure before route activation.
- Compare route fingerprints and proxy reload events; confirm no Production certificate or service is used.

## Out of scope

Nginx/Certbot role implementation, route templates, DNS policy or automated rollback after smoke-test failure (spec 07 owns the first three; Q8 rejects the last).
