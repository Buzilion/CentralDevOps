# Spec 04: Docker and Restricted Deploy Runtime

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 04 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked on spec 03 |
| Depends on | `03_host-bootstrap-and-hardening` (its checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/infrastructure-v1.md` (`INF`), `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§5–6; `docs/design/naming-and-repository-conventions.md` §§3, 5–7; `docs/design/variables-and-secrets.md` §§1, 3.2, 4.3, 4.5; v5 design §§6.2, 8.5, 9.4, 11.1, 12.1, 16 steps 3–4, 17 #1 |

## What

Add the on-demand `configure-vps.yml` operation and its exact profile/limit/dry-run contract. Install and verify Docker Engine and Compose, create the platform's shared `edge` and fixed-subnet `db` networks, and provision a separate, unprivileged deploy identity. That identity may use only the root-owned `centraldevops-deploy` and `centraldevops-route` entrypoints through narrowly scoped sudo; it is not a member of the `docker` group and cannot change those entrypoints. Install the read-only GHCR pull credential as a root-only file.

This spec does not deploy an app or expose a public Docker, PostgreSQL, or app port. The deploy entrypoints created here are fail-closed interfaces; the deployment behavior is delivered by spec 11.

## Context

- Spec 03 owns the first host bootstrap, hardened SSH access, base accounts, firewall, and pinned Ansible setup. Spec 04 must not run until its checklist is fully complete and the disposable-host hardening proof is recorded.
- The roadmap lists spec 03 as written and its folder is present, but all seven tasks in `03_host-bootstrap-and-hardening/checklist.md` are unchecked; that checklist itself is gated on spec 01. This spec can be reviewed and prepared, but implementation and host changes are blocked until the prerequisite checklists are complete.
- The initial host is an Ubuntu all-in-one VPS per Environment. Role groups and profile names must also support later split-host placement without workflow changes.
- The configure workflow is an infrastructure operation, never part of app deployment. It uses only the selected Environment's inventory and credentials; Production runs wait for the CentralDevOps `Production` approval gate before accessing secrets or connecting.
- Docker's daemon is root-equivalent. Neither the app workload nor the deploy SSH identity may receive Docker socket access. The root-owned server-side scripts are the only deploy-time privileged boundary.

## Requirements

| ID | Statement | Source |
|---|---|---|
| D-01 | `configure-vps.yml` runs only on demand, in CentralDevOps, and rejects the deployment-dispatch GitHub App identity before Environment credentials or host access are used. | INF-14 |
| D-02 | The workflow accepts only `Staging` or `Production`, one exact profile (`app`, `proxy`, `database`, `monitoring`, `all-in-one`), an optional exact host/group limit, and a dry-run flag. It derives the inventory from the selected Environment; operators cannot supply an inventory path. | INF-03, INF-05, INF-08 |
| D-03 | An unknown host/group or a name belonging only to the other Environment is rejected before any SSH connection. No Ansible pattern syntax, comma-separated list, or arbitrary CLI option is accepted as a limit. | INF-05, INF-08 |
| D-04 | Dry run executes Ansible check mode and diff, makes no host changes, and reports the planned changes. Normal configure is idempotent: a second unchanged run reports zero changes. | INF-03, INF-04 |
| D-05 | The profile-to-role mapping matches v5 §6.2 exactly. Roles not yet delivered by later roadmap specs are explicit dependencies; a missing role fails preflight rather than being silently skipped. | INF-03 |
| D-06 | Docker Engine and Compose are installed from the reviewed Ubuntu package source with explicit, reviewed versions. The Docker API is not exposed over TCP, and app containers do not receive the Docker socket. | INF-11; NFR-13 |
| D-07 | The `edge` and `db` Docker bridge networks exist before applications are deployed. Their names are fixed and shared on each Docker host. The `db` network has an inventory-declared fixed subnet, validated not to overlap host/VPS routes or another Docker network. | INF-11; DB-02; v5 §§9.4, 11.1 |
| D-08 | The deploy account is unprivileged, has a separate Environment-specific key, is not in the `docker` group, and can invoke only `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` with arguments validated by those root-owned scripts. | INF-12, INF-13; SEC-06; v5 §8.5 |
| D-09 | The two deploy entrypoints are root-owned and not writable by the deploy account. In this spec they fail closed until spec 11 installs the deployment implementation; invalid argument forms are rejected. | INF-12 |
| D-10 | The GHCR pull token has read-only package access, is installed only on the selected Environment's host at a root-only path and is never exposed in logs, diffs, artifacts, inventory, or the deploy account's readable files. | SEC-11 |
| D-11 | No app service publishes a host port in this initial `docker_edge` topology. PostgreSQL and app ports remain private; the public host exposure remains 80/443 plus SSH per the established access policy. | INF-10, INF-11; NFR-13 |
| D-12 | Staging and Production deploy keys and GHCR credentials are distinct. Their private values exist only as CentralDevOps Environment secrets; public deploy keys may be committed to their matching Environment inventory. | SEC-06, SEC-11 |

## Design

### Configure workflow contract

Create `.github/workflows/configure-vps.yml` with `workflow_dispatch` only:

| Input | Type | Accepted values / behavior |
|---|---|---|
| `target_environment` | choice | Exact case-sensitive `Staging` or `Production`; selects `inventories/staging/hosts.yml` or `inventories/production/hosts.yml` and the matching GitHub Environment |
| `profile` | choice | `app`, `proxy`, `database`, `monitoring`, `all-in-one` |
| `limit` | string, optional | One exact inventory host alias or group name; empty means the selected inventory's full target set |
| `check_mode` | boolean | `true` invokes `ansible-playbook --check --diff`; `false` performs convergence |

The workflow has top-level `permissions: {}` and grants only the permissions needed to checkout reviewed code. Pin actions to reviewed commit SHAs, set `persist-credentials: false`, pass inputs through environment variables, and never interpolate dispatch input directly into `run:`. The job uses the matching GitHub Environment. Its pre-environment job condition must reject the dispatch App's verified numeric actor ID before the Environment-bound job can start. Do not guess the actor ID; carry forward the value proven by spec 02.

Before any SSH operation, run a local preflight that:

1. Confirms the workflow ref is `refs/heads/main`, the actor is not the dispatch App, and all choice inputs are exact allowed values.
2. Selects the inventory exclusively from `target_environment`, parses its hosts and groups, and confirms an optional `limit` exactly names one host or group in that inventory.
3. Rejects patterns, option-like values, separators, whitespace, and any host/group not in the selected inventory. Do not pass an unvalidated input to Ansible.
4. Confirms every role selected by the profile is installed and the inventory contains the required Docker network and deploy-key facts.

Any preflight failure stops before SSH or secret-bearing tasks. For Production, GitHub's Environment approval is required before the privileged job can access its secrets.

### Configure profiles

Use the v5 §6.2 role sets. The `baseline` referenced below is `common`, `users`, `ssh_hardening`, `firewall`, `docker`, `deploy_runtime`, `monitoring_agent`, plus the `backup` volume configuration where specified.

| Profile | Exact role set |
|---|---|
| `app` | baseline |
| `proxy` | baseline + `nginx`, `certbot` |
| `database` | `common`, `users`, `ssh_hardening`, `firewall`, `docker`, `deploy_runtime`, `monitoring_agent`, `postgresql`, `backup` |
| `monitoring` | baseline + `collector` |
| `all-in-one` | `app` + `proxy` + `database` (deduplicated role execution) |

Spec 03 supplies the first four baseline security roles; this spec supplies `docker` and `deploy_runtime`. Later specs add `nginx`/`certbot`, `postgresql`, `backup`, `monitoring_agent`/`collector` and their verification. The profile contract is fixed here, but preflight must fail with a clear missing-role message until every role required by a selected profile has been delivered. Do not silently run a partial profile.

### Docker and networks

- Install Docker Engine and the Compose v2 plugin from the official Docker Ubuntu apt repository using explicit package-version variables reviewed and tested for the Ubuntu release pinned by spec 03. Do not use an unverified convenience script or floating install command.
- Configure and verify the Docker daemon has no public TCP listener. Keep access to the Docker socket limited to root and the intended Docker administration group; `cdo-deploy` is not a member of that group.
- Create the external bridge network `edge` for proxy-to-app traffic. Create external bridge network `db` with the fixed subnet supplied by the selected Environment inventory. Require the subnet to be explicit, valid CIDR, and non-overlapping with host routes, VPS/private routes, Docker pools, and other declared network ranges.
- Keep the initial shared network names exactly `edge` and `db`; do not append app or Environment suffixes. The networks are local to each Environment's separate host.
- Do not publish container ports. In the initial `docker_edge` model, proxy and app containers communicate through `edge`; database-enabled apps additionally attach to `db`. Later `private_ip` placement is out of scope here.
- Use Ansible modules for package/service/network state where available, with idempotent handlers. Avoid shell tasks that bypass check mode. Re-running configure with unchanged inputs must report zero changes.

### Restricted deploy runtime

Create role `roles/deploy_runtime/` to:

- Create the dedicated `cdo-deploy` account with no administrative group memberships and no Docker group membership.
- Install only the matching Environment's deploy public key in `authorized_keys`, using the `restrict` option. Do not use unstable GitHub-hosted runner source-address restrictions.
- Install `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` as root-owned, non-deploy-writable entrypoints. Their spec-04 implementations are fail-closed stubs: validate the allowed argument grammar, emit a non-sensitive “deployment implementation unavailable” error, and return nonzero. Spec 11 replaces their behavior while preserving paths, ownership, permissions, and validation boundary.
- Install a sudoers rule that permits `cdo-deploy` to run only those two absolute paths. The scripts revalidate every argument and input file; no general shell, Docker command, or other sudo capability is granted.
- Configure SSH and sudo audit logging sufficient to attribute the deploy account's session and each allowed command. Do not log secret contents.
- Install the selected Environment's `GHCR_PULL_TOKEN` at `/root/.config/centraldevops/ghcr-pull-token` with owner `root`, group `root`, mode `0600`; secret-handling tasks use `no_log: true` and never display diffs. The token must have `read:packages` only.

The matching deploy private key and GHCR token are set as `DEPLOY_SSH_PRIVATE_KEY` and `GHCR_PULL_TOKEN` secrets in the CentralDevOps `Staging` or `Production` Environment. Generate separate values for each Environment; do not put private keys or token values in inventory or repository variables. Add the names and kinds to the existing GitHub name catalog in the same implementation change.

### Deliverables

```text
.github/workflows/configure-vps.yml
playbooks/configure.yml
roles/docker/
roles/deploy_runtime/
deployment/scripts/centraldevops-deploy
deployment/scripts/centraldevops-route
deployment/tools/validate-configure-inputs.py
deployment/tools/tests/
docs/runbooks/configure-vps.md
```

Update the Ansible requirements/configuration established by spec 03 only as needed for the chosen Docker modules. Do not create an alternate inventory, duplicate Environment settings, or a separate workflow per Environment.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Docker package versions are explicit inventory/role variables, selected after testing against spec 03's pinned Ubuntu release. | Floating latest packages; install convenience script | Reproducible convergence and reviewable upgrades without assuming a host OS/package version not yet recorded. | Yes |
| D2 | The `db` subnet is a required per-Environment inventory value and is validated for overlap before network creation. | Hard-code the example `172.30.0.0/24` | The design only gives that subnet as an example; host/private-network overlap must be checked on the actual VPS before choosing a value. | Yes |
| D3 | Profile mappings follow v5 §6.2 exactly; missing later-spec roles fail preflight. | Silently skip unavailable roles; temporarily redefine profiles | Prevents a selected profile from claiming success while applying only part of its contract. | Yes |
| D4 | Deploy script paths and privileged boundary are created here as fail-closed stubs, then implemented by spec 11. | Grant sudo before scripts exist; put deploy behavior in the workflow | Allows the restricted runtime to be installed and tested without creating a temporary privilege bypass or moving host deployment logic into Actions. | Yes |
| D5 | The deploy SSH public key and read-only GHCR token are distinct per Environment. | Share credentials across Staging and Production | Limits cross-Environment blast radius and satisfies SEC-06/SEC-11. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Configure cannot reach the other Environment's hosts. | Negative test: cross-Environment and unknown limit rejected before an SSH connection; inspect selected inventory path. |
| Dry run changes nothing on the host. | Snapshot relevant package, service, network, account and sudoers state before/after a check-mode run. |
| A second configure run is idempotent. | Run configure twice with unchanged inputs; second run reports zero changes. |
| The `edge` and `db` networks exist and use the exact names. | `docker network inspect edge db`; verify `db` subnet matches inventory and does not overlap host routes. |
| `cdo-deploy` is not Docker-equivalent. | Confirm no Docker group membership, no socket access, and direct Docker command denied. |
| Deploy sudo is limited to the two root-owned entrypoints. | `sudo -l -U cdo-deploy`; attempts to run a shell, Docker, or unrelated command fail; script files are not writable by `cdo-deploy`. |
| The GHCR credential is secret and root-only. | Inspect path owner/mode and access as `cdo-deploy`; review Ansible output/logs for absence of value. |
| No container or host exposes app, PostgreSQL, or Docker API ports publicly. | Inspect Docker daemon configuration, firewall, container port bindings, and an external port scan. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Spec 03 checklist or disposable-host hardening proof is incomplete. | Do not implement or run configure against any VPS; report the prerequisite as blocked. |
| The workflow is not on `main`, the caller is the dispatch App, or an input is invalid. | Fail/skip before Environment credentials and before any connection; report the failed preflight check without printing secrets. |
| Limit is unknown, malformed, or belongs to the other Environment. | Reject before SSH; never fall back to the full inventory. |
| A profile references a role not yet delivered or an invalid/missing inventory fact. | Fail preflight with the exact missing role/fact; do not apply a partial profile. |
| Docker package source/version is unavailable or checksum/signature validation fails. | Stop the role and leave the prior Docker installation unchanged; do not fall back to an unpinned installer. |
| The `db` subnet overlaps an existing route/network or is invalid. | Stop before creating networks; require an explicit reviewed inventory correction. |
| A secret task fails or would display a diff. | Fail the run without logging the secret value; no plaintext fallback or artifact. |
| A deploy entrypoint receives invalid arguments or implementation is not yet available. | Reject with a nonzero exit and sanitized error; never perform a partial deployment or return success. |

## Testing Strategy

- **Workflow/preflight tests:** exact valid inputs pass; invalid Environment/profile, malformed limit, unknown host/group, cross-Environment host/group and dispatch-App actor are rejected before SSH.
- **Profile tests:** assert the exact role set for each profile, deduplicated `all-in-one` execution, and a clear failure for any missing role.
- **Docker role tests:** idempotent package/service/network state; exact network names; subnet validation including overlap; no public TCP Docker listener; check mode does not mutate.
- **Deploy runtime tests:** separate authorized keys; `cdo-deploy` absent from privileged/Docker groups; `sudo -l` allows only the two entrypoints; script ownership/modes and argument rejection; direct Docker and arbitrary sudo commands fail.
- **Credential handling:** use a synthetic canary token on a disposable test host, verify root-only file access and absence from workflow logs, Ansible output, diffs and artifacts. Do not use a production credential in tests.
- **Host acceptance:** after spec 03's disposable VPS proof, configure that disposable host; verify networks, deploy identity and read-only GHCR pull behavior. Do not install real application workloads or weaken the firewall.
- **Runbook:** document exact safe configure, check-mode, limit-validation and audit commands, plus recovery steps. No Production host is used for destructive or negative tests.

## Out of Scope

- Host bootstrap, SSH hardening proof and base roles owned by spec 03.
- `verify-vps.yml`, which is delivered by spec 05; this spec supplies the verification evidence and checks that spec 05 must formalize.
- Registry, Compose schema/policy, capacity checks and app-level image pulls (spec 06 and later). The host role creates Docker and shared networks only.
- Nginx/Certbot, PostgreSQL provisioning, backup and monitoring role implementations (specs 07, 08, 13 and 14). Their profile role names and membership are contractual here.
- Production deployment authorization, Compose rendering, deploy/route script functionality, health checks, rollback, locks and records (specs 10–11).
- Public app/PostgreSQL ports, Docker socket access for apps, or any app deployment.
