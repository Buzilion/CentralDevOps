# Task 2: README and CODEOWNERS

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | Task 1 (the README plan note quotes its probe result) |

## Goal

Replace the one-line README with the repository entry point, including the GitHub plan assumption, and add `.github/CODEOWNERS` covering the protected paths.

## Context

`README.md` currently has a title and one sentence. SEC-17 requires a note on the plan and visibility assumption so a later change (for example making the repository private on the Free plan) is noticed. SEC-13 requires code-owner review on `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`, `.github/CODEOWNERS` and `.github/rulesets/**` before merging into protected `main` or `release/*`.

## Relevant files or references

- `README.md` (edit), `.github/CODEOWNERS` (create)
- `docs/design/naming-and-repository-conventions.md` §8.2 (directory map to document)
- `docs/design/variables-and-secrets.md`, `docs/prd/01_init-cicd_291026/prd-v1.md`
- Spec Decisions D6, D7

## Proposed approach

1. README sections: purpose, the two environments, documentation map (PRD, design, specs roadmap), target directory map marked as "created by later specs", conventions in one short list (names, Environments, digest-only deploys), how to run the local checks (`python3 deployment/tools/check-github-names.py` and the unit tests), and a **Platform assumptions** section.
2. The assumptions section states: Environments and their protection rules are required; this depends on the GitHub plan and repository visibility; value verified on the date and with the result from Task 1; change of plan or visibility must trigger a re-audit using `docs/runbooks/github-environments.md`.
3. CODEOWNERS entries, one line per protected pattern: `/apps/`, `/deployment/`, `/roles/`, `/.github/workflows/`, `/.github/actions/`, `/.github/CODEOWNERS`, `/.github/rulesets/`, all owned by the owner handle from Decision D7. Confirm the handle with the owner if the organization intends a team.
4. Do not mention secrets values, hosts or addresses.

## Acceptance criteria

- README contains the plan and visibility note with the verification date and result.
- Every protected pattern in F-03 has a CODEOWNERS entry using a valid owner.
- GitHub reports no CODEOWNERS errors for the file.
- README links resolve to existing files.

## Source reference

SEC-13, SEC-17; F-03, F-09.

## Verify

```powershell
gh api repos/Buzilion/CentralDevOps/codeowners/errors --jq ".errors"
# expect [] once the file is on the default branch (run after the change is merged, or against the branch with ?ref=<branch>)
Select-String -Path README.md -Pattern "Platform assumptions"
# expect one match
```

## Out of scope

Empty directory skeletons, `ansible.cfg`, inventories, the ruleset that enforces review (Task 5).
