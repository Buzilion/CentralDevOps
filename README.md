# CentralDevOps

## Purpose

CentralDevOps is designed to provide shared CI/CD workflows and infrastructure automation for application repositories. It centralizes deployment policy and privileged release execution; deployments use immutable image digests rather than mutable tags.

## Environments

The target model is exactly two GitHub Environments, not one per VPS. The following settings match the API audit completed on 2026-10-31:

| Environment | Configured behavior |
|---|---|
| `Staging` | No required reviewers; accepts runs from any branch. |
| `Production` | Requires repository-owner approval without administrator bypass; accepts runs from `release/*` branches. |

In the design, each Environment maps to its corresponding deployment target. The current API audit confirms the Production reviewer and `release/*` policy; Staging has no branch restriction. See the [GitHub Environments runbook](docs/runbooks/github-environments.md).

## Documentation

- **Requirements:** [Parent PRD](docs/prd/01_init-cicd_291026/prd-v1.md) · [Access and secrets PRD](docs/prd/01_init-cicd_291026/access-and-secrets-v1.md)
- **Design:** [Naming and repository conventions](docs/design/naming-and-repository-conventions.md) · [Variables and secrets](docs/design/variables-and-secrets.md) · [Infrastructure contracts and invariants](docs/design/infrastructure-contracts-and-invariants.md) · [Source design (v5)](docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md)
- **Specifications:** [Spec roadmap](docs/specs/01_init-cicd_291026/00_spec-roadmap.md) · [Foundation and access spec](docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md)
- **Operations:** [GitHub Environments apply and audit runbook](docs/runbooks/github-environments.md)

## Target directory map — implementation added by later specs

This is the intended layout, not a claim that every path exists. Later specs create implementation directories only when needed; no empty skeletons are added. The documentation directories and `deployment/tools/` already exist.

| Path | Purpose and timing |
|---|---|
| `.github/CODEOWNERS` | Code ownership rules; added by this foundation task. |
| `.github/workflows/`, `.github/actions/` | Central workflows and shared actions; added by later specs. |
| `.github/rulesets/` | Repository branch protection ruleset; added by this foundation task. |
| `inventories/{staging,production}/` | Environment-specific Ansible inventory; added by later specs. |
| `apps/<app-slug>/` | Reviewed per-app deployment registry; added by later specs. |
| `playbooks/`, `roles/<role_snake_case>/` | Ansible operations and reusable roles; added by later specs. |
| `deployment/scripts/`, `deployment/nginx-templates/`, `deployment/keys/`, `deployment/schemas/` | Runtime scripts, templates, public keys, and schemas; added by later specs. |
| `deployment/tools/` | Validation utilities; present and extended by later specs. |
| `docs/prd/<initiative>/`, `docs/design/`, `docs/notes/requirements/<initiative>/<version>/`, `docs/runbooks/` | Requirements, enduring design, source notes, and operational procedures; present. |

## Conventions

- Use lowercase kebab-case for app slugs and descriptive directories; use `SCREAMING_SNAKE_CASE` with subsystem prefixes for variables and secrets.
- Use only the GitHub Environment names `Staging` and `Production`; keep variable and secret names the same in both Environments, with each Environment supplying its own value.
- Deploy by immutable image digest; mutable tags are not deployment inputs.

## Local checks

Run from the repository root:

```sh
python3 deployment/tools/check-github-names.py
python3 -m unittest discover -s deployment/tools/tests
```

On Windows, use `py -3` in place of `python3`.

## Platform assumptions

GitHub's [Environments REST documentation](https://docs.github.com/en/rest/deployments/environments) states that public repositories support Environments, deployment-branch policies, required reviewers, and wait timers on current plans (legacy plans excluded). Private or internal repositories need Pro, Team, or Enterprise for Environment and deployment-branch features, and Enterprise for required-reviewer or wait-timer protection rules.

**Repository-specific status (2026-10-31):** With `GH_TOKEN` unset, `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission` succeeded as `aldoawp` with `PUBLIC` visibility and `ADMIN` permission. The Buzilion organization plan is `Free`. The Environment list is exactly `["Production","Staging"]`; Production requires approval by `aldoawp`, disallows administrator bypass, and accepts only `release/*`, while Staging has no approval or branch restriction. This foundation work created no Environment secrets or variables.

Use the [GitHub Environments runbook](docs/runbooks/github-environments.md) to re-audit after any visibility or plan change. Environment protection settings and the active `main`/`release/*` ruleset (ID `26226141`) are verified; the canonical ruleset payload is maintained at `.github/rulesets/main.json`.
