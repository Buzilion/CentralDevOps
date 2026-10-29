# Task 4: Lint workflow

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | Task 3 (checker and tests exist) |

## Goal

Add `.github/workflows/lint.yml` with the jobs `workflow-lint` and `naming-and-secrets`, so every pull request is checked for unpinned actions, injection patterns, naming and forbidden-name violations, and private key material.

## Context

This is the first workflow in the repository and sets the pattern for all later ones: pinned SHAs, empty top-level permissions, minimal per-job permissions, no direct interpolation of inputs into shell. The job names are the status checks that the `main` ruleset (Task 5) requires, so they must not change afterwards.

## Relevant files or references

- Create `.github/workflows/lint.yml`
- Task 3 outputs under `deployment/tools/`
- Spec sections: Design > Lint workflow, Versions, Error Behavior
- Official sources: actionlint releases and its `checksums.txt`, zizmor release `v1.31.1`

## Proposed approach

1. Look up the commit SHA of the `actions/checkout` release chosen in the spec (re-check for a newer stable release) and pin it with the version in a trailing comment. Use `persist-credentials: false`.
2. `workflow-lint`: download the actionlint release archive for Linux x86_64 from the GitHub release, verify its SHA-256 against a value pinned in the workflow, run it. Install zizmor with `pip install zizmor==<pinned>` and run it on `.github/`. Fail on any finding.
3. `naming-and-secrets`: run the checker and the unit tests.
4. Set `permissions: {}` at top level and `contents: read` per job. Pass any needed values through `env:`.
5. Prove the negative cases on a scratch branch: one workflow with an unpinned action, one with `${{ github.event.inputs.x }}` in `run:`. Confirm both fail, then delete the branch and its pull request.

## Acceptance criteria

- On a clean pull request, both jobs pass.
- The unpinned-action fixture fails `workflow-lint`.
- The injection fixture fails `workflow-lint`.
- A fixture referencing `secrets.STAGING_TOKEN` fails `naming-and-secrets`.
- The workflow itself passes actionlint and zizmor with no suppressions.
- No `pull_request_target` trigger, no write permission and no secret is used.

## Source reference

SEC-02, SEC-14, NFR-15; F-04, F-05, F-06.

## Verify

```powershell
gh run list --workflow lint.yml --limit 5
# latest run on the pull request: both jobs "success"
gh pr checks <scratch-pr-number>
# negative fixtures: the named job shows "fail"
Select-String -Path .github/workflows/lint.yml -Pattern "uses:\s+\S+@(?![0-9a-f]{40}\b)" 
# expect no matches (every uses: is a full SHA)
```

## Out of scope

Requiring these checks on `main` (Task 5), Dependabot, caching.
