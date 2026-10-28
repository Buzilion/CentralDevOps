# CentralDevOps: GitHub Environment, Variables, Secrets, and Ansible Inventory Naming

## User questions

1. Currently, CentralDevOps has two environments, `Staging` and `Production`. How should GitHub environment variables and secrets be named as the infrastructure grows to include multiple different VPS instances in each environment? How should this work with the current Ansible inventory structure, which separates `Staging/hosts.yml` and `Production/hosts.yml`?
2. What conventional naming scheme is suitable for a scalable GitHub infrastructure platform, including environment variables and secrets?

---

## 1. Recommended approach for multiple VPS per environment

**Keep the two GitHub Environments, `Staging` and `Production`. Do not create one GitHub Environment per VPS.**

Treat GitHub Environments as deployment and security boundaries, and let Ansible inventory manage the individual servers. Ansible supports grouping multiple hosts by their purpose, assigning variables to groups, and targeting selected hosts without maintaining a separate GitHub variable for every server.

The principle is that **the variable name stays the same across environments; its value changes according to the selected GitHub Environment.** For example, `ANSIBLE_INVENTORY_PATH` points to the staging inventory in `Staging` and the production inventory in `Production`.

Keep separate inventories, which helps prevent an infrastructure operation intended for staging from accidentally targeting production.

### Recommended structure

```text
CentralDevOps
├── GitHub Environment: Staging
│   ├── Variables
│   │   └── ANSIBLE_INVENTORY_PATH=inventories/staging/hosts.yml
│   ├── Secrets
│   │   └── Staging-only credentials
│   └── Ansible inventory
│       └── inventories/staging/hosts.yml
│
└── GitHub Environment: Production
    ├── Variables
    │   └── ANSIBLE_INVENTORY_PATH=inventories/production/hosts.yml
    ├── Secrets
    │   └── Production-only credentials
    └── Ansible inventory
        └── inventories/production/hosts.yml
```

## 2. Naming convention for GitHub variables and secrets

I recommend **uppercase `SCREAMING_SNAKE_CASE`, with prefixes based on the subsystem or responsibility**. GitHub configuration variable names are case-insensitive, cannot contain spaces, cannot start with a number, and cannot start with the reserved `GITHUB_` prefix.

Use prefixes such as:

| Prefix | Responsibility | Examples |
|---|---|---|
| `ANSIBLE_` | Configuration management | `ANSIBLE_INVENTORY_PATH`, `ANSIBLE_SSH_PRIVATE_KEY` |
| `VPS_` | VPS provider and provisioning | `VPS_PROVIDER_API_TOKEN` |
| `DEPLOY_` | Deployment behavior | `DEPLOY_HEALTHCHECK_TIMEOUT` |
| `GHCR_` | Container registry access | `GHCR_PULL_TOKEN` |
| `APP_` | Application-specific configuration | `APP_DOMAIN`, `APP_CONTAINER_PORT` |
| `BACKUP_` | Backup policies and operations | `BACKUP_RETENTION_DAYS` |
| `MONITORING_` | Monitoring integrations | `MONITORING_ENDPOINT` |

These prefixes are a proposed convention, not mandatory GitHub standards. The objective is to make the purpose and owner of each setting obvious as the platform grows.

Avoid names like `SERVER_IP`, `KEY`, `TOKEN`, or `PASSWORD`. They do not communicate which service owns the value or which workflow should use it.

## 3. What should you actually configure?

### A. CentralDevOps repository-level variables

Use repository-level variables for non-sensitive configuration shared across infrastructure workflows and environments.

| Variable | Example value | Reason |
|---|---|---|
| `ANSIBLE_CONFIG_PATH` | `ansible.cfg` | Common Ansible configuration path |
| `ANSIBLE_REQUIREMENTS_PATH` | `requirements.yml` | Ansible dependencies |
| `ANSIBLE_PLAYBOOKS_PATH` | `playbooks` | Common playbook directory |

These are examples; use only the variables your workflows actually consume.

### B. CentralDevOps environment-level variables

Configure the following separately under **Settings → Environments → Staging** and **Production**.

| Variable name | Staging value | Production value |
|---|---|---|
| `ANSIBLE_INVENTORY_PATH` | `inventories/staging/hosts.yml` | `inventories/production/hosts.yml` |

Add other environment-specific operational settings only when there is a concrete need for them.

I recommend deriving the inventory path from the selected GitHub Environment rather than asking someone to enter an arbitrary inventory path manually. This reduces the chance of selecting a production inventory during a staging operation.

### C. CentralDevOps environment-level secrets

Use the same naming convention in both environments, but store different credential values where isolation is required.

| Secret name | Staging | Production |
|---|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY` | Staging automation key | Production automation key |
| `VPS_PROVIDER_API_TOKEN` | Staging-scoped provider token, if needed | Production-scoped provider token, if needed |
| `ANSIBLE_VAULT_PASSWORD` | Staging vault password, if used | Production vault password, if used |

The SSH key approach assumes each environment's key is authorized on the hosts it needs to manage. If different server groups require different credentials, model that security boundary explicitly rather than automatically creating a new GitHub secret for every VPS.

Keep credentials out of the inventory file. GitHub restricts environment secrets to jobs that reference the relevant environment, subject to its protection rules.

## 4. How should Ansible inventory handle multiple VPS?

Keep the existing environment-specific inventory structure and extend each inventory with server groups.

```text
CentralDevOps/
├── inventories/
│   ├── staging/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   │   ├── all.yml
│   │   │   ├── app_nodes.yml
│   │   │   └── proxy_nodes.yml
│   │   └── host_vars/
│   │       └── stg-app-01.yml
│   │
│   └── production/
│       ├── hosts.yml
│       ├── group_vars/
│       │   ├── all.yml
│       │   ├── app_nodes.yml
│       │   └── proxy_nodes.yml
│       └── host_vars/
│           └── prod-app-01.yml
```

An example `inventories/staging/hosts.yml`:

```yaml
all:
  children:
    app_nodes:
      hosts:
        stg-app-01:
          ansible_host: 203.0.113.10
        stg-app-02:
          ansible_host: 203.0.113.11

    proxy_nodes:
      hosts:
        stg-proxy-01:
          ansible_host: 203.0.113.12

    database_nodes:
      hosts:
        stg-db-01:
          ansible_host: 203.0.113.13
```

The IP addresses above are illustrative.

With this structure, a playbook can target `app_nodes` instead of hardcoding a particular VPS. If you add `stg-app-03`, it becomes part of the group without requiring another GitHub Environment variable.

Ansible's inventory and group-variable mechanism is designed for this kind of host organization.

## 5. What should the workflow inputs look like?

Keep infrastructure and application workflows distinct.

For `configure-vps.yml`, an input might select a server profile such as `app`, `proxy`, or `database`. A separate target selection can narrow the operation to a host or group. Validate any free-text target against the chosen inventory before running Ansible.

For `verify-vps.yml`, allow verification of a specific host, a specific group, or the entire environment.

For each application's `deploy.yml`, preserve the two inputs already specified:

| Input | Purpose |
|---|---|
| `image_ref` | The exact image to deploy, preferably a full immutable reference such as `ghcr.io/org/app@sha256:...` |
| `target_environment` | `Staging` or `Production` |

**Do not add a GitHub variable for each target VPS.** Instead, map each application and environment to a stable inventory group or deployment target in version-controlled configuration. Adding another application host should not force a redesign of every application's workflow.

## 6. One important distinction about CentralDevOps secrets

The existing architecture uses a composite action from CentralDevOps inside each application's `deploy.yml`. There is an important credential boundary here: a composite action does not automatically gain access to secrets stored in the CentralDevOps repository. Secrets must be explicitly made available to it through the caller workflow.

There are two choices:

- **Keep the composite action model.** Application repository environments supply the secrets required by that deployment job. This is straightforward, but infrastructure credentials may need to be duplicated across repositories.
- **Centralize the deployment execution.** Have the application workflow submit a deployment request to a workflow that actually runs in CentralDevOps. That workflow can use CentralDevOps's own environment configuration and credentials. Validate the cross-repository triggering and authorization design before implementing it.

Do not assume that placing a reusable workflow file in CentralDevOps automatically makes CentralDevOps repository secrets available to every application that calls it. GitHub requires explicit secret passing and environment binding.

For long-term maintainability, centralized deployment execution is preferable when many applications will share the same VPS fleet. Keep application-specific runtime configuration and secrets owned by each application, while centralizing server access and infrastructure operations.

## 7. Final naming rules

1. **Uppercase `SCREAMING_SNAKE_CASE`** for GitHub variables and secrets.
2. **Subsystem prefixes** such as `ANSIBLE_`, `VPS_`, `DEPLOY_`, and `GHCR_`.
3. **Environment-specific values belong in the environment, not in the variable name.** Use `ANSIBLE_SSH_PRIVATE_KEY` in both environments rather than separate names like `STAGING_SSH_PRIVATE_KEY` and `PRODUCTION_SSH_PRIVATE_KEY`.
4. **Per-host configuration belongs in Ansible inventory**, including host addresses, host-specific users, and role-specific settings where appropriate.
5. **Secrets contain credentials; variables contain ordinary configuration.** Do not treat public host addresses or inventory paths as secrets merely because they concern infrastructure.

One plan limitation to check before implementation: GitHub requires a supported paid plan for environment secrets and variables in private or internal repositories. Verify the plan and repository visibility before relying on these settings.

**Final recommendation:** keep `Staging` and `Production`, use identical variable and secret names across the two environments, maintain independent Ansible inventories, and organize the VPS hosts into role-based groups. This scales better than encoding individual server identities into GitHub secret names.

## References

- [GitHub Actions variables](https://docs.github.com/en/actions/learn-github-actions/variables)
- [GitHub deployment environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub environment secrets and variables](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [GitHub secrets in workflows](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Ansible inventory introduction](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
- [Ansible inventory: organizing host and group variables](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables)
