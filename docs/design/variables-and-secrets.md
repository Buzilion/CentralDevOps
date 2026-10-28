# GitHub Variables and Secrets (v1)

| Item | Value |
|---|---|
| Status | Draft for review |
| Created | 2026-10-29 |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` and the module PRDs in the same folder (`SEC`, `REL`, `DEP`, `INF`, `REG`, `RTE`, `DB`, `BKP`, `OBS`) |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§4 naming and secrets, §13.2 backups). "§" references below point to it |

This document lists every GitHub variable and secret the platform needs: its name, what it is for, and how and where to get the value. Only values that a workflow actually consumes are listed (SEC-02, NFR-23). Items that the design does not name but that the design needs in practice are in section 7 and are marked as proposals.

---

## 1. Overview

### 1.1 Where values live

| Level | Where to set it in GitHub | Holds |
|---|---|---|
| CentralDevOps repository | Settings → Secrets and variables → Actions → Variables | Configuration that has the same value in both Environments |
| CentralDevOps Environment (`Staging`, `Production`) | Settings → Environments → *name* → Environment variables / Environment secrets | Values that differ per Environment, and all server, registry, backup and monitoring credentials (SEC-06) |
| App repository Environment (`Staging`, `Production`) | Same path, in each app repository | App runtime configuration and secrets (SEC-08) |
| Organization | Org Settings → Secrets and variables → Actions, repository access **Selected repositories** | Only the dispatch GitHub App credentials (SEC-04, SEC-10). Org-level values are not Environment-scoped |

### 1.2 Naming rules (SEC-02, SEC-03)

1. `SCREAMING_SNAKE_CASE`, with an ownership prefix: `ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_`, `MONITORING_`.
2. The **same name in both Environments**; the Environment supplies the value. Never `STAGING_` or `PRODUCTION_` names, never a `GITHUB_` prefix (GitHub rejects it), never generic names such as `TOKEN` or `KEY`.
3. Credentials are secrets. Ordinary configuration (paths, domains, public keys, host key pins) is a variable or a committed file.
4. Per-host facts (address, user—including the provider-supplied initial SSH username—groups, ports, private IP, capacity budget) are never GitHub variables. They live in `inventories/<env>/` or the registry `apps/<app>/<env>.yml`.

### 1.3 Quick reference

"Differs" means the value must be different in `Staging` and `Production`.

| Repository | Name | Kind | Level | Differs | Section |
|---|---|---|---|---|---|
| CentralDevOps | `ANSIBLE_CONFIG_PATH` | Variable | Repository | No | 3.1 |
| CentralDevOps | `ANSIBLE_REQUIREMENTS_PATH` | Variable | Repository | No | 3.1 |
| CentralDevOps | `ANSIBLE_PLAYBOOKS_PATH` | Variable | Repository | No | 3.1 |
| CentralDevOps | `DEPLOY_REGISTRY_DIR` | Variable | Repository | No | 3.1 |
| CentralDevOps | `ANSIBLE_INVENTORY_PATH` | Variable | Environment | Yes | 3.2 |
| CentralDevOps | `DEPLOY_HEALTHCHECK_TIMEOUT` | Variable | Environment | No (default) | 3.2 |
| CentralDevOps | `MONITORING_ENDPOINT` | Variable | Environment | Per stack | 3.2 |
| CentralDevOps | `BACKUP_RETENTION_DAYS` | Variable | Environment | No (default) | 3.2 |
| CentralDevOps | `BACKUP_S3_ENDPOINT` | Variable | Environment | Per bucket | 3.2 |
| CentralDevOps | `BACKUP_S3_REGION` | Variable | Environment | Per bucket | 3.2 |
| CentralDevOps | `BACKUP_S3_BUCKET` | Variable | Environment | Per bucket | 3.2 |
| CentralDevOps | `ANSIBLE_SSH_PRIVATE_KEY` | Secret | Environment | **Yes** | 4.1 |
| CentralDevOps | `VPS_INITIAL_ACCESS_PASSWORD` | Secret | Environment | **Yes; temporary per VPS** | 4.10 |
| CentralDevOps | `DEPLOY_SSH_PRIVATE_KEY` | Secret | Environment | **Yes** | 4.3 |
| CentralDevOps | `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | Secret | Environment | **Yes** | 4.4 |
| CentralDevOps | `GHCR_PULL_TOKEN` | Secret | Environment | Recommended | 4.5 |
| CentralDevOps | `BACKUP_RESTIC_PASSWORD` | Secret | Environment | **Yes** | 4.6 |
| CentralDevOps | `BACKUP_S3_ACCESS_KEY_ID` | Secret | Environment | Recommended | 4.7 |
| CentralDevOps | `BACKUP_S3_SECRET_ACCESS_KEY` | Secret | Environment | Recommended | 4.7 |
| CentralDevOps | `MONITORING_GRAFANA_CLOUD_TOKEN` | Secret | Environment | Recommended | 4.8 |
| CentralDevOps | `ANSIBLE_VAULT_PASSWORD` | Secret | Environment | Yes | 4.2 (only if Vault is used) |
| App repositories | `DEPLOY_DISPATCH_APP_ID` | Secret | Organization (selected repos) or Environment | No | 5.3 |
| App repositories | `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | Secret | Organization (selected repos) or Environment | No | 5.3 |
| Each app | `APP_*` (for example `APP_PUBLIC_API_ORIGIN`) | Variable | Environment | App-defined | 5.1 |
| Each app | `APP_*` (for example `APP_AUTH_SECRET`, `APP_DB_PASSWORD`) | Secret | Environment | **Yes** | 5.2 |

---

## 2. Prerequisite: Environments and protection rules

Create exactly two Environments, `Staging` and `Production`, in CentralDevOps and in every app repository (SEC-01). Do not create an Environment per VPS.

| Repository | Environment | Required reviewers | Deployment branches |
|---|---|---|---|
| CentralDevOps | `Staging` | None (DEP-08) | `main` only (§8.3 #1, DEP-16) |
| CentralDevOps | `Production` | **Yes**: the repository owner initially (SEC-05); the deployment team replaces or joins them later (SEC-18, open question Q6) | `main` only |
| Each app | `Staging` | None | `main` (or release branches) |
| Each app | `Production` | None by default, so a deployment has exactly one approval, in CentralDevOps (SEC-15) | `main` (or release branches) |

Record the GitHub plan and repository-visibility assumption in the README, because Environment secrets and variables depend on it (SEC-17).

---

## 3. CentralDevOps variables

Variables are plain configuration and are visible in logs. Never put a credential here (SEC-03).

### 3.1 Repository-level variables

Same value in both Environments.

| Name | Value | Description | How to get the value |
|---|---|---|---|
| `ANSIBLE_CONFIG_PATH` | `ansible.cfg` | Ansible configuration file used by the infrastructure workflows | Fixed by the repository layout (§5.1). Change only if the file moves |
| `ANSIBLE_REQUIREMENTS_PATH` | `requirements.yml` | Ansible collections and roles installed before a run | Same |
| `ANSIBLE_PLAYBOOKS_PATH` | `playbooks` | Directory with `bootstrap.yml`, `configure.yml`, `verify.yml` and `restore-database.yml` | Same |
| `DEPLOY_REGISTRY_DIR` | `apps` | Root of the app registry; files are `apps/<app>/<env>.yml` | Same |

Note on `DEPLOY_REGISTRY_DIR`: design §4.3 lists it as an Environment variable. It is set at repository level here because the `authorize` job of `deploy-app.yml` declares no Environment (§8.2), and a job without an Environment cannot read Environment-scoped variables. The registry must be read in that job. A repository-level variable is also readable by the `deploy` job, so nothing is lost.

### 3.2 Environment-level variables

Set in both `Staging` and `Production`.

| Name | Staging | Production | Description | How to get the value |
|---|---|---|---|---|
| `ANSIBLE_INVENTORY_PATH` | `inventories/staging/hosts.yml` | `inventories/production/hosts.yml` | Inventory used by infrastructure operations and by the `deploy` job. Derived from the selected Environment, never typed by the operator (INF-08), so a Staging run cannot reach a Production host | Path of the committed inventory (§6.4). Must point at the inventory of the same Environment |
| `DEPLOY_HEALTHCHECK_TIMEOUT` | `90` | `90` | Seconds the deployment waits for the container health check before it rolls back (DEP-11, DEP-12) | Default from the design. Raise only for an app with a proven slow start, and keep the typical deployment within 5 minutes (NFR-06) |
| `MONITORING_ENDPOINT` | Grafana Cloud endpoint | Grafana Cloud endpoint | Non-secret URL the collector (Grafana Alloy) sends metrics and logs to (OBS-01) | Grafana Cloud portal → your stack → the connection details for metrics and logs (or the OpenTelemetry gateway). Also see section 7 for the account/user ID the collector needs |
| `BACKUP_RETENTION_DAYS` | `14` | `14` | Days of Restic snapshots kept before pruning (BKP-06) | Default from the design. Configurable per Environment |
| `BACKUP_S3_ENDPOINT` | Sumopod S3 endpoint URL | Sumopod S3 endpoint URL | Endpoint of the backup bucket (BKP-03) | Sumopod console → S3 object storage (a separate product from the VPS) |
| `BACKUP_S3_REGION` | Sumopod S3 region | Sumopod S3 region | Region of the backup bucket | Same |
| `BACKUP_S3_BUCKET` | Bucket name | Bucket name | Bucket that holds the Restic repository of the Environment | Same. The design uses one bucket with one Restic repository per Environment; see section 7 for how the two repositories are kept apart |

---

## 4. CentralDevOps secrets (Environment scope)

All secrets in this section are **Environment secrets** of CentralDevOps (SEC-06). Do not store them at repository or organization level.

General handling:

- Generate every key or password on a trusted workstation, store the recovery copy where stated, set the GitHub secret, then delete the local plaintext files.
- Use a separate value for `Staging` and `Production` wherever the table in section 1.3 says so. A Staging credential must never open a Production resource.
- If key files pass through Windows editors, make sure they keep LF line endings. CRLF makes OpenSSH reject a private key.
- Secret values are masked in logs but are not to be echoed, written to artifacts or passed as workflow inputs (SEC-12, NFR-12).

### 4.1 `ANSIBLE_SSH_PRIVATE_KEY`

- **Description:** Private key of the admin automation account on the VPS. On a fresh host, bootstrap first connects with the provider username and initial-access password; after installing the matching public key, Ansible uses this key for the independent second login and later operations.
- **Used by:** `bootstrap-vps.yml`, `configure-vps.yml`, `verify-vps.yml`. Never by `deploy-app.yml` (SEC-07, INF-13).
- **Differs per Environment:** Yes.
- **How to get it:**
  1. Generate one ed25519 key pair per Environment, with an empty passphrase because the key is used unattended: `ssh-keygen -t ed25519 -C "cdo-admin-staging" -f cdo-admin-staging` (and `cdo-admin-production`).
  2. Commit the **public** key to the Environment's inventory data (section 9) so `bootstrap-vps.yml` installs it on the admin account.
  3. Set the whole private key file, including the `BEGIN`/`END` lines, as the secret. Delete the local copy.
- **Notes:** Keep an encrypted copy in the password manager only if operators need the admin identity outside GitHub (for example the database SSH tunnel, DB-07). Rotation: section 11.

### 4.2 `ANSIBLE_VAULT_PASSWORD` (only if Ansible Vault is used)

- **Description:** Password that decrypts Ansible Vault files.
- **Used by:** Infrastructure workflows.
- **Differs per Environment:** Yes.
- **How to get it:** Generate a random password of at least 32 characters in the password manager. Store the recovery copy there and set the GitHub secret.
- **Notes:** The PRDs do not require Vault. Do not create this secret unless a role actually reads Vault-encrypted files (§4.4 "only if Ansible Vault is used").

### 4.3 `DEPLOY_SSH_PRIVATE_KEY`

- **Description:** Private key of the **restricted deploy account** on the VPS. That account is not in the `docker` group and may only run the two root-owned scripts `centraldevops-deploy` and `centraldevops-route` through sudo (INF-12, §8.5).
- **Used by:** The `deploy` job of `deploy-app.yml`, after request authorization and, for Production, approval.
- **Differs per Environment:** Yes. A different key from the admin key, and a different account.
- **How to get it:**
  1. Generate one ed25519 pair per Environment: `ssh-keygen -t ed25519 -C "cdo-deploy-staging" -f cdo-deploy-staging` (and `cdo-deploy-production`), empty passphrase.
  2. Commit the **public** key to the Environment's inventory data (section 9). The `deploy_runtime` role installs it in the deploy account's `authorized_keys` with the `restrict` option. Do not use a `from=` restriction, because GitHub-hosted runner addresses are not stable (§8.5).
  3. Set the private key as the secret and delete the local file.
- **Notes:** Never commit a private key file (SEC-06). The Staging key must fail to log in to a Production host, and the reverse. Only CentralDevOps holds this key; no app repository does (SEC-09, NFR-10).

### 4.4 `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`

- **Description:** `age` private key that decrypts the sealed bundle (runtime env, Compose file, manifest) an app sends with its deployment request (§7.2, REL-07). It exists in the `deploy` job only after Environment approval.
- **Used by:** The `deploy` job of `deploy-app.yml`.
- **Differs per Environment:** Yes. A bundle sealed for one Environment cannot be opened with the other's key.
- **How to get it:**
  1. Install `age` (for example `winget install FiloSottile.age`) and run `age-keygen -o staging.agekey` (and `production.agekey`).
  2. Commit the printed **public** key (`age1…`) as `deployment/keys/staging.age.pub` and `deployment/keys/production.age.pub`.
  3. Set the content of the key file (the `AGE-SECRET-KEY-1…` line) as the secret and delete the local file.
- **Notes:** No recovery copy is needed, because bundles are created per deployment. If the key is lost, generate a new pair and follow the rotation in section 11. During a rotation the pinned `request-deploy` action must accept two recipients.

### 4.5 `GHCR_PULL_TOKEN`

- **Description:** Read-only token that lets each VPS pull private images from GHCR (SEC-11). `configure-vps.yml` installs it on the host as a root-only file; the deploy script uses it for `docker pull` by digest. Apps never see it (SEC-09).
- **Used by:** `configure-vps.yml`.
- **Differs per Environment:** Recommended, so one token can be revoked without affecting the other Environment.
- **How to get it:**
  1. Use a dedicated machine user (not a person's account) that has read access to the app packages.
  2. GitHub → that user's Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate new token. GHCR does not accept fine-grained tokens.
  3. Select only the `read:packages` scope and set an expiry. If the organization enforces SAML SSO, authorize the token for the organization.
  4. Make sure the machine user can read every package (repository access, or the package's access settings).
  5. Set the token as the secret.
- **Notes:** The token must have no write scope. Rotation: section 11.

### 4.6 `BACKUP_RESTIC_PASSWORD`

- **Description:** Password of the encrypted Restic repository of the Environment (BKP-03). All backups are encrypted client-side with it. `configure-vps.yml` installs it on the host as a root-readable secret.
- **Used by:** `configure-vps.yml` (backup role), restore drills and disaster recovery.
- **Differs per Environment:** Yes (BKP-03).
- **How to get it:**
  1. Generate a unique random password of at least 32 characters per Environment, in the organization's password manager (or `openssl rand -base64 48`).
  2. Store the **recovery copy** in the password manager, accessible to at least two authorized operators (BKP-04). Store it in its own entry, **separate from the S3 credentials**, and never in the VPS, the repository or the bucket.
  3. Set the same value as the GitHub secret (the automation copy).
- **Notes:** If this password is lost, the backups are unreadable. Do not rotate it by replacing it; add a new key to the repository first (section 11).

### 4.7 `BACKUP_S3_ACCESS_KEY_ID` and `BACKUP_S3_SECRET_ACCESS_KEY`

- **Description:** Access key pair for the Sumopod S3 bucket that holds the Restic repository (BKP-05). Installed on the host by `configure-vps.yml`.
- **Used by:** `configure-vps.yml` (backup role), restore drills and disaster recovery.
- **Differs per Environment:** Recommended, so a compromised Staging host cannot read or delete Production backups.
- **How to get it:**
  1. Sumopod console → S3 object storage (separate from the VPS product): create the bucket if it does not exist.
  2. Create an access key with the least privilege the provider allows (only that bucket, or only that Environment's path). It must not manage anything else on Sumopod.
  3. Copy the secret access key at creation (it is usually shown once) and set both values as secrets.
  4. Record whether the provider supports server-side encryption and versioning, and enable them if it does (BKP-05, open question Q2).
- **Notes:** Keep these credentials separate from the Restic password and its recovery copy. No single location may hold both (BKP-04). Verify the endpoint with a test backup and an isolated Staging restore before Production (BKP-08).

### 4.8 `MONITORING_GRAFANA_CLOUD_TOKEN`

- **Description:** Least-privilege token the collector on each VPS uses to push metrics and logs to Grafana Cloud (OBS-01).
- **Used by:** `configure-vps.yml` (monitoring_agent role).
- **Differs per Environment:** Recommended, so one Environment's token can be revoked alone.
- **How to get it:**
  1. Grafana Cloud portal → Security → Access Policies → create a policy for your stack, named for example `centraldevops-staging` and `centraldevops-production`.
  2. Give it only the write scopes the collector needs, `metrics:write` and `logs:write`.
  3. Add a token to the policy with an expiry, copy it at creation and set it as the secret.
- **Notes:** The non-secret endpoint is `MONITORING_ENDPOINT` (section 3.2). Watch plan quotas and ingestion (OBS-06, open question Q10).

### 4.9 Caution: secrets are separated by workflow code, not by GitHub scope

GitHub makes every secret of an Environment available to any job that references that Environment. Both `bootstrap-vps.yml` and the `deploy` job of `deploy-app.yml` reference the same Environments. So `ANSIBLE_SSH_PRIVATE_KEY` and `VPS_INITIAL_ACCESS_PASSWORD` are kept away from the deployment workflow only by code: `deploy-app.yml` must never reference them (SEC-07). This is why `.github/workflows/**` is under CODEOWNERS review (SEC-13), why actions are pinned and why workflows are linted (SEC-14). Treat any pull request that touches secret references in workflows as a security change.

### 4.10 `VPS_INITIAL_ACCESS_PASSWORD`

- **Description:** Temporary provider-issued password for the provider username recorded for the host in the selected Environment's inventory. It is used only for the first SSH connection to a fresh VPS; the password is not stored in inventory or passed as a workflow input.
- **Used by:** `bootstrap-vps.yml`, for the initial connection only.
- **Differs per Environment:** Yes. For an Environment with multiple fresh hosts, set it to the target VPS's provider password and bootstrap one host at a time.
- **How to get it:**
  1. Create the VPS in the Sumopod console and retrieve its initial SSH username and password.
  2. Record the username in the host's inventory and set the password as the selected CentralDevOps Environment secret.
- **Notes:** Keep the initial password available while bootstrap creates accounts, applies updates and the base firewall, then installs the admin public key. Verify the independent key-based login before SSH hardening disables root and password login. Delete this secret after that check succeeds; if it fails, do not harden the host.

---

## 5. App repository variables and secrets

Configured in each app repository, in both Environments, except the dispatch credentials in 5.3.

### 5.1 Environment variables: `APP_*`

- **Description:** Non-secret runtime configuration of the app, for example `APP_PUBLIC_API_ORIGIN`. The app's `deploy.yml` writes them into the runtime env file that goes into the sealed bundle.
- **How to get the values:** Defined by the app team. Use the Environment's own value (for example the Staging API URL in `Staging`).
- **Rules:** The runtime env file must contain exactly the keys declared in the manifest's `runtime_env.required`, and none of the reserved keys (DEP-10).

### 5.2 Environment secrets: app-defined

- **Description:** Runtime secrets of the app, for example `APP_AUTH_SECRET` and `APP_DB_PASSWORD`. They stay in the app's Environments and travel only inside the `age`-sealed bundle (SEC-08, REL-07).
- **How to get the values:**
  - Self-generated secrets (session or signing secrets, the database password): generate random values in the password manager, for example `openssl rand -base64 32`. Use a different value per Environment.
  - Third-party credentials: take them from the provider, using test or sandbox credentials in `Staging`.
  - `APP_DB_PASSWORD` is rendered into the runtime key `DB_PASSWORD` (DB-05). On the first deployment the central deployment creates the database role with this password; to rotate it, change the secret and redeploy (DB-04).
- **Rules:**
  - Names start with `APP_` and never with `GITHUB_`. The mapping from secret name to runtime key is in the app's `deploy.yml`.
  - These keys are **reserved** and must not be provided by the app: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `IMAGE_REF`, `EDGE_ALIAS` and any key starting with `CENTRALDEVOPS_`. CentralDevOps injects them.
  - Keep the whole sealed bundle small. The dispatch payload is limited to about 65 KB, so the bundle should stay under about 40 KB (REL-12).
  - Never put secrets in image layers, build arguments, labels or committed Compose files (REG-10).

### 5.3 Dispatch GitHub App credentials

| Name | Kind | Description |
|---|---|---|
| `DEPLOY_DISPATCH_APP_ID` | Secret | ID of the dispatch-only GitHub App |
| `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | Secret | Private key (`.pem`) of that GitHub App |

- **Description:** The app's `deploy.yml` creates a short-lived installation token from these credentials and uses it only to dispatch `deploy-app.yml` in CentralDevOps (SEC-10, REL-09). No PAT and no shared secret is used.
- **Level:** Organization secrets with repository access **Selected repositories**, limited to the app repositories, or per-Environment secrets. Not CentralDevOps itself. Identical in both Environments.
- **How to get them:**
  1. Organization Settings → Developer settings → GitHub Apps → New GitHub App. Name it for example `centraldevops-dispatch`, uncheck **Webhook → Active**, and allow installation only on this organization.
  2. Under Repository permissions grant **Actions: Read and write** and nothing else (repository metadata read is added automatically).
  3. Install the App on the organization with **Only select repositories** and choose **CentralDevOps** only.
  4. Copy the App ID from the App's About page into `DEPLOY_DISPATCH_APP_ID`.
  5. Generate a private key on the App page, set the downloaded `.pem` content as `DEPLOY_DISPATCH_APP_PRIVATE_KEY`, then delete the file.
- **Notes:** `actions: write` technically allows dispatching any CentralDevOps workflow. This residual risk is accepted and mitigated: infrastructure workflows reject the App identity (INF-14), Production needs approval, and a valid OIDC proof is required for every deployment (§4.5). Design v5 §4.5 and SEC-10 treat both values as secrets, so the ID is stored as a secret here. The App ID itself is not sensitive; the older v3 contract kept it as a variable.

---

## 6. Credentials that need no configuration

| Credential | Where it comes from | What to check |
|---|---|---|
| `GITHUB_TOKEN` (automatic, per run) | Issued by GitHub for every run | App `build.yml` pushes the image with `packages: write` (REL-02). App and central workflows declare the least permissions they need (SEC-14). CentralDevOps uses it for `gh attestation verify` when attestation is required (DEP-05). Set the repository default workflow permission to read-only |
| OIDC identity token (per run) | The app's `deploy.yml` requests it with the request-bound audience | The job needs `permissions: id-token: write` and `contents: read` (REL-06, REL-08). No secret is stored |
| Build provenance attestation | `actions/attest-build-provenance` in the app's `build.yml` | The job needs `id-token: write` and `attestations: write` (REL-04). Required for Production digests |

---

## 7. Proposed additions (not named in design v5)

The design leaves these gaps. They are listed so the spec stage can decide; none should be created until a workflow consumes it.

| Proposed name | Kind and level | Why it is needed | How to get the value | Decision |
|---|---|---|---|---|
| `MONITORING_INSTANCE_ID` (name to be confirmed) | Variable, Environment | The collector authenticates to Grafana Cloud with a user (instance) ID plus the token | Grafana Cloud portal → your stack → connection details | If metrics and logs use different endpoints, add one endpoint and one ID per signal |
| `BACKUP_S3_PREFIX` | Variable, Environment | The design uses one bucket with one Restic repository per Environment. A path prefix such as `staging` and `production` keeps the two repositories apart | Chosen by the platform owner | Not needed if each Environment gets its own bucket, or if the backup role derives the path from the Environment |
| `BACKUP_RETENTION_MONTHS` | Variable, Environment | Design §13.2 requires "a few monthly copies", but only `BACKUP_RETENTION_DAYS` exists | Chosen by the platform owner | Depends on open question Q4 |
| `ANSIBLE_CERTBOT_EMAIL` | Variable, Environment | Contact address for the Let's Encrypt account used by the certbot role | A monitored mailbox of the platform owner | Optional; Certbot can register without an email |

---

## 8. Deliberately not configured

| Not configured | Reason |
|---|---|
| `VPS_PROVIDER_API_TOKEN` | Sumopod has no API; VPSs are created manually (§4.4) |
| A DNS API token | DNS is managed manually at Masterweb, and certificates use HTTP-01 only (RTE-03) |
| A PAT or shared secret for dispatching deployments | Forbidden by SEC-10; the dispatch GitHub App is used |
| The deploy SSH key, the admin key, `GHCR_PULL_TOKEN` or any server credential in an app repository | SEC-09, NFR-10 |
| `STAGING_*`, `PRODUCTION_*`, `GITHUB_*` names, or any per-VPS variable such as `SERVER_IP` | SEC-02, SEC-03 |
| A PostgreSQL superuser password | Not stored in GitHub; apps never use a superuser (DB-01) and the roles are created by the deploy script on the host |
| `DEPLOY_STATUS_APP_*` | GitHub Deployments integration is deferred (DEP-21) |

---

## 9. Public values and external stores (not GitHub variables or secrets)

| Item | Where it lives | How to get the value |
|---|---|---|
| SSH host key pins | `inventories/<env>/known_hosts`, reviewed in pull requests (INF-09) | Read the host key fingerprint in the Sumopod console and compare it with the key scanned over SSH. Never trust a fresh `ssh-keyscan` from the same connection |
| Admin and deploy SSH **public** keys | `inventories/<env>/group_vars/all.yml` (proposed location; SEC-03 only requires a variable or a committed file) | The `.pub` files generated in 4.1 and 4.3 |
| `age` public keys | `deployment/keys/staging.age.pub` and `deployment/keys/production.age.pub` | Generated in 4.4 |
| Per-host facts: address, user, groups, private IP, memory budget | `inventories/<env>/hosts.yml`, `group_vars`, `host_vars` | Sumopod console; budget is the physical RAM minus the OS, Docker, Nginx, PostgreSQL and collector reserve (INF-20) |
| Registry: domains, placement, limits, database settings | `apps/<app>/<env>.yml` | Reviewed through CODEOWNERS (SEC-13) |
| Recovery copy of `BACKUP_RESTIC_PASSWORD` | Organization password manager, two or more operators | Generated in 4.6 |
| Alert contact points and recipients | Grafana Cloud | Defined with open question Q5 (OBS-08) |
| DNS A/AAAA records | Masterweb DNS | Created manually before the first deployment of a domain (RTE-03) |

---

## 10. Setup procedure

1. Create the `Staging` and `Production` Environments with their protection rules in CentralDevOps (section 2).
2. Generate key material per Environment: admin SSH key, deploy SSH key, `age` key pair and the Restic password. Commit the public halves, store the recovery copies (4.6) and delete local plaintext files.
3. Create the external credentials: GHCR token (4.5), S3 keys (4.7), Grafana token (4.8) and the dispatch GitHub App (5.3).
4. Set the variables of section 3 in the repository and in both Environments.
5. Set the secrets of section 4 in both Environments, and the dispatch App secrets of section 5.3 at organization level for the app repositories.
6. For each app, create its two Environments, its `APP_*` variables and secrets, and its workflows (REG-09).
7. Verify: compare `gh variable list` and `gh secret list` (for each Environment) with the quick reference in 1.3, and confirm no name is missing, extra or misspelled.

Example commands with the GitHub CLI (replace `<ORG>`). Setting a secret without a value prompts for it, so the value never lands in shell history.

```bash
# repository variable
gh variable set ANSIBLE_CONFIG_PATH --repo <ORG>/CentralDevOps --body "ansible.cfg"

# Environment variable
gh variable set ANSIBLE_INVENTORY_PATH --env Staging --repo <ORG>/CentralDevOps --body "inventories/staging/hosts.yml"

# Environment secret, typed at the prompt
gh secret set GHCR_PULL_TOKEN --env Staging --repo <ORG>/CentralDevOps

# organization secret limited to the app repositories
gh secret set DEPLOY_DISPATCH_APP_ID --org <ORG> --visibility selected --repos app-one,app-two
```

```powershell
# Environment secret from a key file (PowerShell)
Get-Content -Raw .\cdo-deploy-staging | gh secret set DEPLOY_SSH_PRIVATE_KEY --env Staging --repo <ORG>/CentralDevOps

# list what is configured
gh secret list --env Staging --repo <ORG>/CentralDevOps
gh variable list --env Staging --repo <ORG>/CentralDevOps
```

---

## 11. Rotation (SEC-16)

Each rotation is rehearsed once on Staging without a deployment outage, then written into the runbook. Procedures follow §15.5; rows marked "same pattern" are not named there.

| Secret | Procedure |
|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY`, `DEPLOY_SSH_PRIVATE_KEY` | Generate a new pair, add the new public key through `configure-vps.yml`, switch the GitHub secret, remove the old public key from the host, run `verify-vps.yml` |
| `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | Add the new public key to `deployment/keys/` (two recipients during the transition), update the secret, update the pinned `request-deploy` SHA in the apps, then drop the old recipient |
| `GHCR_PULL_TOKEN` | Create the new token, update the secret, re-run `configure-vps.yml`, revoke the old token |
| `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | Generate a new private key on the GitHub App, update the organization secret, delete the old key |
| `BACKUP_RESTIC_PASSWORD` | `restic key add` with the new password, update the password manager copy and the host secret, then `restic key remove` the old key |
| `BACKUP_S3_*`, `MONITORING_GRAFANA_CLOUD_TOKEN` | Same pattern: create the new credential, update the secret, re-run `configure-vps.yml`, revoke the old one |
| App `APP_*` secrets | Change the secret in the app Environment and redeploy. For `APP_DB_PASSWORD` the deployment updates the database role password (DB-04) |

---

## 12. Open items that affect this document

| # | Question | Effect on variables and secrets |
|---|---|---|
| Q2 | Does Sumopod S3 support provider-side encryption, versioning and per-path access keys? | Decides how least-privilege `BACKUP_S3_*` keys can be scoped per Environment (4.7) and whether `BACKUP_S3_PREFIX` is needed (7) |
| Q4 | How many monthly backup copies, and how long are deployment records kept? | May add `BACKUP_RETENTION_MONTHS` (7) |
| Q5 | Who receives alerts and by which channel? | Configured in Grafana Cloud, not GitHub (9) |
| Q6 | Does the deployment team replace the owner as Production approver or join the owner? | Required reviewers of the CentralDevOps `Production` Environment (2) |
| Q10 | Which Grafana Cloud plan, and what ingestion volume? | May change the stack, `MONITORING_ENDPOINT` and the access policy (3.2, 4.8) |
