# Task 1: Deploy job and approval gate

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md` |
| Depends on | Spec 10's authorization and preflight checklist |
| Needs | A CentralDevOps ref permitted by the selected Environment, `Staging` and `Production` Environments, and their protection rules |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Add the privileged deployment job after authorization without allowing the raw dispatch request to select secrets, an Environment or a host.

## Relevant files or references

- Extend `.github/workflows/deploy-app.yml`
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-08, DEP-16)
- `docs/design/variables-and-secrets.md` §§2, 3.2 and 4.3–4.4
- v5 design §§8.2–8.3
- Spec 10's authorized-plan output contract

## Proposed approach

1. Make the `deploy` job depend on successful authorization/preflight and consume the resolved app, Environment, host and digest outputs from spec 10. Do not promote raw dispatch inputs to trusted outputs.
2. Set the job's Environment from the validated Environment output. Keep all Environment-secret use, bundle decryption and SSH steps inside this job so the Production approval gate precedes them.
3. Keep Staging free of manual approval and require the CentralDevOps `Production` Environment protection for Production. Do not revalidate the already-verified source identity token after a human approval delay.
4. Restrict execution to a CentralDevOps workflow ref permitted by the selected Environment (any branch for `Staging`, `release/*` only for `Production`) and the permissions required by checkout, deployment and the sanitized result handoff.
5. Use a distinct concurrency group for each resolved app/Environment pair with `cancel-in-progress: false`. Do not share one group across all apps in an Environment.
6. Preserve explicit failure states for authorization, approval, deploy and cancellation; never report an approval-waiting or cancelled run as a deployment success.

## Acceptance criteria

- An unauthorized or preflight-failing request never starts the privileged job.
- A Staging deployment starts without a human approval step.
- A Production deployment waits in the CentralDevOps `Production` Environment before accessing Environment secrets or opening SSH.
- The Production target is selected from the authorized plan, not a dispatch input.
- A delayed approval does not cause the workflow to reject a request solely because its already-verified source identity token has expired.
- Different apps use different concurrency groups, so one app's pending run cannot be replaced by another app's deployment.

## Source reference

DEP-08, DEP-16; SEC-05, SEC-06; v5 §§8.1–8.3.

## Verify

- Validate workflow syntax and the existing workflow lint/name checks.
- Inspect the job dependency graph and verify that no step using Environment secrets can run before authorization and required Production approval.
- In GitHub, confirm the Production job reaches the pending-review state before any deploy step runs. Perform any delayed-approval integration test only in an explicitly approved controlled window.

## Out of scope

OIDC verification, registry/manifest/Compose preflight, replay protection or app-side polling (specs 10 and 12).
