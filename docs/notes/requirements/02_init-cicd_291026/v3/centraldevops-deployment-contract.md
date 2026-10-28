# CentralDevOps — Deployment Contract (v3)

Companion to `centraldevops-complete-infrastructure-design.md`. These are **contracts and skeletons**, not drop-in production files. Pin third-party actions and the `request-deploy` action to reviewed commit SHAs, and test each piece on Staging first. Domains, addresses and IDs are illustrative.

---

## 1. Registry: `apps/<app>/<env>.yml` (CentralDevOps)

Authoritative, reviewed by CODEOWNERS. `<env>` is lowercase (`staging`, `production`).

```yaml
app: customer-builder                       # ^[a-z][a-z0-9-]{1,30}$
environment: staging                        # staging | production
repository: example-org/customer-builder    # must equal the OIDC `repository` claim
image: ghcr.io/example-org/customer-builder # lowercase package path
allowed_refs: [refs/heads/main]
require_attestation: false                  # true recommended for production

domains:                                    # allow-list; manifest must pick from here
  - builder-staging.example.com

placement:                                  # inventory groups; each must resolve to exactly 1 host in v3
  app_group: app_nodes
  proxy_group: proxy_nodes
  database_group: database_nodes

routing:
  upstream_mode: docker_edge                # docker_edge | private_ip
  host_port: 21001                          # unique per app host; used for private_ip

limits:                                     # enforced on the rendered Compose
  memory: 512m
  cpus: "0.50"

database:
  enabled: true
  name: customer_builder_stg
  user: customer_builder_stg
```

Validation (CI on pull request, and again at deploy time):

- Schema valid; `app` + `environment` unique; filename matches content.
- Every domain is unique across all registry files.
- `host_port` unique per resolved app host and within an allowed range (e.g. 21000–29999).
- Sum of `limits.memory` per host is within that host's budget in inventory (`capacity_memory_mb` minus `reserved_memory_mb`).
- Placement groups exist in the matching inventory.

Host budget in inventory:

```yaml
# inventories/staging/host_vars/stg-aio-01.yml
capacity_memory_mb: 8192
reserved_memory_mb: 2048      # OS, Docker, Nginx, PostgreSQL, collector
```

---

## 2. App manifest: `deploy/<env>.yml` (app repository)

Route and runtime contract only. No secrets, hosts, or keys.

```yaml
app:
  name: customer-builder          # must equal registry app
  service: app                    # Compose service that receives traffic
  container_port: 3000
  edge_alias: customer-builder-staging

routing:
  enabled: true
  domain: builder-staging.example.com   # must be in registry domains
  tls: true

health:
  path: /health
  timeout_seconds: 90

runtime_env:
  required:                       # names only; exactly these keys must be in the sealed runtime.env
    - APP_AUTH_SECRET
    - DB_PASSWORD

release_command: null             # optional one-off command run with the new image before replacement, e.g. ["node","migrate.js"]
```

Rules:

- Centrally injected, **reserved** keys the app must not provide: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `IMAGE_REF`, `EDGE_ALIAS`, and any key starting with `CENTRALDEVOPS_`.
- Unknown keys in the manifest are rejected (schema `additionalProperties: false`).
- `runtime.env` keys that are neither declared in `runtime_env.required` nor optional-declared are rejected.

---

## 3. Compose conventions and policy

```yaml
services:
  app:
    image: ${IMAGE_REF:?IMAGE_REF must be provided}
    restart: unless-stopped
    env_file: [.env]
    expose: ["3000"]
    mem_limit: 512m
    cpus: 0.50
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:3000/health || exit 1"]
      interval: 15s
      timeout: 3s
      retries: 5
      start_period: 20s
    networks:
      edge:
        aliases: ["${EDGE_ALIAS:?EDGE_ALIAS must be provided}"]
      db: {}

networks:
  edge: { external: true, name: edge }
  db:   { external: true, name: db }
```

Policy check (`centraldevops-compose-policy`) runs on `docker compose --env-file compose.env config --format json` and fails on:

| Rule | Reason |
|---|---|
| `privileged`, `cap_add`, `devices`, `pid`/`ipc`/`network_mode: host`, `userns_mode`, weakened `security_opt` | Host takeover |
| Bind mount whose source is outside `/opt/apps/<app>/<env>/`, or `docker.sock` | Host file and Docker access |
| Any `ports:` entry | Bypasses firewall assumptions; deployment adds a private-IP publish itself when needed |
| Network other than the default project network, `edge`, `db` | Cross-app access |
| App service image ≠ requested digest | Image swap |
| Other service images not pinned by version or digest | Reproducibility |
| Routed service without `healthcheck` | Cannot gate routing |
| Missing `mem_limit`/`cpus`, or above the registry ceiling | Noisy neighbour |
| `env_file` other than `.env` | Arbitrary file read |

When `upstream_mode: private_ip`, the deployment adds an override file publishing `<private_ip>:<host_port>:<container_port>` for the routed service only.

---

## 4. Sealed bundle

Created by the app job, decrypted only by an approved CentralDevOps `deploy` job.

- Contents (tar): `runtime.env`, `compose.yml`, `manifest.yml` (copy of `deploy/<env>.yml`), `meta.json` (`{"app_repo":…,"git_sha":…,"run_id":…,"run_attempt":…}`).
- Encryption: `age -r <contents of deployment/keys/<env>.age.pub>`. Armor or base64 the output for transport.
- Public key `deployment/keys/<env>.age.pub` ships with the pinned `request-deploy` action. During key rotation, encrypt to both the old and new recipients.
- Private key: `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` (CentralDevOps Environment secret).
- Size: keep under about 40 KB so the total dispatch payload stays below the ~65 KB limit.

---

## 5. Deploy request and OIDC binding

### 5.1 Dispatch inputs for `deploy-app.yml`

| Input | Meaning |
|---|---|
| `target_environment` | `Staging` or `Production` |
| `image_ref` | `ghcr.io/…@sha256:<64 hex>` |
| `sealed_bundle` | base64 age ciphertext |
| `oidc_token` | JWT from the app job |
| `request_id` | UUID used for run correlation; included in `run-name` |

Note: the `app` is deliberately not an input.

### 5.2 Binding

```text
request_hash = hex(sha256( target_environment + "\n" + image_ref + "\n" + sealed_bundle ))
audience     = "centraldevops-deploy:" + request_hash
```

App side (inside `request-deploy`): `core.getIDToken(audience)` (or the `ACTIONS_ID_TOKEN_REQUEST_URL` endpoint with `&audience=`).

Central side (`deployment/tools/verify-oidc.py`, run in the `authorize` job):

1. Fetch GitHub's JWKS, verify signature, `iss = https://token.actions.githubusercontent.com`, `exp`/`nbf`.
2. Recompute `request_hash` from the dispatch inputs; require `aud` to match.
3. Look up the registry by `repository` claim and the requested environment; fail if no entry.
4. Require `job_workflow_ref` to equal `<repository>/.github/workflows/deploy.yml@<ref>` with `<ref>` in `allowed_refs`.
5. Require the `environment` claim to equal `target_environment`.
6. Require `image_ref` to match `^<registry image>@sha256:[a-f0-9]{64}$`.
7. Output `app`, `environment`, `run_id`, `run_attempt`, `sha`, and the resolved registry path. The `deploy` job later checks the replay record on the server.

Tokens are short-lived, so verification must happen in the `authorize` job before any approval wait.

---

## 6. App workflow skeletons

### 6.1 `deploy.yml`

```yaml
name: Deploy image

on:
  workflow_dispatch:
    inputs:
      target_environment:
        description: Environment to deploy into
        required: true
        type: choice
        options: [Staging, Production]
      image_ref:
        description: ghcr.io/example-org/customer-builder@sha256:...
        required: true
        type: string

permissions:
  contents: read
  id-token: write

jobs:
  request:
    runs-on: ubuntu-latest
    environment: ${{ inputs.target_environment }}
    timeout-minutes: 150
    steps:
      - uses: actions/checkout@REPLACE_WITH_REVIEWED_SHA

      - name: Render runtime environment file
        shell: bash
        env:
          APP_AUTH_SECRET: ${{ secrets.APP_AUTH_SECRET }}
          DB_PASSWORD: ${{ secrets.APP_DB_PASSWORD }}
          APP_PUBLIC_API_ORIGIN: ${{ vars.APP_PUBLIC_API_ORIGIN }}
        run: |
          set -euo pipefail
          umask 077
          mkdir -p "$RUNNER_TEMP/deploy"
          {
            printf 'APP_AUTH_SECRET=%s\n' "$APP_AUTH_SECRET"
            printf 'DB_PASSWORD=%s\n' "$DB_PASSWORD"
            printf 'APP_PUBLIC_API_ORIGIN=%s\n' "$APP_PUBLIC_API_ORIGIN"
          } > "$RUNNER_TEMP/deploy/runtime.env"

      - name: Request deployment from CentralDevOps
        uses: example-org/CentralDevOps/.github/actions/request-deploy@REPLACE_WITH_REVIEWED_SHA
        with:
          target_environment: ${{ inputs.target_environment }}
          image_ref: ${{ inputs.image_ref }}
          runtime_env_file: ${{ runner.temp }}/deploy/runtime.env
          compose_file: compose.yml
          manifest_file: deploy/${{ inputs.target_environment == 'Staging' && 'staging' || 'production' }}.yml
          dispatch_app_id: ${{ vars.DEPLOY_DISPATCH_APP_ID }}
          dispatch_app_private_key: ${{ secrets.DEPLOY_DISPATCH_APP_PRIVATE_KEY }}
          wait_timeout_minutes: 120
```

Notes:

- No `concurrency` is needed here; CentralDevOps serializes per app/environment and locks server-side.
- Delete `$RUNNER_TEMP/deploy` at the end (`if: always()`); never upload it.
- `DEPLOY_DISPATCH_APP_PRIVATE_KEY` is an org secret limited to selected repositories.

### 6.2 `request-deploy` action responsibilities

1. Validate inputs (regexes for `image_ref`, environment choice).
2. Verify the runtime env contains exactly the keys declared in the manifest.
3. Build `bundle.tar`, `age` encrypt, base64.
4. Compute `request_hash`; obtain OIDC token with the bound audience.
5. Mint a dispatch token (`actions/create-github-app-token`, `owner`, `repositories: CentralDevOps`, `permission-actions: write`).
6. `POST /repos/<owner>/CentralDevOps/actions/workflows/deploy-app.yml/dispatches` with `ref: main` and inputs.
7. Find the run whose `run-name` contains `request_id` (list runs for the workflow, `event=workflow_dispatch`, created after dispatch time); if the API in use returns the run ID on dispatch, use it.
8. Poll until completion or timeout; write the result and link to `$GITHUB_STEP_SUMMARY`; exit non-zero unless the central run succeeded.
9. Mask the OIDC token, bundle, and dispatch token; never `set -x`.

---

## 7. `deploy-app.yml` skeleton (CentralDevOps)

```yaml
name: Deploy app
run-name: deploy ${{ inputs.target_environment }} ${{ inputs.request_id }}

on:
  workflow_dispatch:
    inputs:
      target_environment: { required: true, type: choice, options: [Staging, Production] }
      image_ref:          { required: true, type: string }
      sealed_bundle:      { required: true, type: string }
      oidc_token:         { required: true, type: string }
      request_id:         { required: true, type: string }

permissions:
  contents: read

jobs:
  authorize:
    runs-on: ubuntu-latest
    outputs:
      app: ${{ steps.verify.outputs.app }}
      registry_file: ${{ steps.verify.outputs.registry_file }}
    steps:
      - uses: actions/checkout@REPLACE_WITH_REVIEWED_SHA
      - id: verify
        shell: bash
        env:
          TARGET_ENVIRONMENT: ${{ inputs.target_environment }}
          IMAGE_REF: ${{ inputs.image_ref }}
          SEALED_BUNDLE: ${{ inputs.sealed_bundle }}
          OIDC_TOKEN: ${{ inputs.oidc_token }}
        run: python3 deployment/tools/verify-oidc.py   # reads env, writes step outputs, never echoes token

  deploy:
    needs: authorize
    runs-on: ubuntu-latest
    environment: ${{ inputs.target_environment }}
    concurrency:
      group: deploy-${{ needs.authorize.outputs.app }}-${{ inputs.target_environment }}
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@REPLACE_WITH_REVIEWED_SHA
      # decrypt bundle -> validate manifest vs registry -> compose policy ->
      # resolve hosts from inventory -> ssh with DEPLOY_SSH_PRIVATE_KEY and pinned known_hosts ->
      # sudo centraldevops-deploy -> sudo centraldevops-route (proxy host) -> smoke test ->
      # GitHub Deployment status on the app repo -> summary
```

Concurrency groups cancel older *pending* runs, so they are not a correctness mechanism (see design §8.2). Server-side `flock` provides that.

Creating a GitHub Deployment on the app repository needs a token with `deployments: write` on that repository. Use a separate small GitHub App (`DEPLOY_STATUS_APP_*`) installed on app repositories, or skip this feature initially and rely on the server record and backup copies. This is an open item.

---

## 8. Server-side script contracts

Installed to `/usr/local/sbin` by the `deploy_runtime` role; owned by root, mode `0750`, group `cdo-deploy` only for execution via sudo.

### 8.1 `centraldevops-deploy <app> <env> <incoming_dir> <image_ref> <run_id> <run_attempt>`

1. Validate arguments (`^[a-z][a-z0-9-]{1,30}$`, `staging|production`, digest regex); canonicalize `<incoming_dir>` under `/var/lib/centraldevops/incoming/` and require ownership by the deploy user and no symlinks.
2. Take `flock` on `/var/lock/centraldevops-<app>-<env>.lock`.
3. Reject the replay of an already recorded `run_id`+`run_attempt`.
4. Re-run the Compose policy locally using the host's trusted copy of the policy script.
5. Ensure database and role if enabled (`CREATE ROLE … LOGIN PASSWORD …` via `psql` using a peer-authenticated superuser; password passed over stdin, never on the command line).
6. Copy files to `/opt/apps/<app>/<env>/` with correct modes (`.env` 0600, root or app owner); move current files to `previous/`.
7. `docker pull` the digest (using root-only GHCR credential configured by Ansible), optionally run `release_command`.
8. `docker compose -p <app>-<env> up -d --remove-orphans`; wait until the service reports `healthy` or the timeout elapses.
9. On failure restore `previous/` and exit non-zero; on success append the deployment record (`/var/lib/centraldevops/deployments/<app>-<env>/history.jsonl`).

### 8.2 `centraldevops-route <app> <env> <domain> <upstream> <tls>`

1. Validate arguments, check the domain against the registry copy the deploy script placed on the host.
2. Take the proxy `flock`.
3. Render from the trusted templates; compare with the existing file; exit 0 if unchanged.
4. HTTP-only vhost → `nginx -t` → reload → Certbot webroot (when no certificate exists) → HTTPS vhost → `nginx -t` → reload.
5. On any failure restore the previous config file and do not reload a broken configuration.

Both scripts print only non-sensitive progress and a final machine-readable result line.

---

## 9. Nginx templates (shape)

```nginx
# http-only.conf.j2
server {
  listen 80;
  server_name {{ domain }};
  location /.well-known/acme-challenge/ { root /var/www/acme; }
  location / { return 301 https://$host$request_uri; }
}

# https.conf.j2 (addition)
server {
  listen 443 ssl;
  http2 on;
  server_name {{ domain }};
  ssl_certificate     /etc/letsencrypt/live/{{ domain }}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/{{ domain }}/privkey.pem;
  location / {
    proxy_pass {{ upstream }};
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 60s;
  }
}
```

With a fresh domain, serving a redirect before the certificate exists is fine for the challenge path; `https` only exists after issuance. Resolve upstream hostnames through Docker's DNS resolver (`resolver 127.0.0.11`) with a variable, or restart/reload Nginx after the app container is recreated, so a changed container IP does not leave Nginx with a stale address.

---

## 10. Naming catalogue (quick reference)

| Scope | Name | Kind |
|---|---|---|
| CentralDevOps repo | `ANSIBLE_CONFIG_PATH`, `ANSIBLE_REQUIREMENTS_PATH`, `ANSIBLE_PLAYBOOKS_PATH` | variable |
| CentralDevOps env | `ANSIBLE_INVENTORY_PATH`, `DEPLOY_HEALTHCHECK_TIMEOUT`, `DEPLOY_REGISTRY_DIR`, `MONITORING_ENDPOINT`, `BACKUP_RETENTION_DAYS` | variable |
| CentralDevOps env | `ANSIBLE_SSH_PRIVATE_KEY`, `ANSIBLE_VAULT_PASSWORD`, `DEPLOY_SSH_PRIVATE_KEY`, `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`, `GHCR_PULL_TOKEN`, `BACKUP_*`, `MONITORING_GRAFANA_CLOUD_TOKEN`, `VPS_PROVIDER_API_TOKEN` | secret |
| Organization | `DEPLOY_DISPATCH_APP_ID` | variable |
| Organization (selected repos) | `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | secret |
| App env | `APP_*` | variable |
| App env | `APP_*_SECRET`, `APP_DB_PASSWORD`, … | secret |
| Committed (not GitHub settings) | `inventories/<env>/known_hosts`, `deployment/keys/<env>.age.pub`, `apps/<app>/<env>.yml` | public config |
