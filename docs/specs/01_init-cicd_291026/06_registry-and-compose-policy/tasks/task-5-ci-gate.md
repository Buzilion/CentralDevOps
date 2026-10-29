# Task 5: Required registry policy CI gate

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Tasks 1–4; spec 01 workflow lint, ruleset and runbook are complete |
| Needs | No GitHub secrets or VPS credentials; code-owner review |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Run registry, inventory, capacity, Compose and test validation on every pull request, and make the result a required `main` status check.

## Relevant files or references

- Update `.github/workflows/lint.yml`
- Update `.github/rulesets/main.json`
- Create `.github/actions/validate-app-manifest/action.yml`
- Update `docs/runbooks/github-environments.md`
- Create `docs/runbooks/registry-and-compose-policy.md`
- Spec sections: CI and downstream call contract, Deliverables
- Spec 01 `lint.yml` and GitHub Environments runbook

## Proposed approach

1. Add a `registry-policy` job to the existing lint workflow for pull requests and pushes to `main`, using `ubuntu-24.04` as established by spec 01.
2. Grant no permissions beyond read-only checkout. Pin actions and Python/Docker Compose tooling according to repository conventions; do not use Environment secrets.
3. Run schema validation, registry/inventory integrity, capacity checks, all unit tests and rendered Compose fixtures. An empty production `apps/` directory must not skip the test suite.
4. Add the exact `registry-policy` status context to the committed ruleset and the apply/audit runbook. Apply and audit the live ruleset with the documented `gh api` procedure; do not close this task until the live settings require the check.
5. Provide a composite app-manifest validation entry point that app pull-request workflows can call with a pinned CentralDevOps revision and a workspace-relative manifest path. Reject paths resolving outside the workspace. It must need no secrets and validate schema only; registry cross-checking remains in central deployment preflight.
6. Document local commands, required inventory facts, failure rule IDs, the app-CI invocation and the sanitized-output guarantee. Do not turn this into the REG-10 app onboarding guide.
7. Document the validator invocation contract for specs 10 and 12; those specs remain responsible for wiring it into their workflows.

## Acceptance criteria

- `registry-policy` runs on pull requests and pushes to `main` and has no secrets or host access.
- The workflow installs only pinned dependencies and runs the same validators used by deployment preflight.
- App pull-request CI can validate a manifest with the pinned CentralDevOps entry point without exposing runtime values or requiring registry credentials.
- The action accepts only a manifest path relative to the caller workspace and passes it to the validator without shell interpolation.
- The required status context appears in the ruleset and runbook, and the live ruleset audit reports it as required.
- A valid empty registry passes after all fixtures and tests run; a deliberately invalid fixture fails the job.
- Workflow lint and the naming/secrets checker remain passing.

## Source reference

REG-01, REG-04, REG-07; SEC-13, SEC-14; P-04, P-07, D6.

## Verify

- Run `actionlint`, `zizmor`, the repository name checker and the focused Python test suite.
- Inspect the workflow for least-privilege permissions, pinned actions and no direct shell interpolation of untrusted data.
- Apply and audit the live ruleset; confirm the required status context in the payload, runbook and GitHub settings is identical.

## Out of scope

Changing GitHub Environment protections, wiring the app validator into a specific app repository, app onboarding documentation or adding a deployment workflow.
