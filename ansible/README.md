# Ansible

This directory is the central source of truth for Ansible configuration used by Buzilion VPS deployments. `ansible.cfg`, `requirements.txt`, and `requirements.yml` provide the shared Ansible configuration, runtime, and collections; common server roles remain under `roles/`.

## Reusable application deployment

Applications call `.github/workflows/deploy-to-vps.yml`, which checks out this repository's Ansible configuration, installs its dependencies, validates the inventory and playbook, and runs `playbooks/deployment.yml` with the `app_deployment` role. The workflow receives the app image, Compose project and service names, deployment directory, proxy network, inventory, target environment, immutable image tag, and the caller's list of required runtime keys.

Each app should maintain a GitHub Environment for every `target_environment` it uses (CustomerBuilderEngine uses `development`, `staging`, and `production`). The reusable workflow binds its job to the requested environment, so the caller's environment-specific values are used. Configure these values separately for every app:

**Variables**
- `VPS_KNOWN_HOSTS` — pinned `known_hosts` entry for the target VPS.
- `APP_RUNTIME_VARIABLES_JSON` — JSON object of non-secret runtime environment variables, for example `{"NEXT_PUBLIC_SUPABASE_URL":"https://example.supabase.co","NEXT_PUBLIC_SUPABASE_ANON_KEY":"public-key","PORT":"3000"}`.
- `GHCR_USERNAME` — optional username override; defaults to the workflow actor.

**Secrets**
- `VPS_SSH_PRIVATE_KEY` — SSH private key matching the VPS authorized key.
- `APP_RUNTIME_SECRETS_JSON` — optional JSON object of app-specific secret environment variables, for example `{"SUPABASE_SERVICE_ROLE_DATABASE_URL":"...","INDOSMM_API_KEY":"...","CRON_SECRET":"..."}`.
- `GHCR_TOKEN` — optional GHCR token override; defaults to the caller's `GITHUB_TOKEN`.
- `CENTRALDEVOPS_READ_TOKEN` — optional read-only token if the caller's `GITHUB_TOKEN` cannot check out a private CentralDevOps repository.

Runtime JSON values must be strings, use valid environment variable names, and must not duplicate a name between the variables and secrets objects. Each caller lists required keys in `required_runtime_variables_json`; deployment fails if one is missing or empty. Do not put credentials in inventory. The workflow masks each secret value before passing the combined runtime environment to Ansible and Docker Compose. The application image must define a Docker healthcheck; deployment waits for it to become healthy. Node.js applications can also set the optional `healthcheck_path` input to require that endpoint to return HTTP 200. The deployment creates the configured proxy network if it is missing.

The `customer-builder-engine` inventory defines the `development`, `staging`, and `production` groups. Other applications can add their own inventory file with a group matching each `target_environment`. The workflow limits the play to the requested group.

## VPS bootstrap

Run `.github/workflows/bootstrap-vps.yml` manually and enter one or more exact Ansible host aliases in the `target_hosts` input, separated by commas (for example, `buz-dev-1,buz-prod-1`). GitHub's manual-dispatch form has no multi-select control, so the workflow validates this text input against all inventory sources under `ansible/inventory/`; groups, wildcards, and unknown aliases are rejected.

Selected hosts are grouped by their `development`, `staging`, or `production` inventory group. Each group runs serially as a separate GitHub Environment job, retaining that environment's credentials and approval rules. Hosts in one group share that environment's bootstrap credentials (`DEV_*`, `STG_*`, or `PROD_*`); its corresponding `*_VPS_KNOWN_HOSTS` variable must contain pinned keys for every selected VPS.

For the `bootstrap-vps.yml` workflow, create `development`, `staging`, and `production` Environments in the CentralDevOps repository. Configure each environment with:

**Variables**
- `DEV_VPS_USERNAME`, `STG_VPS_USERNAME`, or `PROD_VPS_USERNAME` — username for the selected VPS.
- `DEV_VPS_KNOWN_HOSTS`, `STG_VPS_KNOWN_HOSTS`, or `PROD_VPS_KNOWN_HOSTS` — pinned host keys for the selected VPS.
- `DEV_SSH_PUBLIC_KEY`, `STG_SSH_PUBLIC_KEY`, or `PROD_SSH_PUBLIC_KEY` — public key to install for the deployment account.

**Secrets**
- `DEV_VPS_PASSWORD`, `STG_VPS_PASSWORD`, or `PROD_VPS_PASSWORD` — temporary bootstrap password for the selected VPS.

The app deployment workflow uses the calling repository's `GITHUB_TOKEN` with `packages: read` to pull its private GHCR image. Grant that repository access to the package in GHCR package settings. The deployment account must have passwordless sudo; the VPS must have Docker Engine and the Docker Compose v2 plugin installed. Keep SSH host-key checking enabled and configure a production environment approval policy appropriate to the deployment process.

Deployments require the full 40-character commit SHA from a successful image build. The role deploys the exact GHCR image, joins the configured external proxy network without publishing a host port, and waits for the image's Docker healthcheck. Database migrations remain a separate release operation.
