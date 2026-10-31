# GitHub Environments — CentralDevOps

## Status

**Applied and audited on 2026-10-31.** The `GH_TOKEN` environment override could not resolve the repository; after unsetting it, the `aldoawp` keyring account resolved it with `ADMIN` permission. The repository is public on the Free plan. Production requires approval by `aldoawp`, disallows administrator bypass, and accepts only `release/*`; Staging has no reviewers or branch restriction. This foundation work created no Environment secrets or variables. The owner has since removed the pre-existing Environment entries; current repository and Environment counts are zero. The organization-level F-10 audit remains pending because the active token lacks `admin:org`.

The current requirements are exactly two Environments: `Staging` accepts all branches without reviewers, and `Production` requires approval by the repository owner, disallows administrator bypass, and accepts only protected `release/*` branches. The repository ruleset is a separate Task 5 gate for `main` and `release/*`.

## Probe evidence

| Date | Who | Result |
|---|---|---|
| 2026-10-30 | `GH_TOKEN` environment override | `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission` failed with `GraphQL: Could not resolve to a Repository with the name 'Buzilion/CentralDevOps'. (repository)`. |
| 2026-10-31 | `aldoawp` keyring account after unsetting `GH_TOKEN` | `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission` returned `{"nameWithOwner":"Buzilion/CentralDevOps","viewerPermission":"ADMIN","visibility":"PUBLIC"}`. |
| 2026-10-31 | `aldoawp` keyring account | `gh api orgs/Buzilion --jq .plan.name` returned `free`. |
| 2026-10-31 | `aldoawp` keyring account | `gh api orgs/Buzilion/memberships/aldoawp --jq '{state,role}'` returned `{"role":"admin","state":"active"}`. |
| 2026-10-31 | `aldoawp` keyring account | `gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] | sort'` returned `["Production","Staging"]`. |
| 2026-10-31 | `aldoawp` keyring account | Production GET returned reviewer `aldoawp`, `prevent_self_review: false`, `can_admins_bypass: false`, and deployment-branch policy `{protected_branches:false,custom_branch_policies:true}`. Its branch-policy endpoint returned `release/*`. |
| 2026-10-31 | `aldoawp` keyring account | Staging GET returned no protection rules and `deployment_branch_policy: null`, allowing all branches. |
| 2026-10-31 | `aldoawp` keyring account | A later audit found an unexpected Staging `required_reviewers` rule for `aldoawp`. Reapplied the intended `{"wait_timer":0,"reviewers":[]}` configuration; the follow-up GET returned no protection rules and a null branch policy. |
| 2026-10-31 | `aldoawp` keyring account | A Staging PUT with both branch-policy booleans set to `false` was rejected with HTTP 422 and made no change. Omitting the policy correctly leaves it `null`, which allows all branches. |
| 2026-10-31 | `aldoawp` keyring account | Repository ruleset `main` ID `26226141` is active with both ref patterns, required review/check rules, and only the `aldoawp` pull-request-only bypass. |
| 2026-10-31 | `aldoawp` keyring account | Repository ruleset `main` ID `26226141` is active for `refs/heads/main` and `refs/heads/release/*`, with deletion, non-fast-forward, pull-request, required-status-check rules, and the D6 `aldoawp` pull-request-only bypass. |

**Plan check:** the public repository and Free plan support Environment protection rules. If the repository becomes private/internal, required-reviewer and wait-timer rules require Enterprise; re-audit before relying on the gate.

## Preconditions

Before applying anything, confirm all of the following:

1. If `GH_TOKEN` overrides the authorized keyring account, unset it for this PowerShell session and confirm `gh auth status` shows `aldoawp`; then `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission` must return the intended repository and `viewerPermission` must be `ADMIN`.
2. `gh api orgs/Buzilion --jq .plan.name` returns a plan value, and the plan supports both Environment branch policies and required-reviewer rules for the repository's visibility (public on a current plan, or private/internal on Enterprise for required-reviewer rules).
3. The current Environment list has been reviewed. Do not delete an unexpected Environment to force the count; resolve it with the repository owner first.
4. Confirm that the repository owner handle named by Decision D7, `aldoawp`, resolves to the intended owner before applying the reviewer rule.

## Apply

Run these commands in PowerShell only after the preconditions pass. They create or update the two named Environments and add the Production `release/*` policy. Do not create any secret or variable here.

```powershell
# Confirm access and plan first. Stop if the repository is not ADMIN-accessible,
# or if visibility/plan capability is not positively established.
Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
gh auth status
gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission
gh api orgs/Buzilion --jq .plan.name

# Review existing environments before applying. For a fresh setup, expect [].
gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] | sort'

# The spec currently assumes this owner handle; confirm it before continuing.
$ownerHandle = "aldoawp"
$ownerId = gh api "users/$ownerHandle" --jq .id
if (-not $ownerId) { throw "Could not resolve the confirmed repository-owner user ID." }

$stagingBody = @'
{
  "wait_timer": 0,
  "reviewers": []
}
'@
$stagingBody | gh api -X PUT repos/Buzilion/CentralDevOps/environments/Staging --input -

$productionBody = @"
{
  "wait_timer": 0,
  "reviewers": [
    { "type": "User", "id": $ownerId }
  ],
  "prevent_self_review": false,
  "can_admins_bypass": false,
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
"@
$productionBody | gh api -X PUT repos/Buzilion/CentralDevOps/environments/Production --input -

gh api -X POST repos/Buzilion/CentralDevOps/environments/Production/deployment-branch-policies -f 'name=release/*' -f 'type=branch'
```

The commands above are for a fresh setup. If either Environment or a branch policy already exists, inspect it before reapplying; do not blindly add duplicate policies or remove unrelated settings.

## Audit

Run each command after applying. Stop and investigate if any output differs from the expected value.

```powershell
gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] | sort'
# Expected: ["Production","Staging"]

gh api repos/Buzilion/CentralDevOps/environments/Production --jq '[.protection_rules[].type] | sort'
# Expected: ["branch_policy","required_reviewers"]

gh api repos/Buzilion/CentralDevOps/environments/Production --jq '.protection_rules[] | select(.type=="required_reviewers") | {reviewers:[.reviewers[].reviewer.login],prevent_self_review}'
# Expected: {"reviewers":["aldoawp"],"prevent_self_review":false}

gh api repos/Buzilion/CentralDevOps/environments/Production --jq '.can_admins_bypass'
# Expected: false

gh api repos/Buzilion/CentralDevOps/environments/Production --jq '.deployment_branch_policy'
# Expected: {"protected_branches":false,"custom_branch_policies":true}

gh api repos/Buzilion/CentralDevOps/environments/Production/deployment-branch-policies --jq '[.branch_policies[] | {name,type}] | sort_by(.name)'
# Expected: [{"name":"release/*","type":"branch"}]

gh api repos/Buzilion/CentralDevOps/environments/Staging --jq '[.protection_rules[]? | select(.type=="required_reviewers")]'
# Expected: []

gh api repos/Buzilion/CentralDevOps/environments/Staging --jq '.deployment_branch_policy'
# Expected: null (all branches are allowed)
```

Append an evidence row after each audit with the local date, the operator's GitHub login, and the actual result.

## Repository branch protection

The API reports active ruleset `main` (ID `26226141`) for both `refs/heads/main` and `refs/heads/release/*`. It blocks branch deletion and non-fast-forward updates; requires pull requests, one approval, code-owner review, dismissal of stale approvals and approval of the latest push; and requires `workflow-lint` and `naming-and-secrets`. Extra approval for unattributed changes is disabled so the rules match the spec. The sole repository collaborator/codeowner is `aldoawp`, so the ruleset has only that user as a `pull_request`-only bypass actor. This is the D6 temporary exception; remove it when an independent codeowner/reviewer is added. `.github/rulesets/main.json` matches the active settings but is not yet committed on `main`.

Apply the committed ruleset only after every required status check has run at least once:

```powershell
gh api -X POST repos/Buzilion/CentralDevOps/rulesets --input .github/rulesets/main.json
```

For an existing ruleset, inspect its id and update that ruleset with `PUT` rather than creating a duplicate:

```powershell
gh api repos/Buzilion/CentralDevOps/rulesets --jq '[.[] | {id,name,enforcement,include:.conditions.ref_name.include}]'
gh api -X PUT repos/Buzilion/CentralDevOps/rulesets/<ruleset-id> --input .github/rulesets/main.json
```

Audit both the ref patterns and the active rules:

```powershell
gh api repos/Buzilion/CentralDevOps/rulesets --jq '[.[] | {id,name,enforcement,include:.conditions.ref_name.include}]'
gh api repos/Buzilion/CentralDevOps/rulesets/<ruleset-id> --jq '{name,enforcement,include:.conditions.ref_name.include,bypass_actors,rules:[.rules[] | {type,parameters}]}'
```

The include list must contain `refs/heads/main` and `refs/heads/release/*`; the ruleset must be active and include the deletion, non-fast-forward, pull-request and required-status-check rules. The bypass list must contain only `aldoawp` with mode `pull_request`. The API audit confirmed these settings. Release scratch-branch direct/force-push and deletion attempts were refused; the effective-rules API confirms the same rules for `main`. Direct update/deletion attempts against `main` were intentionally not made to avoid risking the default branch. PR `#3` later completed with a failed required check and GitHub reported it blocked and review-required; it was closed unmerged. GitHub's API adds default fields to returned rules, while the substantive settings match the canonical `.github/rulesets/main.json` payload.

## Secrets and variables audit

These read-only commands report counts or names/visibility only; do not request or record secret values. Organization-level endpoints require an authorized org admin token with `admin:org` or the corresponding fine-grained Actions read permission.

```powershell
gh api repos/Buzilion/CentralDevOps/actions/secrets --jq '.total_count'
gh api repos/Buzilion/CentralDevOps/actions/variables --jq '.total_count'
gh api repos/Buzilion/CentralDevOps/environments/Production/secrets --jq '.total_count'
gh api repos/Buzilion/CentralDevOps/environments/Production/variables --jq '.total_count'
gh api repos/Buzilion/CentralDevOps/environments/Staging/secrets --jq '.total_count'
gh api repos/Buzilion/CentralDevOps/environments/Staging/variables --jq '.total_count'

gh api orgs/Buzilion/actions/secrets --jq '[.secrets[] | {name,visibility}]'
gh api orgs/Buzilion/actions/variables --jq '[.variables[] | {name,visibility}]'
```

The repository and Environment counts must be zero at this foundation stage. Organization entries must be empty or have `visibility: "selected"`; no value field is needed for this audit.

## Initial Task 6 audit (superseded)

This preliminary entry is superseded by the initial foundation acceptance audit below; see the post-remediation audit at the end for current results.

| Requirement | Command or evidence | Result |
|---|---|---|
| F-01 | `gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] \| sort'` | Pass: `["Production","Staging"]`. |
| F-02 | Production and Staging Environment GETs and Production branch-policy endpoint | Pass: Production requires `aldoawp`, prevents administrator bypass, and accepts only `release/*`; Staging has no reviewers and a null policy. |
| F-03 | `gh api 'repos/Buzilion/CentralDevOps/codeowners/errors?ref=main' --jq '.errors'` | Pass: `[]`. |
| F-04 | Ruleset `26226141` GET, effective-rules GETs for `main` and `release/*`, and scratch `release/*` push/force/delete attempts | Partial: active rules cover both patterns; direct push, force push, and deletion were refused on the scratch release branch. No direct update/deletion attempt was made against `main` to avoid risking the default branch. |
| F-05 | `gh pr checks 1`; temporary negative-fixture PR `#2` and its Actions logs | Pass: both jobs passed on PR `#1`; unpinned-action and template-injection fixtures failed `workflow-lint`, and `secrets.STAGING_TOKEN` failed `naming-and-secrets`. |
| F-06 | `py -3.12 deployment/tools/check-github-names.py`; `py -3.12 -m unittest discover -s deployment/tools/tests -v` | Pass: checker exit `0`; 14 tests passed. |
| F-07 | `test_forbidden_name_in_deploy_workflow_reports_f01` in the checker suite | Pass: forbidden name reported as `F01`. |
| F-08 | `git log --all --format='%H' --no-patch -G '-----BEGIN [A-Z ]*PRIVATE KEY-----'`; checker run | Pass: no matching history commits; checker exit `0`. No key material was printed. |
| F-09 | `gh repo view Buzilion/CentralDevOps --json visibility,viewerPermission`; `gh api orgs/Buzilion --jq .plan.name`; README | Pass: repository `PUBLIC`, permission `ADMIN`, organization plan `free`; README records these facts. |
| F-10 | Repository/environment secret-variable list endpoints; organization endpoint attempts | Gap: repository-level counts are zero. Production currently has 4 secrets and 5 variables; Staging has 2 secrets and 3 variables. Organization-level audit returned HTTP 403 because the token lacks `admin:org`; no values were retrieved and nothing was deleted. Existing Environment entries conflict with this spec's empty-at-acceptance requirement and need owner review. |
| F-11 | This runbook's apply/audit commands and the dated evidence above | Pass: procedures and current evidence are recorded. |

**Task 6 status at initial audit:** blocked because Environment entries existed and the active token could not audit organization-level settings. The entries have since been removed; see the post-remediation audit below.

## Foundation acceptance audit (initial, 2026-10-31)

| Requirement | Command or evidence | Result |
|---|---|---|
| F-01 | `gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] \| sort'` | Pass: `["Production","Staging"]`. |
| F-02 | Production and Staging Environment GETs and Production deployment-branch-policy GET | Pass: Production reviewer `aldoawp`, self-review allowed, administrator bypass disabled, only `release/*`; Staging has no reviewers and a null branch policy (all branches). |
| F-03 | `gh api 'repos/Buzilion/CentralDevOps/codeowners/errors?ref=main' --jq '.errors'` | Pass: `[]`. |
| F-04 | Ruleset `26226141` GET, effective-rules GETs for `main` and `release/protection-probe`, scratch `release/*` push/force/delete attempts, and scratch PR `#3` | Partial: active rules and effective coverage for both patterns confirmed; direct/force pushes and deletion on the scratch release branch were refused. No direct update/deletion attempt was made against `main` to avoid risking the default branch. PR `#3` merge was refused while checks were queued, but the run never completed, so merge refusal for a failing check remains unverified. |
| F-05 | `gh pr checks 1`; temporary negative-fixture PR `#2` and its Actions logs | Pass: both jobs passed on PR `#1`; the unpinned action and shell-injection fixtures failed `workflow-lint`, and `secrets.STAGING_TOKEN` failed `naming-and-secrets`. |
| F-06 | `py -3.12 deployment/tools/check-github-names.py`; `py -3.12 -m unittest discover -s deployment/tools/tests -v` | Pass: checker exit `0`; 14 tests passed. |
| F-07 | `test_forbidden_name_in_deploy_workflow_reports_f01` in the checker suite | Pass: forbidden name reported as `F01`. |
| F-08 | `git log --all --format='%H' --no-patch -G '-----BEGIN [A-Z ]*PRIVATE KEY-----'`; checker run | Pass: no matching history commits; checker exit `0`. No key material was printed. |
| F-09 | `gh repo view Buzilion/CentralDevOps --json visibility,viewerPermission`; `gh api orgs/Buzilion --jq .plan.name`; README | Pass: repository `PUBLIC`, permission `ADMIN`, organization plan `free`; README records these facts. |
| F-10 | Repository/environment secret-variable list endpoints; organization endpoint attempts | Gap: repository-level counts are zero. Production currently has 4 secrets and 5 variables; Staging has 2 secrets and 3 variables. Organization-level audit returned HTTP 403 because the active token lacks `admin:org`; no values were retrieved and nothing was deleted. These Environment entries conflict with this spec's empty-at-acceptance requirement and need owner review. |
| F-11 | This runbook's apply/audit commands and the dated evidence above | Pass: apply and audit steps are recorded. |

**Task 6 status:** repository and Environment secret/variable acceptance now passes after owner cleanup. The organization-level audit remains blocked: the active `aldoawp` token has `read:org` but not `admin:org`, and both organization Actions endpoints return HTTP 403. No secret values were accessed or recorded.

## Post-remediation foundation audit (2026-10-31)

| Requirement | Command or evidence | Result |
|---|---|---|
| F-01 | `gh api repos/Buzilion/CentralDevOps/environments --jq '[.environments[].name] \| sort'` | Pass: `["Production","Staging"]`. |
| F-02 | Production and Staging Environment GETs and Production deployment-branch-policy GET | Pass after correction: Production reviewer `aldoawp`, self-review allowed, administrator bypass disabled, only `release/*`; Staging has no protection rules and a null branch policy. |
| F-03 | `gh api 'repos/Buzilion/CentralDevOps/codeowners/errors?ref=main' --jq '.errors'` | Pass: `[]`. |
| F-04 | Ruleset `26226141` GET, effective-rules GET for `main`, prior scratch `release/*` push/force/delete attempts, and PR `#3` state/checks | Partial: the active ruleset includes both ref patterns and the expected rules; release scratch attempts were refused. PR `#3` completed with `workflow-lint` failure, `naming-and-secrets` success, `mergeStateStatus=BLOCKED`, and `reviewDecision=REVIEW_REQUIRED`; it was closed unmerged. No direct update/deletion attempt was made against `main` to avoid risking the default branch. The payload is on the feature branch but is not yet present on `main`. |
| F-05 | `gh pr checks 1`; temporary negative-fixture PR `#2` and its Actions logs | Pass: both jobs passed on PR `#1`; unsafe fixtures failed the expected jobs on PR `#2`. |
| F-06 | `py -3.12 deployment/tools/check-github-names.py`; `py -3.12 -m unittest discover -s deployment/tools/tests -v` | Pass: checker exit `0`; all 14 tests passed. |
| F-07 | `test_forbidden_name_in_deploy_workflow_reports_f01` in the checker suite | Pass. |
| F-08 | `git log --all --format='%H' -G '-----BEGIN [A-Z ]*PRIVATE KEY-----'`; checker run | Pass: no matching history commits; checker exit `0`. No key material was printed. |
| F-09 | `gh repo view Buzilion/CentralDevOps --json visibility,viewerPermission`; `gh api orgs/Buzilion --jq .plan.name`; README | Pass: repository `PUBLIC`, permission `ADMIN`, organization plan `free`; README records these facts. |
| F-10 | Repository and Environment secret/variable count endpoints; organization endpoint attempts | Partial: repository, Production and Staging counts are all zero. Organization secret and variable endpoints returned HTTP 403 because `admin:org` is not authorized; no values were accessed. |
| F-11 | This runbook's apply and audit commands and the dated evidence above | Pass: procedures and expected outputs are recorded. |

Task 6 remains blocked until an authorized organization-level audit proves that no organization secret or variable is visible to all repositories. Request `admin:org` for the active account with `gh auth refresh -h github.com -s admin:org`, or have an organization admin run the two read-only organization commands above and provide the name/visibility-only results.
