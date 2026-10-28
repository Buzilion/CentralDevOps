# CentralDevOps — Complete VPS Infrastructure and Deployment Design

**Status:** Recommended target design  
**Initial runtime:** Docker Compose on one or a small number of Ubuntu VPS instances  
**Infrastructure automation:** GitHub Actions + Ansible  
**Container registry:** GitHub Container Registry (GHCR)  
**Routing:** Nginx + DNS + TLS  
**Monitoring:** Grafana Cloud with a collector on each VPS

This design combines the existing VPS infrastructure proposal, the routing/workflow proposal, and the requirement that every application repository retains two manually triggered workflows: `build.yml` and `deploy.yml`.

---

## 1. Executive decisions

1. **Keep `build.yml` and `deploy.yml` in every application repository.** They are the app-specific, manually triggered entry points. Building and deploying are separate operations.
2. **Use an immutable GHCR image digest as deployment identity.** The deploy workflow must receive both the target environment and the image reference to deploy. Prefer `ghcr.io/OWNER/IMAGE@sha256:...` over a mutable tag such as `latest`.
3. **Centralize deployment mechanics in a versioned composite action in CentralDevOps.** The app's `deploy.yml` calls the action. The app job selects its own `Staging` or `Production` GitHub Environment, so its application-specific configuration and secrets are available to the job.
4. **Do not assume secrets in one repository's GitHub Environment are accessible from another repository.** Composite actions run inside the caller's job and must receive any secret they need explicitly. A reusable workflow in CentralDevOps would use CentralDevOps' environment secrets when its own job declares an environment; it does not automatically gain the caller app's environment secrets. This is why a composite action is the simpler fit for the current secret-ownership model.
5. **CentralDevOps owns server configuration and routing implementation.** Each app repo declares the route it needs (domain, port, health endpoint, etc.); CentralDevOps validates that declaration and renders/activates the Nginx configuration.
6. **Keep the three CentralDevOps infrastructure workflows separate:** `bootstrap-vps.yml`, `configure-vps.yml`, and `verify-vps.yml`. They are not part of every application deployment.
7. **Start with Docker Compose; do not start with Kubernetes or a cluster scheduler.** Make apps stateless and deployments repeatable now, so moving to multiple VPS instances later is a controlled infrastructure change rather than an app rewrite.

### Important account-plan check

GitHub currently documents that GitHub Free supports Environments and environment secrets for public repositories; private repositories require GitHub Pro, Team, or Enterprise for these features. If your app repositories are private and you remain on Free, the planned private-repository `Staging`/`Production` Environments and their secrets will not work as designed. Confirm the plan before relying on them, or upgrade/use an alternative secrets and approval arrangement. See [GitHub's environment documentation](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

---

## 2. Target architecture

```text
                          GitHub
  ┌────────────────────────────────────────────────────────┐
  │ CentralDevOps repository                               │
  │  ├─ bootstrap-vps.yml                                  │
  │  ├─ configure-vps.yml                                  │
  │  ├─ verify-vps.yml                                     │
  │  ├─ Ansible playbooks and roles                        │
  │  ├─ shared deploy-compose composite action             │
  │  └─ Nginx route templates / deployment contract        │
  │                                                        │
  │ Application repository A                               │
  │  ├─ build.yml   (manual: build source → GHCR image)    │
  │  ├─ deploy.yml  (manual: image digest + environment)   │
  │  ├─ compose.yml                                      │
  │  └─ deploy/{staging,production}.yml                    │
  └────────────────────────────────────────────────────────┘
                │                             │
                │ build                       │ deploy request
                ▼                             ▼
     GitHub Actions runner         Shared CentralDevOps action
                │                             │ SSH (deploy-only key)
                ▼                             ▼
             GHCR                       Target VPS
                                      ┌──────────────────────┐
     Immutable image digest ────────▶ │ Docker Engine        │
                                      │ Docker Compose       │
                                      │ Nginx reverse proxy  │◀── DNS / public 80,443
                                      │ App containers       │
                                      │ Optional PostgreSQL  │
                                      │ Grafana Alloy/agent  │──▶ Grafana Cloud
                                      └──────────────────────┘
                                                │
                                                └── encrypted off-host backups
```

### Responsibilities by component

| Component | Owns |
|---|---|
| Application repository | Application source, tests, Dockerfile, app-specific Compose definition, runtime `.env` keys, image build workflow, deploy workflow, desired domain/port/health check |
| CentralDevOps | VPS bootstrap/configuration/verification, Ansible roles, deployment script/action, Nginx templates, routing validation, host-level monitoring and backup policy |
| GitHub Environments | Environment-scoped application configuration/secrets and deployment approval rules, where the account plan supports them |
| CentralDevOps Environments | Infrastructure-level access for Ansible and server administration; they are **not** the app repository's environments |
| GHCR | Versioned images and their immutable digests |
| DNS provider (for example Cloudflare) | Domain records pointing at the public reverse proxy/load balancer |
| Grafana Cloud | Central dashboards, log/metric ingestion, and alerting |
| VPS provider | Compute, network, disks, snapshots if used, and later API-based provisioning |

### Operations remain separate

- **Provision:** create the VPS in the provider or later through OpenTofu/Terraform.
- **Bootstrap:** establish trusted admin access and initial OS security.
- **Configure:** install and maintain the services selected for that host profile.
- **Verify:** audit current state without reconfiguring the machine.
- **Build:** package application source into an immutable image in GHCR.
- **Deploy:** take a specific image digest and environment, then apply the app runtime and route.
- **Scale:** separately decide to add capacity, create/configure additional hosts, and register healthy instances with the load balancer.

Ansible should configure the desired host state. It should not decide autonomously when traffic requires another VPS.

---

## 3. Repository structures

### 3.1 CentralDevOps

```text
CentralDevOps/
├── ansible.cfg
├── requirements.yml
├── inventories/
│   ├── staging/
│   │   ├── hosts.yml
│   │   └── host_vars/
│   └── production/
│       ├── hosts.yml
│       └── host_vars/
├── playbooks/
│   ├── bootstrap.yml
│   ├── configure.yml
│   ├── verify.yml
│   └── decommission.yml          # add when lifecycle automation is ready
├── roles/
│   ├── common/
│   ├── users/
│   ├── ssh_hardening/
│   ├── firewall/
│   ├── docker/
│   ├── nginx/
│   ├── postgresql/
│   ├── backup/
│   └── monitoring_agent/
├── deployment/
│   ├── scripts/
│   │   ├── deploy-compose.sh
│   │   └── register-route.sh
│   ├── nginx-templates/
│   │   └── app-server.conf.j2
│   └── schemas/
│       └── app-manifest.schema.json
├── .github/
│   ├── workflows/
│   │   ├── bootstrap-vps.yml
│   │   ├── configure-vps.yml
│   │   └── verify-vps.yml
│   └── actions/
│       └── deploy-compose/
│           └── action.yml
└── README.md
```

Keep the deployment action and its scripts versioned. Application workflows should reference a fixed, reviewed CentralDevOps release/tag or commit SHA; pinning to a commit SHA is the strongest reproducibility choice. When the action changes, intentionally update app repos to the reviewed version.

### 3.2 Each application repository

```text
customer-builder/
├── .github/
│   └── workflows/
│       ├── build.yml
│       └── deploy.yml
├── Dockerfile
├── compose.yml
├── deploy/
│   ├── staging.yml
│   └── production.yml
├── src/
└── README.md
```

`build.yml` is intentionally app-local because application tests and build requirements differ. Centralize common build steps later only if doing so removes meaningful duplication.

---

## 4. CentralDevOps infrastructure workflows

The three workflows have different responsibilities. They are infrastructure operations, not steps that must run each time an app is deployed.

### 4.1 `bootstrap-vps.yml`

**Run when:** a new VPS has been created and needs its first secure configuration.

Typical operations:

- Connect through the initial trusted SSH access supplied during VPS creation.
- Create named admin and deployment accounts/groups.
- Install base packages and apply OS security updates.
- Install and validate SSH public-key authentication.
- Configure initial firewall rules.
- Harden SSH only after confirming the new account/key can connect independently.

Do not immediately disable the initial access path after editing SSH configuration. Validate the new login in a separate connection first to avoid locking yourself out.

### 4.2 `configure-vps.yml`

**Run when:** a host first needs its services installed, or its intended configuration changes.

Use a host profile input to select roles rather than installing all software on every server:

| Profile | Typical roles |
|---|---|
| `app` | Common security baseline, users, Docker/Compose, deployment directories, monitoring agent |
| `proxy` | Common baseline, users, Docker, Nginx, TLS automation, monitoring agent |
| `database` | Common baseline, users, PostgreSQL, backups, monitoring agent |
| `monitoring` | Common baseline and the selected monitoring stack/collector |
| `all-in-one` | A deliberate combination for a small initial setup |

Configuration should be **idempotent**: repeatedly applying it converges on the same desired state. Prefer Ansible modules and handlers over ad hoc shell commands.

### 4.3 `verify-vps.yml`

**Run when:** after bootstrap/configuration, following infrastructure changes, or during an audit/troubleshooting session.

Run read-only checks where possible and report a clear PASS/FAIL result for SSH access, expected users, firewall state, Docker/Compose, Nginx configuration and service health, PostgreSQL if installed, monitoring connectivity, disk space, required directories, and backup status.

### 4.4 Infrastructure environments and secrets

Use `CentralDevOps` repository Environments named `Staging` and `Production` for infrastructure workflows. Keep host addresses and profile names as ordinary configuration; protect SSH private keys, provider API tokens, and other credentials as secrets. Use production environment protection/approval where available.

The infrastructure admin key used by Ansible must not be the same key exposed to application deployment workflows.

---

## 5. Application workflow contract: build first, deploy separately

Both app workflows are triggered manually through `workflow_dispatch` as requested.

### 5.1 `build.yml`: source code → image in GHCR

Suggested flow:

1. The operator manually starts `Build image` and selects the source branch/tag/ref.
2. The workflow checks out that exact ref and runs the project's tests/quality checks.
3. It builds the Docker image and pushes it to GHCR.
4. It obtains the registry digest produced by the push.
5. It writes the immutable image reference and source/build metadata to the workflow summary and a downloadable metadata artifact.

The actual container image lives in **GHCR**. The GitHub Actions artifact should be metadata such as `build-metadata.json`, not a second copy of the image tarball.

Recommended deployment identifier:

```text
ghcr.io/OWNER/IMAGE@sha256:<manifest-digest>
```

You may also publish a convenient tag such as `sha-<full-git-commit>`, but deploy by digest. Tags can be moved; a digest identifies the exact pushed image content. See [GitHub's container registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

Example metadata:

```json
{
  "image_ref": "ghcr.io/example-org/customer-builder@sha256:REPLACE_WITH_REAL_DIGEST",
  "git_commit": "REPLACE_WITH_FULL_COMMIT_SHA",
  "source_ref": "main",
  "build_run_id": "REPLACE_WITH_RUN_ID",
  "repository": "example-org/customer-builder"
}
```

The digest and fields above are examples; the workflow must write real values produced by the current build.

**How the operator deploys the build:** copy the exact `image_ref` from the build summary/metadata artifact into the `image_ref` input of the separate `deploy.yml` run. Since the two workflows are separate manual runs, do not assume a previous workflow's outputs will automatically populate a later run's inputs.

### 5.2 `deploy.yml`: exact image digest + environment → deployed app

Required manual inputs:

| Input | Type | Meaning |
|---|---|---|
| `target_environment` | Choice: `Staging`, `Production` | Environment to which the image should be deployed |
| `image_ref` | String | Full immutable GHCR reference, including `@sha256:...` |

The deploy workflow should reject an image that does not match this application's expected GHCR package and an immutable digest. Do not accept arbitrary image repositories or rely on `latest`.

High-level flow:

```text
Operator manually starts deploy.yml
              │
              ├── target_environment = Staging / Production
              └── image_ref = ghcr.io/...@sha256:...
                              │
                              ▼
              App job selects its own GitHub Environment
                              │
                              ▼
              Render a temporary runtime .env from app secrets
                              │
                              ▼
              Call the CentralDevOps composite action
                              │
                              ▼
              Validate manifest + image reference
                              │
                              ▼
              Securely transfer deploy inputs to target VPS
                              │
                              ▼
              Pull exact image → validate Compose → start/update service
                              │
                              ▼
              Wait for app health check
                              │
                              ▼
              Register/update Nginx route → nginx -t → reload
                              │
                              ▼
              External smoke test + deployment record
```

Use deployment concurrency keyed by application and environment so two deployments of the same app/environment do not race. Do not cancel a deployment halfway through merely because a newer workflow was triggered.

---

## 6. The central deployment action and the secrets boundary

### 6.1 Why a composite action is recommended now

A composite action runs as a step inside the calling app workflow job. Therefore:

- The app's `deploy.yml` can set `environment: ${{ inputs.target_environment }}` and use the app repository's `vars` and `secrets` for that environment.
- The central action can receive the image reference, app manifest, runtime environment file path, host, and deployment credentials as explicit inputs.
- The shared logic for SSH transfer, directory preparation, image pull, Compose commands, route registration, validation, health checks, and reporting is maintained once in CentralDevOps.
- The action does **not** automatically read secrets from the CentralDevOps repository's `Staging` or `Production` environment. It also cannot directly use the `secrets` context without the caller passing the needed values as inputs.

A reusable workflow is useful when CentralDevOps should own several jobs/runners or its own deployment job/environment. However, if that job declares a CentralDevOps environment, its environment secrets are from CentralDevOps. Caller app environment secrets are not transparently substituted. If app runtime secrets are later moved to a dedicated external secret manager or a centrally managed deployment environment, reevaluate a reusable workflow then. See [GitHub's reusable workflow documentation](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) and [composite action/reusable workflow comparison](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations).

### 6.2 Deployment credentials: recommended options

Use a **separate, deployment-only account/key**. Never pass the Ansible admin key into application repositories.

Preferred when you have a GitHub organization:

- Store separate `STAGING_DEPLOY_SSH_KEY` and `PRODUCTION_DEPLOY_SSH_KEY` organization secrets.
- Limit each secret's repository access to the specific approved app repositories.
- Keep production and staging hosts/keys separate.
- The app `Staging`/`Production` environment still controls the job gate and application secrets.
- Keep in mind organization secrets are not themselves environment-scoped; only expose them to trusted repositories and protect workflow changes/branches.

If organization secrets are unavailable, use environment-scoped deploy keys in each app repository. This duplicates a narrowly scoped credential but is safer than reusing the administrator credential.

For each VPS, pin the expected SSH host key in a known-hosts value/secret and use strict host-key checking. Do not blindly trust a fresh `ssh-keyscan` result from the same deployment connection as proof of server identity.

### 6.3 GHCR authentication on the VPS

If packages are private, the VPS needs permission to pull them. Provision a dedicated read-only package credential to the host through Ansible, with restrictive file permissions and an explicit rotation procedure. Keep it separate from the deployment SSH key. Avoid printing registry credentials or `.env` contents in workflow logs.

If practical, configure package access so the intended app image/package is available to the relevant deployment host and token. Public packages do not require host registry authentication, but make packages public only if that is an intentional security decision.

### 6.4 Example interface for the composite action

The central action should expose stable, purpose-level inputs similar to:

```yaml
# CentralDevOps/.github/actions/deploy-compose/action.yml
name: Deploy application with Docker Compose
inputs:
  app_name: { required: true, description: "Stable application slug" }
  target_environment: { required: true, description: "Staging or Production" }
  image_ref: { required: true, description: "Immutable GHCR image reference" }
  deploy_host: { required: true, description: "Target host or private address" }
  ssh_user: { required: true, description: "Deployment account" }
  ssh_private_key: { required: true, description: "Deployment-only SSH key" }
  ssh_known_hosts: { required: true, description: "Pinned SSH host key entry" }
  compose_file: { required: true, description: "Application Compose file" }
  manifest_file: { required: true, description: "Environment-specific deployment manifest" }
  runtime_env_file: { required: true, description: "Path to temporary .env file" }
runs:
  using: composite
  steps:
    # Implement validation, SSH setup, secure file transfer, remote deployment,
    # route registration, health checks, and a deployment summary here.
    # Never echo private key material, tokens, or runtime .env contents.
    - shell: bash
      run: echo "Implement the deployment steps for this action interface"
```

This is the **contract/interface**, not a fully implemented production action. Replace the placeholder step with reviewed scripts and tests before using it. Validate every input, particularly `app_name`, `target_environment`, image repository and digest. Keep remote deployment code root-owned or otherwise protected from modification by the deployment user.

---

## 7. Example application workflow definitions

The following snippets are implementation examples, not drop-in files. Pin third-party actions and the CentralDevOps action to reviewed commit SHAs in the production versions.

### 7.1 `build.yml` pattern

```yaml
name: Build image

on:
  workflow_dispatch:
    inputs:
      source_ref:
        description: Branch, tag, or commit to build
        required: true
        default: main
        type: string

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout selected source ref
        uses: actions/checkout@v6
        with:
          ref: ${{ inputs.source_ref }}

      - name: Record the checked-out source commit
        id: source
        shell: bash
        run: echo "commit=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/example-org/customer-builder:sha-${{ steps.source.outputs.commit }}
          labels: |
            org.opencontainers.image.source=https://github.com/${{ github.repository }}
            org.opencontainers.image.revision=${{ steps.source.outputs.commit }}

      - name: Publish immutable image reference in summary
        env:
          IMAGE_DIGEST: ${{ steps.build.outputs.digest }}
          GIT_COMMIT: ${{ steps.source.outputs.commit }}
          SOURCE_REF: ${{ inputs.source_ref }}
        run: |
          set -euo pipefail
          IMAGE_REF="ghcr.io/example-org/customer-builder@${IMAGE_DIGEST}"
          {
            echo "## Built image"
            echo
            echo "- Image reference: \\`${IMAGE_REF}\\`"
            echo "- Source ref: \\`${SOURCE_REF}\\`"
            echo "- Commit: \\`${GIT_COMMIT}\\`"
          } >> "$GITHUB_STEP_SUMMARY"
          printf '{"image_ref":"%s","git_commit":"%s","source_ref":"%s"}\n' \
            "$IMAGE_REF" "$GIT_COMMIT" "$SOURCE_REF" > build-metadata.json

      - name: Upload build metadata
        uses: actions/upload-artifact@v4
        with:
          name: build-metadata
          path: build-metadata.json
          if-no-files-found: error
```

Replace `example-org/customer-builder` with the actual lowercase package path. The example computes the commit from the checked-out source so a manually selected `source_ref` is not accidentally tagged with the workflow dispatch branch's SHA. Configure package access so the deployment host can pull this package.

### 7.2 `deploy.yml` pattern

```yaml
name: Deploy image

on:
  workflow_dispatch:
    inputs:
      target_environment:
        description: Environment to deploy into
        required: true
        type: choice
        options:
          - Staging
          - Production
      image_ref:
        description: Full GHCR ref, e.g. ghcr.io/example-org/customer-builder@sha256:...
        required: true
        type: string

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.target_environment }}
    concurrency:
      group: deploy-${{ github.repository }}-${{ inputs.target_environment }}
      cancel-in-progress: false
    steps:
      - name: Checkout app deployment files
        uses: actions/checkout@v6

      - name: Render runtime environment file
        shell: bash
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          AUTH_SECRET: ${{ secrets.AUTH_SECRET }}
          PUBLIC_API_ORIGIN: ${{ vars.PUBLIC_API_ORIGIN }}
        run: |
          set -euo pipefail
          mkdir -p .deploy-tmp
          umask 077
          {
            printf 'DATABASE_URL=%s\n' "$DATABASE_URL"
            printf 'AUTH_SECRET=%s\n' "$AUTH_SECRET"
            printf 'PUBLIC_API_ORIGIN=%s\n' "$PUBLIC_API_ORIGIN"
          } > .deploy-tmp/runtime.env
          chmod 600 .deploy-tmp/runtime.env

      - name: Deploy with CentralDevOps
        uses: example-org/CentralDevOps/.github/actions/deploy-compose@REPLACE_WITH_REVIEWED_COMMIT_SHA
        with:
          app_name: customer-builder
          target_environment: ${{ inputs.target_environment }}
          image_ref: ${{ inputs.image_ref }}
          deploy_host: ${{ vars.DEPLOY_HOST }}
          ssh_user: ${{ vars.DEPLOY_USER }}
          ssh_private_key: ${{ secrets.DEPLOY_SSH_PRIVATE_KEY }}
          ssh_known_hosts: ${{ secrets.DEPLOY_SSH_KNOWN_HOSTS }}
          compose_file: compose.yml
          manifest_file: deploy/${{ inputs.target_environment == 'Staging' && 'staging' || 'production' }}.yml
          runtime_env_file: .deploy-tmp/runtime.env
```

Notes:

- This example assumes the SSH deploy key is available to the app job as `secrets.DEPLOY_SSH_PRIVATE_KEY`. That can be an environment secret in each app environment, or you can adapt the workflow to use carefully restricted organization-level deploy secrets. If using different keys for staging and production, select the matching one explicitly.
- The action must validate the `image_ref` against the expected package for this repository before executing a remote pull.
- The environment-specific manifest should be checked into the app repo and must not contain secrets.
- Each app maps its own required secrets into `runtime.env`; CentralDevOps centralizes safe transfer/deployment mechanics, not the app's business-specific environment variable names.
- The runner-side `.deploy-tmp` directory must not be uploaded as a general artifact or included in debug output. Delete it at the end of the job if needed.
- Keep `workflow_dispatch` deployments restricted to trusted branches, especially for production. Required reviewers/branch policies depend on GitHub plan and repository visibility.

---

## 8. Application configuration and Docker Compose

### 8.1 App-owned deployment manifest

The app repo declares the intended hostname and container contract. For example:

```yaml
# deploy/staging.yml
app:
  name: customer-builder
  service: app
  container_port: 3000
  edge_alias: customer-builder-staging

routing:
  enabled: true
  domain: builder-staging.example.com
  tls: true

health:
  path: /health
  timeout_seconds: 90
```

A production manifest would contain its production domain/alias. These are examples, not live DNS records. CentralDevOps should validate the manifest against a schema, check app slug/domain uniqueness, reject unsafe values, and render the final Nginx configuration using its own trusted template.

### 8.2 Compose conventions

The app repo owns `compose.yml` because it knows which services belong to the app. It should refer to the immutable image passed by the workflow and use explicit Docker networks.

Example of the relevant shape:

```yaml
services:
  app:
    image: ${IMAGE_REF:?IMAGE_REF must be provided}
    restart: unless-stopped
    env_file:
      - .env
    expose:
      - "3000"
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:3000/health || exit 1"]
      interval: 15s
      timeout: 3s
      retries: 5
      start_period: 20s
    networks:
      edge:
        aliases:
          - ${EDGE_ALIAS:?EDGE_ALIAS must be provided}
      private: {}

  db:
    image: postgres:16
    restart: unless-stopped
    # Configure a persistent volume, database credentials, and backups.
    # Do not publish PostgreSQL to the public host interface.
    networks:
      - private

networks:
  edge:
    external: true
    name: edge
  private:
    internal: true
```

Adapt the database section to the actual app, and pin production database image versions. The app's runtime `.env` and the Compose interpolation variables (for example `IMAGE_REF` and `EDGE_ALIAS`) may be separate files in the finalized deployment script. Validate the rendered config with `docker compose config` before changing the running app.

Important networking points:

- CentralDevOps creates the external `edge` network during VPS configuration. If Compose declares it with `external: true`, Compose expects it to already exist and will fail if it does not.
- Nginx and the app container must share the `edge` network for Nginx to route to the app by Docker DNS alias.
- Do not publish app or PostgreSQL ports to the public host interface merely to make them reachable from Nginx.
- `internal: true` networks block ordinary external network access. Make sure a service that needs outbound API calls has an appropriate non-internal network as well.
- A Docker network is local to a Docker host. It does not connect containers on different VPS instances.

### 8.3 Runtime files on the VPS

Use predictable, per-app/per-environment directories, for example:

```text
/opt/apps/customer-builder/staging/
├── compose.yml
├── .env                 # app runtime secrets; mode 0600
├── compose.env           # image ref and deployment interpolation values
└── deployment.json       # deployed digest and metadata; no secrets

/opt/apps/customer-builder/production/
...

/opt/centraldevops/nginx/conf.d/
├── customer-builder-staging.conf
└── customer-builder-production.conf
```

Protect ownership and permissions. Never commit `.env` files, print them, upload them to ordinary CI artifacts, or include them in deployment summaries.

---

## 9. Routing: app declares, CentralDevOps implements

Routing has three separate responsibilities.

### 9.1 DNS provider

Create/update the DNS record for each domain so it points to the public IP (or load balancer) in front of Nginx. Change DNS when a hostname or destination changes. DNS is not a substitute for application health checks or an internal load balancer.

### 9.2 Application repository

Declare the desired route in `deploy/staging.yml` and `deploy/production.yml`: domain, internal port, service alias, TLS requirement, and health endpoint. Keep the manifest free of credentials.

### 9.3 CentralDevOps

Own the infrastructure implementation:

- Nginx role and trusted templates.
- Route registration/deregistration scripts.
- Domain and app-slug validation.
- TLS provisioning/renewal and certificate paths.
- `nginx -t` validation and reload.
- Health/smoke checks and deployment rollback behavior.

The app workflow must not write an arbitrary Nginx server block directly into production without validation. CentralDevOps should render a deterministic file per app/environment, validate the full Nginx configuration, and reload Nginx only if validation succeeds.

### 9.4 Route activation sequence

1. Validate the manifest and verify the requested hostname maps to this app/environment.
2. Pull the selected image and launch/update the application.
3. Wait for the app's health check to pass.
4. Render/update the Nginx route using the CentralDevOps template.
5. Run `nginx -t`; on failure, retain the last known-good route and fail the deployment.
6. Reload Nginx only after validation passes.
7. Run an HTTPS smoke test against the public hostname.
8. Write a deployment record with the new and previous image digests.

For initial low-traffic use, ordinary Compose replacement may cause a brief interruption. If zero/near-zero downtime becomes a requirement, add a blue/green rollout for stateless app containers: start the inactive slot, health-check it, switch the validated Nginx upstream, then retire the old slot. Keep stateful services (especially PostgreSQL) outside the duplicated app slots.

### 9.5 TLS

Use HTTPS everywhere. CentralDevOps should own certificate issuance/renewal and Nginx TLS configuration. Let’s Encrypt with Certbot or another well-supported ACME integration is reasonable; use DNS-01 with a narrowly scoped DNS API token where required by your DNS/proxy arrangement. Never put the DNS API token in an app manifest.

---

## 10. Security baseline

### Host access and operating system

- Use SSH public-key authentication; disable password login/root SSH only after verifying the intended access path.
- Use separate named admin and deployment identities.
- Restrict inbound ports to what is necessary. Usually public `80/443` for the proxy and `22` for SSH; restrict SSH source IPs or use a VPN where practical.
- Apply security updates and login-rate limiting; use fail2ban or an equivalent only as part of a tested configuration.
- Keep PostgreSQL and backend app ports off the public interface.
- Keep backups and runtime environment files readable only by the intended service/admin account.

### Docker-specific controls

- Do not expose the Docker API socket on a public network.
- Treat access to the Docker socket or the `docker` group as effectively root-level access. A compromised deployment key/user with unrestricted Docker access can take over the host.
- Prefer a narrow deployment command/script and dedicated deploy identity over sharing admin SSH credentials. If the deploy user is in the `docker` group for the initial implementation, explicitly treat the key and workflow as privileged production access and protect their use accordingly.
- Avoid publishing app/database ports unless required. Docker's published-port firewall behavior can bypass assumptions made from UFW alone; do not rely on UFW alone to protect accidentally published container ports.
- Do not put credentials in image layers, build arguments, Docker labels, or source-controlled Compose files.

### GitHub Actions controls

- Use least-privilege workflow permissions (`contents: read`, `packages: write` for build; minimal permissions for deploy).
- Restrict production deployment to trusted refs/branches and approved users.
- Use `concurrency` to prevent concurrent deploys of the same app/environment.
- Pin CentralDevOps and third-party actions to reviewed SHAs in production.
- Validate user-supplied image refs and deployment manifest data. Never interpolate arbitrary input into privileged shell commands without strict validation.
- Keep secrets out of logs and artifacts.
- Keep Ansible administrative keys, application deployment keys, and GHCR read credentials separate.

---

## 11. Monitoring, logs, backups, and rollback

### 11.1 Monitoring

Use Grafana Cloud as the central place for dashboards/alerts, with Grafana Alloy or a suitable collector on each VPS. Avoid installing a complete, isolated Grafana server on every host just to monitor it.

Monitor at minimum:

- CPU, RAM, disk use/inodes and network throughput.
- VPS availability and SSH connectivity.
- Docker/container restarts and health state.
- Application HTTP availability, latency and 5xx rate.
- Nginx errors and TLS certificate expiry.
- PostgreSQL availability, connection count, disk usage and backup success if installed.
- Backup age and failed backup jobs.

Create alerts for disk pressure, recurring container restarts, broken app health checks, certificate expiry, backup failures, and persistent elevated 5xx rates. Logs and metrics should still be available centrally if a VPS becomes unavailable.

### 11.2 Backups

- Back up PostgreSQL using database-aware backups such as `pg_dump` (and/or appropriate physical backups for the recovery objective).
- Copy backups off the VPS to separate object storage or a separate backup destination; a local backup on the same disk does not protect against disk/host loss.
- Define retention, encryption, access controls, and backup monitoring.
- Test restores on a schedule. A successful backup command without a tested restore is not enough.
- Use VPS snapshots as an additional recovery layer, not as the only database backup.
- Keep user uploads and durable files in object storage rather than on a single app container's writable filesystem.

### 11.3 Rollback

Every deployment record should include:

```json
{
  "app": "customer-builder",
  "environment": "Staging",
  "image_ref": "ghcr.io/example-org/customer-builder@sha256:...",
  "previous_image_ref": "ghcr.io/example-org/customer-builder@sha256:...",
  "git_commit": "...",
  "deployed_at_utc": "...",
  "workflow_run_url": "..."
}
```

On failure, do not switch the route to an unhealthy app. Keep or restore the prior image/route where possible. The simplest manual rollback is to run `deploy.yml` again using the previous known-good digest. Database schema changes need backward-compatible migration/rollback planning; restoring an old container alone cannot safely reverse every data migration.

---

## 12. VPS scaling roadmap

### Phase 1 — One VPS, low traffic

A single `all-in-one` VPS is acceptable as a cost-conscious starting point if its shared failure domain and limited capacity are understood. It may host Nginx, app containers, and PostgreSQL for small workloads. Use persistent volumes, off-host backups, host monitoring, and strict network boundaries from day one.

### Phase 2 — Separate stateful components

As usage/reliability requirements grow:

- Move PostgreSQL to a dedicated database VPS or managed database.
- Restrict database access to private networking/VPN and authorized app hosts.
- Move uploads to object storage.
- Keep Grafana Cloud and alerting independent of the app VPS.

### Phase 3 — Multiple app VPS instances

Before adding app instances, ensure:

- App processes are stateless or externalize sessions/state.
- All instances use the same immutable image digest for a release.
- Sessions, uploads, and other durable data are not stored only on a single instance.
- A load balancer routes to healthy instances.
- Deploy/rollback automation knows which hosts should receive the release.
- Observability is centralized.

At that point, add a provisioning layer such as OpenTofu/Terraform to create VMs through the provider API, feed resulting addresses/metadata to Ansible, apply a chosen profile, verify health, and register the host with the load balancer. Only after this lifecycle works reliably should you investigate autoscaling or a cluster scheduler.

**Networking warning:** Docker's `edge` bridge network is local to a single VPS. If Nginx is on a different VPS from the app, it cannot reach that app using the local Docker DNS alias. Route to a private IP/port over private networking or a VPN, or adopt a suitable overlay/service-discovery design. Avoid exposing backend service ports to the public internet just to connect separate hosts.

You do not need Kubernetes or Docker Swarm at the beginning. Independent Compose hosts behind a load balancer can be a sensible intermediate step if app state is externalized and deployment automation targets each instance correctly.

---

## 13. Operational runbooks

### First setup of a new VPS

```text
Create VPS manually in provider
  → verify initial SSH access
  → run bootstrap-vps.yml
  → verify the new admin access in a second SSH session
  → run configure-vps.yml with the required profile
  → run verify-vps.yml
  → deploy a non-critical test app
  → verify HTTPS, logs, alerts, and backups
```

### Build and deploy an application

```text
Run app build.yml manually with source_ref
  → inspect test/build result
  → copy exact ghcr.io/...@sha256:... image_ref from the summary
  → run app deploy.yml manually with target_environment + image_ref
  → environment gates/secrets become available
  → CentralDevOps action validates and deploys the immutable image
  → health/smoke checks pass
  → verify deployment record and monitoring
```

### Change VPS configuration

```text
Update and review Ansible roles/playbooks
  → run configure-vps.yml against Staging
  → run verify-vps.yml
  → promote the reviewed change to Production
  → run configure-vps.yml against Production
  → run verify-vps.yml
```

### App rollout fails

```text
Stop route activation if health/config validation fails
  → retain previous known-good route/image where possible
  → inspect workflow logs and centralized app/host logs
  → redeploy the previous known-good image digest if required
  → record cause and follow-up remediation
```

---

## 14. Implementation order

Build a reliable vertical slice before implementing every infrastructure component.

1. **Repository foundation:** create the CentralDevOps structure, Ansible config, inventories, and environment/secret naming standard.
2. **Host security:** implement and test `common`, `users`, `ssh_hardening`, and `firewall`; prove a fresh disposable VPS remains accessible after hardening.
3. **Docker profile:** install Docker Engine/Compose, create application directories, and create the shared `edge` network on hosts that will run Nginx/apps.
4. **Verification:** implement `verify-vps.yml` early so each subsequent infrastructure role has explicit health checks.
5. **Nginx and TLS:** deploy the proxy, test a single route, verify `nginx -t` and certificate renewal, and confirm failed validation cannot break current routes.
6. **First application build:** implement `build.yml`, push an image to GHCR, and verify the workflow outputs the actual immutable digest.
7. **First application deployment:** implement the app `deploy.yml` input contract and CentralDevOps `deploy-compose` composite action. Deploy to Staging, validate health and route registration, then deploy to Production.
8. **Secrets and safe rollback:** restrict deployment credentials, render `.env` securely, verify no secret leakage, and test redeployment of a previous digest.
9. **Observability and backups:** add host/app monitoring, alerts, off-host backups, and a restore test before treating the host as production-ready.
10. **Scale preparation:** externalize uploads/session state, separate PostgreSQL when justified, and add OpenTofu/Terraform plus load-balancer registration only when additional hosts are actually needed.

---

## 15. Final recommendations

The final design should preserve these ownership boundaries:

- **The application repository chooses what to build and which immutable image/environment to deploy.** It owns its `build.yml`, `deploy.yml`, Compose definition, runtime key mapping, and environment-specific deployment manifest.
- **CentralDevOps owns how the deployment is executed and how the server is operated.** It owns the shared deploy action/scripts, host configuration, Ansible roles, Nginx route rendering/validation, and verification routines.
- **GHCR owns the image artifact; the digest is the release identity.** A Git commit SHA is useful metadata, but the pushed registry digest is the exact image to deploy.
- **Infrastructure workflows and application workflows are separate.** Do not rerun VPS bootstrap/configuration just to release a new app image.
- **Use a composite action now because the caller app job needs access to its own environment secrets.** Revisit a reusable workflow if runtime secret ownership changes or CentralDevOps needs to own a multi-job deployment graph.
- **Do not overbuild for hypothetical scale.** Make the single-VPS workflow repeatable, secure, observable, recoverable, and digest-based. Add more VPS instances only after the app can run statelessly across them.

## References

- [GitHub — Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub — Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [GitHub — Reusable workflow configurations and composite actions](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations)
- [GitHub — Working with the container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub — Publishing and installing a package with GitHub Actions](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions)
- [Ansible — Playbooks](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks.html)
- [Docker — Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker — Compose in production](https://docs.docker.com/compose/how-tos/production/)
- [Nginx — Server names](https://nginx.org/en/docs/http/server_names.html)
