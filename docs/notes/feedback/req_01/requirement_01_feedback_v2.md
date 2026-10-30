# Requirement 01 Feedback v2

**Source:** [bootstrap-vps-v3.md](../requirements/01/bootstrap-vps-v3.md)  
**Previous answers:** [requirement_01_feedback_v1.md](./requirement_01_feedback_v1.md)  
**Status:** Draft. Existing facts are recorded where known; every `[FILL IN: ...]` or `[CONFIRM: ...]` needs owner verification.

Do not put private keys, passwords, API tokens, or other secret values in this file. Add only the approved GitHub Environment secret/variable names. Do not enable `apply` while required placeholders or identity collisions remain unresolved.

## 1. Inventory identity and address mapping

**Draft answer:** Development runs locally on each developer workstation and is not a VPS target. The inventories retain four VPS aliases for staging and production. They currently map to `43.157.247.221` and set `ansible_user: deploy`. This mapping has not been verified as the live Sumopod topology. The feedback records one active VPS (`buz-prod-1`) and uses that ID for all four aliases as a temporary mapping; verify the addresses and host identity with Sumopod before bootstrap. If staging and production share one physical VPS, they do not have host-level isolation and need an explicitly reviewed shared-host approval and credential policy, or separate VPSs before independent host policies can be applied.

`ansible_user: deploy` is the existing deployment account setting; it is not proof of the provider bootstrap username. Keep it separate from `bootstrap_user`.

| Inventory alias | Environment group | Current `ansible_host` (verify or replace) | `bootstrap_host_id` | `bootstrap_fqdn` | `bootstrap_user` | Other aliases on this VPS, or `No` |
|---|---|---|---|---|---|---|
| `buz-staging-cbe-1` | staging | `43.157.247.221` | `buz-prod-1` (temporary; only one active VPS is recorded) | cbe-staging.buzilion.id | ubuntu | `buz-prod-cbe-1`, `buz-staging-om-1`, `buz-prod-om-1` |
| `buz-prod-cbe-1` | production | `43.157.247.221` | `buz-prod-1` | cbe.buzilion.id | ubuntu | `buz-staging-cbe-1`, `buz-staging-om-1`, `buz-prod-om-1` |
| `buz-staging-om-1` | staging | `43.157.247.221` | `buz-prod-1` (temporary; only one active VPS is recorded) | om-staging.buzilion.id | ubuntu | `buz-staging-cbe-1`, `buz-prod-cbe-1`, `buz-prod-om-1` |
| `buz-prod-om-1` | production | `43.157.247.221` | `buz-prod-1` | om.buzilion.id | ubuntu | `buz-staging-cbe-1`, `buz-prod-cbe-1`, `buz-staging-om-1` |

Use the same `bootstrap_host_id` only for aliases confirmed to refer to the same physical VPS. If staging and production aliases share a VPS, document the intended shared-host arrangement and its single effective GitHub Environment approval/credential policy; do not describe them as host-isolated. Otherwise, assign each physical VPS its own stable ID and correct address. Do not use an alias or IP address as a substitute for a stable host ID, and do not assume the bootstrap username is `ubuntu`.

## 2. Host FQDNs and Customer Builder Engine route

**Known route values:** Customer Builder Engine uses `cbe.buzilion.id`, listens on `0.0.0.0:3000` inside its container, and has health endpoint `/api/health`.

**Draft answer:** The route table proposes `cbe.buzilion.id` for production at `buz-prod-cbe-1`; confirm that assignment before `apply`. Do not assume it also serves staging. Verify that its public DNS A record and any configured AAAA record resolve to the target's verified address.

| Application/route | FQDN | Environment | Exact inventory alias | Docker network | Stable Docker service name/network alias | Upstream port | Health path |
|---|---|---|---|---|---|---|---|
| Customer Builder Engine | `cbe.buzilion.id` | production | buz-prod-cbe-1 | cbe-proxy, cbe-backend | `customer-builder` | `3000` | `/api/health` |
| Customer Builder Engine | `cbe-staging.buzilion.id` | staging | buz-staging-cbe-1 | cbe-proxy, cbe-backend | `customer-builder` | `3000` | `/api/health` |
| Outbound Marketing | `om.buzilion.id` | production | buz-prod-om-1 | om-proxy, om-backend | `outbound-marketing` | `3100` | `/api/health` |
| Outbound Marketing | `om-staging.buzilion.id` | staging | buz-staging-om-1 | om-proxy, om-backend | `outbound-marketing` | `3100` | `/api/health` |

Nginx should join `cbe-proxy` and use `http://customer-builder:3000`. The application also joins `cbe-backend` for database traffic; keep the proxy and backend networks distinct. `0.0.0.0` is the container bind address, not an Nginx upstream destination; do not publish port 3000 on the VPS host.

For every selectable host that needs host-level TLS/HTTPS checks, supply its `bootstrap_fqdn` in the inventory table in section 1. List any additional application route FQDNs here. Use `N/A` only when that host or route does not need TLS/HTTPS.

## 3. Provider bootstrap SSH authentication

**Draft answer:** For a fresh VPS, the first SSH connection uses the provider-created `bootstrap_user` and its password from a protected GitHub Environment secret. The workflow pins the host key, installs the separate `deploy` public key, and verifies a new deploy-key session before disabling SSH password and keyboard-interactive authentication. On later runs it uses deploy-key access if the password is no longer accepted. Do not put the password in this document, inventory, or a dispatch input.

Development is local and does not require a VPS bootstrap password or GitHub VPS Environment.

| Target environment | Exact protected GitHub Environment name | Bootstrap password secret name | Authorized username/hosts verified | Pinned SSH host-key source/value configured |
|---|---|---|---|---|
| staging | `Staging` | `BUZ_STG_[X]_PASSWORD` | `BUZ_STG_[X]_USERNAME` | [FILL IN: approved fingerprint/source and configuration name] |
| production | `Production` | `BUZ_PROD_1_PASSWORD` | `ubuntu` | [FILL IN: approved fingerprint/source and configuration name] |

Use the separate per-environment `deploy` key pair for ongoing access; the bootstrap password is only for initial password-authenticated access and is never placed in workflow inputs or inventory.

## 4. Deployment account, groups, keys, and ownership

**Account decision:** Sumopod provides the bootstrap account for initial SSH provisioning; the workflow does not create it. Create or reconcile only `deploy` for ongoing access. Do not create a separate administrator/break-glass account.

**Recommended baseline:** Give `deploy` the primary group `deploy`, a locked local password, and a dedicated Ed25519 key for key-only SSH. Keep the current passwordless-sudo contract: the deployment playbook runs with Ansible `become: true`, and the Ansible setup guide requires passwordless sudo. This makes `deploy` effectively root-equivalent, so keep production runs behind protected-environment approvals. Do not add `deploy` to the `docker` group by default; the current deployment uses sudo for Docker operations, and membership in `docker` is also root-equivalent.

**Repository evidence:** The Customer Builder Engine deployment workflow sets `/opt/customerbuilder`; the shared Ansible role creates that directory as `root:root` mode `0755` and its `compose.yaml` as `root:root` mode `0644`. Keep those deployment-control files root-owned to match the existing workflow rather than changing them to `deploy:deploy`. The Outbound Marketing repository currently has local-development PostgreSQL configuration but no remote deployment workflow, so its path below is a proposed default, not an existing deployment setting.

| Account/resource | Recommended configuration | Decision / evidence |
|---|---|---|
| `deploy` (only account created/managed) | Distinct from the provider bootstrap account; primary group `deploy`; shell `/bin/bash`; locked local password; dedicated Ed25519 public key. Grant the passwordless sudo required by the current deployment playbook. Do not add other supplementary groups by default; add `docker` only if a future deployment path must run Docker without sudo. | Install the public key using the existing CentralDevOps environment variable `STG_SSH_PUBLIC_KEY` or `PROD_SSH_PUBLIC_KEY`. Put the matching private key in the calling application's protected `staging` or `production` Environment secret named `VPS_SSH_PRIVATE_KEY`. Use different key pairs for staging and production, and never reuse the bootstrap key. Passwordless sudo is confirmed by the current `become: true` playbook and `ansible/README.md`. |
| Application deployment roots | Customer Builder Engine: `/opt/customerbuilder`, directory `root:root` mode `0755`, `compose.yaml` `root:root` mode `0644` (matches the current role). Outbound Marketing: use `/opt/outbound-marketing` with the same ownership and modes if/when its remote deployment workflow is added. Keep any runtime data owned by the UID/GID of the process or container that writes it, not by `deploy`. | The CBE path and modes are present in the current deployment workflow/role. The Outbound Marketing path is a recommended default only; no remote deployment workflow currently uses it. The current Compose manifest references runtime environment values rather than storing secret values in the file; if a secret file is introduced later, use `root:root` mode `0600`. |
| Nginx and SSH configuration | Nginx is planned as a container, not a host package. Recommended host configuration directory: `/opt/buzilion/nginx`, owned by `root:root` mode `0750`; configuration files `root:root` mode `0644` and mounted read-only. Recommended SSH hardening drop-in: `/etc/ssh/sshd_config.d/00-buzilion-hardening.conf`, `root:root` mode `0644`; validate with `sshd -t` before activation. | These are recommended managed paths because no host Nginx configuration path exists yet. `deploy` must not be able to modify host security or reverse-proxy configuration without the approved sudo path. |
| PostgreSQL data | Customer Builder Engine currently uses external Supabase, so no VPS PostgreSQL data path is defined for it. For Outbound Marketing, use a persistent Docker named volume `outbound_postgres_data` mounted at `/var/lib/postgresql`; keep ownership as created/required by the pinned PostgreSQL image. If a bind mount is chosen instead, use `/var/lib/buzilion/outbound-marketing/postgres`, mode `0700`, owned by the numeric UID/GID from that exact image. Never assign database files to `deploy`. | Outbound Marketing's local Compose file currently uses `postgres:18.6`, database/user `outbound_marketing`, and a named volume. Reuse that image version only after pinning and testing the production image; determine its numeric UID/GID from the pinned image rather than guessing. |
| Other persistent service paths | No additional persistent VPS service paths are established. Prefer a separate named volume per service; for a host bind mount, use `/var/lib/buzilion/<service>` with mode `0700` and the UID/GID required by that service's pinned image. | `N/A` for the currently documented CBE deployment. Add a specific path and owner only when another persistent service is selected. |

Set `/home/deploy` to `deploy:deploy` mode `0750`, `/home/deploy/.ssh` to `deploy:deploy` mode `0700`, and `authorized_keys` to `deploy:deploy` mode `0600`. If using a sudoers drop-in, use `/etc/sudoers.d/90-deploy` owned by `root:root` mode `0440` and validate it with `visudo -cf`. Keep the original bootstrap session available until a new `deploy` SSH session, key, sudo access, and ownership checks all pass.

Define the provider bootstrap username, `deploy` public key and sudo policy, paths, groups, and ownership through approved inventory or protected GitHub Environment configuration—not dispatch inputs. The actual private keys belong only in protected Environment secrets.

## 5. Sumopod provider firewall

**Observed settings from the supplied Sumopod firewall screenshot:**

| Protocol | Port | Source IP address | Description |
|---|---|---|---|
| TCP | 22 | `0.0.0.0/0` | SSH remote access |
| TCP | 80 | `0.0.0.0/0` | HTTP web server |
| TCP | 443 | `0.0.0.0/0` | HTTPS web server |

**Draft answer:** The shown rules allow TCP/22, TCP/80, and TCP/443 from any IPv4 source. In particular, TCP/22 is not restricted to trusted management IPs in this view; restrict its source range if Sumopod supports it. The screenshot does not identify a physical VPS or establish that these rules are current for every target, so verify its scope and check whether separate IPv6 rules exist. Keep TCP/22 available for intended SSH access, and keep TCP/80 and TCP/443 open only when Nginx is selected. Do not expose PostgreSQL or application container ports. No supported Sumopod firewall API has been identified; treat provider firewall changes as a manual Sumopod process unless the provider confirms and documents a supported API. The workflow can report host-firewall state but must not claim it verified the provider firewall.

| Physical VPS / `bootstrap_host_id` | Screenshot applies and is current? | TCP/22 access verified? | Nginx selected (TCP/80 and 443 needed)? | IPv6 rules checked? | Provider rule evidence/verification date | Operator and manual change process |
|---|---|---|---|---|---|---|
| [FILL IN] | [FILL IN: yes/no] | [FILL IN: yes/no] | [FILL IN: yes/no] | [FILL IN: yes/no] | [FILL IN] | [FILL IN: Sumopod portal/support process and responsible owner] |

If there is more than one physical VPS, add one row per VPS. Confirm the provider-side rules do not contradict the intended host firewall policy before `apply`.

## 6. Cloudeka backup configuration

**Known values carried forward from v1:**

- Endpoint: `https://kencana.basic.box.cloudeka.id`
- Region: `kencana`
- Bucket: `buz-stg-prod-1-lb4jef`
- Access key ID variable: `BUZ_STG_PROD_1_ID`
- Secret access key secret: `BUZ_STG_PROD_1_SECRET`
- Recovery objectives: RPO at most 12 hours and RTO at most 4 hours; retain seven days of backups.

**Proposed prefix pattern:** `bootstrap/<environment>/<bootstrap_host_id>/postgresql/`. Approve or replace this pattern so staging and production backups use the intended non-overlapping prefixes for their physical VPSs. Local development has no VPS backup prefix.

| Item | Answer to confirm |
|---|---|
| At-rest encryption | Require server-side encryption for all objects using provider-managed AES-256 or a managed KMS key, and confirm the setting applies to existing and new objects. If Cloudeka does not support this, encrypt backups client-side with a separately managed, recoverable key before upload. Document key ownership, rotation, and recovery; HTTPS alone does not protect stored data. |
| Bucket versioning | Enable bucket versioning and restrict suspend/disable permissions to bucket administrators. Test recovery of an overwritten or deleted object, and configure lifecycle handling for noncurrent versions as described below. |
| Lifecycle/retention | Scope lifecycle rules to the approved backup prefix. Expire current backups after seven days, expire noncurrent versions so they cannot accumulate indefinitely, and abort incomplete multipart uploads after one day. Confirm how Cloudeka counts lifecycle age and applies version expiration; test that a restorable backup remains available for the required seven-day window and that expired versions are eventually removed. |
| Credential scope | Use separate credentials per environment (and per VPS where practical), restricted to bucket `buz-stg-prod-1-lb4jef` and that host's approved prefix. Give the backup writer only prefix-limited listing if needed and object-write/multipart permissions; use a separate restore identity with read/list access. Do not grant routine credentials object-delete, bucket-configuration, versioning, or lifecycle permissions; let lifecycle rules remove expired backups. Store credentials only as protected GitHub Environment secrets and rotate/revoke them through the approved process. |
| Approved prefix | [CONFIRM `bootstrap/<environment>/<bootstrap_host_id>/postgresql/` for staging/production or provide the approved alternative] |
| Database role/name and protected secret names | [FILL IN: database/user configuration and GitHub Environment secret names only; do not include secret values] |

HTTPS is indicated by the supplied endpoint. Confirm the provider's at-rest encryption, versioning, lifecycle, and credential-scope capabilities before implementation. Validate that the initial backup can be restored to an isolated test database without overwriting production data.

## 7. Grafana Cloud and notification configuration

**Draft answer:** Alloy should send the approved metrics, logs, and traces to the Grafana Cloud stack. Store non-secret endpoints and stack identifiers in protected Environment variables; store the API token only in a protected Environment secret. Do not enable alert routes until the recipient and routing configuration are approved.

| Signal/configuration | Required value or configuration name |
|---|---|
| Metrics endpoint and stack/user identifier | https://prometheus-prod-52-prod-ap-southeast-2.grafana.net/api/prom/push; User: 3703229 |
| Logs endpoint and stack/user identifier | https://logs-prod-032.grafana.net/loki/api/v1/push; User: 1847279 |
| Traces/OTLP endpoint and stack identifier | tempo-prod-23-prod-ap-southeast-2.grafana.net:443; User: 1841580 |
| Environment variable names for endpoints/identifiers | BUZ_PROD_1_GRAFANA_CLOUD_PROMETHEUS_URL; BUZ_PROD_1_GRAFANA_CLOUD_PROMETHEUS_USER; BUZ_PROD_1_GRAFANA_CLOUD_LOKI_URL; BUZ_PROD_1_GRAFANA_CLOUD_LOKI_USER; BUZ_PROD_1_GRAFANA_CLOUD_TEMPO_URL; BUZ_PROD_1_GRAFANA_CLOUD_TEMPO_USER; BUZ_PROD_1_GRAFANA_CLOUD_OTLP_ENDPOINT; BUZ_PROD_1_GRAFANA_CLOUD_INSTANCE_ID |
| Grafana Cloud API-token secret name | BUZ_PROD_1_GRAFANA_CLOUD_API_TOKEN |
| Alert/operations email | `aristaaldo2@gmail.com` |
| Notification mechanism and owner | [FILL IN: approved mechanism and responsible operator; confirm whether reboot-pending notifications use the same recipient.] |

Until the address and notification mechanism are explicitly approved, leave alert destinations and reboot notifications unconfigured, report them as missing, and do not allow the separate reboot action to proceed.

## 8. ACME email and approved service versions

**Draft answer:** Use an explicitly approved, monitored ACME registration email and pin every selected service to an approved version. Do not use an unbounded `latest` tag. The current Docker role uses Docker's official Ubuntu APT repository but does not pin package versions. Outbound Marketing's local-development Compose file uses `postgres:18.6`; this is only a candidate, not an approved VPS version. No approved Nginx image/digest or Alloy package version is recorded. Keep `apply` disabled for any selected service until its exact version is approved and pinned.

| Item | Required answer |
|---|---|
| ACME/Let's Encrypt registration email | `aristaaldo2@gmail.com` |
| Docker Engine package/source and version | Use Docker's official Ubuntu APT repository (`https://download.docker.com/linux/ubuntu`). Pin exact approved versions of `docker-ce`, `docker-ce-cli`, `containerd.io`, and `docker-buildx-plugin` in Ansible configuration; update only through a reviewed change and staging validation. No exact versions are currently pinned or approved. |
| Docker Compose v2 plugin version | Use `docker-compose-plugin` from the same official Docker APT repository and pin its exact approved package version alongside the Engine versions. No exact version is currently pinned or approved. |
| Nginx container image | `N/A` until approved. Keep Nginx unselected until an explicit official image version and immutable image digest are approved. |
| PostgreSQL container image | `N/A` for VPS bootstrap until approved. `postgres:18.6` is the existing local-development candidate only; approve it for VPS use only after compatibility and backup/restore testing, then pin its immutable image digest. |
| Grafana Cloud Alloy package/source and version | `N/A` until approved. No Alloy package source or exact version is recorded; if selected, approve a trusted package source and exact version pin before enabling `apply`. |

If versions differ between staging and production, record the approved value for each environment. Development runs locally and is not managed by the VPS bootstrap. The Customer Builder Engine application image remains managed by the separate application-deployment workflow.

## Apply-readiness checklist

Keep `apply` disabled until all applicable items below are completed and validated:

- Every selected inventory host has a verified address, stable physical-host ID, public FQDN, bootstrap username, and unambiguous environment.
- Repeated addresses/host IDs are either corrected or explicitly approved as a shared-host configuration with one effective environment policy.
- The CBE route target, Docker network alias, DNS records, and any other TLS/HTTPS routes are confirmed.
- Bootstrap key pairs are authorized on the intended hosts; GitHub Environment values and pinned SSH host keys are configured.
- The `deploy` account/key and account/path ownership configuration are approved.
- Sumopod provider firewall rules and the manual operator process are confirmed.
- Cloudeka encryption, versioning, lifecycle, credential scope, backup prefix, and isolated restore are verified.
- Grafana Cloud endpoints/identifiers and the API-token secret are configured; notification/alert recipients are explicitly confirmed or disabled.
- The ACME email and approved service versions are supplied.
