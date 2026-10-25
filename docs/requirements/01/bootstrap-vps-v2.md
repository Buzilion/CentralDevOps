# Requirements: GitHub Workflow to Bootstrap a VPS

**Status:** Enhanced draft for review  
**Scope:** Requirements only; this document does not implement the workflow.

## 1. Goal and scope

Provide a manually triggered GitHub Actions workflow that configures one already-provisioned VPS into a secure, production-ready host for the selected services.

The workflow must:

- Configure an existing VPS; creating or resizing VPS resources through a cloud-provider API is out of scope.
- Target exactly one host per run, selected from an approved Ansible inventory.
- Establish a secure host baseline and install the selected production services.
- Be safe to retry and report clearly when a precondition or configuration step fails.
- Keep application build and release deployment in the existing, separate application-deployment workflow.

The existing `bootstrap-vps.yml` workflow and Ansible roles may inform requirements, but the new workflow design must not be constrained to or copied from their current implementation.

## 2. Supported target and dispatch inputs

### Supported target

- Ubuntu Server 24.04 LTS is the only supported operating system for the first version.
- The VPS must already be reachable over SSH and have a pre-created account with the privileges needed for initial configuration.
- The selected Ansible inventory must provide the connection address and the public DNS hostname for the host. The hostname must be under `buzilion.id`, and its DNS records must already point to the selected VPS.
- Inventory must not contain passwords, private keys, or other credentials.

### Manual workflow inputs

The workflow must use `workflow_dispatch` and prompt the operator for:

1. **Inventory:** one approved inventory file from a controlled list.
2. **Target host:** one exact Ansible host alias from that inventory.
3. **Execution mode:** `validate` (default, no remote changes) or `apply` (perform the bootstrap).
4. **Optional service selections:** PostgreSQL and Grafana Cloud Alloy, both defaulting to off. Base hardening, Docker, and containerized Nginx are part of the standard profile.

GitHub Actions cannot dynamically populate a host dropdown from an inventory file. The host input should therefore be a string, then validated before any remote changes. Reject unknown inventory files, aliases not present in the selected inventory, groups, wildcards, multiple hosts, arbitrary IP addresses, and arbitrary DNS names.

The inventory must identify the target's environment unambiguously so `apply` can use the corresponding protected GitHub Environment. Production changes require the production Environment's approval rules. Runs targeting the same host must not execute concurrently.

Treat all dispatch values as untrusted input: validate against strict allowlists and do not interpolate raw values into shell scripts. Restrict `apply` to an approved protected ref, grant the workflow only the permissions it needs, and pin third-party actions to reviewed immutable revisions.

### Inventory contract

Each selectable host must provide:

- An Ansible connection address, such as `ansible_host`.
- An explicit public FQDN, such as `bootstrap_fqdn`; do not infer it from the host alias or IP address.
- An unambiguous environment classification for GitHub approval and credential selection.

**Repository gap:** the currently inspected inventory files contain host aliases and `ansible_host` addresses, but no obvious public FQDN field. Add and validate an explicit hostname field before relying on inventory for TLS and HTTPS checks.

## 3. Preconditions and credential handling

- The initial SSH username is a pre-created sudo-capable bootstrap account and must come from approved inventory or GitHub Environment configuration, not a free-form dispatch input. If initial password authentication is used, its password must come from a protected GitHub Environment secret, never from a workflow-dispatch input.
- Pin and verify the VPS SSH host key. Do not trust an unverified key collected during the same workflow run.
- Store public SSH keys in GitHub Environment variables or another approved non-secret configuration store. Store matching private keys only in protected GitHub Environment secrets so the workflow can verify the final key-based access.
- Store credentials for optional services only in protected GitHub Environment secrets. Do not print secrets, put them in command-line arguments, include them in artifacts, or expose them in workflow summaries.
- Use minimum required workflow permissions. Temporary credential files must have restrictive permissions and be removed when the job ends.
- If a selected service requires missing credentials or configuration, fail before applying changes and identify the missing configuration without revealing secret values.

## 4. Accounts and SSH hardening

The final host access model is:

- `deploy` is the automation account used by the separate application-deployment workflow. It uses key-only SSH and has the passwordless sudo and Docker access required by that workflow.
- A separate key-only administrator account provides controlled break-glass access. Its account name and whether it is created or verified as pre-existing must be configured explicitly.
- Only approved accounts may remain in the final SSH allowlist. The initial bootstrap account must not be left as an unreviewed alternate access path.
- Membership in the Docker group is effectively root-level access. The workflow must grant it only to explicitly approved accounts and document this privilege.

Before disabling password authentication, the workflow must:

1. Install the approved public keys for `deploy` and the administrator account.
2. Verify that each account can establish a new SSH session using its matching private key.
3. Verify the required sudo access for each account.
4. Validate the proposed SSH daemon configuration with `sshd -t`.

After successful checks, configure and verify:

- Public-key authentication enabled.
- Password and keyboard-interactive authentication disabled.
- Root SSH login disabled.
- Maximum authentication attempts set to three.
- SSH access limited to the approved account allowlist.
- Fail2ban installed, enabled, and protecting SSH.

Keep the original session available until the new-key sessions and configuration validation pass. If any access check fails, stop before locking out the bootstrap path and restore the previous SSH configuration.

## 5. Firewall and public exposure

The host firewall must:

- Deny inbound traffic by default and allow outbound traffic by default.
- Permit only public TCP ports **22, 80, and 443** for this standard profile.
- Apply equivalent policy to IPv4 and IPv6 when IPv6 is configured.
- Keep PostgreSQL and application container ports private; do not publish PostgreSQL port 5432 to the public network.
- Detect and report other publicly exposed ports. Do not silently remove an unrecognized rule if doing so could disrupt an existing service; stop for an explicit decision.

Port 83 is not required; it was a typo for port 80. Port 80 is required for the selected Let's Encrypt HTTP-01 challenge and may redirect normal traffic to HTTPS.

Because the administrator's laptop IP and GitHub-hosted runner egress can change, SSH on TCP/22 is expected to be reachable from public IPv4/IPv6 addresses in this version. This broader exposure is accepted in exchange for avoiding brittle IP allowlists and must be mitigated by key-only authentication, disabled root/password login, Fail2ban, and the SSH retry limit. A private VPN or fixed-egress gateway can be considered in a later revision.

The host firewall and any provider-level firewall must not contradict each other. If the VPS provider exposes a supported API, provider firewall rules should be brought into the same policy. Otherwise, the workflow must clearly state and verify the required provider-side manual configuration; it must not claim the host is fully protected when that boundary is unknown.

## 6. Workflow execution phases

### 6.1 Validate (no mutation)

Before applying changes, validate:

- The inventory file, exact host alias, environment, hostname, and required inputs.
- SSH host-key pinning and connectivity using the approved bootstrap account.
- Sudo capability and Ubuntu 24.04 LTS version.
- Required secrets and service configuration for the selected profile.
- DNS resolution of the inventory hostname to the selected host address, including any configured AAAA record.
- Baseline health thresholds in Section 10.

The `validate` mode must not change the VPS. It must return a failing status for an invalid target, unsupported host, missing prerequisite, or failed safety check.

### 6.2 Apply baseline and services

For an approved `apply` run:

1. Capture a non-secret baseline report of OS, resource use, failed critical services, and existing public listeners.
2. Apply available Ubuntu package updates and install the required base/security packages. Do not perform a distribution-release upgrade.
3. Establish and verify the final SSH accounts and keys before applying the SSH lock-down.
4. Apply the host firewall and provider-firewall requirements without dropping the active management path.
5. Install and enable Docker Engine and the Docker Compose plugin.
6. Create or verify the shared Docker network used by the reverse proxy and application deployments.
7. Start the standard Nginx container and any selected optional services.
8. Configure TLS, persistence, backup, and monitoring for the selected profile.

The workflow must stop on the first failed mandatory phase, preserve useful diagnostics, and never report success after a partial failure. It must not reboot automatically. If updates require a reboot, report that fact and wait for an explicitly approved maintenance policy.

## 7. Standard and optional services

### Docker and Nginx (standard profile)

- Install Docker Engine and Docker Compose v2 from a trusted package source; enable Docker at boot.
- Run Nginx in a container, connected to the shared Docker network used by the separate app-deployment workflow.
- Publish only Nginx's HTTP/HTTPS ports on the host: TCP 80 and 443.
- Do not publish application container ports directly to the public interface.
- Configure the proxy to route only to explicitly configured application upstreams and to redirect ordinary HTTP requests to HTTPS while allowing the ACME challenge path.
- Use maintained, explicitly selected container versions; do not rely on an unbounded `latest` tag.
- Ensure containers have suitable restart behavior and health checks.

### PostgreSQL (optional)

When selected:

- Run PostgreSQL as a container on the VPS.
- Keep database files in a persistent host-backed or named volume outside the container's writable layer. Container restart or replacement must not delete database data.
- Do not publish PostgreSQL to the public network. Permit access only from explicitly approved local/container networks.
- Keep database credentials in protected configuration; never place them in the Compose file committed to the repository or in workflow logs.
- Define and verify a health check (for example, `pg_isready`) and explicit data-directory ownership.
- A rerun or container recreation must preserve the data volume. Never use a destructive volume-removal command as part of bootstrap.

### Grafana Cloud Alloy (optional)

When selected:

- Install and start Alloy as a managed container/service using the approved Grafana Cloud configuration.
- Retrieve authentication tokens from protected secrets and never log them.
- Verify that Alloy starts and can deliver the configured telemetry. The exact metrics/logs to collect and alert destinations remain an open decision.
- If Alloy is not selected, report monitoring as not configured; do not imply that external telemetry or alerting is active.

## 8. TLS and DNS

- Use Let's Encrypt with the HTTP-01 challenge for the explicit inventory hostname under `buzilion.id`.
- Require public DNS to resolve to the selected VPS and TCP/80 to be reachable for certificate issuance and renewal.
- Configure HTTPS on TCP/443 and redirect non-challenge HTTP traffic to HTTPS.
- Configure automatic certificate renewal and verify the renewal configuration without replacing a valid production certificate unnecessarily.
- Verify the public HTTPS endpoint for every enabled public service using its configured health-check path.

The exact FQDN(s), ACME registration email, DNS A/AAAA values, and public health-check paths must be supplied in inventory or protected environment configuration before implementation.

## 9. PostgreSQL backup and recovery (when PostgreSQL is selected)

- Store backups off-host in Cloudeka's S3-compatible storage.
- Complete successful backups often enough that no more than 12 hours of data can be lost; alert or fail validation if the last successful backup is older than 12 hours.
- Retain seven days of backups.
- Encrypt backups in transit and at rest. Use provider-side encryption where available; otherwise encrypt before upload.
- Prefer a workload/instance identity if the VPS provider supports one. Otherwise use a dedicated, least-privilege Cloudeka credential limited to the required bucket/prefix and operations. Install any host-side credential with restrictive permissions and never expose it in logs.
- During initial setup, create and upload a backup, then restore it into an isolated test database before reporting PostgreSQL as recovery-ready. Continue this restore test daily using a schedule that works when GitHub Actions is unavailable; never overwrite the production database during a test.
- Record the time and result of each backup and restore test, and surface failures to the operator.
- Meet the stated recovery objectives: **RPO <= 12 hours** and **RTO <= 4 hours**, demonstrated by restoring from the off-site backup.

The backup endpoint, bucket, region, encryption/versioning features, lifecycle behavior, and supported credential mechanism must be configured before implementation.

## 10. Health checks and acceptance criteria

The bootstrap is successful only when all applicable checks pass:

- No failed critical systemd units.
- Supported OS and required configuration are present.
- `MemAvailable` is at least 10% of total memory; less than 10% is a failure.
- Warn when any critical filesystem is more than 80% used; fail at 90% used or higher.
- SSH daemon configuration passes validation, password/root SSH login is disabled, and separate key-based logins work for both `deploy` and the administrator account.
- Host/provider firewall rules match the approved policy for IPv4 and IPv6; only expected public ports are reachable.
- Docker and Compose respond; Nginx is healthy and the configured HTTPS endpoint succeeds.
- If PostgreSQL is enabled, the database is healthy, has persistent storage, is not publicly exposed, and the initial backup/restore proof and ongoing schedule meet Section 9.
- If Alloy is enabled, its service is healthy and telemetry delivery succeeds.
- The final report distinguishes passed checks, warnings, skipped optional services, and failures.

## 11. Idempotency, recovery, and auditability

- Re-running bootstrap must converge configuration without duplicating users, keys, firewall rules, services, or schedules.
- Existing PostgreSQL data and other persistent service data must not be deleted or reset by a rerun.
- Back up existing SSH and firewall configuration before replacing it; validate staged configuration before activation.
- Apply SSH and firewall changes in a way that preserves or can restore management access. If a new-key login fails, do not disable the old access method.
- Serialize runs per target host to avoid overlapping changes.
- Mask secrets and produce a concise, non-secret job summary listing the selected inventory/host, selected services, validation results, warnings, and any required manual recovery action.
- The workflow must not silently fall back to insecure authentication, permissive firewall rules, or success-shaped defaults when inputs are invalid.

## 12. Decisions still required before workflow implementation

1. **Inventory/FQDN:** Which inventory files should be selectable, and what exact public FQDN belongs to each target? Add an explicit FQDN field (and environment mapping) to each selectable host; the current inventory files inspected expose aliases and addresses but no obvious FQDN field.
2. **Accounts:** Is the initial bootstrap account the same account as `deploy` or a separate temporary account? What is the final administrator/break-glass account name, and should bootstrap create it or verify a pre-created account?
3. **VPS provider firewall:** Which provider controls the VPS network firewall, and can its firewall be managed through an API? Cloudeka is identified as the backup-storage provider, not necessarily the VPS provider.
4. **Cloudeka storage:** What are the S3 endpoint, bucket, and region, and which encryption, lifecycle, versioning, and credential options does the account support?
5. **Grafana Cloud:** Which Alloy endpoint/token configuration, telemetry signals, and alert destinations should be configured?
6. **Proxy routes and TLS:** What FQDN-to-upstream mapping and HTTPS health-check path should be used for each application? Which ACME registration email should be configured?
7. **Maintenance policy:** When may package changes that require a reboot be applied? Until then, the workflow must report a required reboot and leave the host running.
