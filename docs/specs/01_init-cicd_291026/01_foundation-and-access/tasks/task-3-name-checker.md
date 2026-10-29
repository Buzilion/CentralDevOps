# Task 3: Name and key-material checker

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` |
| Depends on | none |

## Goal

Build `deployment/tools/check-github-names.py` with its catalog and unit tests, enforcing rules `N01` to `N05`, `F01` and `K01`.

## Context

There are no workflows yet, so the checker is tested with fixtures. Later specs add workflows and catalog entries; this tool then fails any pull request that introduces a badly named, uncataloged or forbidden reference, or committed private key material. The tool must be usable on a laptop and on the runner.

## Relevant files or references

- Create `deployment/tools/check-github-names.py`, `deployment/tools/github-names.json`, `deployment/tools/tests/test_check_github_names.py`
- `docs/design/variables-and-secrets.md` §1.3 (names to seed), `docs/design/naming-and-repository-conventions.md` §2
- Spec sections: Design > Name catalog, Checker behavior

## Proposed approach

1. Seed the catalog with every CentralDevOps-repository name from the §1.3 table (kind, level, `introduced_by` spec folder for each). Leave out app-repository names. Add the `forbidden_in` rule for `.github/workflows/deploy-app.yml`.
2. Implement the checker with the standard library only (`argparse`, `json`, `re`, `pathlib`, `subprocess` for `git ls-files`). Keep the rules table-driven so a new rule is one entry.
3. Output format `path:line RULE message`; never print matched key material.
4. Skip binary files and `.git/` in the key scan; skip the catalog file's own rule text if it contains the header regex.
5. Unit tests per the spec's Testing Strategy, using `tempfile.TemporaryDirectory` fixtures. Build the PEM header string at run time inside the test so the test file does not trigger the scan.

## Acceptance criteria

- A repository root with no workflows exits 0.
- Each failure case in the spec's unit-test list exits 1 with the expected rule ID and the correct line number.
- `secrets.GITHUB_TOKEN` passes; `secrets.inherit` and dynamic access fail with `N05`.
- A broken or incomplete catalog exits 2.
- A detected private key block is reported by location only; the output contains none of its characters.
- The tool works on Python 3.10 and later with no third-party package.

## Source reference

SEC-02, SEC-03, SEC-06, SEC-07, NFR-12, NFR-23; F-06, F-07, F-08.

## Verify

```powershell
python deployment/tools/check-github-names.py
# expect exit code 0 on the repository as it stands
python -m unittest discover -s deployment/tools/tests -v
# expect all tests OK
```

## Out of scope

The CI workflow that runs it (Task 4), actionlint and zizmor, creating any GitHub variable or secret.
