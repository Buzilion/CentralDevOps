# Task 6: Foundation acceptance audit

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | Tasks 1 to 5 |

## Goal

Prove that every requirement in the spec holds on the real repository and record the evidence, so spec 02 can start from a verified base.

## Context

This is the closing audit of the spec. It changes no behavior; it only checks, fixes gaps found by the checks within this spec's scope, and records results. The org-level restriction audit (F-10) and the history scan (F-08) only make sense once everything else is in place.

## Relevant files or references

- `docs/runbooks/github-environments.md` (append the evidence log and the org-level audit commands)
- Spec sections: Requirements F-01 to F-11, Invariants, Testing Strategy

## Proposed approach

1. Re-run every audit command from Tasks 1 and 5 and record the output.
2. Org-level audit: `gh api orgs/Buzilion/actions/secrets --jq ".secrets[] | {name, visibility}"` and the same for `variables`. Every entry must have visibility `selected` (or the list is empty). Record the result and the command in the runbook.
3. History scan: `git log --all -p -S"PRIVATE KEY-----"` and a run of the checker over the working tree.
4. Confirm the README note matches the facts found in Task 1.
5. Confirm there are no GitHub variables or secrets in the repository: `gh api repos/Buzilion/CentralDevOps/actions/secrets` and `.../variables` return zero entries, and the same for each Environment.
6. List any gap as a defect in this spec and fix it, or raise it for the owner. Do not start spec 02 with an open gap.

## Acceptance criteria

- The evidence log in the runbook has a dated entry for each of F-01 to F-11 with the command run and its result.
- No org-level secret or variable is visible to all repositories.
- History and tree contain no private key material.
- Repository and Environment secrets and variables are empty at this point.
- The spec's `checklist.md` shows Tasks 1 to 5 complete before this one is marked complete.

## Source reference

SEC-01, 04, 05, 06, 13, 14, 17; F-01 to F-11.

## Verify

```powershell
gh api orgs/Buzilion/actions/secrets --jq ".secrets[] | {name, visibility}"
gh api orgs/Buzilion/actions/variables --jq ".variables[] | {name, visibility}"
git log --all -p -S"PRIVATE KEY-----" | Select-String "BEGIN .* PRIVATE KEY"
# expect no output
python deployment/tools/check-github-names.py; echo $LASTEXITCODE
# expect 0
```

## Out of scope

Creating any secret, variable or app-repository Environment.
