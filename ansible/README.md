# Ansible

This directory is the central source of truth for Ansible configuration used by Buzilion VPS deployments. `ansible.cfg` provides shared configuration, `requirements.txt` pins the Ansible controller package, and `requirements.yml` pins Galaxy collections. GitHub workflows use these manifests for dependency installation and cache invalidation.

## Reusable application deployment

Applications call `.github/workflows/deploy-to-vps.yml`, which checks out this repository's Ansible configuration, installs its dependencies, validates the inventory and playbook, and runs `playbooks/deployment.yml` with the `app_deployment` role. The workflow receives the app image, Compose project and service names, deployment directory, required proxy network, optional backend network, inventory, target environment, immutable image tag, and the caller's list of required runtime keys.

Each app should maintain a GitHub Environment for every remote `target_environment` it uses (CustomerBuilderEngine uses `staging` and `production`). Development runs locally on each developer workstation and is not a VPS deployment target. The reusable workflow binds its job to the requested remote environment, so the caller's environment-specific values are used. Configure these values separately for every app:

**Variables**
- `VPS_KNOWN_HOSTS` — pinned `known_hosts` entry for the target VPS.
- `APP_RUNTIME_VARIABLES_JSON` — JSON object of non-secret runtime environment variables, for example `{"NEXT_PUBLIC_SUPABASE_URL":"https://example.supabase.co","NEXT_PUBLIC_SUPABASE_ANON_KEY":"public-key","PORT":"3000"}`.
- `GHCR_USERNAME` — optional username override; defaults to the workflow actor.

**Secrets**
- `VPS_SSH_PRIVATE_KEY` — SSH private key matching the VPS authorized key.
- `APP_RUNTIME_SECRETS_JSON` — optional JSON object of app-specific secret environment variables, for example `{"SUPABASE_SERVICE_ROLE_DATABASE_URL":"...","INDOSMM_API_KEY":"...","CRON_SECRET":"..."}`.
- `GHCR_TOKEN` — optional GHCR token override; defaults to the caller's `GITHUB_TOKEN`.
- `CENTRALDEVOPS_READ_TOKEN` — optional read-only token if the caller's `GITHUB_TOKEN` cannot check out a private CentralDevOps repository.

Runtime JSON values must be strings, use valid environment variable names, and must not duplicate a name between the variables and secrets objects. Each caller lists required keys in `required_runtime_variables_json`; deployment fails if one is missing or empty. Do not put credentials in inventory. The workflow masks each secret value before passing the combined runtime environment to Ansible and Docker Compose. The application image must define a Docker healthcheck; deployment waits for it to become healthy. Node.js applications can also set the optional `healthcheck_path` input to require that endpoint to return HTTP 200. The deployment creates the configured proxy network and, when configured, backend network if either is missing.

The `customer-builder-engine` inventory defines the `staging` and `production` groups. Do not add a development group: local development does not use a VPS inventory. Other applications can add their own inventory file with groups matching these supported remote environments. The workflow limits the play to the requested group.

## VPS bootstrap

Run `.github/workflows/bootstrap-vps.yml` manually. Choose exactly one approved inventory, enter one exact host alias, select `validate` (the read-only default) or `apply`, then choose optional services. Selecting Nginx or PostgreSQL adds Docker to the effective service plan. Development remains local and is not a VPS target. `apply` is accepted only from the repository's default branch and runs in the target's protected `Staging` or `Production` Environment.

The selected inventory host must define a verified `ansible_host`, provider-created `bootstrap_user` with non-interactive sudo, and stable `bootstrap_host_id`; its environment must be unambiguous through the `staging` or `production` group. Keep `ansible_user: deploy` for the separate application deployment workflow; bootstrap connects as `bootstrap_user` and does not assume `ubuntu`. The workflow rejects unknown aliases, arbitrary addresses, unresolved address/identity collisions, unsupported PostgreSQL targets, and route DNS that does not match the selected VPS. Current inventory identity blockers are tracked in [`docs/feedback/implementation_gap_v1.md`](../docs/feedback/implementation_gap_v1.md).

The playbook `playbooks/bootstrap.yml` orchestrates reusable roles and task files under `roles/bootstrap*`. Its assessment phase is read-only. For a fresh VPS, the workflow first authenticates as `bootstrap_user` with the protected per-host SSH password secret. It installs the `deploy` public key and verifies a new deploy-key SSH session before disabling SSH password and keyboard-interactive authentication. On later runs, it falls back to the deploy key when the bootstrap password is no longer accepted. Host-key checking remains enabled. Package transactions are simulated before apply and run only during the 00:00-00:59 Asia/Singapore maintenance hour; transactions involving explicitly pinned service packages are deferred. Daily APT package-list updates remain enabled, but unattended package installs and automatic reboots are disabled. The bootstrap never reboots the VPS; if an update leaves a reboot pending, the run reports it for a separate approved manual maintenance action. Provider-side Sumopod firewall rules remain manual and are not claimed as verified by automation.

Create protected `Staging` and `Production` Environments in the CentralDevOps repository. Configure separate bootstrap and deploy key pairs in each applicable Environment:

**Variables**
- For Staging, `BOOTSTRAP_<NORMALIZED_HOST_ID>_SSH_KNOWN_HOSTS`; for Production, `BUZ_PROD_KNOWN_HOSTS` — independently verified pinned `known_hosts` entry for the inventory address. The workflow maps the selected Environment variable's stored value to the runner's `BOOTSTRAP_KNOWN_HOSTS`; it does not generate a trusted host key.
- For Staging, `STG_SSH_PUBLIC_KEY`; for Production, `<NORMALIZED_HOST_ID>_SSH_PUBLIC_KEY` — deploy account's Ed25519 public key.
- `SUMOPOD_FIREWALL_REVIEWED` — `true` only after checking provider rules for the physical VPS.
- `SUMOPOD_SSH_SOURCE_RESTRICTED` — `true` only when provider SSH sources are restricted to approved management egress.
- `SUMOPOD_PUBLIC_SSH_EXCEPTION_APPROVED` — `true` only for an owner-approved public-source exception.
- `BOOTSTRAP_SHARED_HOST_APPROVED` — `true` only after reviewing an explicitly resolved same-environment alias collision.

**Secrets**
- `<NORMALIZED_HOST_ID>_PASSWORD` — password for the provider-created bootstrap account, used for initial SSH access to a fresh VPS (for example, `BUZ_PROD_1_PASSWORD` for `bootstrap_host_id: buz-prod-1`).
- For Staging, `VPS_SSH_PRIVATE_KEY`; for Production, `<NORMALIZED_HOST_ID>_SSH_PRIVATE_KEY` — deploy key matching the selected public-key variable.

`<NORMALIZED_HOST_ID>` is the uppercase `bootstrap_host_id` with hyphens replaced by underscores. Store no credentials in inventory or dispatch inputs. The password is passed only through the protected runner environment and temporary permission-restricted files; remove its secret after initial setup if subsequent runs should use deploy-key access only.

Configure optional service variables only when selecting that service. Docker requires exact package pins: `BOOTSTRAP_DOCKER_CE_PACKAGE_VERSION`, `BOOTSTRAP_DOCKER_CLI_PACKAGE_VERSION`, `BOOTSTRAP_CONTAINERD_PACKAGE_VERSION`, `BOOTSTRAP_BUILDX_PACKAGE_VERSION`, and `BOOTSTRAP_COMPOSE_PACKAGE_VERSION`. Nginx requires digest-pinned `BOOTSTRAP_NGINX_IMAGE` and `BOOTSTRAP_CERTBOT_IMAGE`. PostgreSQL requires digest-pinned `BOOTSTRAP_POSTGRES_IMAGE` and `BOOTSTRAP_AWS_CLI_IMAGE`, image-specific `BOOTSTRAP_POSTGRES_DATA_DIRECTORY`, and `BOOTSTRAP_POSTGRES_BACKUP_POLICY_VERIFIED=true` after the documented storage and recovery policy is verified. Alloy requires `BOOTSTRAP_ALLOY_PACKAGE_VERSION`, `BOOTSTRAP_ALLOY_DELIVERY_VERIFIED=true`, and the per-host Grafana Cloud variables and token named in the v3 requirements.

PostgreSQL additionally uses `OUTBOUND_MARKETING_DB_PASSWORD`, `BUZ_STG_PROD_1_ID` / `BUZ_STG_PROD_1_SECRET`, and separate restore credentials `BUZ_STG_PROD_1_RESTORE_ID` / `BUZ_STG_PROD_1_RESTORE_SECRET`. The playbook stores credentials in root-only files, never exposes database ports, uses the persistent `outbound_postgres_data` volume, and configures scheduled off-host backups and an isolated initial restore test. Bucket lifecycle, versioning, encryption policy, and credential scope still require the manual verification recorded in the implementation-gap document.
