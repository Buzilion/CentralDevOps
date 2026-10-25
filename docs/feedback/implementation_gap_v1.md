# Bootstrap VPS v3 — implementation gaps

The new workflow and modular Ansible artifacts are in place. The implementation is deliberately fail-closed: `validate` and `apply` will stop when required identity, key, approval, version, or recovery inputs are missing. The items below require owner/provider confirmation before the affected targets or optional services can complete a run.

## 1. Inventory identity and host collisions — blocks every current target

Both selectable inventories currently map all four aliases to `ansible_host: 43.157.247.221` and `ansible_user: deploy`. All four currently define `bootstrap_user: ubuntu`; the staging aliases use `bootstrap_host_id: buz-stg-1`, and the production aliases use `bootstrap_host_id: buz-prod-1`. Those IDs conflict with the shared address and are not proof of separate physical VPSs. The bootstrap workflow uses `bootstrap_user`, not `ansible_user`, for initial access.

Confirm the physical topology and addresses with Sumopod before treating these IDs as verified. If the aliases share one VPS, use one verified `bootstrap_host_id` and an effective `bootstrap_environment: production` policy for aliases that span staging and production. If they are separate VPSs, correct the duplicate addresses and retain separate IDs. The preflight rejects an `ansible_host` collision when physical identity or bootstrap-environment ownership is unresolved.

The current mappings also span both `staging` and `production` at the same address, but assign different host IDs (`buz-stg-1` and `buz-prod-1`). Do not infer one physical VPS from the address alone. If Sumopod confirms these aliases share a VPS, update every alias to the same verified `bootstrap_host_id` and configure one effective `bootstrap_environment` policy (Production when any alias is production). The app inventory groups remain separate for route selection. The workflow allows shared aliases without a separate approval variable only when physical identity and bootstrap policy agree; otherwise correct the addresses or identities. Also confirm environment-specific Docker network names and deployment isolation before allowing staging and production routes to share one VPS.

## 2. Protected SSH configuration

For each verified physical host, configure the protected `Staging` or `Production` Environment with:

- `<NORMALIZED_HOST_ID>_PASSWORD` for the provider-created bootstrap account's initial SSH login (for example, `BUZ_PROD_1_PASSWORD`). Do not put the password in inventory, dispatch inputs, or this document.
- For Staging, `BOOTSTRAP_<NORMALIZED_HOST_ID>_SSH_KNOWN_HOSTS`; for Production, `BUZ_PROD_KNOWN_HOSTS`, containing an independently verified pinned host key for the selected `ansible_host`. The workflow does not generate the trusted host key.
- For Staging, `VPS_SSH_PRIVATE_KEY` and `STG_SSH_PUBLIC_KEY`; for Production, `<NORMALIZED_HOST_ID>_SSH_PRIVATE_KEY` and `<NORMALIZED_HOST_ID>_SSH_PUBLIC_KEY` for a separate Ed25519 deploy key pair.

The workflow uses the bootstrap password for a fresh VPS, installs and verifies the deploy key, then disables SSH password and keyboard-interactive authentication. It falls back to the deploy key for subsequent runs on an already-hardened VPS. The deploy private key must be unencrypted and match its public key. Confirm that the `Staging` and `Production` GitHub Environments exist and that Production approval/deployment-branch restrictions are configured. The workflow limits `apply` to the repository default branch, but repository/environment protection settings cannot be verified from this code.

## 3. Sumopod provider firewall

No supported Sumopod firewall API or verified per-host provider rule set is available in the repository. Before `apply`, inspect the exact VPS rules, including IPv6, TCP/22 management sources, and TCP/80/443 only for Nginx. Configure the Environment variables `SUMOPOD_FIREWALL_REVIEWED=true` and either `SUMOPOD_SSH_SOURCE_RESTRICTED=true` or the owner-approved `SUMOPOD_PUBLIC_SSH_EXCEPTION_APPROVED=true`. These are operator attestations, not automated provider checks.

## 4. Optional service approvals and secrets

All service inputs default to off. Configure the following only for the selected services:

- **Docker:** approve and configure exact package versions in `BOOTSTRAP_DOCKER_CE_PACKAGE_VERSION`, `BOOTSTRAP_DOCKER_CLI_PACKAGE_VERSION`, `BOOTSTRAP_CONTAINERD_PACKAGE_VERSION`, `BOOTSTRAP_BUILDX_PACKAGE_VERSION`, and `BOOTSTRAP_COMPOSE_PACKAGE_VERSION`.
- **Nginx:** approve immutable digest references in `BOOTSTRAP_NGINX_IMAGE` and `BOOTSTRAP_CERTBOT_IMAGE`. Verify the proposed FQDN-to-host mapping and DNS A/AAAA records. The workflow validates DNS, issues/retains Let's Encrypt certificates, installs a daily renewal timer, and reports an undeployed application route as pending.
- **PostgreSQL:** approve immutable `BOOTSTRAP_POSTGRES_IMAGE` and `BOOTSTRAP_AWS_CLI_IMAGE` digests, and set `BOOTSTRAP_POSTGRES_DATA_DIRECTORY` to the data directory required by that exact image. For each inventory application, configure `<APP>_DB_PASSWORD`, app-scoped S3 writer and restore credentials, and `<APP>_POSTGRESQL_BACKUP_POLICY_VERIFIED=true`; `<APP>` is derived from the inventory filename. Before setting the policy attestation, verify the inventory's bucket versioning, lifecycle-age semantics, encryption, least-privilege/prefix scope, and credential isolation. The role requests AES256 for each upload, checks the returned object encryption, schedules the inventory's backup interval, and performs an isolated initial restore test. It does not independently inspect bucket lifecycle/versioning policy or run quarterly restore drills; those remain operator-owned.
- **Grafana Cloud Alloy:** approve `BOOTSTRAP_ALLOY_PACKAGE_VERSION` and configure the per-host `BUZ_PROD_1_GRAFANA_CLOUD_*` values and `BUZ_PROD_1_GRAFANA_CLOUD_API_TOKEN` (the normalized host ID determines the variable prefix). `BOOTSTRAP_ALLOY_DELIVERY_VERIFIED=true` is currently a manual gate. Confirm the actual Grafana delivery test and how containerized applications will send traces; Alloy currently listens for OTLP only on host loopback. No alert destination is configured.

The workflow stores service secrets in temporary protected Ansible variables files or root-only host files and does not print them. PostgreSQL and Alloy selection fail before remote mutation when their required manual readiness gates are absent.

## 5. Maintenance, notifications, and host capacity

The implementation never reboots. Package upgrades are simulated first and deferred outside the `00:00` hour in `Asia/Singapore`; confirm whether the approved window means the full 00:00–00:59 hour or only a narrower start time. If a proposed system transaction includes Docker, Nginx, PostgreSQL, or Alloy packages, the whole transaction is deferred so unselected or explicitly pinned service packages are not changed by the base role. Pending reboot state and affected package names are reported, but the supplied reboot-notification recipient has no verified delivery mechanism or responsible owner, so no notification is sent.

The playbook reports available memory and memory pressure, warns above 80% critical filesystem use, and fails at 90%. The requirements do not specify per-service minimum resource budgets or a quantitative memory-pressure threshold, so the implementation does not claim a universal memory-capacity pass. Review the selected-service profile on each VPS before `apply`.

## 6. GitHub setup and initial validation

The workflow requires the `Staging` and `Production` protected Environments and the variables/secrets listed in `ansible/README.md`. GitHub Environment rules and Sumopod settings must be configured outside this repository. Once host identity and credentials are verified, run `validate` first and review its non-secret report before `apply`.

## 7. Validation audit depth

The read-only assessment verifies host identity/access, Ubuntu version, sudo, failed units, public listeners, host-firewall allow rules, disk usage, package-update candidates, pending reboot state, and selected PostgreSQL health/backup freshness. It reports Docker availability and existing container names, but does not yet fully compare Docker package pins, Nginx's existing route/configuration/certificate state, or Alloy's installed configuration and telemetry delivery during `validate`. The corresponding apply roles validate their staged configuration and selected-service health before reporting success; extend the read-only inspectors before using `validate` as a complete drift/acceptance audit.
