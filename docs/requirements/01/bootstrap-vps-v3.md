# Requirements: GitHub Workflow to Bootstrap a VPS

**Version:** 3  
**Status:** Updated requirements draft  
**Scope:** Requirements only; this document does not implement the workflow.

## 1. Goal and scope

Provide a manually triggered GitHub Actions workflow that configures one already-provisioned VPS for a selected set of services.

The workflow must:

- Support only staging and production VPS targets. Development runs locally on each developer workstation and is outside VPS bootstrap scope.
- Configure an existing VPS; creating or resizing VPS resources through a provider API is out of scope.
- Target exactly one approved inventory host per run.
- Establish a secure host baseline and install only the selected optional services.
- Use protected password-based SSH for initial access to a fresh VPS and key-based SSH for the final managed account.
- Safely inspect and reconcile services that are already installed or configured.
- Be safe to retry and report clearly when a precondition or configuration step fails.
- Keep application build and release deployment in the existing, separate application-deployment workflow.
- Never reboot the host as part of bootstrap or package updates.

## 2. Supported targets, inventory, and dispatch inputs

### 2.1 Supported target

- Ubuntu Server 24.04 LTS is the only supported operating system for this version.
- The VPS must already exist and be reachable over SSH using a provider-created bootstrap account and its password, stored only in a protected GitHub Environment secret.
- Sumopod is the VPS provider. No supported provider-management API is currently identified; the workflow must not assume it can manage provider firewall rules through an API.
- Only these inventory files may be selected:
  - `ansible/inventory/customer-builder-engine.yml`
  - `ansible/inventory/outbound-marketing.yml`
- Inventory must provide the connection address, a stable physical-host identifier, the provider bootstrap username, and the target environment. A host-level FQDN is required only when host-level DNS/TLS checks are selected; Nginx routes must always have explicit route FQDNs.
- The target environment must be `staging` or `production`; development is not a VPS inventory or bootstrap target.
- Inventory must not contain passwords, private keys, API tokens, or other credentials.

### 2.2 Manual workflow inputs

The workflow must use `workflow_dispatch` and prompt the operator for:

1. **Inventory:** one of the two approved inventory files above.
2. **Target host:** one exact Ansible host alias from the selected inventory.
3. **Execution mode:** `validate` (default, read-only) or `apply`.
4. **Optional service selections:** Docker, Nginx, PostgreSQL, and Grafana Cloud Alloy. All default to off.

Nginx and PostgreSQL are containerized and therefore depend on Docker. Selecting either must include Docker in the effective service plan; the run summary must report that dependency. Docker may also be selected on its own. Alloy must not require Docker unless a separately approved implementation chooses a container runtime and includes Docker as a dependency.

GitHub Actions cannot dynamically populate a host dropdown from an inventory file. The host input must therefore be a string and must be validated before any remote changes. Reject unknown inventory files, aliases not present in the selected inventory, groups, wildcards, multiple hosts, arbitrary IP addresses, and arbitrary DNS names.

The inventory must identify the target's environment unambiguously so `apply` can use the corresponding protected GitHub Environment. Production changes require that Environment's approval rules. Serialize runs by the stable physical-host identifier, not merely by inventory alias, so aliases for the same VPS cannot be changed concurrently.

Treat all dispatch values as untrusted input: validate against strict allowlists and do not interpolate raw values into shell scripts. Restrict `apply` to an approved protected ref, grant the workflow only the permissions it needs, and pin third-party actions to reviewed immutable revisions. Never accept credentials or keys as dispatch inputs.

### 2.3 Inventory contract and repository findings

Each selectable host must provide:

- `ansible_host`: the SSH connection address.
- `bootstrap_host_id`: a stable identifier for the physical VPS, used for collision detection and concurrency control.
- `bootstrap_user`: the provider-created account used only for initial configuration.
- An unambiguous environment classification for GitHub approval and credential selection.
- `bootstrap_fqdn` only when a host-level DNS/TLS check is required.
- Explicit service-route configuration, including the FQDN, when Nginx is selected.

The existing application-deployment inventory may retain `ansible_user: deploy` for its current purpose. The bootstrap workflow must use `bootstrap_user`; it must not assume that `ansible_user` is the provider bootstrap account.

The inspected inventories currently define these aliases:

- Customer Builder Engine: `buz-staging-cbe-1` and `buz-prod-cbe-1`.
- Outbound Marketing: `buz-staging-om-1` and `buz-prod-om-1`.

Repository facts and remaining identity checks:

- All four aliases currently use `ansible_host: 43.157.247.221` and `ansible_user: deploy`; the inventories do not yet contain `bootstrap_user` or `bootstrap_host_id`.
- Feedback records one active Sumopod VPS, `buz-prod-1`, and uses it as a temporary `bootstrap_host_id` for all four aliases. Verify the live provider topology and address before treating that mapping as authoritative.
- The proposed route FQDNs are listed in Section 8. A separate `bootstrap_fqdn` is not required unless a host-level DNS/TLS check is selected.
- `validate` must report missing fields and address/host-identity collisions. `apply` must fail until each target has a verified address, host identity, bootstrap username, and environment. If staging and production aliases resolve to one physical VPS, require explicit shared-host approval and one effective GitHub Environment approval/credential policy; do not describe the aliases as host-isolated.

Do not derive a hostname from an alias or IP address. DNS A and any configured AAAA records must be checked against the selected target before TLS or HTTPS validation.

## 3. Preconditions and credential handling

- For a fresh VPS, the first SSH connection must use the provider-created bootstrap username from approved inventory and its password from the protected `Staging` or `Production` GitHub Environment. Name the per-host secret `<NORMALIZED_HOST_ID>_PASSWORD`, where the stable host ID is uppercase with hyphens replaced by underscores (for example, `buz-prod-1` becomes `BUZ_PROD_1_PASSWORD`).
- Never put the bootstrap password in inventory, workflow-dispatch inputs, command-line arguments, logs, artifacts, or summaries. Keep the independently verified SSH host-key pin in `BOOTSTRAP_<NORMALIZED_HOST_ID>_SSH_KNOWN_HOSTS`.
- Attempt the protected bootstrap password first. If password authentication is unavailable, allow a deploy-key connection for an already-bootstrapped VPS; otherwise stop before remote changes and report which credential configuration is missing without exposing secret values.
- The provider bootstrap account is distinct from the `deploy` account. Do not assume its username is `ubuntu` or use the deployment account as the initial bootstrap account.
- Pin and verify the VPS SSH host key. Do not trust an unverified key collected during the same workflow run.
- Store the `deploy` public key in a GitHub Environment variable or another approved non-secret configuration store. Store its matching private key only in a protected GitHub Environment secret so the workflow can verify final key-based access.
- Store service credentials only in protected GitHub Environment secrets. Do not print secrets, put them in command-line arguments, include them in artifacts, or expose them in workflow summaries.
- Use minimum required workflow permissions. Temporary credential files must have restrictive permissions and be removed when the job ends.
- If a selected service requires missing credentials or configuration, fail before applying changes and identify the missing configuration without revealing secret values.

## 4. Accounts, groups, and ownership

Account names, public keys, group memberships, and managed paths must come from approved inventory or protected GitHub Environment configuration, not free-form dispatch inputs.

The provider bootstrap account is supplied by Sumopod, is not created or deleted by this workflow, and is used only for initial configuration. Create or reconcile only one account, `deploy`, for ongoing access. Do not create a separate administrator/break-glass account.

| Account or resource | Required configuration |
|---|---|
| `deploy` | Dedicated account for the separate application-deployment workflow; distinct from the bootstrap account. Create if absent or verify and reconcile if present. Use `/bin/bash`, a locked local password, primary group `deploy`, and a dedicated Ed25519 key for key-only SSH. Set `/home/deploy` to `deploy:deploy` mode `0750`, `.ssh` to `deploy:deploy` mode `0700`, and `authorized_keys` to `deploy:deploy` mode `0600`. Preserve the current passwordless-sudo requirement. If managed through `/etc/sudoers.d/90-deploy`, set owner `root:root`, mode `0440`, and validate it with `visudo -cf`. This makes `deploy` effectively root-equivalent; protect production runs accordingly. Do not add supplementary groups by default or add `deploy` to the `docker` group: the current deployment path uses sudo for Docker, and Docker-group membership is also root-equivalent. |
| `deploy` key configuration | In the calling application's protected `staging` or `production` Environment, use the existing `STG_SSH_PUBLIC_KEY` or `PROD_SSH_PUBLIC_KEY` variable and the matching `VPS_SSH_PRIVATE_KEY` secret. Use different key pairs for staging and production. |
| Customer Builder Engine deployment files | Keep `/opt/customerbuilder` and its `compose.yaml` root-owned, with directory mode `0755` and file mode `0644`, matching the existing deployment role. Do not change these deployment-control files to `deploy:deploy`. Runtime data must be owned by the UID/GID of the process or container that writes it. |
| Outbound Marketing deployment root | No remote deployment workflow currently uses a VPS path. If one is added, `/opt/outbound-marketing` with root-owned control files is a proposed default, not a path this bootstrap workflow must create now. |
| Nginx and SSH configuration | Nginx is a container. Use `/opt/buzilion/nginx` as the root-owned host configuration directory (mode `0750`); keep configuration files root-owned, mode `0644`, and mounted read-only. If a secret file is needed, keep it `root:root` mode `0600`. Use `/etc/ssh/sshd_config.d/00-buzilion-hardening.conf` for the managed SSH drop-in, owned by root with mode `0644`; validate it with `sshd -t` before activation. |
| PostgreSQL data | Customer Builder Engine currently uses external Supabase and has no VPS PostgreSQL data path. For Outbound Marketing, prefer the persistent named volume `outbound_postgres_data` mounted at the data directory required by the approved image. If using a bind mount, use `/var/lib/buzilion/outbound-marketing/postgres`, mode `0700`, and the numeric UID/GID required by that exact image. Never assign database files to `deploy`. |
| Other persistent service paths | Give each selected service a persistent volume or explicit host path and set its ownership to the UID/GID required by that service's approved image. Do not create paths for unselected services. |

The workflow must verify `deploy`'s new key-based SSH session and required sudo access before excluding the provider bootstrap username from the SSH allowlist. It must also verify the expected groups, directory ownership, and file modes.

Before changing SSH authentication:

1. Install the approved public key for `deploy`.
2. Verify that `deploy` can establish a new SSH session using its matching private key.
3. Verify the required sudo access, groups, and ownership.
4. Validate the proposed SSH daemon configuration with `sshd -t`.

After successful checks, configure and verify:

- Public-key authentication enabled.
- Password and keyboard-interactive authentication disabled.
- Root SSH login disabled.
- Maximum authentication attempts set to three.
- SSH access limited to the approved account allowlist, with `deploy` as the only account created or managed by this workflow.
- Fail2ban installed, enabled, and protecting SSH.

Keep the original session available until the new `deploy` key-based session and configuration validation pass. If any access check fails, stop before locking out the bootstrap path and restore the previous SSH configuration.

## 5. Firewall and public exposure

The host firewall must:

- Deny inbound traffic by default and allow outbound traffic by default.
- Permit TCP/22 for SSH in the base profile.
- Permit TCP/80 and TCP/443 only when Nginx is selected and configured.
- Apply equivalent policy to IPv4 and IPv6 when IPv6 is configured.
- Keep PostgreSQL and application container ports private; do not publish PostgreSQL port 5432 or an application port to the public network.
- Detect and report other publicly exposed ports. Do not silently remove an unrecognized rule if doing so could disrupt an existing service; stop for an explicit decision.

The supplied Sumopod screenshot shows TCP/22, TCP/80, and TCP/443 allowed from `0.0.0.0/0`. It does not establish which VPS the rules apply to, whether they are current, or whether IPv6 rules exist. Verify provider rules per physical VPS rather than treating the screenshot as proof of current configuration.

Restrict provider-side SSH sources to trusted, stable management egress where available. GitHub-hosted runner egress may not be stable; if a source restriction cannot support the authorized workflow, require an explicit owner-approved exception before using public SSH access. In that case retain key-only SSH, disabled password/root login, Fail2ban, and the SSH authentication-attempt limit. Do not infer IPv6 exposure from the IPv4 screenshot.

No supported Sumopod firewall API is currently identified. Before `apply`, verify through Sumopod's supported management process that TCP/22 is available to authorized management sources and that TCP/80 and TCP/443 are open only when Nginx is selected. The workflow must report this as a manual provider-side boundary and must not claim provider-level protection was verified by automation. Do not proceed if provider-side rules are known to contradict the intended host policy.

## 6. Validation, reconciliation, and apply behavior

### 6.1 Validate (read-only)

Before applying changes, validate:

- The inventory file, exact host alias, canonical host identity, environment, FQDN, and service selections.
- There are no unresolved host-identity or `ansible_host` collisions.
- The pinned SSH host key and either password-based connectivity for initial bootstrap or deploy-key connectivity for an already-bootstrapped host.
- Sudo capability and Ubuntu 24.04 LTS version.
- Required secrets and service configuration for the effective service profile.
- DNS resolution of the configured hostname to the selected host address, including any configured AAAA record.
- Existing users, groups, file ownership, firewall rules, public listeners, installed packages, service units, containers, Docker networks, configuration drift, persistent data, and current health for selected services.
- Baseline health thresholds in Section 11.

`validate` must not change the VPS. It must return a failing status for an invalid target, unsupported host, missing prerequisite, ambiguous inventory mapping, or failed safety check. It should summarize which selected services are absent, already compliant, or have configuration drift and what `apply` would change.

### 6.2 Apply

For an approved `apply` run:

1. Capture a non-secret baseline report of OS, resource use, failed critical services, installed service versions, existing configuration state, persistent data, and public listeners.
2. Inspect the proposed package update set and apply updates under the maintenance rules in Section 10. Do not perform a distribution-release upgrade.
3. Establish and verify the final SSH account, key, groups, and ownership before applying SSH lock-down.
4. Apply the host firewall policy without dropping the active management path.
5. Reconcile only the selected services and their required dependencies.
6. Configure service-specific persistence, backups, TLS, and monitoring as selected.
7. Run the configuration and availability checks for every selected item.

For every selected service or managed item, the workflow must:

1. Check whether the package, service, container, network, user, file, or other item already exists.
2. If it is absent, install or create it using the approved version and configuration.
3. If it exists, compare its installed version, configuration, ownership, permissions, and runtime state with the intended state. Do not treat mere presence or a running process as proof of compliance.
4. Reconcile safe configuration drift idempotently. Stage and validate configuration before activation; preserve existing data and back up existing managed configuration before replacement.
5. Verify that the item is available and healthy after reconciliation, and verify the relevant configuration, endpoint, or network behavior.

Do not reinstall, reset, or recreate an already-correct service just because the workflow was rerun. If existing state is incompatible, unmanaged, or cannot be corrected safely without a destructive change or unapproved migration, stop before that change and report the required operator decision.

Services that were not selected must not be installed or reconfigured. Report any existing unselected service that creates an unexpected public listener or conflicts with the selected profile; do not silently disable or remove it.

The workflow must stop on the first failed mandatory phase, preserve useful non-secret diagnostics, and never report success after a partial failure. It must not reboot automatically.

## 7. Optional services

### 7.1 Docker (optional)

When selected directly or as a dependency:

- Install Docker Engine and the Docker Compose v2 plugin from a trusted package source, using explicitly approved versions; enable Docker at boot.
- If Nginx or an application uses Docker, create or verify the approved shared Docker network used by the reverse proxy and the separate application-deployment workflow.
- Do not expose the Docker daemon or socket over the network.
- Check the installed versions, daemon configuration, service state, and network configuration on every run. Preserve existing container data and volumes.

### 7.2 Nginx (optional)

When selected:

- Run Nginx in a container connected to the approved shared Docker network.
- Publish only Nginx's HTTP/HTTPS ports on the host: TCP 80 and 443.
- Do not publish application container ports directly to the public interface.
- Configure only explicitly approved application routes and upstreams.
- Use maintained, explicitly selected container versions; do not rely on an unbounded `latest` tag.
- Configure suitable restart behavior and health checks.
- Validate the complete Nginx configuration before activation and verify Nginx availability after changes.

### 7.3 PostgreSQL (optional)

PostgreSQL is an optional VPS service for Outbound Marketing. Customer Builder Engine currently uses external Supabase and does not require a VPS PostgreSQL instance. Do not install PostgreSQL for that application unless a separately reviewed requirement changes.

When selected for Outbound Marketing:

- Run PostgreSQL as a container on the VPS. Docker is a required dependency.
- Use the persistent `outbound_postgres_data` named volume by default. Keep database files outside the container's writable layer and preserve them across restarts and container replacement. If a bind mount is approved instead, use the path and image-specific ownership in Section 4.
- Do not publish PostgreSQL to the public network. Permit access only from explicitly approved local/container networks.
- Use `outbound_marketing` as the database and database user, matching the current local-development configuration. Store non-secret names in approved environment configuration and the password only in a protected GitHub Environment secret named `OUTBOUND_MARKETING_DB_PASSWORD`; never commit credentials or expose them in logs.
- Pin an approved image version and immutable digest before `apply`. The local `postgres:18.6` image is a candidate only, not an approved VPS version.
- Define and verify a health check (for example, `pg_isready`) and the data-directory ownership required by the pinned image.
- Never remove the data volume as part of bootstrap. Configure and validate the off-host backup and restore requirements in Section 9 before reporting PostgreSQL as recovery-ready.

### 7.4 Grafana Cloud Alloy (optional)

When selected:

- Install and run Alloy as a managed service with an explicitly approved version and configuration.
- Configure Alloy to send the approved metrics, logs, and traces to the Grafana Cloud stack.
- For the currently recorded stack, configure these non-secret values in the protected GitHub Environment:

  | Signal | Endpoint | Stack/user identifier |
  |---|---|---|
  | Metrics | `https://prometheus-prod-52-prod-ap-southeast-2.grafana.net/api/prom/push` | `3703229` |
  | Logs | `https://logs-prod-032.grafana.net/loki/api/v1/push` | `1847279` |
  | Traces | `tempo-prod-23-prod-ap-southeast-2.grafana.net:443` | `1841580` |

- Use the variable names `BUZ_PROD_1_GRAFANA_CLOUD_PROMETHEUS_URL`, `BUZ_PROD_1_GRAFANA_CLOUD_PROMETHEUS_USER`, `BUZ_PROD_1_GRAFANA_CLOUD_LOKI_URL`, `BUZ_PROD_1_GRAFANA_CLOUD_LOKI_USER`, `BUZ_PROD_1_GRAFANA_CLOUD_TEMPO_URL`, `BUZ_PROD_1_GRAFANA_CLOUD_TEMPO_USER`, `BUZ_PROD_1_GRAFANA_CLOUD_OTLP_ENDPOINT`, and `BUZ_PROD_1_GRAFANA_CLOUD_INSTANCE_ID`. Store the token only in the protected Environment secret `BUZ_PROD_1_GRAFANA_CLOUD_API_TOKEN`; never accept it as a dispatch input or log it.
- Verify that Alloy starts and can deliver each configured telemetry signal.
- The supplied proposed alert recipient is `aristaaldo2@gmail.com`. Do not create or enable alert destinations, contact points, or routing policies until the recipient and notification mechanism are confirmed.
- If Alloy is not selected, report monitoring as not configured; do not imply that external telemetry or alerting is active.

## 8. TLS, DNS, and application routes

TLS and public HTTPS checks apply only when Nginx is selected.

- Use Let's Encrypt with the HTTP-01 challenge for an explicit route FQDN. The supplied ACME registration email is `aristaaldo2@gmail.com`.
- Require public DNS to resolve to the selected VPS and TCP/80 to be reachable for certificate issuance and renewal. Check A records and any configured AAAA records.
- Configure HTTPS on TCP/443, redirect ordinary HTTP traffic to HTTPS, and verify automatic certificate renewal without unnecessarily replacing a valid production certificate.
- Do not derive application hostnames from inventory aliases. Validate the explicit FQDN-to-upstream mapping before enabling a route.

The supplied route map is:

| Application | Environment / inventory alias | FQDN | Nginx network | Application networks | Upstream | Health path |
|---|---|---|---|---|---|---|
| Customer Builder Engine | staging / `buz-staging-cbe-1` | `cbe-staging.buzilion.id` | `cbe-proxy` | `cbe-proxy`, `cbe-backend` | `customer-builder:3000` | `/api/health` |
| Customer Builder Engine | production / `buz-prod-cbe-1` | `cbe.buzilion.id` | `cbe-proxy` | `cbe-proxy`, `cbe-backend` | `customer-builder:3000` | `/api/health` |
| Outbound Marketing | staging / `buz-staging-om-1` | `om-staging.buzilion.id` | `om-proxy` | `om-proxy`, `om-backend` | `outbound-marketing:3100` | `/api/health` |
| Outbound Marketing | production / `buz-prod-om-1` | `om.buzilion.id` | `om-proxy` | `om-proxy`, `om-backend` | `outbound-marketing:3100` | `/api/health` |

These are the supplied proposed route assignments. Verify the physical target, address, and DNS records before `apply`. Nginx must join only the proxy network(s) used by selected routes; each application may also join its separate backend network. Keep the proxy and backend networks distinct. If staging and production share one VPS, use environment-specific networks and upstream aliases so the two environments cannot collide or route to each other's containers.

Customer Builder Engine listens on `0.0.0.0:3000` inside its container. Do not publish port 3000 on the VPS host; Nginx must use the stable Docker service name or network alias, not `0.0.0.0`, as its upstream destination. Do not publish the Outbound Marketing application port 3100 on the VPS host either.

For each enabled route, verify the HTTPS health endpoint returns the expected healthy response. If its application has not yet been deployed, report the route as pending rather than healthy. Local development runs on developer workstations and is outside VPS TLS checks.

## 9. PostgreSQL backup and recovery

When PostgreSQL is selected:

- Store backups off-host in Cloudeka's S3-compatible storage using:
  - **Endpoint:** `https://kencana.basic.box.cloudeka.id`
  - **Region:** `kencana`
  - **Bucket:** `buz-stg-prod-1-lb4jef`
  - **Access key ID:** GitHub Environment variable `BUZ_STG_PROD_1_ID`
  - **Secret access key:** protected GitHub Environment secret `BUZ_STG_PROD_1_SECRET`
- Use the prefix `bootstrap/<environment>/<bootstrap_host_id>/postgresql/` so each environment and physical VPS has a non-overlapping location. Do not use one alias-specific prefix for aliases that share a physical VPS.
- Run backups on a schedule independent of GitHub Actions, frequently enough to meet **RPO <= 12 hours**. Report or fail validation when the last successful backup is older than 12 hours.
- Retain seven days of current backups. Scope lifecycle rules to the approved prefix; expire current objects after seven days, expire noncurrent versions seven days after they become noncurrent, and abort incomplete multipart uploads after one day. Verify the provider's lifecycle-age semantics preserve the required restorable window.
- Require encryption in transit and at rest. Use provider-managed AES-256 or managed KMS server-side encryption where supported and verify it applies to new and existing objects. If server-side encryption is unavailable, encrypt backups client-side with a separately managed, recoverable key before upload; document key ownership and recovery.
- Enable bucket versioning and restrict its suspension or disablement to bucket administrators. Test recovery of an overwritten or deleted object.
- Use least-privilege credentials scoped to this bucket and prefix. Prefer separate credentials per environment and physical VPS where supported. A writer should have only the required prefix-limited list and object-write/multipart permissions; use a separate read/list identity for restores. Do not grant routine credentials object-delete, bucket-configuration, versioning, or lifecycle permissions. If Cloudeka cannot scope access to a prefix, use a dedicated bucket or otherwise isolate the credential; do not claim prefix isolation that is not enforced.
- Store credentials only in protected GitHub Environment configuration and any required root-owned host file; host-side credential files must have restrictive permissions and never appear in logs. Rotate/revoke credentials through the approved process.
- During initial setup, create and upload a backup, then restore it into an isolated test database before reporting PostgreSQL as recovery-ready. Never overwrite production data during a restore test. Perform and record a restore drill at least quarterly to demonstrate the **RTO <= 4 hours** objective; the backup schedule itself must continue when GitHub Actions is unavailable.
- Record the time and result of each backup and restore test, and surface failures to the operator.
- Use `outbound_marketing` as the database and database user, matching the current local-development configuration. Store the password in the protected Environment secret `OUTBOUND_MARKETING_DB_PASSWORD`; do not include secret values in this document.

The names `BUZ_STG_PROD_1_ID` and `BUZ_STG_PROD_1_SECRET` are the supplied credential names, not proof that the credentials are isolated or least-privilege. Verify the actual permissions and storage capabilities before enabling PostgreSQL `apply`. Do not enable PostgreSQL `apply` until encryption, versioning, lifecycle, credential scope, the prefix, and the initial isolated restore are verified.

## 10. Package updates and reboot handling

- The maintenance window for package updates that may require a reboot is 00:00 GMT+8 (`Asia/Singapore`).
- `validate` may inspect available updates at any time. Before applying package updates, inspect the proposed transaction. Updates known or suspected to require a reboot may be applied only at the approved 00:00 GMT+8 maintenance window; when uncertain, treat an update as reboot-requiring and defer it outside the window.
- The workflow must never reboot the VPS, including when a package manager or service reports that a reboot is required. Disable or reject package-manager settings that would cause an automatic reboot.
- If an update leaves a reboot pending, keep the host running and report the pending status and affected update information without exposing secrets. The supplied proposed reboot-notification recipient is `aristaaldo3@gmail.com`; the delivery mechanism and responsible owner are not supplied. Do not claim a notification was sent until that mechanism is configured and verified.
- Any reboot is outside this bootstrap workflow and must be a separate, manually triggered operation for the exact targeted VPS, with authorization, applicable protected-environment approval, pre-reboot notification, and pre- and post-reboot health checks. Do not implement or enable an automated reboot action until its notification mechanism is configured. It must never select multiple hosts through a broad inventory selection.

## 11. Health checks and acceptance criteria

Bootstrap is successful only when all applicable checks pass:

- No failed critical systemd units.
- Supported OS, target identity, and required base configuration are present.
- Report available memory and active memory pressure. Fail only when the host cannot safely support the selected services or shows active memory exhaustion; do not use a fixed free-memory percentage as a universal pass/fail threshold.
- Warn when any critical filesystem is more than 80% used; fail at 90% used or higher.
- SSH daemon configuration passes validation, password/root SSH login is disabled, and key-based SSH access works for `deploy` after bootstrap access is excluded from the allowlist.
- Account memberships, sudo access, managed directory ownership, and required file permissions match the declared configuration.
- Host firewall rules match the approved policy for IPv4 and IPv6; only expected public ports are reachable. The report must distinguish host firewall checks from the manually managed Sumopod firewall.
- Docker and Compose respond when Docker is selected or required by a dependency.
- Nginx is healthy and the configured HTTPS endpoint succeeds when Nginx and the route are selected.
- If PostgreSQL is enabled, the database is healthy, has persistent storage, is not publicly exposed, and the initial backup/restore proof and ongoing schedule meet Section 9.
- If Alloy is enabled, its service is healthy and delivery of each configured telemetry signal succeeds. Alerting remains unconfigured until its destination is confirmed.
- A pending reboot is explicitly reported and the host remains running.
- The final report distinguishes passed checks, warnings, skipped optional services, pending dependencies, and failures. It must not label an unavailable selected service as healthy; see Section 12 for required report contents.

## 12. Idempotency, recovery, and auditability

- Re-running bootstrap must converge configuration without duplicating users, keys, firewall rules, services, or schedules.
- Existing PostgreSQL data and other persistent service data must not be deleted or reset by a rerun.
- Back up existing managed configuration before replacement and validate staged configuration before activation. Preserve management access while changing SSH or firewall policy; if a new-key login fails, do not disable the old access method.
- Mask secrets and produce a concise, non-secret job summary listing the selected inventory/host, canonical host ID, requested and effective services, existing-service reconciliation results, validation results, warnings, pending reboot status, and any required manual recovery action.

## 13. Decisions and prerequisites before workflow implementation

Use these supplied values as the starting configuration:

1. **Inventories and aliases:** `customer-builder-engine` and `outbound-marketing` under `ansible/inventory/`; aliases are listed in Section 2.3.
2. **Current topology evidence:** all four aliases use `43.157.247.221`; feedback records one active VPS, `buz-prod-1`, as a temporary mapping. Verify this with Sumopod before using it as the canonical host identity.
3. **Account roles:** Sumopod supplies the bootstrap account; manage only `deploy` for ongoing access. Preserve its current passwordless-sudo contract and do not create a separate administrator/break-glass account.
4. **VPS provider:** Sumopod. Provider firewall management is manual unless a supported API is confirmed.
5. **Backup storage:** use the Cloudeka endpoint, region, bucket, credential names, and standard prefix in Section 9; meet RPO <= 12 hours, RTO <= 4 hours, and seven-day retention.
6. **Monitoring:** use the Grafana Cloud endpoints, user/stack identifiers, variable names, and API-token secret in Section 7. The supplied proposed alert recipient is `aristaaldo2@gmail.com`.
7. **Application routes:** use the proposed four-route map in Section 8, including the supplied CBE service name, port, and health path. Verify its target and DNS before enabling a route.
8. **ACME:** use `aristaaldo2@gmail.com` as the supplied registration email when Nginx is selected.
9. **Reboot policy:** inspect updates before applying them; defer reboot-requiring updates outside the 00:00 GMT+8 maintenance window. Bootstrap never reboots. Any reboot operation is separate and manually triggered.

Resolve these prerequisites before `apply`, as applicable to the selected target and services:

1. Verify each target's current address, physical-host ID, provider bootstrap username, and environment. Verify host-level FQDNs only where host-level DNS/TLS checks are required. Resolve shared-host aliases with one effective GitHub Environment approval/credential policy.
2. Configure the protected `Staging` or `Production` Environment, the provider bootstrap account's per-host `<NORMALIZED_HOST_ID>_PASSWORD` secret, and the independently verified SSH host-key pin. Configure the separate `deploy` key pair using the names in Section 4.
3. Verify Sumopod's provider-side rules for the physical VPS, including IPv6 and the supported manual change process. Use a restricted SSH source where feasible; otherwise obtain explicit approval for the documented public-source exception.
4. Before selecting Docker, pin approved Docker Engine and Compose package versions from Docker's official Ubuntu APT repository. Before selecting Nginx, approve its image version and immutable digest, the route target, DNS, and TCP/80/443 reachability.
5. Before selecting PostgreSQL, approve and pin its image digest, verify Cloudeka encryption/versioning/lifecycle and least-privilege access, configure the standard prefix and database secret, and pass the isolated restore test.
6. Before selecting Alloy, approve its package source and version and configure the supplied Grafana values and token. Alerting remains disabled until its recipient and notification mechanism are confirmed.
7. Configure and verify a notification mechanism and responsible owner before enabling alert routes or any separate automated reboot operation. The supplied reboot-notification recipient is `aristaaldo3@gmail.com`; do not treat the address alone as proof that delivery is configured.

An unresolved prerequisite for an unselected optional service must not block an otherwise valid `apply`. Missing or unverified prerequisites for the selected target, effective service plan, or required security baseline must stop that run before mutation.
