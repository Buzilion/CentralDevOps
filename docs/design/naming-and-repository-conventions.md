# CentralDevOps Naming and Repository Conventions (v1)

| Item | Value |
|---|---|
| Status | Draft for review |
| Created | 2026-10-29 |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Companion guide | `docs/design/variables-and-secrets.md` |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` |

This document defines the canonical names and file locations for the CentralDevOps v1 platform. The parent PRD and module PRDs remain the requirements source; this guide consolidates their explicit names and fills gaps with consistent defaults. In particular, the host-alias pattern and Compose project name below are conventions added here because the PRDs do not prescribe a complete pattern for them.

## 1. Sources and scope

The standards here are based on the parent PRD and all nine module PRDs:

- `infrastructure-v1.md` (INF)
- `access-and-secrets-v1.md` (SEC)
- `app-release-v1.md` (REL)
- `central-deployment-v1.md` (DEP)
- `registry-and-policy-v1.md` (REG)
- `routing-and-tls-v1.md` (RTE)
- `database-v1.md` (DB)
- `backup-and-recovery-v1.md` (BKP)
- `observability-v1.md` (OBS)

All module PRDs are in `docs/prd/01_init-cicd_291026/`. Variable and secret names, placement, and handling are detailed in `docs/design/variables-and-secrets.md`; follow that guide for those values.

## 2. Canonical casing and separators

| Identifier | Canonical format | Examples |
|---|---|---|
| GitHub Environment | Exact PascalCase names | `Staging`, `Production` |
| Environment path/file component | Lowercase full name | `staging`, `production` |
| Environment code in host aliases | Lowercase short code | `stg`, `prd` |
| Application slug | Lowercase kebab-case | `customer-builder` |
| Workflow, playbook, and Markdown filenames | Lowercase kebab-case | `deploy-app.yml`, `restore-database.yml`, `naming-and-repository-conventions.md` |
| Ansible roles, groups, and variables | Lowercase snake_case | `ssh_hardening`, `database_nodes`, `private_ip` |
| GitHub variables and secrets | `SCREAMING_SNAKE_CASE` with an ownership prefix | `DEPLOY_HEALTHCHECK_TIMEOUT`, `APP_AUTH_SECRET` |
| Shared Docker network | Fixed lowercase name | `edge`, `db` |

Use lowercase directory names. Use kebab-case for descriptive multiword directories, except for Ansible's `group_vars` and `host_vars` conventions. Keep existing initiative-directory names such as `01_init-cicd_291026`; do not rename them as part of unrelated work.

## 3. Environments and VPS hosts

### 3.1 Environments

Every CentralDevOps and onboarded app repository has exactly two GitHub Environments: `Staging` and `Production` (SEC-01). Each Environment maps to its corresponding deployment VPS; do not create an Environment per VPS.

| Use | Staging | Production |
|---|---|---|
| GitHub Environment and workflow input value | `Staging` | `Production` |
| Inventory directory | `inventories/staging/` | `inventories/production/` |
| Central registry file | `apps/<app>/staging.yml` | `apps/<app>/production.yml` |
| App route manifest | `deploy/staging.yml` | `deploy/production.yml` |
| Host-alias environment code | `stg` | `prd` |

Use the full, case-sensitive Environment name in workflow inputs and GitHub settings. Use the lowercase form in paths and filenames. Use `stg` and `prd` only in short host identifiers, not as alternative GitHub Environment names. Do not create separate `STAGING_` or `PRODUCTION_` variable/secret names; keep the same prefixed name in both Environments and let the Environment supply its value (SEC-02).

### 3.2 VPS inventory aliases

Use this stable pattern for each VPS inventory alias:

```text
<environment-code>-<host-purpose>-<two-digit-number>
```

| Part | Values |
|---|---|
| Environment code | `stg`, `prd` |
| Host purpose | `aio` for the initial all-in-one host; `app`, `proxy`, or `database` for a dedicated host if the topology is later split |
| Number | Starts at `01` within each environment and purpose |

Examples: `stg-aio-01` (the v5 design example), `prd-aio-01`, `stg-proxy-01`, and `prd-database-01`.

The alias is the inventory host key and the stem of its `host_vars` file, for example `host_vars/stg-aio-01.yml`. Keep IP addresses and other per-host facts in that Environment's inventory, not in the alias or a GitHub variable (INF-07, SEC-03). The all-in-one host belongs to each applicable role group; do not create a separate VPS identity for every role. Keep aliases stable when placement changes and express role membership through inventory groups.

## 4. Applications and release images

### 4.1 Application identifiers

Use a stable lowercase kebab-case slug matching `^[a-z0-9]+(-[a-z0-9]+)*$`, such as `customer-builder`. Reuse it as the registry's `app` value, the CentralDevOps registry directory, and by default the app repository name and final GHCR image component. Do not add an environment suffix to the application slug.

CentralDevOps owns one reviewed registry file per app and Environment:

```text
apps/<app-slug>/staging.yml
apps/<app-slug>/production.yml
```

For example, `apps/customer-builder/staging.yml` and `apps/customer-builder/production.yml`. The registry owns the image repository, allowed refs, domains, placement, limits, and database settings. The app name is derived from the authenticated repository and registry; it is never a deployment input (REG-01, DEP-02).

The app repository owns its route-only manifests:

```text
deploy/staging.yml
deploy/production.yml
```

These manifests request the app's route and runtime contract only. They do not choose its image repository, placement, resource limits, or allowed refs (REG-02).

### 4.2 GHCR image names and release identity

Use this canonical image repository:

```text
ghcr.io/<github-owner>/<app-slug>
```

Use lowercase path components and the app slug as the image name, for example `ghcr.io/example-org/customer-builder`. The reviewed registry entry is the source of truth for the repository name.

Deploy only a full immutable digest reference:

```text
ghcr.io/<github-owner>/<app-slug>@sha256:<64-hex-digest>
```

The `sha-<full-commit>` tag may be published as a convenience, but tags (including `latest`) are not valid deployment inputs. Production digests require verified provenance as configured in the registry (REL-03, REL-04, REL-05, DEP-04, DEP-05).

## 5. Docker networks and Compose projects

### 5.1 Shared network names

The platform-managed external Docker networks have fixed names on each applicable host:

| Network | Purpose |
|---|---|
| `edge` | Private proxy-to-app routing when the proxy and app share a host |
| `db` | Private app-to-PostgreSQL connectivity |

Do not append an app or Environment suffix to these names. An Environment has its own VPS and Docker Engine; the network names are local to that host. App Compose configurations may use their project-scoped default network and the permitted external networks, but must not redefine the platform networks or publish ports publicly (INF-11, REG-05, DB-02, RTE-02).

### 5.2 Compose project names

Use one stable Compose project for each app and Environment:

```text
centraldevops-<app-slug>-<environment-path>
```

Examples:

- `centraldevops-customer-builder-staging`
- `centraldevops-customer-builder-production`

The CentralDevOps deployment derives this name from the authorized app and selected Environment and passes it explicitly to Compose with `--project-name`. Do not rely on the current directory name or accept a caller-supplied project name. If an app's `compose.yml` declares a top-level `name`, it must match the derived name and pass policy validation. Keep the name stable across releases; a live project rename can change which containers, networks, or volumes Compose targets.

The app-owned Compose file is named `compose.yml`. Durable app bind mounts must remain under `/opt/apps/<app-slug>/<environment-path>/`; the project name and this directory both distinguish the app and Environment (REG-05, BKP-14).

## 6. Workflow and action names

Use these canonical paths:

| Repository | Path | Operation |
|---|---|---|
| CentralDevOps | `.github/workflows/bootstrap-vps.yml` | On-demand VPS bootstrap |
| CentralDevOps | `.github/workflows/configure-vps.yml` | On-demand host configuration |
| CentralDevOps | `.github/workflows/verify-vps.yml` | Read-only host verification |
| CentralDevOps | `.github/workflows/deploy-app.yml` | Authenticated central deployment |
| CentralDevOps | `.github/actions/request-deploy/action.yml` | Shared app-side request, sealing, dispatch, and polling |
| Each app repository | `.github/workflows/build.yml` | Manual test, build, and GHCR publication |
| Each app repository | `.github/workflows/deploy.yml` | Manual request to deploy a digest |

Use lowercase kebab-case `.yml` filenames for new workflows. Keep build and deploy as separate app operations, and keep the three infrastructure workflows separate from application deployments. Do not create one workflow file per Environment; use the exact `target_environment` values `Staging` and `Production`. The privileged deploy workflow and its credentials remain in CentralDevOps; the app workflow requests deployment through the reviewed shared action (INF-14, REL-01, REL-09, REL-11, DEP-01).

## 7. Ansible resource names and locations

| Resource | Canonical naming and location |
|---|---|
| Ansible configuration and collections | Root `ansible.cfg` and `requirements.yml` |
| Environment inventories | `inventories/staging/hosts.yml` and `inventories/production/hosts.yml` |
| Pinned SSH host keys | `inventories/<environment>/known_hosts` |
| Inventory groups | Lowercase snake_case plural role groups: `app_nodes`, `proxy_nodes`, `database_nodes` |
| Shared group variables | `inventories/<environment>/group_vars/all.yml` and one `<group-name>.yml` per group |
| Host variables | `inventories/<environment>/host_vars/<inventory-alias>.yml` |
| Playbooks | `playbooks/`; established names are `bootstrap.yml`, `configure.yml`, `verify.yml`, and `restore-database.yml` |
| Roles | `roles/<role_snake_case>/`; defined roles are `common`, `users`, `ssh_hardening`, `firewall`, `docker`, `nginx`, `certbot`, `postgresql`, `backup`, `monitoring_agent`, and `deploy_runtime` |
| Configure profiles | Exact values: `app`, `proxy`, `database`, `monitoring`, `all-in-one` |

`wireguard` is a reserved later-phase role name if private networking between hosts is needed; do not install it unless that design is approved (INF-21).

Use snake_case for Ansible group names, role names, and Ansible variables. Keep the inventory as the only source for host-specific addresses, users, groups, ports, private IPs, and capacity budgets; keep app placement and policy in the registry. Never hard-code a host or address in a workflow. Public keys and pinned host keys may be committed in their documented locations; private keys and credentials must not be committed (INF-07, INF-08, INF-09, SEC-03, SEC-06).

## 8. Repository ownership and file placement

### 8.1 Ownership boundary

| Repository/owner | Owns | Must not own |
|---|---|---|
| CentralDevOps platform owner | Infrastructure workflows and Ansible, inventories, reviewed app registry, schemas and policy, deployment scripts, shared request action, and central deployment workflow | App source code, app runtime secrets, or mutable release identity |
| App team in its app repository | App source and Dockerfile, `compose.yml`, route manifests, build/deploy request workflows, and app runtime configuration/secrets | Admin or deploy SSH keys, GHCR pull token, central decryption key, or authority to choose central placement and policy |

The registry is centrally reviewed; the app's manifest and Compose file are app-owned inputs constrained by the registry and deployment policy. App teams propose registry changes through a CentralDevOps pull request rather than editing or copying central workflow logic. Each repository uses the same two GitHub Environments; credentials stay with the owner and Environment defined by the PRDs (SEC-01, SEC-08, SEC-09, REG-02, REG-09).

### 8.2 CentralDevOps directory map

Create new platform files in the directory that owns their function:

```text
CentralDevOps/
├── .github/
│   ├── CODEOWNERS
│   ├── workflows/                 # bootstrap-vps, configure-vps, verify-vps, deploy-app
│   └── actions/request-deploy/action.yml
├── inventories/
│   ├── staging/
│   │   ├── hosts.yml
│   │   ├── known_hosts
│   │   ├── group_vars/             # all.yml, app_nodes.yml, proxy_nodes.yml, database_nodes.yml
│   │   └── host_vars/<host>.yml
│   └── production/                 # same layout
├── apps/<app-slug>/
│   ├── staging.yml
│   └── production.yml
├── playbooks/
├── roles/<role_snake_case>/
├── deployment/
│   ├── scripts/                    # centraldevops-deploy, centraldevops-route, centraldevops-compose-policy
│   ├── nginx-templates/            # http-only.conf.j2, https.conf.j2
│   ├── keys/                       # staging.age.pub, production.age.pub; public keys only
│   ├── schemas/                    # registry.schema.json, app-manifest.schema.json
│   └── tools/                      # verify-oidc.py
├── docs/
│   ├── prd/<initiative>/           # parent and module PRDs
│   ├── design/                     # standards and enduring design documents
│   └── notes/requirements/<initiative>/<version>/
└── README.md
```

- Put repository-wide standards and enduring design documents in `docs/design/`. This file belongs at `docs/design/naming-and-repository-conventions.md`.
- Put the parent PRD and its module PRDs together in `docs/prd/<initiative>/`; use lowercase kebab-case Markdown filenames, such as `infrastructure-v1.md`.
- Put evolving source requirements/design material in `docs/notes/requirements/<initiative>/<version>/`.
- Put Ansible host-specific facts only in `inventories/<environment>/`; put app-specific placement and policy only in `apps/<app-slug>/`.
- Put infrastructure automation in `playbooks/` and `roles/`; put server-side deployment scripts, templates, schemas, public keys, and validation tools in their respective `deployment/` subdirectories.
- Create or maintain CentralDevOps code-owner rules at `.github/CODEOWNERS`. Require code-owner review for `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`, `.github/CODEOWNERS` and `.github/rulesets/**` before merging to `main` or `release/*`; protect both branch patterns with the same repository ruleset (SEC-13).

### 8.3 App repository directory map

The app repository owns app code and the unprivileged request path:

```text
<app-repository>/
├── .github/workflows/
│   ├── build.yml
│   └── deploy.yml
├── Dockerfile
├── compose.yml
├── deploy/
│   ├── staging.yml
│   └── production.yml
└── README.md
```

Do not add CentralDevOps registry files, host inventories, privileged deployment scripts, or server credentials to an app repository. Keep app secrets in the app's GitHub Environments and only inside the sealed deployment bundle when sent to CentralDevOps (SEC-08, SEC-09, REL-07).
