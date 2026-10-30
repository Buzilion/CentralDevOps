# GitHub Environments — CentralDevOps

## Status

**Applied and audited on 2026-10-31.** The `GH_TOKEN` environment override could not resolve the repository; after unsetting it, the `aldoawp` keyring account resolved it with `ADMIN` permission. The repository is public on the Free plan. Production now requires approval by `aldoawp`, disallows administrator bypass, and accepts only `release/*`; Staging has no reviewers or branch restriction. No Environment secrets or variables were created.

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
| 2026-10-31 | `aldoawp` keyring account | A Staging PUT with both branch-policy booleans set to `false` was rejected with HTTP 422 and made no change. Omitting the policy correctly leaves it `null`, which allows all branches. |

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

Task 5 remains pending; no `.github/rulesets/main.json` file is present or applied. The planned repository ruleset will protect both `refs/heads/main` and `refs/heads/release/*` with identical rules. It will block branch deletion and non-fast-forward updates; require pull requests, one approval, code-owner review, dismissal of stale approvals and approval of the latest push; and require the configured status checks (`workflow-lint`, `naming-and-secrets`, plus checks added by later specs such as `registry-policy`).

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
gh api repos/Buzilion/CentralDevOps/rulesets/<ruleset-id> --jq '{name,enforcement,include:.conditions.ref_name.include,rules:[.rules[].type]}'
```

The include list must contain `refs/heads/main` and `refs/heads/release/*`; the ruleset must be active and include the deletion, non-fast-forward, pull-request and required-status-check rules. Task 5's scratch-branch tests must verify the same behavior for both branch patterns. These commands are planned; the ruleset has not been applied or audited.
