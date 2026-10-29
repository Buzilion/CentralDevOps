# Task 1: GitHub Environments and plan probe

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | none (first task of the whole project) |
| Needs | Repository admin rights on `Buzilion/CentralDevOps` through `gh` |

## Goal

Prove that Environments with protection rules work for this repository, then create `Staging` and `Production` with the settings in the spec and record how to reproduce and audit them.

## Context

The whole deployment model relies on a Production approval gate in CentralDevOps. GitHub only allows Environments and their protection rules on public repositories for the Free plan; private repositories need Pro or Team. The PRD claims it works on Free, so this must be proven before any later spec stores a secret. On 2026-10-30 the repository was not reachable with the current `gh` token (`gh repo view Buzilion/CentralDevOps` failed to resolve it).

## Relevant files or references

- Create `docs/runbooks/github-environments.md`
- `docs/design/variables-and-secrets.md` §2 (protection table)
- Spec sections: Design > GitHub settings, Error Behavior
- Update `docs/specs/01_init-cicd_291026/01_foundation-and-access/checklist.md` only through the checklist workflow, not here

## Proposed approach

1. Confirm access: `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission`. Need `ADMIN`. If not reachable, stop and report (Error Behavior).
2. Record visibility and, if possible, the organization plan (`gh api orgs/Buzilion --jq .plan.name`; the plan is visible only to owners).
3. Create both Environments with `gh api -X PUT repos/Buzilion/CentralDevOps/environments/<Name>`. For `Production`, set `reviewers` to the owner user (look up the numeric id with `gh api users/<handle> --jq .id`), `prevent_self_review: false`, and `deployment_branch_policy` `{protected_branches:false, custom_branch_policies:true}`. Do the same branch policy for `Staging` without reviewers.
4. Add the `main` branch policy to each: `gh api -X POST repos/Buzilion/CentralDevOps/environments/<Name>/deployment-branch-policies -f name=main -f type=branch`.
5. If the API accepts the reviewer rule, run the audit. If it silently ignores the rule or refuses it, treat it as the plan failure in Error Behavior.
6. Write the runbook: preconditions, every apply command, every audit command with its expected `--jq` output, and an evidence log table (date, who, result).
7. Do not create any secret or variable.

## Acceptance criteria

- The environments list contains exactly `Production` and `Staging`.
- `Production` shows a required-reviewers protection rule naming the owner, and a deployment branch policy of `main` only.
- `Staging` shows no reviewers and a `main`-only policy.
- If the plan probe fails, the runbook records the failure and the task is reported blocked, not completed.
- The runbook lists commands that reproduce the settings from scratch and audit them.

## Source reference

SEC-01, SEC-05, SEC-15 (CentralDevOps side), SEC-17 (probe evidence); F-01, F-02, F-11.

## Verify

```powershell
gh api repos/Buzilion/CentralDevOps/environments --jq "[.environments[].name] | sort"
# expect ["Production","Staging"]
gh api repos/Buzilion/CentralDevOps/environments/Production --jq "[.protection_rules[].type] | sort"
# expect it to include "required_reviewers" and "branch_policy"
gh api repos/Buzilion/CentralDevOps/environments/Production/deployment-branch-policies --jq "[.branch_policies[].name]"
# expect ["main"]
gh api repos/Buzilion/CentralDevOps/environments/Staging/deployment-branch-policies --jq "[.branch_policies[].name]"
# expect ["main"]
```

## Out of scope

Variables, secrets, org-level settings (Task 6), app repository Environments (spec 02).
