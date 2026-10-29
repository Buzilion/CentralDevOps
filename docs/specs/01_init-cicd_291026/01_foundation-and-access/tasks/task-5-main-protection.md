# Task 5: Main branch ruleset

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | Task 1 (plan probe passed), Task 2 (CODEOWNERS on `main`), Task 4 (check names exist) |

## Goal

Enforce review and checks on `main` with a repository ruleset committed as `.github/rulesets/main.json` and applied with `gh api`.

## Context

CODEOWNERS and lint do nothing until the default branch requires them. The ruleset must be applied only after the check names have run at least once, otherwise pull requests wait forever for a check GitHub has never seen. A sole owner cannot approve their own pull request (Decision D6), so this task also settles the bypass question.

## Relevant files or references

- Create `.github/rulesets/main.json`; update `docs/runbooks/github-environments.md` (ruleset apply and audit commands, evidence)
- Spec sections: Design > GitHub settings, Decisions D5 and D6, Error Behavior

## Proposed approach

1. Write the ruleset payload: target `branch`, include `refs/heads/main`, enforcement `active`, rules `deletion`, `non_fast_forward`, `pull_request` (1 approval, code-owner review, dismiss stale reviews, require last-push approval), `required_status_checks` (`workflow-lint`, `naming-and-secrets`, strict).
2. Ask the owner whether a second reviewer exists. If not, add the owner as a bypass actor with mode `pull_request` and record the exception and its removal condition in the runbook. Do not add any other bypass.
3. Apply with `gh api -X POST repos/Buzilion/CentralDevOps/rulesets --input .github/rulesets/main.json`; record the ruleset id in the runbook for updates (`PUT`).
4. Test on a scratch branch: a direct push to `main` is refused; a pull request touching `.github/workflows/` cannot merge without a code-owner review; a pull request with a failing check cannot merge. Delete the scratch branch afterwards.

## Acceptance criteria

- The ruleset is active on `main` and matches the committed JSON.
- A direct push, force push and branch deletion on `main` are refused.
- A pull request touching a protected path cannot merge without code-owner review (or the recorded bypass, if D6 applies).
- A pull request with a failing `workflow-lint` or `naming-and-secrets` check cannot merge.
- The runbook documents the apply and update commands and any bypass exception.

## Source reference

SEC-13, SEC-14, NFR-17; F-03, F-04.

## Verify

```powershell
gh api repos/Buzilion/CentralDevOps/rulesets --jq "[.[] | {name, enforcement}]"
# expect the main ruleset with enforcement "active"
git push origin HEAD:main
# from a scratch clone with no bypass: expect "protected branch / repository rule violations"
gh pr merge <scratch-pr-with-failing-check> --squash
# expect refusal while checks fail
```

## Out of scope

Approver model changes after the deployment team exists (spec 15), tag rules, signed commits.
