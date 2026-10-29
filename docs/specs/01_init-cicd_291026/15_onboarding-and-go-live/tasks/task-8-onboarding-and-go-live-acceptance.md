# Task 8: Onboarding and go-live acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Tasks 1-7 |
| Needs | All five gates `PASS`, the second-app Staging proof, and the normal CentralDevOps Production approval |
| Summary | Write `summaries/task-8-summary.md` when this task closes |

## Goal

Validate the full onboarding flow through a controlled Production deployment using the existing central workflow and approval path.

## Relevant files or references

- `docs/runbooks/app-onboarding.md`
- `docs/runbooks/production-go-live-record.md`
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (REG-09 to REG-12)
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-06)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-15, SEC-16, SEC-18)
- Specs 06 and 09-14

## Proposed approach

1. Confirm the second app's Staging proof and registry state remain valid, and confirm the CentralDevOps workflow tree is unchanged for onboarding.
2. Verify that every go-live gate in `production-go-live-record.md` is `PASS`; if not, stop before requesting Production.
3. Request Production with the same immutable digest that passed Staging, using the normal app workflow and CentralDevOps Production Environment approval.
4. Verify the central run result, app health, route, migration compatibility, and deployment record. Follow the existing rollback path if health fails.
5. Update the onboarding and go-live records with dated, sanitized evidence and close the task only after the complete flow succeeds.

## Acceptance criteria

- The second app follows the published onboarding contract and reaches Production only after all five gates pass.
- No CentralDevOps workflow edit or app-side server credential is introduced to onboard it.
- Production used an immutable digest, the required CentralDevOps approval, and the existing deployment/rollback path.
- The app passed its health check and the result is recorded without secrets or runtime values.
- App-owned schema changes remain backward compatible; CentralDevOps did not run an undeclared migration.
- The final go-live record is complete and consistent with the accepted gate evidence.

## Source reference

REG-09 to REG-12; DB-06; SEC-15, SEC-16, SEC-18; parent PRD §8; v5 §§11.3, 15.2-15.3.

## Verify

- Follow the app and central run URLs, compare the deployed digest with the Staging-verified digest, and confirm the Production Environment approval is present.
- Confirm the CentralDevOps workflow diff remains empty for onboarding.
- Confirm the go-live record has five `PASS` statuses and the task summary contains only sanitized evidence.

## Out of scope

Waiving an incomplete gate, adding an alternate Production path, or claiming go-live from a Staging-only run.
