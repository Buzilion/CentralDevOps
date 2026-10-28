# CentralDevOps — Complete VPS Infrastructure and Deployment Design (v4.1, compressed)

**Status:** Compressed edition of v4 (same decisions, tighter wording, section numbers preserved). The `deploy-app.yml` build is gated on the spike in §17 #1.
**Supersedes:** `centraldevops-complete-infrastructure-design.md` (v4) for reading; v4 remains the full-text version.
**Companions:** `centraldevops-deployment-contract.md` (schemas, workflow skeletons, script contracts), `centraldevops-decision-log.md`. Both are still v3 versions, not updated for v4.

| Item | Decision |
|---|---|
| Runtime | Docker Compose, one all-in-one Ubuntu VPS per environment at first |
| VPS provider | Sumopod (private network, firewall, console; no snapshots, no API). S3 storage is a separate product (§17) |
| Scale | Up to **6 apps** within 6 months |
| Recovery | **RTO 4 h, RPO 12 h** |
| Infra automation | GitHub Actions + Ansible, run from CentralDevOps |
| App deployment | **Same-repo workflow** in the app repo with standard GitHub Actions auth; no cross-repo dispatch now. Confirmed by spike §17 #1 before `deploy-app.yml` is built |
| Registry | GHCR, deploy by immutable digest |
| Routing / TLS | Nginx; DNS at Masterweb (domains at exabytes.co.id); Let's Encrypt **HTTP-01** |
| Database | One shared PostgreSQL per environment, per-app DB and role; per-app container path documented |
| Rollout | Compose replace; blue/green later |
| Monitoring | Grafana Cloud, collector on each VPS |

---

## 1. Executive decisions

1. Every app repo has two manual workflows: `build.yml` and `deploy.yml`, kept separate.
2. **The GHCR digest is the release identity.** Deploy `ghcr.io/OWNER/IMAGE@sha256:…`, never a mutable tag.
3. **Same-repo deployment (v4).** The app's `deploy.yml` calls the CentralDevOps reusable `deploy-app.yml`, pinned to a reviewed commit SHA. A called reusable workflow runs in the caller's context (see correction), so where the deploy SSH key lives is settled by the spike (§17 #1) **before** `deploy-app.yml` is built.
4. **Standard GitHub auth** (`GITHUB_TOKEN`, OIDC where appropriate); no shared secret or PAT. OIDC audience and claims are validated in the spike (§8).
5. **App runtime secrets stay app-owned** (app `Staging`/`Production` Environment), encrypted at rest and in transit, never plaintext in artifacts. Whether a sealed age bundle is needed is decided by the spike; add it only if a trust boundary is crossed.
6. **Central registry `apps/<app>/<env>.yml`** decides placement, allowed domains and resource ceilings. The app manifest declares only the wanted route (domain, port, service, health path). No per-VPS GitHub variables.
7. **Two GitHub Environments, `Staging` and `Production`, in every repo,** with identical variable/secret names and per-environment values. Prefixes (`ANSIBLE_`, `DEPLOY_`, `GHCR_`, …) show ownership. Per-host data lives in Ansible inventory.
8. **Three separate infra workflows:** `bootstrap-vps.yml`, `configure-vps.yml`, `verify-vps.yml`, never part of an app deployment.
9. **Design for a separate proxy (and later DB/app hosts) from day one.** Placement is data in registry and inventory, not workflow logic.
10. **No Kubernetes or Swarm yet.** Stateless apps, repeatable deploys and rehearsed recovery first.

### Correction to v2

v2 claimed a CentralDevOps reusable workflow would use CentralDevOps' environment secrets. Per GitHub docs, a called reusable workflow runs in the **caller's** context, so `environment:` resolves in the caller's repo and cannot expose CentralDevOps-held credentials. Truly centralized execution needs a workflow running **in CentralDevOps** via cross-repo `workflow_dispatch` (the v3 model). v4 uses a same-repo workflow instead; the spike (§17 #1) must validate OIDC audience/claims and Environment-secret behavior and confirm server credentials stay out of reach of app code.

### Plan check (resolved)

Environment secrets/variables work on the organization's repositories. Document the plan/visibility assumption in the README so a downgrade is noticed.

---

## 2. Requirements and capacity targets

| Requirement | Consequence |
|---|---|
| Up to 6 apps in ~6 months | One VPS per environment works only with **mandatory per-app memory/CPU limits** and a registry capacity check (§9.3). Revisit sizing at 4 apps |
| RTO 4 h | Lost VPS is rebuilt from code: bootstrap → configure → redeploy recorded digests → restore DB. Timed restore drill required (§13.3) |
| RPO 12 h | DB dumps every **6 h**, off-host to S3 (§13.2). Alert when newest good backup is older than **8 h** |
| Brief deploy interruption OK | Plain `docker compose up -d`; blue/green deferred (§14) |
| Staging and Production | **Separate VPS instances**, never shared |
| Sizing | Production: **2 vCPU, 4 GB, 60 GB SSD**. Staging (estimate): **1 vCPU, 2 GB, 20 GB**. Multiple apps per VPS, count bounded by limits and capacity check (§9.3) |

---

## 3. Target architecture

```text
 GitHub
 ┌──────────────────────────────────────────────────────────────┐
 │ App repository (x6)                 CentralDevOps              │
 │  build.yml ──► GHCR digest          bootstrap/configure/       │
 │  deploy.yml (same repo)             verify-vps.yml             │
 │   ├ select Environment              deploy-app.yml (reusable)  │
 │   ├ standard GH auth (OIDC          Ansible roles              │
 │   │  validated in spike)            registry apps/*            │
 │   └ calls deploy-app.yml@<sha> ───► │                          │
 └──────────────────────────────────────────────────────────────┘
                     │ Actions runner, SSH (deploy-only key)
                     ▼
 VPS (per environment)
  Docker Engine / Compose
  Nginx ◄── DNS, public 80/443, Let's Encrypt HTTP-01
    │ edge network (all-in-one) or private IP:port (split proxy)
  App containers (policy-validated Compose)
    │ db network
  Shared PostgreSQL (per-app DB + role)
  Grafana Alloy ──► Grafana Cloud      Backups ──► off-host S3
```

### Responsibilities

| Component | Owns |
|---|---|
| App repo | Source, tests, Dockerfile, `compose.yml`, `deploy/<env>.yml` manifest, `build.yml`, `deploy.yml`, runtime secret mapping, app Environments |
| CentralDevOps | Ansible roles/inventories, infra workflows, `deploy-app.yml`, server-side deploy/route scripts, app registry, Nginx templates, Compose policy, TLS, backups, monitoring |
| CentralDevOps Environments | Infra workflow credentials, backup/monitoring credentials, registry pull token, **production approval gate for infra changes**. Deploy SSH key (and bundle key, if retained) placement follows the spike (§17 #1) |
| App Environments | App runtime secrets/variables, branch restriction, **production approval gate for app deployments** (§4.1) |
| GHCR | Images and digests |
| DNS (Masterweb) | Zone `*.masterweb.com`; A/AAAA managed manually/by provider tooling; HTTP-01 needs no DNS API token |
| Grafana Cloud | Dashboards, ingestion, alerts |
| Sumopod | VPS compute, disks, private network, firewall, console; S3 (separate product) for backups |

**Operations stay separate:** Provision → Bootstrap → Configure → Verify → Build → Deploy → Scale. Ansible never decides on its own that more capacity is needed.

---

## 4. GitHub Environments, naming and secrets

### 4.1 Environments

Exactly two per repo: **`Staging`** and **`Production`** (not one per VPS).

| Setting | CentralDevOps `Production` | App `Production` |
|---|---|---|
| Required reviewers | **Yes** for production infra changes | **Yes, the approval gate for production deployments** (deploy job runs in the app's Environment; confirm in spike §17 #1) |
| Deployment branches | `main` only | `main` (or release branches) only |
| Secrets | Infra credentials | App runtime secrets (and deploy credentials, per spike) |

**Approvers:** initially the repository owner; once assigned, the deployment team replaces or joins the owner.

### 4.2 Naming rules

1. `SCREAMING_SNAKE_CASE`.
2. Prefix shows ownership: `ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_`, `MONITORING_`.
3. **Same name in both environments;** the Environment supplies the value. Never `STAGING_…`/`PRODUCTION_…`.
4. Per-host facts (address, user, roles, ports) go in inventory/registry, not GitHub variables.
5. Credentials are secrets; ordinary config (paths, public keys, host key pins, domains) is variables or committed files.
6. No `GITHUB_` prefix; avoid generic names (`TOKEN`, `KEY`, `SERVER_IP`).
7. Org-level values are not environment-scoped: use only for credentials with identical scope in both environments, limited to selected repos.

### 4.3 CentralDevOps variables (use only those workflows consume)

| Level | Name | Example | Purpose |
|---|---|---|---|
| Repo | `ANSIBLE_CONFIG_PATH` | `ansible.cfg` | Ansible config |
| Repo | `ANSIBLE_REQUIREMENTS_PATH` | `requirements.yml` | Collections/roles |
| Repo | `ANSIBLE_PLAYBOOKS_PATH` | `playbooks` | Playbook dir |
| Env | `ANSIBLE_INVENTORY_PATH` | `inventories/<env>/hosts.yml` | Derived from the selected Environment, never typed |
| Env | `DEPLOY_HEALTHCHECK_TIMEOUT` | `90` | Default health wait |
| Env | `DEPLOY_REGISTRY_DIR` | `apps` | Registry root (`apps/<app>/<env>.yml`) |
| Env | `MONITORING_ENDPOINT` | provider URL | Non-secret endpoint |
| Env | `BACKUP_RETENTION_DAYS` | `14` | Retention |
| Env | `BACKUP_S3_ENDPOINT`, `BACKUP_S3_REGION`, `BACKUP_S3_BUCKET` | Sumopod S3 | Backup bucket details |

### 4.4 CentralDevOps secrets (Environment scope)

| Name | Used by | Notes |
|---|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY` | bootstrap/configure/verify | Admin key. **Never usable by `deploy-app.yml`** |
| `ANSIBLE_VAULT_PASSWORD` | infra workflows | Only if Ansible Vault is used |
| `DEPLOY_SSH_PRIVATE_KEY` | `deploy-app.yml` | Restricted deploy identity (§8.5); different key and VPS account from admin. Placement (CentralDevOps or app) per spike |
| `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | `deploy-app.yml` | Only if sealed bundle retained (§7.2) |
| `GHCR_PULL_TOKEN` | configure-vps | Read-only package token, installed by Ansible as a root-only file |
| `BACKUP_RESTIC_PASSWORD`, `BACKUP_S3_ACCESS_KEY_ID`, `BACKUP_S3_SECRET_ACCESS_KEY` | configure-vps | S3 keys for the Sumopod bucket; names illustrative; backup tool and key custody open (§17 #3) |
| `MONITORING_GRAFANA_CLOUD_TOKEN` | configure-vps | Collector credential |
| `VPS_PROVIDER_API_TOKEN` | not used | Sumopod has no API; provisioning is manual |

Host key pins are **public**: store in `inventories/<env>/known_hosts` (PR-reviewed), use strict host-key checking, never trust a fresh `ssh-keyscan` on the same connection.

### 4.5 App repositories

| Level | Name | Purpose |
|---|---|---|
| Env variable | `APP_*` | Non-secret config |
| Env secret | app-defined, e.g. `APP_AUTH_SECRET`, `APP_DB_PASSWORD` | Mapped into runtime env file (inside a sealed bundle only if retained, §7.2) |

The dispatch GitHub App (`DEPLOY_DISPATCH_APP_ID`, `DEPLOY_DISPATCH_APP_PRIVATE_KEY`) is **not needed in v4**. If dispatch returns, install a dispatch-only App on CentralDevOps with `actions: write`; residual risk is it can dispatch any CentralDevOps workflow, mitigated by rejecting its identity in infra workflows and by Production approval (§12).

---

## 5. Repository structures

### 5.1 CentralDevOps

```text
CentralDevOps/
├── ansible.cfg, requirements.yml
├── inventories/{staging,production}/
│   ├── hosts.yml, known_hosts
│   ├── group_vars/{all,app_nodes,proxy_nodes,database_nodes}.yml
│   └── host_vars/<host>.yml
├── apps/<app>/{staging,production}.yml     # registry: placement and policy
├── playbooks/{bootstrap,configure,verify,restore-database}.yml
├── roles/
│   ├── common users ssh_hardening firewall docker
│   ├── nginx certbot postgresql backup monitoring_agent
│   ├── deploy_runtime     # server-side scripts + sudoers + dirs
│   └── wireguard          # later, if no provider private networking
├── deployment/
│   ├── scripts: centraldevops-{deploy,route,compose-policy}
│   ├── nginx-templates/{http-only,https}.conf.j2
│   ├── keys/{staging,production}.age.pub   # only if sealed bundle retained
│   ├── schemas/{registry,app-manifest}.schema.json
│   └── tools/verify-oidc.py                # scope set by the spike
├── .github/
│   ├── CODEOWNERS         # apps/**, deployment/**, roles/**, workflows/** need review
│   ├── workflows/{bootstrap-vps,configure-vps,verify-vps,deploy-app}.yml  # deploy-app is workflow_call
│   └── actions/request-deploy/action.yml   # only if the spike shows it is needed
└── README.md
```

### 5.2 App repository

```text
customer-builder/
├── .github/workflows/{build.yml,deploy.yml}
├── Dockerfile, compose.yml
├── deploy/{staging.yml,production.yml}    # route manifest, no secrets
└── README.md
```

---

## 6. Infrastructure workflows (CentralDevOps)

On-demand, never part of an app deployment. Each declares `environment: ${{ inputs.target_environment }}` to pick up that Environment's inventory path and secrets.

### 6.1 `bootstrap-vps.yml`
Once per new VPS: connect with the provider's initial access, create admin and deploy accounts, install the admin public key, apply updates, base firewall, then SSH hardening **only after a second independent login succeeds**.

### 6.2 `configure-vps.yml`
Idempotently converges a host onto a profile.

| Input | Meaning |
|---|---|
| `target_environment` | `Staging` / `Production` |
| `profile` | `app`, `proxy`, `database`, `monitoring`, `all-in-one` |
| `limit` | Optional host/group, validated against the inventory |
| `check_mode` | `--check --diff` dry run |

| Profile | Roles |
|---|---|
| `app` | common, users, ssh_hardening, firewall, docker, deploy_runtime, monitoring_agent, backup (volumes) |
| `proxy` | baseline + nginx, certbot |
| `database` | baseline + postgresql, backup |
| `monitoring` | baseline + collector |
| `all-in-one` | app + proxy + database |

### 6.3 `verify-vps.yml`
Read-only PASS/FAIL for: SSH access and users, firewall, Docker/Compose, `edge` and `db` networks, Nginx config/service, certificate expiry, PostgreSQL and listen addresses, deploy scripts present/root-owned/checksum-matching, monitoring connectivity, disk/inodes, **newest backup age**, deploy-user sudoers. Accepts a host, group or whole environment.

### 6.4 Inventory

Separate inventory per environment; roles are groups; an all-in-one host is a member of several groups.

```yaml
# inventories/staging/hosts.yml (illustrative)
all:
  children:
    app_nodes:      { hosts: { stg-aio-01: {} } }
    proxy_nodes:    { hosts: { stg-aio-01: {} } }
    database_nodes: { hosts: { stg-aio-01: {} } }
  hosts:
    stg-aio-01:
      ansible_host: 203.0.113.10
      private_ip: 10.0.0.10          # used when roles split
```

Splitting later = adding hosts to groups and changing registry placement, not rewriting workflows.

---

## 7. Application workflows

### 7.1 `build.yml` (manual: source → GHCR)

Operator selects `source_ref`; the workflow checks out that exact ref, tests, builds, pushes, and records the **digest** in the summary and a metadata artifact (metadata only; the image is in GHCR).

- Convenience tag `sha-<full-commit>`; **deploy by digest only**.
- `actions/attest-build-provenance` (`id-token: write`, `attestations: write`). Registry flag `require_attestation` (§9.2) makes CentralDevOps run `gh attestation verify`. **Required for Production** (deployment fails on verification failure); optional for Staging.
- Set `org.opencontainers.image.source`.

Operator copies `image_ref` from the build summary into the deploy run.

### 7.2 `deploy.yml` (manual: request a deployment)

Inputs: `target_environment` (`Staging`/`Production`), `image_ref` (full `ghcr.io/…@sha256:…`).

Runs in the app repo and calls `deploy-app.yml` (pinned SHA). No dispatch, dispatch App or polling. Steps:

1. `permissions: contents: read, id-token: write`; the deploy job declares `environment: ${{ inputs.target_environment }}` (which repo's Environment/secrets a called workflow resolves is validated in the spike).
2. Reject malformed `image_ref` early (regex; `deploy-app.yml` re-validates against the registry).
3. Render the runtime env file from this environment's secrets/variables (same repo, no trust boundary crossed).
4. **Sealed bundle / request-bound OIDC audience (conditional):** v3 encrypted `runtime.env`, `compose.yml`, `deploy/<env>.yml` into an `age` bundle and bound the audience to `sha256(environment | image_ref | sealed_bundle)`. Keep only if the spike shows plaintext would cross a trust boundary or leak via artifacts. Either way, never pass runtime secrets as plaintext artifacts.
5. The result is the app's own Actions run, which is also the deployment history (§13.4). The workflow fails if deployment fails.

The app never learns the registry pull token; whether it also never holds the deploy SSH key depends on the spike. Mask tokens in logs.

If cross-repo dispatch is reintroduced (v3 mechanics): dispatch-only App, sealed bundle as base64 input (payload limit ~65 KB), poll the central run.

---

## 8. Central deployment pipeline (`deploy-app.yml`)

Reusable (`workflow_call`), called from the app's `deploy.yml`. **Do not build until the spike (§17 #1) confirms this design.**

### 8.1 Trust model

No dispatch token; identity comes from the run's OIDC claims. The spike validates audience and claim values (`repository`, `job_workflow_ref`, `environment` as seen through a reusable-workflow call). Intended checks (audience row applies only if the request carries data to bind, §7.2 step 4):

| Check | Source of truth |
|---|---|
| Signature, issuer, expiry | GitHub OIDC JWKS (`https://token.actions.githubusercontent.com`) |
| Audience = value fixed by the spike (v3: `centraldevops-deploy:` + recomputed `sha256(environment \| image_ref \| bundle)`) | Binds token to this exact request |
| `repository` claim | Maps to the app via registry. **App name is derived, never an input** |
| `job_workflow_ref` | `<repo>/.github/workflows/deploy.yml@refs/heads/<allowed ref>` |
| `ref` | In registry `allowed_refs` |
| `environment` claim | Equals `target_environment` |
| `run_id` + `run_attempt` | Single use, recorded in the server deployment record; replays rejected |
| `image_ref` | Matches `ghcr.io/<registry image repository>@sha256:<64 hex>` |
| Provenance (`require_attestation`) | `gh attestation verify` against app repo and workflow |

### 8.2 Job structure

1. **`authorize`**: no Environment, no secrets. Verifies OIDC and request binding (tokens expire fast, so no waiting behind approval), loads and schema-validates `apps/<app>/<env>.yml`, outputs the resolved plan.
2. **`deploy`**: `environment: ${{ inputs.target_environment }}` (resolved per spike; Production approval gate; `DEPLOY_*` secrets). Decrypts the bundle if used, validates manifest and Compose policy, deploys.

Concurrency: `group: deploy-<app>-<environment>`, `cancel-in-progress: false`. GitHub keeps one *pending* run per group, so this is a convenience only; **correctness comes from server-side locking** (§8.4). No single environment-wide group (a pending deploy could be cancelled with 6 apps).

### 8.3 Deploy job steps

1. Check out CentralDevOps at the same reviewed SHA the app pinned.
2. If a bundle is used, decrypt with `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` into a `umask 077` temp dir; `::add-mask::` every secret; never upload it.
3. **Validate the manifest** (schema; domain in registry `domains`; sane port and health path).
4. **Run Compose policy** on `docker compose config --format json` (§9.4).
5. Resolve registry inventory groups to hosts. In v3/v4 each placement group must resolve to **exactly one host** (running multiple apps within limits, §9.3); fail otherwise.
6. Verify the runtime env has exactly the manifest-declared keys, none reserved.
7. SSH with the **deploy identity**, pinned host keys, strict checking. Copy validated inputs to an incoming dir owned by the deploy user, then call the root-owned script via sudo (§8.5).
8. Server script: create/update DB and role if enabled (§11), pull the exact digest, back up previous release files, render `compose.env`, `docker compose up -d`, wait for container health.
9. On first deploy or route change, register the route (§10); HTTPS smoke test from the runner.
10. Write deployment record and run summary. GitHub Deployments integration is deferred; app Actions run history is the deployment history, with off-host backups (§13.2). Never print `.env` content.

### 8.4 Server-side locking and rollback

- `flock` per app/env for deploys; a separate `flock` for the proxy so two apps never edit/reload Nginx at once.
- Keep `previous/` (compose.env, compose.yml, image ref). On health failure: restore the previous release and **leave the route unchanged**. A failed first deployment is left stopped.
- Manual rollback: rerun `deploy.yml` with the previous digest. Migrations must be backward-compatible (§11.3); an old container cannot undo a schema change.

### 8.5 Deploy identity on the VPS

- Unprivileged account (e.g. `cdo-deploy`) with its own key `DEPLOY_SSH_PRIVATE_KEY`; **not in the `docker` group** (root-equivalent).
- `sudoers` allows only `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` with validated arguments. Scripts are root-owned, not deploy-user-writable, and re-validate every argument and file.
- GitHub-hosted runner IPs are unstable, so no `from=` in `authorized_keys`; use `restrict`, sudoers scoping and audit logs.
- SSH logging plus the deployment record give the audit trail.

---

## 9. Registry, manifest and Compose policy

Schemas/examples: `centraldevops-deployment-contract.md`.

### 9.1 Who decides what

| Concern | Decided by |
|---|---|
| Image repo, allowed refs, domains, placement, resource ceilings, DB, attestation | **Registry** `apps/<app>/<env>.yml` (CODEOWNERS-reviewed) |
| Wanted domain, container port, service name, health path, TLS, required runtime keys, optional release command | **App manifest** `deploy/<env>.yml` |
| Services, images, healthchecks, volumes | App `compose.yml` (subject to policy) |

The manifest may only request a domain the registry allocated to that app/env, preventing hostname claims or certificate issuance for arbitrary domains.

### 9.2 Registry file (summary)

```yaml
app: customer-builder
environment: staging
repository: example-org/customer-builder
image: ghcr.io/example-org/customer-builder
allowed_refs: [refs/heads/main]
require_attestation: false        # true for production
domains: [builder-staging.example.com]
placement: { app_group: app_nodes, proxy_group: proxy_nodes, database_group: database_nodes }
routing:
  upstream_mode: docker_edge      # docker_edge | private_ip
  host_port: 21001                # central, unique per host; for private_ip
limits: { memory: 512m, cpus: "0.50" }
database: { enabled: true, name: customer_builder_stg, user: customer_builder_stg }
```

### 9.3 Capacity control

A CI check sums `limits.memory` of all registry entries per placement host and fails the PR if the total exceeds the host budget declared in inventory (RAM minus reserve for OS, Docker, Nginx, PostgreSQL, collector). The app count per VPS is whatever fits the budget (Production 2 vCPU/4 GB/60 GB; Staging est. 1 vCPU/2 GB/20 GB, §2).

### 9.4 Compose policy (central, on rendered config)

The server runs the app's `compose.yml`, so it is privileged input. Reject:

- `privileged`, `cap_add`, `devices`, `pid`/`ipc`/`network_mode: host`, `userns_mode`, weakening `security_opt`
- bind mounts outside `/opt/apps/<app>/<env>/`; never the Docker socket
- published `ports` (central deployment adds a publish only for `private_ip`, bound to the private IP)
- networks other than the app default, `edge`, `db` (external)
- app-service image ≠ requested digest; other images not digest/version-pinned
- missing `healthcheck` on the routed service; missing/over-ceiling memory/CPU limits
- `env_file` other than `.env`

---

## 10. Routing and TLS

### 10.1 Placement contract

| `upstream_mode` | When | Nginx upstream |
|---|---|---|
| `docker_edge` | Proxy and app same host (initial) | `http://<edge_alias>:<container_port>` over Docker `edge` |
| `private_ip` | Proxy on another host | `http://<app private_ip>:<host_port>`; published only on private IP; firewall allows only the proxy host |

Docker networks are host-local. A split proxy needs private networking: Sumopod's private network (confirm it links separate VPSs) or WireGuard. Never expose backend ports publicly.

### 10.2 DNS

Create the A/AAAA record at Masterweb pointing to the proxy's public IP **before** the first deployment of a domain. Current TTL **14400 s (4 h)**; see §13.3. The deployment pre-checks resolution against the proxy IP and fails clearly instead of burning Let's Encrypt attempts.

### 10.3 Route activation (HTTP-01)

Runs inside the central deployment after the health check; idempotent (unchanged route = no rewrite/reload).

1. Validate domain ∈ registry; render `/opt/centraldevops/nginx/conf.d/<app>-<env>.conf` from the trusted template.
2. **New domain:** HTTP-only block (ACME challenge at `/.well-known/acme-challenge/` from a shared webroot) → `nginx -t` → reload.
3. Certbot webroot (HTTP-01). Use the Let's Encrypt staging endpoint when testing.
4. HTTPS block (80→443 redirect, modern TLS, HSTS after verification, forwarded headers, timeouts) → `nginx -t` → reload.
5. On `nginx -t` failure: restore the last good file, no reload, fail the deployment.
6. HTTPS smoke test from the runner.
7. Renewal via Certbot systemd timer with a deploy hook (`nginx -t` then reload). `verify-vps.yml` flags certificates expiring in <21 days.

HTTP-01 limits: no wildcards, port 80 reachable, one certificate per domain. Revisit if a CDN/proxy (e.g. Cloudflare) is added.

### 10.4 Separate proxy credential

With a separate proxy host, `centraldevops-route` runs there through the same restricted deploy identity (distinct `proxy_group` host). App and proxy hosts each get their own `authorized_keys`/sudoers from the `deploy_runtime` role.

---

## 11. Database

### 11.1 Model

One PostgreSQL per environment (`postgresql` role), **one database and login role per app**, no superuser use. Apps connect only over the `db` network (or a private IP once moved).

All-in-one host:

- Ansible creates Docker bridge `db` with a fixed subnet (e.g. `172.30.0.0/24`).
- PostgreSQL listens on `localhost` and the `db` gateway only; `pg_hba.conf` allows the `db` subnet with `scram-sha-256`; firewall allows 5432 only from it.
- The network must exist before PostgreSQL binds: systemd drop-in to start after `docker.service`; `verify-vps.yml` confirms the listener after reboot.
- App gets non-secret `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` from CentralDevOps and supplies `DB_PASSWORD` from its own secrets (in the bundle only if retained).
- Deployment idempotently creates DB/role from the registry and sets the password from app secrets. Rotation = change the secret and redeploy.

### 11.2 Migration path to per-app container

The `DB_*` contract is unchanged. Add a `db` service on a private network in the app's Compose, point `DB_HOST` at it, restore from backup, set `database.enabled: false`. Moving PostgreSQL to a separate VPS = change `DB_HOST` to its private IP and the registry `database_group`.

### 11.3 Migrations

Backward compatible with the previous release (expand/contract). **Apps own migrations:** via ORM (e.g. Prisma) or directly with a PostgreSQL GUI client. CentralDevOps does not run them; ORM apps may use the optional manifest `release_command` (one-off container with the new image **before** the replace, aborting on failure) or migrate at container start. PostgreSQL is never public (§12.1), so GUI access uses an SSH tunnel with the admin identity.

---

## 12. Security baseline and threat model

### 12.1 Host and Docker

- SSH key auth only; disable root/password login after validating the new path.
- Separate admin and deploy identities/keys; deploy user not in Docker group.
- Public ports: 80/443 only; SSH restricted by source IP/VPN where practical. Docker published ports bypass UFW; the Compose policy forbids them.
- PostgreSQL and app ports never public; Docker API never exposed.
- No secrets in image layers, build args, labels or committed Compose files.
- Automatic security updates; fail2ban or equivalent only after testing.
- Root-owned deploy scripts, checksum-verified by `verify-vps.yml`.

### 12.2 GitHub Actions

- Least-privilege `permissions`; app `deploy.yml` needs `contents: read`, `id-token: write`.
- Pin third-party actions and `request-deploy` to reviewed SHAs.
- Never interpolate untrusted input in shell; pass via `env:` and validate with strict regexes.
- Production Environments restricted to `main`, with reviewers where the deploy job runs (§4.1).
- CODEOWNERS on `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`; registry changes are security changes.
- If the dispatch App returns, infra workflows reject its `github.actor`.

### 12.3 Threats and mitigations

| Threat | Mitigation |
|---|---|
| Compromised app repo deploys another app's image/domain | App derived from OIDC `repository`; image must match registry repo; domain allow-list |
| Forged/replayed deploy request | OIDC claim verification (audience per spike); one-time `run_id`+`run_attempt`; short token life |
| Dispatch App key leaked | N/A in v4. If reintroduced: App only dispatches CentralDevOps workflows; deploys still need valid OIDC; infra workflows reject its identity; Production approval; rotate key |
| Malicious Compose file | Central policy on rendered config (§9.4) |
| Secret leakage in logs | `add-mask`, no `set -x`, no temp-dir artifact upload, short-lived temp files, no plaintext secrets in inputs/artifacts |
| Lost VPS | Rebuild from code + restore (§13.3) |
| Same-host blast radius (6 apps share Docker and PostgreSQL) | Per-app DB/role, resource ceilings, policy, non-root containers recommended; accepted at this scale |

---

## 13. Observability, backups, recovery

### 13.1 Monitoring

Grafana Cloud with Alloy (or similar) per VPS. Monitor CPU, RAM, disk/inodes, container restarts/health, Nginx errors, certificate expiry, PostgreSQL availability/connections, HTTP availability/latency/5xx per app, backup age. Alerts: disk pressure, restart loops, failed health, certificate expiry (<21 d), **newest good backup >8 h**, elevated 5xx. An external uptime probe is needed so alerts fire if the VPS is down; **host-down and backup-age alerts are mandatory** within the plan used.

Start on the free plan only if quotas cover expected usage: estimate ingestion before go-live, measure afterwards, watch quota, upgrade or cut log volume as needed.

### 13.2 Backups (RPO 12 h)

| Item | Frequency | Method | Destination |
|---|---|---|---|
| PostgreSQL | **Every 6 h** | `pg_dump` per DB + `pg_dumpall --globals`, encrypted | Sumopod S3 (§17 #2) |
| App volumes/uploads | Daily, or move uploads to object storage | restic or equivalent | Same bucket |
| Deployment records and config | After each deploy | copy | Same bucket |
| Whole-VPS snapshot | n/a | Sumopod has none | n/a |

One S3 bucket (endpoint, region, name, access key ID/secret from Sumopod). Backup tool and key custody remain open (§17 #3). Retention 14 days (`BACKUP_RETENTION_DAYS`) plus a few monthly copies; encrypted, access-controlled, monitored. With no snapshots, S3 backups plus code are the only recovery path. Keep uploads and durable files out of container writable layers.

### 13.3 Disaster recovery (RTO 4 h)

```text
Create new VPS (manual, Sumopod console; 15 min)
→ DNS update or reassign IP (15 min + TTL)
→ bootstrap-vps.yml + configure-vps.yml all-in-one (30 min)
→ restore PostgreSQL from latest dump (30–60 min)
→ redeploy each app at its last known digest (app Actions history / backup records) (6 × 5 min)
→ verify-vps.yml + smoke tests (15 min)
```

**DNS TTL:** A/AAAA TTL is 14400 s (4 h), equal to the whole RTO; a new IP may be cached up to 4 h. Either lower production TTLs beforehand (e.g. 300–600 s) or keep the recovery IP the same. This is a recommendation; TTL policy remains your decision.

`playbooks/restore-database.yml` and a written runbook are mandatory. **Run a timed restore drill on Staging before Production go-live and at least quarterly,** recording elapsed time against 4 h. Mind Let's Encrypt rate limits when reissuing many certificates after a rebuild.

### 13.4 Deployment record

On the host and mirrored off-host. GitHub Deployments mirroring is deferred; app Actions run history suffices for now.

```json
{"app":"customer-builder","environment":"Staging","image_ref":"ghcr.io/…@sha256:…",
 "previous_image_ref":"ghcr.io/…@sha256:…","git_commit":"…","source_run":"…",
 "central_run_url":"…","deployed_at_utc":"…","result":"success"}
```

---

## 14. Rollout strategy and scaling roadmap

### 14.1 Rollout

Now: Compose replace; seconds of interruption accepted. Later: **blue/green** for stateless containers (start inactive slot, health-check, switch a validated Nginx upstream, retire old slot); PostgreSQL stays outside slots. The registry/route contract already abstracts the upstream, so only the server script changes.

### 14.2 Scaling

1. **Now:** one all-in-one VPS per environment, ~4–6 small apps, limits and capacity check.
2. **Split stateful:** DB to own VPS or managed DB; private networking; object storage for uploads.
3. **Split proxy:** `proxy_nodes` host, `upstream_mode: private_ip`.
4. **Multiple app hosts:** placement becomes a set of hosts (relaxing "exactly one host"), load balancer, rolling deploy, stateless apps; OpenTofu/Terraform only if Sumopod gains an API.

Add each step only on a measurable need.

---

## 15. Operational runbooks

### 15.1 New VPS
Create at Sumopod → verify initial access → `bootstrap-vps.yml` → verify second login → `configure-vps.yml` → `verify-vps.yml` → deploy a non-critical test app → verify HTTPS, logs, alerts, backups → restore drill (Staging).

### 15.2 Onboard an application
1. CentralDevOps PR adding `apps/<app>/staging.yml` and `production.yml` (domain, ports, placement, limits, DB); capacity check must pass.
2. Create DNS records.
3. In the app repo: `build.yml`, `deploy.yml`, `compose.yml`, `deploy/<env>.yml`, both Environments (Production approval gate), secrets.
4. Run `build.yml`, deploy to Staging, verify, then Production.

### 15.3 Build and deploy

```text
build.yml (source_ref) → copy image_ref
→ deploy.yml (target_environment, image_ref), same repo
→ deploy-app.yml: authorize → (Production approval) → deploy
→ policy → copy → deploy → health → route → smoke → record
→ result = the app's own Actions run
```

### 15.4 Change VPS configuration
Review Ansible change → `configure-vps.yml` Staging (check mode first) → `verify-vps.yml` → same for Production (approval).

### 15.5 Rotate secrets
- Admin/deploy SSH keys: add new public key via configure, switch secret, remove old key, verify.
- Age key (only if bundle retained): add new public key to `deployment/keys/`, update `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`, bump pinned SHA in apps (two recipients during transition).
- GHCR pull token: rotate, rerun `configure-vps.yml`.
- Dispatch App key (only if reintroduced): generate new, update org secret, delete old.

### 15.6 Rollout fails
Route unchanged → read central and app run logs and container logs → rerun `deploy.yml` with the previous digest if needed → record the cause.

---

## 16. Implementation order

1. Foundation: structure, `ansible.cfg`, inventories, naming standard, CODEOWNERS, registry schema.
2. **Spike (§17 #1):** same-repo reusable workflow + OIDC audience/claims + Environment secret behavior on a throwaway app, before building the pipeline.
3. Host security roles; prove access survives hardening on a disposable VPS.
4. Docker role, `edge`/`db` networks, `deploy_runtime` role (scripts, sudoers).
5. `verify-vps.yml` early, extended per role.
6. Nginx + Certbot (HTTP-01): one route; failed `nginx -t` cannot break existing routes; renewal hook tested.
7. PostgreSQL role, per-app DB provisioning, systemd ordering test across reboot.
8. App `build.yml` with digest output and attestation.
9. `deploy-app.yml` (after the spike) and app `deploy.yml`; Staging, then Production behind approval.
10. Backups, off-host storage, restore drill, monitoring/alerts. **Not production-ready until the timed restore passes.**
11. Capacity-check CI; onboard apps 2–6.
12. Scale preparation (split proxy/DB, blue/green) only when needed.

---

## 17. Open items, assumptions and verification spikes

| # | Item | Why it matters | Status |
|---|---|---|---|
| 1 | **Same-repo workflow spike:** validate OIDC audience and claims (`repository`, `job_workflow_ref`, `environment`) for a reusable-workflow call; which repo's Environment/secrets a called workflow sees and where `DEPLOY_SSH_PRIVATE_KEY` can safely live; whether an age bundle is still needed | Deployment model depends on it | **Open. Required before building `deploy-app.yml`** |
| 2 | **Sumopod capabilities:** private network, firewall, console; no snapshots, no API; S3 is separate (endpoint, region, bucket, access key ID, secret) | Backup destination, split hosts, provisioning | **Resolved.** IPv6, static/reserved IP, outbound restrictions unconfirmed |
| 3 | Backup destination, tool, key custody | RPO and recovery | **Destination resolved** (S3 from #2). **Tool and key custody open** |
| 4 | Migration strategy | Deploy safety | **Resolved:** app-owned, ORM (e.g. Prisma) or PostgreSQL GUI (§11.3) |
| 5 | `require_attestation` for Production | Supply chain | **Resolved:** required for Production, optional for Staging |
| 6 | Production approval | Friction vs control | **Resolved:** approval-gated; owner first, team later (§4.1) |
| 7 | Staging and Production on separate VPSs | Cost, isolation | **Confirmed** |
| 8 | VPS sizing | Registry ceiling | **Resolved:** Prod 2 vCPU/4 GB/60 GB; Staging est. 1 vCPU/2 GB/20 GB; multiple apps, count not fixed (§2, §9.3) |
| 9 | DNS provider, DR TTL | DR timing | **Resolved:** Masterweb, domains at exabytes.co.id, TTL 14400 s (§13.3) |
| 10 | Grafana Cloud limits | Alerting, log volume | **Resolved:** free plan if quotas suffice; measure, upgrade or reduce; host-down and backup-age alerts required (§13.1) |
| 11 | GitHub plan stays paid for private repos | Environments depend on it | Assumption (unchanged) |
| 12 | GitHub Deployments integration | Deployment history | **Deferred:** app Actions run history for now |

---

## References

- [GitHub — Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub — Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [GitHub — OpenID Connect in Actions](https://docs.github.com/en/actions/concepts/security/openid-connect)
- [GitHub — Manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [GitHub — Artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub — Working with the container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Ansible — Inventory](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
- [Docker — Compose in production](https://docs.docker.com/compose/how-tos/production/)
- [Docker — Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Let's Encrypt — Rate limits](https://letsencrypt.org/docs/rate-limits/)
- [Certbot documentation](https://eff-certbot.readthedocs.io/)
- [age encryption](https://github.com/FiloSottile/age)
