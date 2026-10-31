# Task 5: Protected branches ruleset

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | Task 1 (plan probe passed), Task 2 (CODEOWNERS coverage), Task 4 (check names exist) |

## Goal

Enforce the same review and checks on `main` and `release/*` with the repository ruleset committed as `.github/rulesets/main.json` and applied with `gh api`.

## Context

CODEOWNERS and lint do nothing until protected branches require them. The ruleset must be applied only after the check names have run at least once, otherwise pull requests wait forever for a check GitHub has never seen. A sole owner cannot approve their own pull request (Decision D6), so this task also settles the bypass question.

## Relevant files or references

- Create `.github/rulesets/main.json`; update `docs/runbooks/github-environments.md` (ruleset apply and audit commands, evidence)
- Spec sections: Design > GitHub settings, Decisions D5 and D6, Error Behavior

## Proposed approach

1. Write the ruleset payload: target `branch`, include both `refs/heads/main` and `refs/heads/release/*`, enforcement `active`, rules `deletion`, `non_fast_forward`, `pull_request` (1 approval, code-owner review, dismiss stale reviews, require last-push approval), `required_status_checks` (`workflow-lint`, `naming-and-secrets`, strict). Apply identical rules to both ref patterns.
2. The collaborator audit shows only `@aldoawp`, who is also the sole codeowner. Apply Decision D6 by adding only that user as a bypass actor with mode `pull_request`; record the exception and removal condition in the runbook. Do not add any other bypass.
3. Apply with `gh api -X POST repos/Buzilion/CentralDevOps/rulesets --input .github/rulesets/main.json`; record the ruleset id in the runbook for updates (`PUT`).
4. Against each target pattern, test that direct pushes, force-pushes and deletion are refused; a pull request touching `.github/workflows/` cannot merge without code-owner review; and a pull request with a failing required check cannot merge. Delete any scratch branches after the tests.

## Acceptance criteria

- The ruleset is active and matches the committed JSON; its target patterns include `refs/heads/main` and `refs/heads/release/*`.
- Direct pushes, force-pushes and branch deletion are refused for both `main` and `release/*`.
- A pull request touching a protected path cannot merge without code-owner review (or the recorded bypass, if D6 applies).
- A pull request with a failing `workflow-lint` or `naming-and-secrets` check cannot merge.
- The runbook documents the apply and update commands and any bypass exception.

## Source reference

SEC-13, SEC-14, NFR-17; F-03, F-04.

## Verify

```powershell
gh api repos/Buzilion/CentralDevOps/rulesets --jq "[.[] | {name, enforcement, include: .conditions.ref_name.include}]"
# expect an active ruleset whose include patterns contain refs/heads/main and refs/heads/release/*
gh api repos/Buzilion/CentralDevOps/rulesets/<ruleset-id> --jq ".bypass_actors"
# expect only @aldoawp with bypass_mode "pull_request" until a second codeowner/reviewer is added
git push origin HEAD:main
# from a scratch clone with no bypass: expect "protected branch / repository rule violations"
# Repeat the push, PR-review, required-check and deletion tests against a scratch release/* branch.
gh pr merge <scratch-pr-with-failing-check> --squash
# expect refusal while checks fail
```

## Out of scope

Approver model changes after the deployment team exists (spec 15), tag rules, signed commits.
