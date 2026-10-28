# CentralDevOps — Complete VPS Infrastructure and Deployment Design (v3)

**Status:** Recommended target design, decisions confirmed (see `centraldevops-decision-log.md`)  
**Supersedes:** `v2/centraldevops-complete-infrastructure-design.md`, `v2/centraldevops-routing-registration-latest-conversation.md`, `v2/centraldevops-github-environment-and-secret-naming.md`  
**Companion documents:** `centraldevops-deployment-contract.md` (schemas, workflow skeletons, script contracts), `centraldevops-decision-log.md` (decisions, v2 → v3 changes, open items)

| Item | Decision |
|---|---|
| Runtime | Docker Compose, one all-in-one Ubuntu VPS per environment at first |
| VPS provider | Sumopod (capabilities to be verified, see §17) |
| Scale target | Up to **6 applications** within 6 months |
| Recovery targets | **RTO 4 hours, RPO 12 hours** |
| Infrastructure automation | GitHub Actions + Ansible, run from CentralDevOps |
| Application deployment | **Centralized execution**: the app requests, CentralDevOps executes with its own credentials |
| Registry | GHCR, deploy by immutable digest |
| Routing / TLS | Nginx, DNS at an external provider, Let's Encrypt **HTTP-01** |
| Database | One shared PostgreSQL per environment, per-app database and role; path to per-app container documented |
| Rollout | Simple Compose replace; blue/green is a documented later phase |
| Monitoring | Grafana Cloud with a collector on each VPS |

---

## 1. Executive decisions

1. **Every app repository keeps two manual workflows: `build.yml` and `deploy.yml`.** Build and deploy stay separate operations.
2. **The immutable GHCR digest is the release identity.** Deploy `ghcr.io/OWNER/IMAGE@sha256:…`, never a mutable tag.
3. **Deployment executes in CentralDevOps.** The app's `deploy.yml` only *requests* a deployment. A CentralDevOps workflow (`deploy-app.yml`) holds all server credentials, validates the request, and performs the deployment. No app repository ever holds an SSH key or a server address.
4. **The request is authenticated with GitHub OIDC, not with a shared secret.** The app job proves its identity (repository, workflow file, ref, environment, run) with a short-lived OIDC token whose audience is bound to a hash of the request. See §8.
5. **App runtime secrets stay owned by the app** (in the app's `Staging`/`Production` GitHub Environment) but reach the server only inside a *sealed bundle* encrypted to a CentralDevOps public key that only an approved CentralDevOps deploy job can decrypt.
6. **A central registry in CentralDevOps (`apps/<app>/<env>.yml`) decides where each app runs, which domains it may use, and its resource ceilings.** The app manifest declares only the route it wants (domain, port, service, health path). No per-VPS GitHub variables.
7. **Keep two GitHub Environments, `Staging` and `Production`, in every repo. Use identical variable and secret names in both;** values differ per environment. Subsystem prefixes (`ANSIBLE_`, `DEPLOY_`, `GHCR_`, …) show ownership. Per-host data lives in Ansible inventory.
8. **Keep the three infrastructure workflows separate:** `bootstrap-vps.yml`, `configure-vps.yml`, `verify-vps.yml`. They are never part of an app deployment.
9. **Design the contract for a separate proxy (and later separate DB and app hosts) from day one,** even though each environment starts as one all-in-one VPS. Placement is data in the registry and inventory, not logic in workflows.
10. **Do not start with Kubernetes or Swarm.** Make apps stateless, deployments repeatable and recovery rehearsed first.

### Correction to v2

v2 said a reusable workflow in CentralDevOps "would use CentralDevOps' environment secrets." Per GitHub's reuse documentation, a called reusable workflow runs in the **caller's** repository context, so a job declaring `environment:` resolves that environment in the caller's repository. A reusable workflow therefore cannot give app repositories access to CentralDevOps-held server credentials. Truly centralized execution requires a workflow that **runs in the CentralDevOps repository**, triggered by a cross-repository `workflow_dispatch`. This is the model adopted here. Prove it in the spike in §17 before building on it.

### Plan check (resolved)

Environment secrets and variables on your organization's repositories have been tested and work. Keep the plan/visibility assumption documented in the README so a plan downgrade is noticed.

---

## 2. Requirements and capacity targets

| Requirement | Design consequence |
|---|---|
| Up to 6 apps in ~6 months | One VPS per environment is feasible only with **mandatory per-app memory/CPU limits** and a capacity check in the registry (§9.3). Revisit sizing at 4 apps. |
| RTO 4 h | A lost VPS must be rebuildable from code: bootstrap → configure → redeploy recorded digests → restore the database. A timed restore drill is required (§13.3). |
| RPO 12 h | Database dumps at least every **6 h** (half the RPO, leaves room for one failed run), shipped off-host. Alert when the newest good backup is older than **8 h**. |
| Brief deploy interruption acceptable | Plain `docker compose up -d` replacement; blue/green deferred (§14). |
| Staging and Production | Assumed to be **separate VPS instances**. Never share a host between them. |

---

## 3. Target architecture

```text
                              GitHub
 ┌────────────────────────────────────────────────────────────────┐
 │ App repository (x6)                       CentralDevOps          │
 │  build.yml ──► GHCR image digest          bootstrap/configure/   │
 │  deploy.yml                               verify-vps.yml         │
 │   ├ select GitHub Environment             deploy-app.yml  ◄──┐   │
 │   ├ build sealed bundle (age)             Ansible roles      │   │
 │   ├ OIDC token bound to request           registry apps/*    │   │
 │   └ dispatch ─────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────┘
                                │  CentralDevOps runner, SSH (deploy-only key)
                                ▼
     ┌─────────────────────────────── VPS (per environment) ───────────────┐
     │ Docker Engine / Compose                                             │
     │  Nginx (proxy)  ◄── DNS, public 80/443, Let's Encrypt HTTP-01       │
     │      │ edge network (all-in-one) or private IP:port (split proxy)   │
     │  App containers (policy-validated Compose)                          │
     │      │ db network                                                   │
     │  Shared PostgreSQL (per-app DB + role)                              │
     │  Grafana Alloy ──► Grafana Cloud       Backups ──► off-host storage │
     └─────────────────────────────────────────────────────────────────────┘
```

### Responsibilities

| Component | Owns |
|---|---|
| App repository | Source, tests, Dockerfile, `compose.yml`, `deploy/<env>.yml` route manifest, `build.yml`, `deploy.yml`, runtime secret mapping, app GitHub Environments |
| CentralDevOps | Ansible roles and inventories, the three infra workflows, `deploy-app.yml`, server-side deploy/route scripts, the app registry, Nginx templates, Compose policy, TLS, backups, monitoring |
| CentralDevOps GitHub Environments | Server access credentials, sealed-bundle private key, registry pull token, backup and monitoring credentials, **production approval gate** |
| App GitHub Environments | App runtime secrets/variables and the app-side branch restriction |
| GHCR | Images and digests |
| DNS provider | A/AAAA records (managed manually or by the provider's tooling; HTTP-01 needs no DNS API token) |
| Grafana Cloud | Dashboards, log/metric ingestion, alerts |
| Sumopod | Compute, disks, network, snapshots if offered |

### Operations stay separate

Provision → Bootstrap → Configure → Verify → Build → Deploy → Scale. Ansible never decides on its own that more capacity is needed.

---

## 4. GitHub Environments, naming and secrets

### 4.1 Environments

Both repository kinds use exactly two Environments: **`Staging`** and **`Production`**. Do not create one Environment per VPS.

| Setting | CentralDevOps `Production` | App `Production` |
|---|---|---|
| Required reviewers | **Yes. This is the single approval gate for production deployments and infrastructure changes** | Optional. Avoid a second approval unless required; double approval adds friction without adding safety |
| Deployment branches | `main` only | `main` (or release branches) only |
| Secrets | Server and infrastructure credentials | App runtime secrets |

### 4.2 Naming rules

1. `SCREAMING_SNAKE_CASE` for variables and secrets.
2. Subsystem prefix shows ownership: `ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_`, `MONITORING_`.
3. **Same name in both environments; the environment supplies the value.** Never `STAGING_…`/`PRODUCTION_…` names.
4. Per-host facts (address, user, roles, ports) belong in Ansible inventory or the registry, never in a GitHub variable.
5. Credentials are secrets; ordinary configuration (paths, public keys, host key pins, domains) is variables or committed files.
6. Names must not start with `GITHUB_`. Avoid generic names (`TOKEN`, `KEY`, `SERVER_IP`).
7. **Org-level values are not environment-scoped.** Use them only for credentials with identical scope in both environments, and restrict them to selected repositories.

### 4.3 CentralDevOps repository: variables

| Level | Name | Example | Purpose |
|---|---|---|---|
| Repository | `ANSIBLE_CONFIG_PATH` | `ansible.cfg` | Ansible config |
| Repository | `ANSIBLE_REQUIREMENTS_PATH` | `requirements.yml` | Collections/roles |
| Repository | `ANSIBLE_PLAYBOOKS_PATH` | `playbooks` | Playbook directory |
| Environment | `ANSIBLE_INVENTORY_PATH` | `inventories/staging/hosts.yml` / `inventories/production/hosts.yml` | Derived from the selected Environment, never typed in by hand |
| Environment | `DEPLOY_HEALTHCHECK_TIMEOUT` | `90` | Default health wait |
| Environment | `DEPLOY_REGISTRY_DIR` | `apps` | Registry root (files at `apps/<app>/<env>.yml`) |
| Environment | `MONITORING_ENDPOINT` | provider URL | Non-secret endpoint |
| Environment | `BACKUP_RETENTION_DAYS` | `14` | Retention |

Use only the variables workflows actually consume.

### 4.4 CentralDevOps repository: secrets (Environment scope)

| Name | Used by | Notes |
|---|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY` | bootstrap/configure/verify | Admin automation key. **Never usable by `deploy-app.yml`** |
| `ANSIBLE_VAULT_PASSWORD` | infra workflows | Only if Ansible Vault is used |
| `DEPLOY_SSH_PRIVATE_KEY` | `deploy-app.yml` | Restricted deploy identity (§8.5). Different key and different VPS account from the admin key |
| `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | `deploy-app.yml` | Decrypts sealed bundles. Exists only after Environment approval |
| `GHCR_PULL_TOKEN` | configure-vps | Read-only package token installed on the VPS by Ansible (root-only file) |
| `BACKUP_RESTIC_PASSWORD`, `BACKUP_S3_ACCESS_KEY_ID`, `BACKUP_S3_SECRET_ACCESS_KEY` | configure-vps | Names illustrative; depends on backup tool/storage chosen |
| `MONITORING_GRAFANA_CLOUD_TOKEN` | configure-vps | Collector credential |
| `VPS_PROVIDER_API_TOKEN` | future provisioning | Only if Sumopod offers an API and provisioning is automated |

Host key pins are **public** data. Store them in `inventories/<env>/known_hosts` (reviewed in pull requests) and use strict host-key checking. Do not trust a fresh `ssh-keyscan` from the same connection.

### 4.5 App repositories

| Level | Name | Purpose |
|---|---|---|
| Organization variable | `DEPLOY_DISPATCH_APP_ID` | ID of the dispatch-only GitHub App |
| Organization secret (selected repos only) | `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | Lets the app job dispatch workflows in CentralDevOps. No server access |
| Environment variable | `APP_*` | Non-secret app configuration |
| Environment secret | app-defined, e.g. `APP_AUTH_SECRET`, `APP_DB_PASSWORD` | Mapped into the sealed runtime bundle |

The dispatch App is installed on CentralDevOps only, with `actions: write`. Residual risk: that permission technically allows dispatching *any* CentralDevOps workflow. Mitigation: infra workflows reject dispatches made by the App identity, and infra `Production` runs require reviewer approval (§12).

---

## 5. Repository structures

### 5.1 CentralDevOps

```text
CentralDevOps/
├── ansible.cfg
├── requirements.yml
├── inventories/
│   ├── staging/
│   │   ├── hosts.yml
│   │   ├── known_hosts
│   │   ├── group_vars/{all,app_nodes,proxy_nodes,database_nodes}.yml
│   │   └── host_vars/stg-aio-01.yml
│   └── production/ (same layout)
├── apps/                          # registry: reviewed placement and policy
│   └── customer-builder/
│       ├── staging.yml
│       └── production.yml
├── playbooks/
│   ├── bootstrap.yml  configure.yml  verify.yml
│   └── restore-database.yml       # drill and disaster recovery
├── roles/
│   ├── common  users  ssh_hardening  firewall  docker
│   ├── nginx  certbot  postgresql  backup  monitoring_agent
│   ├── deploy_runtime             # installs server-side scripts + sudoers + dirs
│   └── wireguard                  # later, if the provider lacks private networking
├── deployment/
│   ├── scripts/                   # installed to /usr/local/sbin by deploy_runtime
│   │   ├── centraldevops-deploy
│   │   ├── centraldevops-route
│   │   └── centraldevops-compose-policy
│   ├── nginx-templates/{http-only,https}.conf.j2
│   ├── keys/{staging,production}.age.pub
│   ├── schemas/{registry,app-manifest}.schema.json
│   └── tools/verify-oidc.py       # OIDC + request-binding verification
├── .github/
│   ├── CODEOWNERS                 # apps/**, deployment/**, roles/** need review
│   ├── workflows/{bootstrap-vps,configure-vps,verify-vps,deploy-app}.yml
│   └── actions/request-deploy/action.yml   # used by app deploy.yml
└── README.md
```

### 5.2 App repository

```text
customer-builder/
├── .github/workflows/{build.yml,deploy.yml}
├── Dockerfile
├── compose.yml
├── deploy/{staging.yml,production.yml}    # route manifest, no secrets
└── README.md
```

---

## 6. Infrastructure workflows (CentralDevOps)

They are infrastructure operations, run on demand, never as part of an app deployment. Every one declares `environment: ${{ inputs.target_environment }}` so it picks up that Environment's inventory path and secrets.

### 6.1 `bootstrap-vps.yml`
Run once for a new VPS: connect with the provider's initial access, create named admin and deploy accounts, install the admin public key, apply updates, base firewall, then SSH hardening **only after a second, independent login succeeds**.

### 6.2 `configure-vps.yml`
Idempotently converges a host onto a profile.

| Input | Meaning |
|---|---|
| `target_environment` | `Staging` / `Production` (selects inventory and secrets) |
| `profile` | `app`, `proxy`, `database`, `monitoring`, `all-in-one` |
| `limit` | Optional host or group, validated against the selected inventory before use |
| `check_mode` | Dry run with `--check --diff` |

| Profile | Roles |
|---|---|
| `app` | common, users, ssh_hardening, firewall, docker, deploy_runtime, monitoring_agent, backup (volumes) |
| `proxy` | the above baseline + nginx, certbot |
| `database` | baseline + postgresql, backup |
| `monitoring` | baseline + collector |
| `all-in-one` | app + proxy + database, deliberately combined |

### 6.3 `verify-vps.yml`
Read-only PASS/FAIL report for: SSH access and expected users, firewall state, Docker/Compose, the `edge` and `db` networks, Nginx config and service, certificate expiry, PostgreSQL and listen addresses, deploy scripts present, root-owned and unmodified (checksum vs repo), monitoring connectivity, disk/inodes, **newest backup age** and the deploy-user sudoers entry. Accepts a host, a group, or a whole environment.

### 6.4 Inventory

Keep separate inventories per environment. Roles are expressed as groups; one all-in-one host is simply a member of several groups.

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

Splitting later means adding hosts to groups and changing registry placement, not rewriting workflows.

---

## 7. Application workflows

### 7.1 `build.yml` (manual: source → GHCR)

As in v2: operator selects `source_ref`; the workflow checks out that exact ref, tests, builds, pushes, and records the **digest** in the summary and in a metadata artifact. The image lives in GHCR; the artifact is metadata only.

Additions in v3:

- Use an explicit `sha-<full-commit>` tag as a convenience; **deploy by digest only**.
- Add `actions/attest-build-provenance` (permissions `id-token: write`, `attestations: write`) so the digest has a verifiable link to this repository, workflow and commit. The registry flag `require_attestation` (§9.2) lets CentralDevOps verify it with `gh attestation verify`. Recommended **on** for Production.
- Set `org.opencontainers.image.source` so the package is linked to the repository.

Operator flow is unchanged: copy `image_ref` from the build summary into the deploy run.

### 7.2 `deploy.yml` (manual: request a deployment)

| Input | Type |
|---|---|
| `target_environment` | choice: `Staging`, `Production` |
| `image_ref` | string, full `ghcr.io/…@sha256:…` |

The app job does only these things, using the CentralDevOps `request-deploy` composite action (pinned to a reviewed commit SHA):

1. `environment: ${{ inputs.target_environment }}`, `permissions: contents: read, id-token: write`.
2. Reject a malformed `image_ref` early (regex; the central side re-validates against the registry).
3. Render the runtime env file from this environment's secrets/variables.
4. Create the **sealed bundle**: `tar` of `runtime.env`, `compose.yml`, `deploy/<env>.yml`, encrypted with `age` to the public key `deployment/keys/<env>.age.pub` shipped with the pinned action.
5. Compute `request_hash = sha256(environment | image_ref | sealed_bundle)`.
6. Request an OIDC token with audience `centraldevops-deploy:<request_hash>`.
7. Mint a dispatch token from the dispatch App and dispatch `deploy-app.yml` on `main` in CentralDevOps with: `target_environment`, `image_ref`, `sealed_bundle` (base64), `oidc_token`, `request_id`.
8. Poll for the CentralDevOps run (identified by `request_id` in its `run-name`), write its final status and link into the summary, and fail if the central deployment fails. Poll timeout is configurable (default 120 min, longer than a typical approval wait). **A poll timeout does not cancel the central run.**

The app never learns a host, key or registry token. Dispatch inputs are visible in the run UI, which is acceptable because the bundle is ciphertext and the OIDC token is short-lived and single-purpose. Mask the token in logs anyway.

Limits: dispatch payloads are limited (about 65 KB total); a bundle of one `.env`, one Compose file and one manifest is far smaller. If a future app exceeds the limit, switch to an artifact fetched by CentralDevOps.

---

## 8. Central deployment pipeline (`deploy-app.yml`)

### 8.1 Trust model

The dispatch App token only proves that *someone with the org secret* triggered a run. Authenticity comes from the OIDC token.

| Check | Source of truth |
|---|---|
| Token signature, issuer, expiry | GitHub's OIDC JWKS (`https://token.actions.githubusercontent.com`) |
| Audience equals `centraldevops-deploy:` + recomputed `sha256(environment \| image_ref \| bundle)` | Binds the token to this exact request; a forged or altered input fails |
| `repository` claim | Maps to the app through the registry. **The app name is derived, never accepted as an input** |
| `job_workflow_ref` | Must be `<repo>/.github/workflows/deploy.yml@refs/heads/<allowed ref>` |
| `ref` | Must be in the registry's `allowed_refs` (e.g. `refs/heads/main`) |
| `environment` claim | Must equal `target_environment` |
| `run_id` + `run_attempt` | Single use: recorded in the server deployment record; replays are rejected |
| `image_ref` | Must match `ghcr.io/<registry image repository>@sha256:<64 hex>` |
| Provenance (when `require_attestation`) | `gh attestation verify` against the app repository and workflow |

### 8.2 Job structure

1. **`authorize`**: no Environment, no secrets. Verifies the OIDC token and request binding (these tokens expire quickly, so they must not wait behind an approval), loads and schema-validates the registry file `apps/<app>/<env>.yml`, and outputs the resolved plan.
2. **`deploy`**: `environment: ${{ inputs.target_environment }}` (CentralDevOps Environment → approval gate for Production, access to `DEPLOY_*` secrets). Decrypts the bundle, validates the manifest and Compose policy, and deploys.

Concurrency: `group: deploy-<app>-<environment>`, `cancel-in-progress: false`. GitHub keeps at most one *pending* run per group and cancels older pending ones, so this is only a convenience. **Correctness comes from server-side locking** (§8.4), not from workflow concurrency. Do not use a single environment-wide group; with 6 apps a pending deployment could be silently cancelled.

### 8.3 Deploy job steps

1. Check out CentralDevOps `main` (workflow and scripts are reviewed centrally; apps pin the `request-deploy` action, not this part).
2. Decrypt the bundle with `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` into a `umask 077` temp dir; `::add-mask::` every secret value; never upload this directory.
3. **Validate the manifest** (schema; the domain must be in the registry's `domains` allow-list; port and health path sane).
4. **Run the Compose policy** on `docker compose config --format json` (§9.4).
5. Resolve inventory groups from the registry to concrete hosts. In v3 each placement group must resolve to **exactly one host**; fail otherwise.
6. Verify the runtime env contains exactly the keys the manifest declares (and none reserved).
7. Open SSH to the host with the **deploy identity**, pinned host keys, strict checking. Copy the validated inputs to an incoming directory owned by the deploy user, then call the root-owned script through sudo (§8.5).
8. Server script: create/update DB and role if enabled (§11), pull the exact digest, back up the previous release files, render `compose.env`, `docker compose up -d`, wait for the container health check.
9. On first deploy or route change, call route registration (§10); run the HTTPS smoke test from the runner.
10. Write the deployment record, create a **GitHub Deployment + status** on the app repository (history that survives a lost VPS), and write a summary. Never print `.env` content.

### 8.4 Server-side locking and rollback

- `flock` per app/env for the deploy, and a separate `flock` for the proxy so two apps never edit/reload Nginx simultaneously.
- Keep `previous/` (compose.env, compose.yml, image ref). If the health check fails: restore the previous release and **do not change the route**. A first deployment simply fails and is left stopped.
- Manual rollback: rerun `deploy.yml` with the previous known-good digest. Database migrations need to be backward-compatible (§11.3); restoring an old container cannot undo a schema change.

### 8.5 Deploy identity on the VPS

- Separate unprivileged account (e.g. `cdo-deploy`) with its own key `DEPLOY_SSH_PRIVATE_KEY`. **Not in the `docker` group** (that is root-equivalent).
- A `sudoers` entry allows only `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` with validated arguments. The scripts are root-owned, not writable by the deploy user, and re-validate every argument and file themselves.
- GitHub-hosted runner source addresses are not stable, so do not rely on `from=` restrictions in `authorized_keys`; rely on the key restriction options (`restrict`), sudoers scoping and audit logs instead.
- SSH-level logging plus the deployment record give an audit trail.

---

## 9. Registry, manifest and Compose policy

Detailed schemas and examples are in `centraldevops-deployment-contract.md`.

### 9.1 Who decides what

| Concern | Decided by |
|---|---|
| Image repository, allowed refs, domains, placement, resource ceilings, DB, attestation | **Registry** `apps/<app>/<env>.yml` in CentralDevOps (reviewed via CODEOWNERS) |
| Which domain it wants, container port, service name, health path, TLS, required runtime keys, optional release command | **App manifest** `deploy/<env>.yml` |
| Services, images, healthchecks, volumes | App `compose.yml` (subject to policy) |

The manifest may only request a domain the registry already allocated to that app/environment. This prevents an app from claiming another app's hostname or triggering certificate issuance for arbitrary domains.

### 9.2 Registry file (summary)

```yaml
app: customer-builder
environment: staging
repository: example-org/customer-builder
image: ghcr.io/example-org/customer-builder
allowed_refs: [refs/heads/main]
require_attestation: false
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

A CI check in CentralDevOps sums `limits.memory` of all registry entries per placement host and fails the pull request if the total exceeds the host's budget declared in inventory (physical RAM minus reserve for OS, Docker, Nginx, PostgreSQL and the collector). This makes "will app #6 fit" a reviewed decision instead of a surprise.

### 9.4 Compose policy (enforced centrally, on the rendered config)

Because the server executes the app's `compose.yml`, it is privileged input. Reject:

- `privileged`, `cap_add`, `devices`, `pid`/`ipc`/`network_mode: host`, `userns_mode`, `security_opt` that weakens confinement
- bind mounts outside `/opt/apps/<app>/<env>/` (and never the Docker socket)
- published `ports` (only the central deployment adds a publish when `upstream_mode: private_ip`, bound to the private IP)
- networks other than the app's own default, `edge` and `db` (declared external)
- images not equal to the requested digest for the app service; other images must be digest- or version-pinned
- missing `healthcheck` on the routed service, or missing/over-ceiling memory and CPU limits
- `env_file` other than `.env`

---

## 10. Routing and TLS

### 10.1 Placement contract

| `upstream_mode` | When | Upstream used by Nginx |
|---|---|---|
| `docker_edge` | Proxy and app on the same host (initial state) | `http://<edge_alias>:<container_port>` over the Docker `edge` network |
| `private_ip` | Proxy on a different host | `http://<app private_ip>:<host_port>`; the app publishes only on its private IP; firewall allows only the proxy host |

Docker networks are host-local. A split proxy needs private networking from the provider or WireGuard (the `wireguard` role). Never expose backend ports publicly to bridge hosts.

### 10.2 DNS

Create the A/AAAA record at your DNS provider pointing to the proxy's public IP **before** the first deployment of a domain. The deployment pre-checks resolution against the proxy IP and fails with a clear message instead of burning Let's Encrypt validation attempts.

### 10.3 Route activation (HTTP-01)

Routing registration runs inside the central deployment, after the health check, and is idempotent: an unchanged route means no rewrite and no reload.

1. Validate domain ∈ registry allow-list; render deterministic file `/opt/centraldevops/nginx/conf.d/<app>-<env>.conf` from the trusted template.
2. **New domain:** render the HTTP-only server block (ACME challenge location at `/.well-known/acme-challenge/` from a shared webroot) → `nginx -t` → reload.
3. Obtain the certificate with Certbot in webroot mode (HTTP-01). Let's Encrypt limits failed validations; the DNS pre-check protects against this. Use the Let's Encrypt staging endpoint when testing.
4. Render the HTTPS block (redirect 80→443, modern TLS, HSTS after verification, forwarded headers, timeouts) → `nginx -t` → reload.
5. On `nginx -t` failure, restore the last known-good file, do not reload, fail the deployment.
6. HTTPS smoke test from the runner.
7. Renewal by a Certbot systemd timer with a deploy hook that runs `nginx -t` then reload. `verify-vps.yml` flags certificates expiring in under 21 days.

HTTP-01 limitations: no wildcard certificates, port 80 must be reachable from the internet, and each domain needs its own certificate. If a CDN/proxy such as Cloudflare is placed in front later, revisit the validation method.

### 10.4 Separate proxy credential

When the proxy is a different host, `centraldevops-route` runs on the proxy through the same restricted deploy identity (a distinct `proxy_group` host). The app host and proxy host each get their own `authorized_keys`/sudoers set up by the `deploy_runtime` role.

---

## 11. Database

### 11.1 Model

One PostgreSQL instance per environment, managed by the `postgresql` role, with **one database and one login role per app**; no app uses the superuser. Apps connect only over the `db` Docker network (or a private IP once the database moves).

Network design for the all-in-one host:

- Ansible creates a dedicated Docker bridge network `db` with a fixed subnet (for example `172.30.0.0/24`).
- PostgreSQL listens on `localhost` and the `db` network's gateway address only; `pg_hba.conf` permits the `db` subnet with `scram-sha-256`; the firewall allows 5432 only from that subnet.
- The network must exist before PostgreSQL binds to its gateway address. Add a systemd drop-in so PostgreSQL starts after `docker.service`, and have `verify-vps.yml` confirm the listener after a reboot.
- The app receives non-secret `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` injected by CentralDevOps and supplies `DB_PASSWORD` from its own secrets (inside the sealed bundle).
- Central deployment idempotently creates the DB/role from the registry entry and sets the password from the bundle. Rotation = change the app secret and redeploy.

### 11.2 Migration path to per-app container

The contract (`DB_*` variables) is the same. Moving an app to its own Postgres container means changing its Compose file to include a `db` service on a private network and pointing `DB_HOST` at it; restore the app's database from backup into it; set `database.enabled: false` in the registry. Moving PostgreSQL to a separate VPS means changing the `DB_HOST` value to the database host's private IP and the registry `database_group`.

### 11.3 Migrations

Schema migrations must be backward compatible with the previous release (expand/contract). Use the optional manifest `release_command`, run once as a one-off container with the new image **before** the replace, and abort the deployment on failure. Decide per app whether migrations run in `release_command` or at container start (open item).

---

## 12. Security baseline and threat model

### 12.1 Host and Docker

- SSH key authentication only; disable root and password login after validating the new path.
- Admin and deploy identities and keys are separate; the deploy user has no Docker group membership.
- Public ports: 80 and 443 only; SSH restricted by source IP/VPN where practical. Docker published ports can bypass UFW rules; the Compose policy forbids published ports so UFW and Docker agree.
- PostgreSQL and app ports are never public. The Docker API is never exposed.
- No secrets in image layers, build args, labels or committed Compose files.
- Automatic security updates; fail2ban or equivalent only after testing.
- Root-owned deploy scripts, checksum-verified by `verify-vps.yml`.

### 12.2 GitHub Actions

- Least-privilege `permissions`; app `deploy.yml` needs `contents: read` and `id-token: write`.
- Pin third-party actions and the `request-deploy` action to reviewed commit SHAs.
- Never interpolate untrusted input directly in shell; pass via `env:` and validate with strict regexes.
- Restrict Production Environments to `main`; reviewers on CentralDevOps `Production`.
- CODEOWNERS on `apps/**`, `deployment/**`, `roles/**`, and `.github/workflows/**`. Registry changes are security changes.
- Infra workflows reject `github.actor` equal to the dispatch App identity.

### 12.3 Threats and mitigations

| Threat | Mitigation |
|---|---|
| Compromised app repo tries to deploy another app's image or domain | App derived from OIDC `repository`; image must match registry repository; domain allow-list |
| Forged or replayed deploy request | OIDC audience bound to the request hash; one-time `run_id`+`run_attempt`; short token lifetime |
| Dispatch App key leaked | Can only dispatch workflows in CentralDevOps; deploys still require a valid OIDC proof; infra workflows reject its identity and Production requires approval. Rotate the App key |
| Malicious Compose file | Central policy on rendered config (§9.4) |
| Secret leakage in logs | `add-mask`, no `set -x`, no artifact upload of the temp dir, short-lived temp files, secrets only in ciphertext in dispatch inputs |
| Lost VPS | Rebuild from code + restore (§13.3) |
| Same-host blast radius (6 apps share Docker and PostgreSQL) | Per-app DB/role, resource ceilings, policy, non-root containers recommended; accepted risk at this scale |

---

## 13. Observability, backups, recovery

### 13.1 Monitoring

Grafana Cloud with Alloy (or a suitable collector) on each VPS. Monitor CPU, RAM, disk and inodes, container restarts/health, Nginx errors, certificate expiry, PostgreSQL availability and connections, HTTP availability/latency/5xx per app, and backup age. Alerts: disk pressure, restart loops, failed health, certificate expiry (<21 d), **newest good backup older than 8 h**, elevated 5xx. Verify that the free-tier limits cover 6 apps' logs/metrics. Alerts must reach you if the VPS is down (external uptime probe).

### 13.2 Backups (RPO 12 h)

| Item | Frequency | Method | Destination |
|---|---|---|---|
| PostgreSQL | **Every 6 h** | `pg_dump` per database plus `pg_dumpall --globals`, encrypted | Off-host object storage (provider and bucket TBD) |
| App volumes / uploads | Daily, or move uploads to object storage | restic or equivalent | Off-host |
| Deployment records and config | After each deploy | copy | Off-host |
| Whole-VPS snapshot | Weekly, if Sumopod supports | provider | Provider |

Retention default 14 days (`BACKUP_RETENTION_DAYS`) plus a few monthly copies. Backups are encrypted, access-controlled, and monitored. A snapshot is an extra layer, never the only database backup. Keep uploads and durable files out of container writable layers.

### 13.3 Disaster recovery (RTO 4 h)

Recovery sequence for a lost environment VPS, with a target time budget:

```text
Create new VPS (15 min)
→ DNS update or reassign IP (15 min + TTL; lower TTL beforehand)
→ bootstrap-vps.yml + configure-vps.yml all-in-one (30 min)
→ restore PostgreSQL from latest dump (30–60 min, size dependent)
→ redeploy each app at its last known digest (GitHub Deployments history / backup records) (6 × 5 min)
→ verify-vps.yml + smoke tests (15 min)
```

`playbooks/restore-database.yml` and a written runbook are mandatory. **Run a timed restore drill on Staging before Production go-live and at least quarterly afterwards,** and record the real elapsed time against the 4 h target. Remember Let's Encrypt rate limits when reissuing certificates for many domains after a rebuild.

### 13.4 Deployment record

Stored on the host and mirrored to GitHub Deployments and off-host backup:

```json
{"app":"customer-builder","environment":"Staging","image_ref":"ghcr.io/…@sha256:…",
 "previous_image_ref":"ghcr.io/…@sha256:…","git_commit":"…","source_run":"…",
 "central_run_url":"…","deployed_at_utc":"…","result":"success"}
```

---

## 14. Rollout strategy and scaling roadmap

### 14.1 Rollout

Now: Compose replace; a few seconds of interruption per deploy is accepted. Later: **blue/green** for stateless app containers: start the inactive slot, health-check, switch a validated Nginx upstream, retire the old slot. PostgreSQL stays outside the slots. The registry/route contract already abstracts the upstream, so this changes the server script, not the app contract.

### 14.2 Scaling

1. **Now:** one all-in-one VPS per environment, up to ~4–6 small apps, with limits and capacity check.
2. **Split stateful:** database to its own VPS or a managed database; private networking; object storage for uploads.
3. **Split proxy:** `proxy_nodes` host, `upstream_mode: private_ip`.
4. **Multiple app hosts:** registry placement per app becomes a set of hosts (relaxing the "exactly one host" rule), load balancer, rolling deploy, stateless apps, provisioning with OpenTofu/Terraform if Sumopod has an API.

Add each step only when a measurable need appears.

---

## 15. Operational runbooks

### 15.1 New VPS
Create at Sumopod → verify initial access → `bootstrap-vps.yml` → verify second login → `configure-vps.yml` → `verify-vps.yml` → deploy a non-critical test app → verify HTTPS, logs, alerts, backups → run the restore drill (Staging).

### 15.2 Onboard a new application
1. Open a CentralDevOps PR adding `apps/<app>/staging.yml` and `production.yml` (domain, ports, placement, limits, DB). The capacity check must pass.
2. Create DNS records for the domains.
3. In the app repository: add `build.yml`, `deploy.yml`, `compose.yml`, `deploy/<env>.yml`, the two Environments, the secrets, and grant the repo access to the org dispatch secret.
4. Run `build.yml`, deploy to Staging, verify, then Production.

### 15.3 Build and deploy

```text
build.yml (source_ref) → copy image_ref
→ deploy.yml (target_environment, image_ref)
→ app job builds sealed bundle + OIDC token → dispatches deploy-app.yml
→ authorize job → (Production approval) → deploy job
→ policy → copy → deploy → health → route → smoke → record
→ app run reports central result
```

### 15.4 Change VPS configuration
Review Ansible change → `configure-vps.yml` Staging (check mode first) → `verify-vps.yml` → same for Production (approval).

### 15.5 Rotate secrets
- Admin/deploy SSH keys: add the new public key via configure, switch the secret, remove the old key, verify.
- Sealed-bundle age key: add the new public key to `deployment/keys/`, update `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`, bump the pinned `request-deploy` SHA in apps (support two recipients during the transition).
- GHCR pull token: rotate and re-run `configure-vps.yml`.
- Dispatch App key: generate a new one, update the org secret, delete the old.

### 15.6 Rollout fails
Route unchanged → read central and app run logs plus centralized container logs → rerun `deploy.yml` with the previous digest if needed → record the cause.

---

## 16. Implementation order

1. Repository foundation: structure, `ansible.cfg`, inventories, naming standard, CODEOWNERS, `apps/` registry schema.
2. **Spike:** cross-repo dispatch + OIDC verification (§17) on a throwaway app. Do this before building the pipeline.
3. Host security roles; prove access survives hardening on a disposable VPS.
4. Docker role, `edge` and `db` networks, `deploy_runtime` role with the scripts and sudoers.
5. `verify-vps.yml` early, extended with each role.
6. Nginx + Certbot (HTTP-01): one route, failed `nginx -t` cannot break existing routes, renewal hook tested.
7. PostgreSQL role, per-app DB provisioning, systemd ordering test across a reboot.
8. App `build.yml` with digest output and attestation.
9. `request-deploy` action and `deploy-app.yml`; deploy to Staging, then Production behind approval.
10. Backups, off-host storage, restore drill, monitoring and alerts. **Not production-ready until the timed restore passes.**
11. Capacity check CI, onboarding of apps 2–6.
12. Scale preparation (split proxy/DB, blue/green) only when needed.

---

## 17. Open items, assumptions and verification spikes

| # | Item | Why it matters |
|---|---|---|
| 1 | **Dispatch + OIDC spike:** confirm cross-repo dispatch with the GitHub App, OIDC custom audience, claim values (`job_workflow_ref`, `environment`) in your org; confirm a reusable workflow cannot read CentralDevOps secrets | The whole centralized model depends on it |
| 2 | **Sumopod capabilities:** private networking, cloud firewall, snapshots, object storage (S3-compatible?), API, IPv6, static/reserved IP, console access, outbound restrictions | Determines backup destination, split-host design, and provisioning |
| 3 | Backup storage choice and tool (restic vs plain dump upload) and encryption key custody | RPO and recovery |
| 4 | Migration strategy per app: `release_command` or start-up migrations | Deploy safety |
| 5 | `require_attestation` for Production: yes/no | Supply chain assurance versus build setup effort |
| 6 | Production approval only in CentralDevOps (recommended) or also in apps | Friction vs control |
| 7 | Staging and Production assumed on separate VPS instances | Cost and isolation |
| 8 | VPS sizing: RAM/CPU/disk for 6 apps plus PostgreSQL | Capacity ceiling in registry |
| 9 | DNS provider name, TTL policy for DR | DR timing |
| 10 | Grafana Cloud plan limits | Alerting and log volume |
| 11 | GitHub plan stays on a paid tier for private repos | Environments depend on it |

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
