# CentralDevOps — VPS Infrastructure and Deployment Design (v4.2, compressed)

**Status:** Compressed v4: same decisions, restated rules merged, section numbers preserved. `deploy-app.yml` is not built until spike §17 #1 passes.
**Supersedes** v4 and v4.1 for reading; v4 remains the full text.
**Companions (still v3, not updated for v4):** `centraldevops-deployment-contract.md` (schemas, workflow skeletons, script contracts), `centraldevops-decision-log.md`.

| Item | Decision |
|---|---|
| Runtime | Docker Compose; one all-in-one Ubuntu VPS per environment initially |
| VPS provider | Sumopod: own private network, firewall, console; no snapshots, no API. S3 storage is a separate product (§17) |
| Scale | Up to **6 apps** in 6 months |
| Recovery | **RTO 4 h, RPO 12 h** |
| Infra automation | GitHub Actions + Ansible from CentralDevOps |
| App deployment | **Same-repo workflow** in the app repo, standard GitHub Actions auth; no cross-repo dispatch now. Confirmed by spike §17 #1 first |
| Registry | GHCR, deploy by immutable digest |
| Routing / TLS | Nginx; DNS at Masterweb (domains at exabytes.co.id); Let's Encrypt **HTTP-01** |
| Database | One shared PostgreSQL per environment, per-app DB and role; per-app container path documented |
| Rollout | Compose replace; blue/green later |
| Monitoring | Grafana Cloud, collector per VPS |

---

## 1. Executive decisions

1. Each app repo has two manual workflows, `build.yml` and `deploy.yml`; build and deploy stay separate.
2. **The immutable GHCR digest is the release identity.** Deploy `ghcr.io/OWNER/IMAGE@sha256:…`, never a mutable tag.
3. **Same-repo deployment (v4):** the app's `deploy.yml` calls CentralDevOps `deploy-app.yml` (reusable, pinned to a reviewed commit SHA). No cross-repo dispatch or dispatch GitHub App.
4. **Standard GitHub Actions auth** (`GITHUB_TOKEN`, OIDC where appropriate); no shared secret or PAT. The spike validates OIDC audience and claims first (§8).
5. **App runtime secrets stay app-owned** (app's Environment), encrypted at rest and in transit, never plaintext in artifacts. The spike decides whether a sealed age bundle is still needed; add no bundle transfer unless a trust boundary is crossed.
6. **The registry (`apps/<app>/<env>.yml`) decides placement, allowed domains and resource ceilings.** The app manifest declares only the requested route (domain, port, service, health path). No per-VPS GitHub variables.
7. **Two Environments, `Staging` and `Production`, per repo, with identical variable/secret names;** values differ. Prefixes (`ANSIBLE_`, `DEPLOY_`, `GHCR_`, …) show ownership; per-host data lives in inventory.
8. **`bootstrap-vps.yml`, `configure-vps.yml`, `verify-vps.yml` stay separate** and never run as part of an app deployment.
9. **Design for separate proxy (later DB and app) hosts from day one;** placement is registry/inventory data, not workflow logic.
10. **No Kubernetes or Swarm initially.** First make apps stateless, deployments repeatable, recovery rehearsed.

### Correction to v2

v2 claimed a CentralDevOps reusable workflow "would use CentralDevOps' environment secrets." A called reusable workflow actually runs in the **caller's** repo context, so `environment:` resolves there and cannot give app repos access to CentralDevOps-held server credentials. Truly centralized execution needs a workflow **running in CentralDevOps** via cross-repo `workflow_dispatch` (the v3 model). **v4:** dispatch is not needed now, so a same-repo workflow is used. The spike (§17 #1) must first validate OIDC audience/claims and Environment-secret behavior, settle where the deploy SSH key lives, and confirm server credentials stay out of reach of app code.

---

## 2. Requirements and capacity targets

| Requirement | Design consequence |
|---|---|
| Up to 6 apps | One VPS per environment needs **mandatory per-app memory/CPU limits** and a registry capacity check (§9.3). Revisit sizing at 4 apps. |
| RTO 4 h | Rebuild from code: bootstrap → configure → redeploy recorded digests → restore DB. Timed restore drill required (§13.3). |
| RPO 12 h | DB dumps at least every **6 h**, off-host to S3 (§13.2). Alert when newest good backup is older than **8 h**. |
| Brief deploy interruption OK | Plain `docker compose up -d`; blue/green deferred (§14). |
| Staging and Production | **Separate VPS instances** (confirmed); never share a host. |
| Sizing | Production **2 vCPU, 4 GB RAM, 60 GB SSD**; Staging (estimate) 1 vCPU, 2 GB, 20 GB. Each VPS hosts **multiple apps**, count not fixed, bounded by per-app limits and capacity check (§9.3). |

---

## 3. Target architecture

Flow: app `build.yml` → GHCR digest → app `deploy.yml` (same repo, standard Actions auth) → CentralDevOps `deploy-app.yml@<sha>` (registry `apps/*`, Ansible roles, infra workflows) → runner SSHes (deploy-only key) to the VPS.

Per-environment VPS: Docker/Compose; Nginx (public 80/443, HTTP-01) → `edge` network (all-in-one) or private IP:port (split proxy) → policy-validated app containers → `db` network → shared PostgreSQL (per-app DB + role); Grafana Alloy → Grafana Cloud; backups → off-host storage.

| Component | Owns |
|---|---|
| App repo | Source, tests, Dockerfile, `compose.yml`, `deploy/<env>.yml` route manifest, `build.yml`, `deploy.yml`, runtime secret mapping, app Environments |
| CentralDevOps | Ansible roles/inventories, three infra workflows, `deploy-app.yml`, server-side deploy/route scripts, registry, Nginx templates, Compose policy, TLS, backups, monitoring |
| CentralDevOps Environments | Infra, backup and monitoring credentials, registry pull token, **production approval gate for infra changes**; deploy SSH key (and sealed-bundle key, if retained) placement per spike |
| App Environments | App runtime secrets/variables, branch restriction, **production approval gate for app deployments** (§4.1) |
| GHCR | Images, digests |
| DNS (Masterweb) | Zone at `*.masterweb.com`; A/AAAA managed manually or by provider tooling; HTTP-01 needs no DNS API token |
| Grafana Cloud | Dashboards, ingestion, alerts |
| Sumopod | VPS compute, disks, private network, firewall, console; S3-compatible storage (separate product) holds backups |

Operations stay separate: Provision → Bootstrap → Configure → Verify → Build → Deploy → Scale. Ansible never decides on its own that more capacity is needed.

---

## 4. GitHub Environments, naming and secrets

### 4.1 Environments

Exactly **`Staging`** and **`Production`** in both repo kinds; never one per VPS.

| Setting | CentralDevOps `Production` | App `Production` |
|---|---|---|
| Required reviewers | **Yes** for production infra changes | **Yes: the production deployment approval gate**, since the deploy job runs in the app's Environment (confirm in spike) |
| Deployment branches | `main` only | `main` (or release branches) only |
| Secrets | Infra credentials | App runtime secrets (+ deploy credentials, per spike) |

**Approvers:** production deployments must be approval-gated. The repo owner is the initial approver; once the deployment team is assigned, make the team the approver, or add it alongside the owner if both approvals are required.

### 4.2 Naming rules

1. `SCREAMING_SNAKE_CASE`, with ownership prefix `ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_`, `MONITORING_`.
2. **Same name in both environments; the environment supplies the value.** Never `STAGING_…`/`PRODUCTION_…`.
3. Per-host facts (address, user, roles, ports) belong in inventory or the registry, never GitHub variables.
4. Credentials are secrets; ordinary config (paths, public keys, host key pins, domains) is variables or committed files.
5. No `GITHUB_` prefix; avoid generic names (`TOKEN`, `KEY`, `SERVER_IP`).
6. **Org-level values are not environment-scoped:** use only for credentials with identical scope in both environments, restricted to selected repos.

### 4.3 CentralDevOps variables (define only those workflows consume)

| Level | Name | Example / purpose |
|---|---|---|
| Repository | `ANSIBLE_CONFIG_PATH` | `ansible.cfg` |
| Repository | `ANSIBLE_REQUIREMENTS_PATH` | `requirements.yml` |
| Repository | `ANSIBLE_PLAYBOOKS_PATH` | `playbooks` |
| Environment | `ANSIBLE_INVENTORY_PATH` | `inventories/<staging\|production>/hosts.yml`; derived from the selected Environment, never typed by hand |
| Environment | `DEPLOY_HEALTHCHECK_TIMEOUT` | `90`; default health wait |
| Environment | `DEPLOY_REGISTRY_DIR` | `apps`; registry root (`apps/<app>/<env>.yml`) |
| Environment | `MONITORING_ENDPOINT` | provider URL |
| Environment | `BACKUP_RETENTION_DAYS` | `14` |
| Environment | `BACKUP_S3_ENDPOINT`, `BACKUP_S3_REGION`, `BACKUP_S3_BUCKET` | Sumopod S3 bucket details (non-secret) |

### 4.4 CentralDevOps secrets (Environment scope)

| Name | Used by | Notes |
|---|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY` | bootstrap/configure/verify | Admin key. **Never usable by `deploy-app.yml`** |
| `ANSIBLE_VAULT_PASSWORD` | infra workflows | Only if Ansible Vault is used |
| `DEPLOY_SSH_PRIVATE_KEY` | `deploy-app.yml` | Restricted deploy identity (§8.5); different key and VPS account from admin. Placement (CentralDevOps or app) per spike |
| `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | `deploy-app.yml` | Only if sealed bundle retained (§7.2); exists only after Environment approval |
| `GHCR_PULL_TOKEN` | configure-vps | Read-only package token installed by Ansible (root-only file) |
| `BACKUP_RESTIC_PASSWORD`, `BACKUP_S3_ACCESS_KEY_ID`, `BACKUP_S3_SECRET_ACCESS_KEY` | configure-vps | S3 key ID/secret are for the Sumopod bucket; other names illustrative; tool and key custody open (§17 #3) |
| `MONITORING_GRAFANA_CLOUD_TOKEN` | configure-vps | Collector credential |
| `VPS_PROVIDER_API_TOKEN` | not used | Sumopod has no API; provisioning is manual |

Host key pins are **public**: store in `inventories/<env>/known_hosts` (PR-reviewed), use strict host-key checking, never trust a fresh `ssh-keyscan` from the same connection.

### 4.5 App repositories

- Environment variables `APP_*`: non-secret config.
- Environment secrets, app-defined (e.g. `APP_AUTH_SECRET`, `APP_DB_PASSWORD`): mapped into the runtime env file (inside a sealed bundle only if retained, §7.2).

**If cross-repo dispatch returns** (v3 mechanics; not needed in v4): dispatch-only GitHub App on CentralDevOps (`DEPLOY_DISPATCH_APP_ID`, `DEPLOY_DISPATCH_APP_PRIVATE_KEY`, `actions: write`); sealed bundle sent as a base64 input (payload limit ~65 KB); poll the central run. Residual risk: the App can technically dispatch *any* CentralDevOps workflow. Mitigate by infra workflows rejecting `github.actor` equal to the App identity, Production approval, valid OIDC proof still required for deploys, and App key rotation (new key → update org secret → delete old).

---

## 5. Repository structures

### 5.1 CentralDevOps

- `ansible.cfg`, `requirements.yml`, `README.md`
- `inventories/{staging,production}/`: `hosts.yml`, `known_hosts`, `group_vars/{all,app_nodes,proxy_nodes,database_nodes}.yml`, `host_vars/<host>.yml` (e.g. `stg-aio-01`)
- `apps/<app>/{staging,production}.yml`: registry (reviewed placement and policy)
- `playbooks/`: `bootstrap.yml`, `configure.yml`, `verify.yml`, `restore-database.yml` (drill and DR)
- `roles/`: `common users ssh_hardening firewall docker nginx certbot postgresql backup monitoring_agent`; `deploy_runtime` (server-side scripts, sudoers, dirs); `wireguard` (later, if provider lacks private networking)
- `deployment/scripts/` (installed to `/usr/local/sbin` by `deploy_runtime`): `centraldevops-deploy`, `centraldevops-route`, `centraldevops-compose-policy`
- `deployment/nginx-templates/{http-only,https}.conf.j2`, `deployment/schemas/{registry,app-manifest}.schema.json`, `deployment/tools/verify-oidc.py` (scope set by spike), `deployment/keys/{staging,production}.age.pub` (only if sealed bundle retained)
- `.github/CODEOWNERS` (`apps/**`, `deployment/**`, `roles/**` need review); `.github/workflows/{bootstrap-vps,configure-vps,verify-vps,deploy-app}.yml` (`deploy-app.yml` is `workflow_call`); `.github/actions/request-deploy/action.yml` (only if the spike shows it is still needed)

### 5.2 App repository

`.github/workflows/{build.yml,deploy.yml}`, `Dockerfile`, `compose.yml`, `deploy/{staging,production}.yml` (route manifest, no secrets), `README.md`.

---

## 6. Infrastructure workflows (CentralDevOps)

On demand, never part of an app deployment. Each declares `environment: ${{ inputs.target_environment }}` to get that Environment's inventory path and secrets.

- **`bootstrap-vps.yml`:** once per new VPS. Connect with the provider's initial access, create named admin and deploy accounts, install the admin public key, apply updates, base firewall, then SSH hardening **only after a second, independent login succeeds**.
- **`configure-vps.yml`:** idempotently converges a host onto a profile. Inputs: `target_environment` (`Staging`/`Production`), `profile` (`app`, `proxy`, `database`, `monitoring`, `all-in-one`), `limit` (optional host/group, validated against the selected inventory), `check_mode` (`--check --diff`).
- **`verify-vps.yml`:** read-only PASS/FAIL for a host, group or whole environment: SSH access and users, firewall, Docker/Compose, `edge` and `db` networks, Nginx config/service, certificate expiry, PostgreSQL and listen addresses, deploy scripts present/root-owned/unmodified (checksum vs repo), monitoring connectivity, disk/inodes, **newest backup age**, deploy-user sudoers entry.

| Profile | Roles |
|---|---|
| `app` | common, users, ssh_hardening, firewall, docker, deploy_runtime, monitoring_agent, backup (volumes) |
| `proxy` | baseline + nginx, certbot |
| `database` | baseline + postgresql, backup |
| `monitoring` | baseline + collector |
| `all-in-one` | app + proxy + database |

### Inventory

Separate per environment; roles are groups; an all-in-one host belongs to several. Splitting later means adding hosts to groups and changing registry placement, not rewriting workflows.

```yaml
# inventories/staging/hosts.yml  (addresses illustrative)
all:
  children:
    app_nodes:      { hosts: { stg-aio-01: {} } }
    proxy_nodes:    { hosts: { stg-aio-01: {} } }
    database_nodes: { hosts: { stg-aio-01: {} } }
  hosts:
    stg-aio-01:
      ansible_host: 203.0.113.10
      private_ip: 10.0.0.10          # used when roles split across hosts
```

---

## 7. Application workflows

### 7.1 `build.yml` (manual: source → GHCR)

Operator selects `source_ref`; the workflow checks out that exact ref, tests, builds, pushes, and records the **digest** in the summary and a metadata artifact (image in GHCR; artifact is metadata only). Also:

- Add an explicit `sha-<full-commit>` tag for convenience; **deploy by digest only**.
- Add `actions/attest-build-provenance` (`id-token: write`, `attestations: write`) linking the digest verifiably to repo, workflow and commit. Registry flag `require_attestation` (§9.2) makes CentralDevOps run `gh attestation verify`. **Required for Production** (deployment fails on verification failure); optional for Staging.
- Set `org.opencontainers.image.source`.

Operator copies `image_ref` from the build summary into the deploy run.

### 7.2 `deploy.yml` (manual)

Inputs: `target_environment` (choice `Staging`, `Production`), `image_ref` (full `ghcr.io/…@sha256:…`).

The job runs in the app repo and calls `deploy-app.yml` (pinned reviewed SHA) with standard auth. No dispatch, dispatch App or polling. It:

1. Sets `permissions: contents: read, id-token: write` and `environment: ${{ inputs.target_environment }}`; which repo's Environment/secrets a called reusable workflow resolves is validated in the spike.
2. Rejects a malformed `image_ref` early (regex; `deploy-app.yml` re-validates against the registry).
3. Renders the runtime env file from this environment's secrets/variables (same repo, no trust boundary crossed).
4. **Sealed bundle and request-bound OIDC audience (conditional):** v3 encrypted `runtime.env`, `compose.yml`, `deploy/<env>.yml` into an `age` bundle and bound the OIDC audience to `sha256(environment | image_ref | sealed_bundle)`. Keep only if the spike shows plaintext would otherwise cross a trust boundary or leak via artifacts. Either way, runtime secrets are never plaintext in artifacts.
5. The result is the app's own Actions run status, which doubles as deployment history (§13.4); the workflow fails if the deployment fails.

The app never learns the registry pull token; whether it also never holds the deploy SSH key depends on the spike. Mask any token in logs.

---

## 8. Central deployment pipeline (`deploy-app.yml`)

Reusable (`workflow_call`), called from the app's `deploy.yml`. **Not built until spike §17 #1 confirms this design.**

### 8.1 Trust model

No dispatch token; identity is the run's OIDC claims. The spike validates audience and claim values, including how `repository`, `job_workflow_ref` and `environment` appear in a reusable-workflow call. Intended checks (the audience row applies only if the request carries data to bind, §7.2 step 4):

| Check | Source of truth |
|---|---|
| Token signature, issuer, expiry | GitHub OIDC JWKS (`https://token.actions.githubusercontent.com`) |
| Audience equals the spike-fixed value (v3: `centraldevops-deploy:` + recomputed `sha256(environment \| image_ref \| bundle)`) | Binds token to this exact request; forged/altered input fails |
| `repository` claim | Maps to the app via registry. **App name is derived, never an input** |
| `job_workflow_ref` | Must be `<repo>/.github/workflows/deploy.yml@refs/heads/<allowed ref>` |
| `ref` | In registry `allowed_refs` (e.g. `refs/heads/main`) |
| `environment` claim | Equals `target_environment` |
| `run_id` + `run_attempt` | Single use: recorded in the server deployment record; replays rejected |
| `image_ref` | Matches `ghcr.io/<registry image repository>@sha256:<64 hex>` |
| Provenance (when `require_attestation`) | `gh attestation verify` against app repo and workflow |

### 8.2 Jobs

1. **`authorize`:** no Environment, no secrets. Verifies OIDC token and request binding (tokens expire quickly, so must not wait behind an approval), loads and schema-validates `apps/<app>/<env>.yml`, outputs the resolved plan.
2. **`deploy`:** `environment: ${{ inputs.target_environment }}` (resolved per spike → Production approval gate, `DEPLOY_*` secrets). Decrypts the bundle if used, validates manifest and Compose policy, deploys.

Concurrency: `group: deploy-<app>-<environment>`, `cancel-in-progress: false`. GitHub keeps at most one *pending* run per group and cancels older pending ones, so this is only a convenience; **correctness comes from server-side locking** (§8.4). Never use one environment-wide group (a pending deployment could be silently cancelled).

### 8.3 Deploy job steps

1. Check out CentralDevOps at the same reviewed SHA the app pinned.
2. If a bundle is used, decrypt with `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` into a `umask 077` temp dir; `::add-mask::` every secret value; never upload that dir.
3. **Validate the manifest:** schema; domain in registry `domains` allow-list; sane port and health path.
4. **Run the Compose policy** on `docker compose config --format json` (§9.4).
5. Resolve registry groups to hosts. In v3 each placement group must resolve to **exactly one host** (fail otherwise); that host runs multiple apps within per-app limits and capacity check (§9.3).
6. Verify the runtime env has exactly the manifest-declared keys and no reserved ones.
7. SSH with the **deploy identity**, pinned host keys, strict checking. Copy validated inputs to an incoming dir owned by the deploy user, then call the root-owned script via sudo (§8.5).
8. Server script: create/update DB and role if enabled (§11), pull the exact digest, back up previous release files, render `compose.env`, `docker compose up -d`, wait for container health.
9. On first deploy or route change, run route registration (§10); HTTPS smoke test from the runner.
10. Write the deployment record and run summary. GitHub Deployments integration is deferred; each app's Actions run history is the deployment history, and off-host backups (§13.2) allow recovery. Never print `.env` content.

### 8.4 Server-side locking and rollback

- `flock` per app/env for deploys, plus a separate `flock` for the proxy so two apps never edit/reload Nginx simultaneously.
- Keep `previous/` (compose.env, compose.yml, image ref). On health failure: restore the previous release and **do not change the route**; a first deployment simply fails and is left stopped.
- Manual rollback: rerun `deploy.yml` with the previous known-good digest. Migrations must be backward-compatible (§11.3); an old container cannot undo a schema change.

### 8.5 Deploy identity on the VPS

- Separate unprivileged account (e.g. `cdo-deploy`) with its own key `DEPLOY_SSH_PRIVATE_KEY`. **Not in the `docker` group** (root-equivalent).
- `sudoers` allows only `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` with validated arguments. Scripts are root-owned, not deploy-user-writable, and re-validate every argument and file.
- GitHub-hosted runner IPs are unstable, so no `from=` in `authorized_keys`; use key restriction options (`restrict`), sudoers scoping and audit logs.
- SSH logging plus the deployment record form the audit trail.

---

## 9. Registry, manifest and Compose policy

Schemas and examples: `centraldevops-deployment-contract.md`.

### 9.1 Who decides what

| Concern | Decided by |
|---|---|
| Image repository, allowed refs, domains, placement, resource ceilings, DB, attestation | **Registry** `apps/<app>/<env>.yml` (CODEOWNERS-reviewed) |
| Requested domain, container port, service name, health path, TLS, required runtime keys, optional release command | **App manifest** `deploy/<env>.yml` |
| Services, images, healthchecks, volumes | App `compose.yml` (subject to policy) |

The manifest may only request a domain the registry allocated to that app/environment, preventing hostname claims or certificate issuance for arbitrary domains.

### 9.2 Registry file (summary)

```yaml
app: customer-builder
environment: staging
repository: example-org/customer-builder
image: ghcr.io/example-org/customer-builder
allowed_refs: [refs/heads/main]
require_attestation: false        # staging; true for production
domains: [builder-staging.example.com]
placement:
  app_group: app_nodes
  proxy_group: proxy_nodes
  database_group: database_nodes
routing:
  upstream_mode: docker_edge      # docker_edge | private_ip
  host_port: 21001                # allocated centrally, unique per host; used for private_ip
limits: { memory: 512m, cpus: "0.50" }
database: { enabled: true, name: customer_builder_stg, user: customer_builder_stg }
```

### 9.3 Capacity control

A CentralDevOps CI check sums `limits.memory` of all registry entries per placement host and fails the PR if the total exceeds the host budget declared in inventory (physical RAM minus reserve for OS, Docker, Nginx, PostgreSQL, collector). "Will app #6 fit" becomes a reviewed decision. Declare the per-host budget in inventory (§2 sizes).

### 9.4 Compose policy (enforced centrally on rendered config)

The server executes the app's `compose.yml`, so it is privileged input. Reject:

- `privileged`, `cap_add`, `devices`, `pid`/`ipc`/`network_mode: host`, `userns_mode`, weakening `security_opt`
- bind mounts outside `/opt/apps/<app>/<env>/` (never the Docker socket)
- published `ports` (only central deployment adds a publish when `upstream_mode: private_ip`, bound to the private IP)
- networks other than the app's default, `edge` and `db` (external)
- app-service image not equal to the requested digest; other images must be digest- or version-pinned
- routed service without `healthcheck`, or missing/over-ceiling memory and CPU limits
- `env_file` other than `.env`

---

## 10. Routing and TLS

### 10.1 Placement contract

| `upstream_mode` | When | Nginx upstream |
|---|---|---|
| `docker_edge` | Proxy and app on same host (initial) | `http://<edge_alias>:<container_port>` over Docker `edge` network |
| `private_ip` | Proxy on another host | `http://<app private_ip>:<host_port>`; app publishes only on its private IP; firewall allows only the proxy host |

Docker networks are host-local. A split proxy needs private networking: Sumopod's private network (confirm it connects separate VPS instances), else WireGuard (`wireguard` role). Never expose backend ports publicly to bridge hosts.

### 10.2 DNS

Create the A/AAAA record at Masterweb pointing to the proxy's public IP **before** a domain's first deployment. Current TTL is **14400 s (4 h)** (recovery effect: §13.3). The deployment pre-checks resolution against the proxy IP and fails clearly rather than burning Let's Encrypt validation attempts.

### 10.3 Route activation (HTTP-01)

Runs in central deployment after the health check; idempotent (unchanged route = no rewrite, no reload).

1. Validate domain ∈ registry allow-list; render `/opt/centraldevops/nginx/conf.d/<app>-<env>.conf` from the trusted template.
2. **New domain:** render the HTTP-only block (ACME challenge at `/.well-known/acme-challenge/` from a shared webroot) → `nginx -t` → reload.
3. Obtain the certificate with Certbot webroot mode. Let's Encrypt limits failed validations (the DNS pre-check protects against this); use its staging endpoint when testing.
4. Render the HTTPS block (redirect 80→443, modern TLS, HSTS after verification, forwarded headers, timeouts) → `nginx -t` → reload.
5. On `nginx -t` failure: restore the last known-good file, do not reload, fail the deployment.
6. HTTPS smoke test from the runner.
7. Renewal by Certbot systemd timer with a deploy hook running `nginx -t` then reload. `verify-vps.yml` flags certificates expiring in under 21 days.

HTTP-01 limits: no wildcard certificates, port 80 internet-reachable, one certificate per domain. Revisit the method if a CDN/proxy such as Cloudflare is added.

### 10.4 Separate proxy credential

With a separate proxy host, `centraldevops-route` runs on the proxy via the same restricted deploy identity (distinct `proxy_group` host). App and proxy hosts each get their own `authorized_keys`/sudoers via `deploy_runtime`.

---

## 11. Database

### 11.1 Model

One PostgreSQL per environment (`postgresql` role), **one database and login role per app**; no app uses the superuser. Apps connect only over the `db` Docker network (or private IP once the DB moves).

All-in-one network design:

- Ansible creates a Docker bridge network `db` with a fixed subnet (e.g. `172.30.0.0/24`).
- PostgreSQL listens on `localhost` and the `db` gateway address only; `pg_hba.conf` permits the `db` subnet with `scram-sha-256`; firewall allows 5432 only from that subnet.
- The network must exist before PostgreSQL binds to its gateway: add a systemd drop-in so PostgreSQL starts after `docker.service`; `verify-vps.yml` confirms the listener after reboot.
- The app gets non-secret `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` from CentralDevOps and supplies `DB_PASSWORD` from its own secrets (sealed bundle only if retained, §7.2).
- Central deployment idempotently creates the DB/role from the registry entry and sets the password from the app's runtime secrets. Rotation = change the app secret and redeploy.

### 11.2 Migration path to per-app container

The `DB_*` contract is unchanged. Per-app container: add a `db` service on a private network to its Compose file, point `DB_HOST` at it, restore its database from backup, set `database.enabled: false` in the registry. Separate DB VPS: change `DB_HOST` to the database host's private IP and the registry `database_group`.

### 11.3 Migrations

Must be backward compatible with the previous release (expand/contract) and are **owned by each app**: via its ORM (e.g. Prisma) or applied directly with a PostgreSQL GUI client. CentralDevOps does not run migrations; an ORM app may use the optional manifest `release_command` (one-off container run with the new image **before** the replace; failure aborts the deployment) or migrate at container start. PostgreSQL is never public (§12.1), so GUI access uses an SSH tunnel with the admin identity.

---

## 12. Security baseline and threat model

### 12.1 Host and Docker

- SSH key auth only; disable root and password login after validating the new path. Separate admin and deploy identities/keys; deploy user not in the Docker group.
- Public ports: 80 and 443 only; SSH restricted by source IP/VPN where practical. Docker published ports can bypass UFW, so the Compose policy forbids them.
- PostgreSQL and app ports never public; Docker API never exposed.
- No secrets in image layers, build args, labels or committed Compose files.
- Automatic security updates; fail2ban or equivalent only after testing.
- Root-owned deploy scripts, checksum-verified by `verify-vps.yml`.

### 12.2 GitHub Actions

- Least-privilege `permissions`; app `deploy.yml` needs only `contents: read` and `id-token: write`.
- Pin third-party actions and the `request-deploy` action to reviewed commit SHAs.
- Never interpolate untrusted input in shell; pass via `env:` and validate with strict regexes.
- Restrict Production Environments to `main`; reviewers on the Production Environment where the deploy job runs (§4.1).
- CODEOWNERS on `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`; registry changes are security changes.

### 12.3 Threats and mitigations

- **Compromised app repo deploys another app's image or domain:** app derived from OIDC `repository`; image must match registry repository; domain allow-list.
- **Forged or replayed request:** OIDC claim verification (audience per spike); one-time `run_id`+`run_attempt`; short token lifetime.
- **Malicious Compose file:** central policy (§9.4). **Secret leakage in logs:** `add-mask`, no `set -x`, no temp-dir artifact upload, short-lived temp files, no plaintext secrets in inputs/artifacts.
- **Lost VPS:** rebuild from code + restore (§13.3).
- **Same-host blast radius (shared Docker and PostgreSQL):** per-app DB/role, resource ceilings, policy, non-root containers recommended; accepted risk at this scale.
- **Dispatch App key leaked:** N/A in v4; see §4.5.

---

## 13. Observability, backups, recovery

### 13.1 Monitoring

Grafana Cloud with Alloy (or suitable collector) per VPS. Monitor CPU, RAM, disk/inodes, container restarts/health, Nginx errors, certificate expiry, PostgreSQL availability/connections, per-app HTTP availability/latency/5xx, backup age. Alerts: disk pressure, restart loops, failed health, certificate expiry (<21 d), **newest good backup older than 8 h**, elevated 5xx. Alerts must reach you if the VPS is down (external uptime probe); **host-down and backup-age alerts are mandatory** and must be covered by the plan in use.

Start on the free plan only if quotas cover expected usage: estimate ingestion before go-live, measure after, watch quota, upgrade or reduce log volume if needed.

### 13.2 Backups (RPO 12 h)

| Item | Frequency | Method |
|---|---|---|
| PostgreSQL | **Every 6 h** | `pg_dump` per database + `pg_dumpall --globals`, encrypted |
| App volumes / uploads | Daily, or move uploads to object storage | restic or equivalent |
| Deployment records and config | After each deploy | copy |
| Whole-VPS snapshot | Not available (Sumopod has none) | n/a |

All go to the same Sumopod S3 bucket (endpoint, region, bucket name, access key ID/secret). Backup tool and encryption-key custody remain open (§17 #3). Retention default 14 days (`BACKUP_RETENTION_DAYS`) plus a few monthly copies. Backups are encrypted, access-controlled and monitored. With no snapshots, S3 backups plus code are the only recovery path. Keep uploads and durable files out of container writable layers.

### 13.3 Disaster recovery (RTO 4 h)

```text
Create new VPS (manual, Sumopod console; 15 min)
→ DNS update or reassign IP (15 min + TTL; see note below)
→ bootstrap-vps.yml + configure-vps.yml all-in-one (30 min)
→ restore PostgreSQL from latest dump (30–60 min, size dependent)
→ redeploy each app at its last known digest (GitHub Actions run history in each app repo / backup records) (6 × 5 min)
→ verify-vps.yml + smoke tests (15 min)
```

**DNS TTL:** A/AAAA TTL is 14400 s (4 h), equal to the whole RTO; if the replacement VPS gets a new IP, resolvers may keep the old address up to 4 h. Either lower the production A/AAAA TTL beforehand (e.g. 300–600 s) or keep the recovery IP the same. This is a recommendation; TTL policy remains your decision.

`playbooks/restore-database.yml` and a written runbook are mandatory. **Run a timed restore drill on Staging before Production go-live and at least quarterly after,** recording real elapsed time against 4 h. Mind Let's Encrypt rate limits when reissuing many certificates after a rebuild.

### 13.4 Deployment record

On the host, mirrored to off-host backup. GitHub Deployments mirroring is deferred; each app's Actions run history suffices for now.

```json
{"app":"customer-builder","environment":"Staging","image_ref":"ghcr.io/…@sha256:…",
 "previous_image_ref":"ghcr.io/…@sha256:…","git_commit":"…","source_run":"…",
 "central_run_url":"…","deployed_at_utc":"…","result":"success"}
```

---

## 14. Rollout strategy and scaling roadmap

**Rollout:** now, Compose replace (a few seconds' interruption per deploy accepted). Later, **blue/green** for stateless app containers: start the inactive slot, health-check, switch a validated Nginx upstream, retire the old slot; PostgreSQL stays outside. The registry/route contract already abstracts the upstream, so this changes the server script, not the app contract.

**Scaling** (add each step only when a measurable need appears):
1. **Now:** one all-in-one VPS per environment, ~4–6 small apps, with limits and capacity check.
2. **Split stateful:** DB to its own VPS or managed database; private networking; object storage for uploads.
3. **Split proxy:** `proxy_nodes` host, `upstream_mode: private_ip`.
4. **Multiple app hosts:** registry placement becomes a set of hosts (relaxing "exactly one host"), load balancer, rolling deploy, stateless apps. OpenTofu/Terraform provisioning only if Sumopod later offers an API (none today; provisioning stays manual).

---

## 15. Operational runbooks

- **New VPS:** create at Sumopod → verify initial access → `bootstrap-vps.yml` → verify second login → `configure-vps.yml` → `verify-vps.yml` → deploy a non-critical test app → verify HTTPS, logs, alerts, backups → restore drill (Staging).
- **Onboard an app:** (1) CentralDevOps PR adding `apps/<app>/staging.yml` and `production.yml` (domain, ports, placement, limits, DB); capacity check must pass. (2) Create DNS records. (3) In the app repo add `build.yml`, `deploy.yml`, `compose.yml`, `deploy/<env>.yml`, both Environments (Production approval gate) and secrets. (4) Run `build.yml`, deploy to Staging, verify, then Production.
- **Build and deploy:** `build.yml` (`source_ref`) → copy `image_ref` → `deploy.yml` (`target_environment`, `image_ref`); the rest is §8.
- **Change VPS config:** review Ansible change → `configure-vps.yml` Staging (check mode first) → `verify-vps.yml` → same for Production (approval).
- **Rotate secrets:** admin/deploy SSH keys: add the new public key via configure, switch the secret, remove the old key, verify. Sealed-bundle age key (only if retained): add the new public key to `deployment/keys/`, update `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`, bump the pinned SHA in apps, support two recipients during transition. GHCR pull token: rotate, re-run `configure-vps.yml`. Dispatch App key: §4.5.
- **Rollout fails:** route unchanged → read central and app run logs plus centralized container logs → rerun `deploy.yml` with the previous digest if needed → record the cause.

---

## 16. Implementation order

1. Repo foundation: structure, `ansible.cfg`, inventories, naming standard, CODEOWNERS, `apps/` registry schema.
2. **Spike** (§17 #1): same-repo reusable workflow + OIDC audience/claims + Environment secret behavior, on a throwaway app, before building the pipeline.
3. Host security roles; prove access survives hardening on a disposable VPS.
4. Docker role, `edge` and `db` networks, `deploy_runtime` role (scripts, sudoers).
5. `verify-vps.yml` early, extended with each role.
6. Nginx + Certbot (HTTP-01): one route; failed `nginx -t` cannot break existing routes; renewal hook tested.
7. PostgreSQL role, per-app DB provisioning, systemd ordering test across a reboot.
8. App `build.yml` with digest output and attestation.
9. `deploy-app.yml` (only after the spike confirms the design) and app `deploy.yml`; Staging, then Production behind approval.
10. Backups, off-host storage, restore drill, monitoring and alerts. **Not production-ready until the timed restore passes.**
11. Capacity check CI; onboard apps 2–6.
12. Scale preparation (split proxy/DB, blue/green) only when needed.

---

## 17. Open items, assumptions and verification spikes

| # | Item | Status |
|---|---|---|
| 1 | **Same-repo workflow spike:** validate OIDC audience and claims (`repository`, `job_workflow_ref`, `environment`) for a reusable-workflow call; validate Environment-secret behavior (which repo's Environment/secrets a called workflow sees; where `DEPLOY_SSH_PRIVATE_KEY` can safely live); confirm whether a single age-encrypted bundle is still needed. The deployment model depends on it | **Open. Required before building `deploy-app.yml`** |
| 3 | Backup tool and encryption-key custody (destination resolved: Sumopod S3) | **Open** |
| 11 | GitHub paid plan for private repos (Environments depend on it). Environment secrets/variables were tested and work; document the plan/visibility assumption in the README so a downgrade is noticed | Assumption |

**Resolved / confirmed:** #2 Sumopod: private network, firewall, console, separate S3 product; no snapshots, no API; IPv6, static/reserved IP and outbound restrictions not stated, treat as unconfirmed. #4 Migrations app-owned (ORM e.g. Prisma, or PostgreSQL GUI, §11.3). #5 `require_attestation` required and verified for Production, optional for Staging. #6 Production approval-gated; owner initially, deployment team replaces or joins once assigned (§4.1). #7 Separate Staging/Production VPS. #8 VPS sizing (§2); multiple apps per VPS, count not fixed. #9 Masterweb DNS, domains at exabytes.co.id, TTL 14400 s (§13.3). #10 Grafana free plan if quotas suffice; measure, monitor, upgrade or reduce volume; host-down and backup-age alerts required (§13.1). **Deferred:** #12 GitHub Deployments status integration (Actions run history used).

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
