# Task 3: Second-app onboarding proof

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Task 2 |
| Needs | A disposable second app repository, a controlled test domain, and completed specs 06 and 09-12 |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Prove that a second app can follow the onboarding guide and reach verified Staging without changing CentralDevOps workflows.

## Relevant files or references

- `docs/runbooks/app-onboarding.md`
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (REG-07, REG-09, REG-10)
- Specs 06, 09, 10, 11, and 12
- v5 design §§9.1-9.3, 15.2

## Proposed approach

1. Capture the CentralDevOps workflow tree/revision before the test. Use a disposable app repository and a controlled test domain; do not copy production credentials or real application data.
2. Follow the guide to submit reviewed Staging and Production registry entries. Confirm the normal registry, domain/port, and capacity checks pass.
3. Configure the test DNS records and app-owned `build.yml`, `deploy.yml`, Compose file, manifests, Environments, runtime values, and dispatch credentials according to the established contracts.
4. Build an immutable digest and deploy it to Staging through the standard request-deploy and central deployment path. Verify health, route, deployment result, and sanitized run correlation.
5. Compare the CentralDevOps workflow tree/revision with the baseline and confirm no workflow edit was needed.
6. Do not deploy the test app to Production before Task 7 records all five gates as `PASS`. Complete the Production leg in Task 8 after the normal approval is available.

## Acceptance criteria

- A distinct second app follows the onboarding guide and its registry changes pass the existing CI/capacity checks.
- The app deploys successfully to Staging by immutable digest and passes its health/routing verification.
- No CentralDevOps workflow is changed to onboard the app.
- The test uses no Production secret or real production data.
- The Production step remains explicitly gated until Task 7 is complete.

## Source reference

REG-07, REG-09, REG-10; v5 §§9.1-9.3, 15.2; specs 06, 09-12.

## Verify

- Inspect the registry and app PR checks, the Staging deployment result, health verification, and sanitized run URLs.
- Diff the CentralDevOps workflow tree/revision against the pre-test baseline.
- Confirm no secret values appear in logs, artifacts, run summaries, screenshots, or the task summary.

## Out of scope

Production deployment before all go-live gates pass, permanent onboarding of a real customer app, or modifying central workflow logic to special-case the test app.
