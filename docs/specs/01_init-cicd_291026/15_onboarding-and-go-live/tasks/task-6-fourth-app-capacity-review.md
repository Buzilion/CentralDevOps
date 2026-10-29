# Task 6: Fourth-app capacity review

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Task 2; spec 06 registry/capacity checks and spec 14 host observations |
| Needs | Reviewed registry/inventory revisions and the current count of distinct registered apps |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Create a repeatable fourth-app sizing review and record the real review when that onboarding trigger is reached.

## Relevant files or references

- Create `docs/runbooks/capacity-review.md`
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (REG-06, REG-07, REG-12)
- `docs/prd/01_init-cicd_291026/prd-v1.md` (M11)
- v5 design §§2, 9.3, 14.2
- Spec 03 inventory capacity facts; spec 06 capacity validation; spec 14 host observations

## Proposed approach

1. Count distinct apps, not Environment registry files, and document the trigger as the fourth app onboarding.
2. Create a worksheet recording the review date, reviewer, app count, registry/inventory revisions, host placement, and available host observations.
3. For each host, confirm `capacity_budget_mib` is valid and compare the total registered app memory limits with that budget using the spec 06 result. Review per-app CPU and memory ceilings and note observed usage/headroom where telemetry is available.
4. Keep enforced limits distinct from observations. Do not introduce a host CPU budget, hard-code a host size, or change inventory budgets outside a reviewed PR.
5. Record the decision (`no change`, follow-up, or reviewed sizing change), rationale, and an owner/date for each follow-up.
6. If fewer than four apps are registered, verify that the guide carries the trigger, record `not yet triggered`, and do not claim a real REG-12 review from fixture results.

## Acceptance criteria

- `docs/runbooks/capacity-review.md` contains a reusable procedure and a record format.
- If four or more distinct apps are registered, a dated review of the real registry/inventory state exists.
- If fewer than four apps are registered, the record clearly says `not yet triggered`; fixture results are not presented as a completed review.
- The review uses the inventory budget and spec 06 memory result, and does not create a host CPU budget or bypass a capacity failure.
- Any proposed budget change has an owner and goes through the normal reviewed inventory/registry change path.

## Source reference

REG-06, REG-07, REG-12; parent PRD M11; v5 §§2, 9.3, 14.2; spec 03 and spec 06 capacity contracts.

## Verify

- Test the worksheet calculations with fixtures for multiple apps sharing a host and apps on separate hosts.
- Compare any real review totals with the reviewed registry, inventory budgets, and spec 06 CI result.
- Verify the trigger count uses distinct app identities rather than Staging/Production entries.

## Out of scope

Changing the capacity algorithm, selecting new VPS sizes, inventing CPU admission limits, or using a fixture as evidence that the fourth app was onboarded.
