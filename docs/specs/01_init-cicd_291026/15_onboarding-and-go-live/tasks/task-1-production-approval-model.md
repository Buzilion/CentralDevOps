# Task 1: Production approval model

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | None within this spec; all specs 01-14 must be complete before implementation |
| Needs | CentralDevOps Environment administration access; no Production deployment |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Resolve PRD Q6 and ensure the Production approval handoff follows the chosen SEC-18 model without creating a second default approval gate.

## Relevant files or references

- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-05, SEC-15, SEC-18)
- `docs/prd/01_init-cicd_291026/prd-v1.md` (Q6)
- `docs/design/variables-and-secrets.md` §2
- v5 design §§4.1, 17 item 6

## Proposed approach

1. Keep the repository owner as the required reviewer of the CentralDevOps `Production` Environment while no deployment team is assigned.
2. When a deployment team is assigned, replace the owner with that team as the required reviewer. The selected default is one approval by the team; do not retain the owner alongside the team as a second default approval.
3. Keep the CentralDevOps Production deployment branch restriction on `release/*`. Keep app Production Environments without reviewers by default so the central Environment remains the single approval gate.
4. Record the reviewer model and the date/settings evidence without recording private Environment data. If a deployment team is not yet assigned, record the handoff as pending and leave the owner configured.
5. Align the operator instructions in Task 2 and the reviewer field in the go-live record with the actual configuration.

## Acceptance criteria

- PRD Q6 is resolved as documented in spec decision D1.
- The CentralDevOps Production Environment has the owner as its reviewer until a deployment team is assigned; after assignment, the team replaces the owner.
- The CentralDevOps Production branch restriction is `release/*`, and app Production does not add a reviewer by default.
- The task does not claim SEC-18's post-assignment state is configured if no team has been assigned.
- The configuration evidence contains no secret values or private Environment data.

## Source reference

SEC-05, SEC-15, SEC-18; parent PRD Q6; v5 §§4.1, 17 item 6.

## Verify

- Inspect the CentralDevOps `Production` Environment reviewer and branch-protection settings.
- Inspect an app repository's `Production` Environment to confirm there is no second reviewer gate by default.
- Record the selected reviewer model and whether the team handoff is pending or complete.

## Out of scope

Production release approval, changes to deployment authorization, and adding app-side Production reviewers.
