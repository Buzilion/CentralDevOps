# Task 6: Release and rollback runbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Tasks 1 to 5 |
| Needs | Reviewed build/deploy workflow names and the central deployment result/rollback behavior from spec 11 |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Document the supported operator path from an immutable build digest through Staging and Production, including manual rollback by digest.

## Relevant files or references

- Create `docs/runbooks/app-release-and-rollback.md`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-13, REL-14)
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-08, DEP-12, DEP-18)
- v5 design §§15.2–15.3, 15.6

## Proposed approach

1. Document how an operator runs `build.yml`, copies the complete `image_ref` from its summary, and manually runs `deploy.yml` for `Staging`.
2. Document Staging verification and the separate manual `Production` request. State that the approval is in the CentralDevOps Production Environment and app-side Production adds no reviewer by default.
3. Document recovery of the previous known-good digest from the build/run history or deployment record and rerunning the same `deploy.yml` with that digest.
4. Explain the distinction between spec 11's automatic rollback after an unhealthy replacement and the operator's manual rollback after a completed release. Keep migrations backward-compatible.
5. Include expected app and central run URLs, safe failure triage, and the prohibition on tags, app-side SSH, or sharing runtime values in support logs.
6. Keep the guide consistent with the final workflow inputs and do not document any unsupported fallback for oversized bundles.

## Acceptance criteria

- The runbook gives a reproducible build → Staging → verification → Production flow.
- Manual rollback uses only the existing deploy operation and a previous full digest; no tag or separate workflow is suggested.
- Central Production approval is identified as the sole default approval gate.
- Failure steps distinguish automatic central health-check rollback from operator-triggered digest rollback.
- The guide contains no secret values and matches the delivered action/workflow interface.

## Source reference

REL-13, REL-14; DEP-08, DEP-12, DEP-18; v5 §§15.2–15.3, 15.6.

## Verify

- Walk through the documented steps with a synthetic app and digest.
- Check workflow input names, URL locations, approval ownership, and rollback instructions against the implemented files.
- Review the runbook for secret values, unsupported tag usage, or claims that a rollback can reverse app schema migrations.

## Out of scope

App onboarding template, schema-migration procedures, backup/restore runbooks, and implementation of central automatic rollback.
