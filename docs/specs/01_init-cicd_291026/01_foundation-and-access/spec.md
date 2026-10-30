# Spec 01: Repository Foundation and Access Control

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 01 of 15, see `../00_spec-roadmap.md`) |
| Status | Draft for review |
| Depends on | none |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRD | `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`) |
| Design | `docs/design/variables-and-secrets.md`, `docs/design/naming-and-repository-conventions.md`, `docs/design/infrastructure-contracts-and-invariants.md` §4 and §6; v5 design §4, §12.2, §16 step 1 |

## What

Make the CentralDevOps repository safe to build on before any infrastructure or workflow exists. This spec creates the two GitHub Environments with their protection rules, enforces matching branch protections, code-owner review and mandatory checks on `main` and `release/*`, and adds an automated lint that rejects unpinned actions, shell injection patterns, badly named or forbidden variables and secrets, and committed private keys. It also records the GitHub plan assumption in the README. Nothing here touches a VPS.

## Context

- The repository today holds only documentation (`docs/`), the agent skills (`.agents/`) and a one-line `README.md`. There are no workflows, roles, inventories or code. Remote: `https://github.com/Buzilion/CentralDevOps.git`, default branch `main`.
- Every later spec adds workflows that use Environment secrets (SSH keys, age key, S3 and Grafana credentials). The protection rules and review gates must exist first, otherwise the first privileged workflow runs unprotected.
- The v5 design (§16 step 1) puts "structure, `ansible.cfg`, inventories, naming standard, CODEOWNERS, registry schema" first. This spec delivers the naming standard enforcement, CODEOWNERS and structure documentation; Ansible files move to spec 03 and the registry schema to spec 06 (see the roadmap).
- **Plan risk.** Task 1 verified that the repository is public and the Buzilion organization is on Free, a supported combination for Environment protection rules. The API now confirms the Production reviewer rule with administrator bypass disabled and the `release/*` policy, plus Staging's unrestricted branch policy. If the repository becomes private, required-reviewer protection requires Enterprise; re-audit before relying on the gate.
- **Self-approval limit.** GitHub does not let a pull request author approve their own pull request. With a single human owner, "code-owner review required" cannot be satisfied. See Decision D6.

## Requirements

| ID | Statement | Source |
|---|---|---|
| F-01 | CentralDevOps has exactly two deployment Environments, `Staging` and `Production`; each targets its corresponding VPS, and no additional Environment is created per VPS. | SEC-01 |
| F-02 | `Production` requires approval by the repository owner, does not allow administrator bypass, and accepts runs only from protected branches matching `release/*`. `Staging` requires no approval and accepts runs from any branch. Self-review of an approval is permitted while the owner is the sole approver. | SEC-05, v5 §4.1 |
| F-03 | Changes to `apps/**`, `deployment/**`, `roles/**` and `.github/workflows/**` need code-owner review before merging into `main` or `release/*`. `.github/CODEOWNERS` and `.github/rulesets/**` are covered by the same rule. | SEC-13, NFR-17 |
| F-04 | `main` and `release/*` branches cannot be force-pushed or deleted. Pull requests into either require one approval, code-owner review and passing `workflow-lint` and `naming-and-secrets` checks. | SEC-13, SEC-14 |
| F-05 | Every workflow and action under `.github/` pins third-party actions to a 40-character commit SHA, declares explicit least-privilege `permissions`, and never interpolates `github.event` or `inputs` values directly into shell. | SEC-14, NFR-15 |
| F-06 | Every `secrets.<NAME>` and `vars.<NAME>` referenced under `.github/` matches `^(ANSIBLE\|VPS\|DEPLOY\|GHCR\|APP\|BACKUP\|MONITORING)_[A-Z0-9]+(_[A-Z0-9]+)*$`, does not start with `STAGING_`, `PRODUCTION_` or `GITHUB_`, is not a generic name, and appears in the machine-readable name catalog with the right kind (secret or variable). The only exception is the built-in `secrets.GITHUB_TOKEN`. | SEC-02, NFR-23 |
| F-07 | A name listed as forbidden for a workflow cannot be referenced by it. Initially `deploy-app.yml` cannot reference `ANSIBLE_SSH_PRIVATE_KEY`, `VPS_INITIAL_ACCESS_PASSWORD` or `ANSIBLE_VAULT_PASSWORD`. | SEC-07, INF-13 |
| F-08 | No tracked file contains private key material, and repository history contains none. | SEC-06, NFR-12 |
| F-09 | The README states the GitHub plan and repository-visibility assumption that Environments and protection rules depend on, how and when it was verified, and documents the repository layout and conventions. | SEC-17 |
| F-10 | Org-level secrets and variables used by this platform are restricted to selected repositories. None are required yet; the audit proves none broader than intended exist. | SEC-04 |
| F-11 | A runbook records the exact commands to apply and audit Environments, the ruleset and org-level restrictions, with the expected output, so the settings can be reproduced and re-checked. | SEC-01, 04, 05, 13 |

## Design

### Components

```text
.github/
  CODEOWNERS                       # F-03
  rulesets/main.json               # F-03, F-04: protects main and release/* branches
  workflows/lint.yml               # F-04..F-08: jobs workflow-lint, naming-and-secrets
deployment/tools/
  check-github-names.py            # F-06, F-07, F-08 (stdlib only)
  github-names.json                # catalog and forbidden-name rules, data only
  tests/test_check_github_names.py # unittest
docs/runbooks/
  github-environments.md           # F-11: apply, audit, evidence log
README.md                          # F-09
```

No other directory is created. Empty skeleton folders are not added; later specs create `roles/`, `inventories/`, `apps/` and so on when they first hold content, and `README.md` documents the target map from `docs/design/naming-and-repository-conventions.md` §8.2. `docs/runbooks/` is new: the design map has no runbook location, and runbooks are operational instructions rather than design.

### GitHub settings (applied with `gh api`, recorded in the runbook)

| Setting | `Staging` | `Production` |
|---|---|---|
| Required reviewers | none | repository owner (user) |
| Self-review prevention | n/a | off (sole approver) |
| Administrator bypass | not applicable | disabled |
| Deployment branches | all branches | custom policy, branches matching `release/*` only |
| Wait timer | none | none |

Ruleset `main` (target patterns `refs/heads/main` and `refs/heads/release/*`, enforcement active): block deletion, block non-fast-forward, require pull requests with 1 approving review and code-owner review, dismiss stale approvals, require last-push approval, and require status checks `workflow-lint` and `naming-and-secrets` with an up-to-date branch. These protections apply equally to both patterns. Bypass list: empty unless Decision D6 chooses otherwise.

### Name catalog (`deployment/tools/github-names.json`)

Data-only JSON so the checker needs no YAML parser. Shape:

```json
{
  "prefixes": ["ANSIBLE", "VPS", "DEPLOY", "GHCR", "APP", "BACKUP", "MONITORING"],
  "reserved_prefixes": ["STAGING_", "PRODUCTION_", "GITHUB_"],
  "generic_names": ["TOKEN", "KEY", "SECRET", "PASSWORD", "SERVER_IP"],
  "names": {
    "ANSIBLE_SSH_PRIVATE_KEY": { "kind": "secret", "level": "environment", "introduced_by": "03_host-bootstrap-and-hardening" }
  },
  "forbidden_in": {
    ".github/workflows/deploy-app.yml": ["ANSIBLE_SSH_PRIVATE_KEY", "VPS_INITIAL_ACCESS_PASSWORD", "ANSIBLE_VAULT_PASSWORD"]
  }
}
```

The catalog is seeded from the quick-reference table in `docs/design/variables-and-secrets.md` §1.3 for the CentralDevOps repository only. App-repository entries (`DEPLOY_DISPATCH_APP_*`, `APP_*`) are not in the catalog, so CentralDevOps workflows cannot reference them. A new name is added to the catalog in the same pull request that first consumes it; `introduced_by` names the spec that adds it. Variables and secrets themselves are created in GitHub by the spec that consumes them, not here (SEC-02: only consumed names exist).

### Checker behavior (`check-github-names.py`)

Invocation: `python3 deployment/tools/check-github-names.py [--root <dir>]` (default: repository root).

1. Scan `.github/**/*.yml` and `.github/**/*.yaml` for `secrets.<NAME>`, `vars.<NAME>`, `secrets['<NAME>']` and `vars['<NAME>']`. Dynamic forms (`secrets[expr]`, `toJSON(secrets)`, `secrets: inherit`) are violations.
2. Apply F-06 and F-07 per reference. Report `path:line rule-id message`.
3. Scan every tracked text file (`git ls-files`, falling back to a directory walk when not in a Git repository) for the regular expression `-----BEGIN [A-Z ]*PRIVATE KEY-----` and report only `path:line K01`. The matched content is never printed. The checker's own test fixtures build the header at run time so the test file itself does not match.
4. Exit 0 when clean, 1 when any violation exists, 2 on a catalog or usage error.

Rule IDs: `N01` bad pattern, `N02` reserved prefix, `N03` generic name, `N04` not in catalog or wrong kind, `N05` dynamic reference, `F01` forbidden for this workflow, `K01` private key material.

### Lint workflow (`lint.yml`)

Triggers: `pull_request` and `push` to `main`. Never `pull_request_target`. Top-level `permissions: {}`; each job grants `contents: read` only. Runner `ubuntu-24.04`.

- `workflow-lint`: checkout (pinned SHA, `persist-credentials: false`), run `actionlint` from a release archive whose SHA-256 is pinned in the workflow, run `zizmor` at the pinned version against `.github/`. Any finding fails the job.
- `naming-and-secrets`: checkout, run the checker, then run the unit tests with `python3 -m unittest discover -s deployment/tools/tests`.

Workflow inputs and event fields reach shell only through `env:` variables, never `${{ }}` inside `run:`.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Custom checker for names and key material; actionlint and zizmor for everything else. | One custom linter for all rules; gitleaks | actionlint and zizmor already cover pinning, permissions and injection reliably. Only the naming catalog and the forbidden-name rule are specific to this platform. `gitleaks-action` needs a paid license for organizations. | Yes |
| D2 | Checker is Python 3 standard library only, catalog is JSON. | PyYAML, Node, Bash | `verify-oidc.py` in the design is Python, the runner has Python, and avoiding a YAML dependency keeps the check install-free. | Yes |
| D3 | No empty skeleton folders. | `.gitkeep` placeholders for every directory in the map | The map is documented in the README; placeholders add noise and are deleted later. | Yes |
| D4 | `Staging` accepts runs from any branch; `Production` accepts only branches matching `release/*`. | Restrict both Environments to `main`; leave Production unrestricted | Staging supports branch-based testing, while Production runs are limited to release branches and remain approval-gated. | Yes |
| D5 | Settings are applied with `gh api` from the runbook and the ruleset payload is committed under `.github/rulesets/`. | Terraform GitHub provider; manual UI only | One command per setting, reviewable payload, no new tool, repeatable audit. | Yes |
| D6 | **Assumption:** at least two people can act as code owners. If the owner is the only human, the ruleset keeps `require_code_owner_review` and the owner is added as a pull-request-only bypass actor, recorded in the runbook as a known temporary exception to NFR-17 until a second reviewer exists. | Drop code-owner review; use a second account | Without this, the owner cannot merge any change. A visible, narrow bypass is safer than weakening the rule for everyone. Confirm at review. | Yes |
| D7 | **Decision:** `CODEOWNERS` lists the repository owner handle `@aldoawp` unless the organization explicitly designates a team. | Guess a team name | A wrong owner silently disables the review requirement, so Task 2 checks the file with GitHub's CODEOWNERS error report. | Yes |
| D8 | `Staging` allows self-review and has no reviewers. | Reviewer on `Staging` | The PRD requires no Staging approval (DEP-08). | Yes |
| D9 | Runbooks live in `docs/runbooks/`. | `docs/design/`, `docs/notes/` | `docs/design/` holds standards and `docs/notes/` holds evolving source material. Runbooks are operated procedures. | Yes |

## Versions

Checked on 2026-10-30 from the official GitHub release pages (`gh api repos/<repo>/releases/latest`).

| Dependency | Choice | Source |
|---|---|---|
| actionlint | v1.7.12 (released 2026-03-30) | `rhysd/actionlint` releases |
| zizmor | v1.31.1 (released 2026-10-15) | `zizmorcore/zizmor` releases; install with `pip install zizmor==1.31.1` |
| `actions/checkout` | v7.0.1 (released 2026-07-20); the workflow pins the commit SHA of this tag, looked up when the task is implemented | `actions/checkout` releases |
| Runner image | `ubuntu-24.04` | GitHub-hosted runners |
| Python | The runner's system Python 3; the checker must work on Python 3.10 or later | Runner image |

SHA pins and checksums are fixed at implementation time. Re-check the versions then and prefer a newer stable release if one exists.

## Invariants

| Invariant | How to check |
|---|---|
| No workflow step uses an unpinned third-party action. | `zizmor` in `workflow-lint`; negative fixture in Task 4. |
| `deploy-app.yml` can never read the admin key, the provider initial password or the Vault password. | Rule `F01`; unit test with a fixture workflow. |
| Only two Environments exist. | `gh api repos/Buzilion/CentralDevOps/environments --jq "[.environments[].name] \| sort"` returns `["Production","Staging"]`. |
| Staging accepts any branch without approval; Production accepts only `release/*`, requires the owner's approval, and cannot be bypassed by administrators. | Environment audit in the runbook returns no Staging reviewers and a null branch policy; Production has the required-reviewers rule, `can_admins_bypass: false`, and a `release/*` branch policy. |
| `main` and `release/*` accept changes only through reviewed, checked pull requests. | Ruleset audit; Task 5 attempts direct pushes and unreviewed merges against both patterns and both are refused. |
| No private key material is committed. | Rule `K01` plus the history scan in Task 6. |

## Error Behavior

| Situation | Behavior |
|---|---|
| `GH_TOKEN` overrides the authorized keyring account and `gh repo view` cannot resolve the repository. | Unset the override and confirm `gh auth status` shows an account with repository admin access. On 2026-10-31, the `aldoawp` keyring account returned `ADMIN` and active organization membership with role `admin`. |
| The plan or visibility does not allow the required Environment protection rules or rulesets (for example, required reviewers on a private/internal repository without Enterprise). | Task 1 stops, records the finding in the runbook, and asks the owner to make the repository public, upgrade the plan, or change the design. **Do not** continue with a weaker gate; every later spec assumes the Production approval gate exists. |
| The required reviewer cannot be set (user id not found or API refusal). | Fail with the API error. No Production secret may be created until the audit shows the reviewer rule. |
| The checker finds a violation. | Exit 1, print `path:line rule-id`, never the secret-like content. The CI check fails. |
| The catalog is invalid JSON or lacks required keys. | Exit 2 with the reason. The check fails closed. |
| actionlint or zizmor cannot be downloaded or fails its checksum. | The job fails; it never falls back to an unverified binary. |

## Testing Strategy

- **Unit tests** (`unittest`, standard library) for the checker, each using a temporary directory fixture: a valid reference passes; `STAGING_X`, `GITHUB_X`, `TOKEN`, a name with a wrong prefix, an uncataloged name, a variable used as a secret, dynamic access, `secrets: inherit`, a forbidden name in `deploy-app.yml`, and a PEM header in a tracked file each fail with the expected rule ID; `secrets.GITHUB_TOKEN` passes; a PEM match is never echoed.
- **Lint workflow negative fixtures**: on a scratch branch, a workflow with an unpinned action and a workflow with `${{ github.event.inputs.x }}` inside `run:` each fail `workflow-lint`. The scratch branch is deleted afterwards.
- **Settings audit**: the `gh api` audit commands in the runbook, run after Tasks 1 and 5 and again in Task 6, with output saved in the runbook evidence log.
- **History scan**: `git log --all -p -S"PRIVATE KEY-----"` shows no private key block.

## Out of Scope

- Variables and secrets themselves, other than the Environments that will hold them. Each later spec creates the ones it consumes.
- App repository Environments and the dispatch GitHub App (spec 02).
- `ansible.cfg`, inventories and roles (spec 03), registry schema and Compose policy (spec 06).
- Dependabot or automatic SHA updates for pinned actions; renewing pins is a manual reviewed change for now.
- Approver model after the deployment team is assigned (SEC-18, spec 15) and dispatch App narrowing (SEC-19, not delivered).
- Rotation procedures (SEC-16, spec 15).
