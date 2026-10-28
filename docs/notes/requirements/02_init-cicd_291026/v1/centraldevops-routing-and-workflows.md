# CentralDevOps: Application Routing and Infrastructure Workflows

## User questions

1. Where and how should I configure the routing of a new application? Is it in the CentralDevOps repository or in each app repository?
2. Why are there three `.github` workflows in CentralDevOps? Please explain the use of each one, when to use it, and how the flows work.

---

## 1. Where should routing for a new application be configured?

**Recommendation: the application repository declares its routing requirements; CentralDevOps manages how those requirements become active Nginx configuration on the VPS.**

This separates application ownership from infrastructure ownership. Nginx's `server_name` directive determines which server configuration handles a given hostname. CentralDevOps should own the shared Nginx setup and the process that manages those configurations.

### Separate routing into three responsibilities

#### A. DNS provider — where the domain points

Configure the domain's DNS records through your DNS provider, such as Cloudflare. For example, `app.example.com` points to the reverse proxy's public IP address or load balancer.

Configure this when a hostname is introduced or its destination changes.

#### B. Application repository — what the application needs

Declare the hostname, internal service name, port, and whether public routing is enabled. These are application deployment settings, not credentials.

Keep these settings version-controlled alongside the application.

#### C. CentralDevOps — how routing is implemented

Own the Nginx role, configuration templates, TLS setup, validation, reload process, and code that registers or removes application routes.

### Example: adding a new application

Suppose you are deploying `CustomerBuilderEngine`. In the application repository, you could create a configuration file like this:

```yaml
# deploy/staging.yml
app:
  name: customer-builder
  domain: builder-staging.example.com
  container_port: 3000
  network: edge

routing:
  enabled: true
```

This is an illustrative configuration schema; you would define and implement the schema in your deployment logic.

The application repository also defines the container's network attachment. For example, if Nginx and the application run on the same VPS:

```yaml
# compose.yml — relevant sections only
services:
  app:
    image: ghcr.io/your-org/customer-builder:${IMAGE_TAG}
    expose:
      - "3000"
    networks:
      edge:
        aliases:
          - customer-builder

networks:
  edge:
    external: true
    name: edge
```

Here, `edge` is a shared Docker network that CentralDevOps creates when configuring the VPS. Because the network is marked `external: true`, Docker Compose expects it to exist already; it will not create it for you.

CentralDevOps owns an Nginx template that can produce a server block conceptually like this:

```nginx
server {
    listen 80;
    server_name builder-staging.example.com;

    location / {
        proxy_pass http://customer-builder:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Production would have its own hostname and TLS configuration.

The actual configuration should be rendered from validated inputs, tested using `nginx -t`, and reloaded only if validation succeeds.

### What happens when you introduce an app?

1. **Configure the hostname in DNS.** Point the domain to the public proxy or load balancer.
2. **Commit application deployment configuration.** Declare the domain, service name, and internal port in the app repository.
3. **Build and deploy the application.** Publish the image and start the container on the required network.
4. **Register the route through CentralDevOps.** Render Nginx configuration, validate it, and reload Nginx.
5. **Verify HTTPS and application health.** Only consider the deployment complete when the application is reachable.

This means adding an application does **not** require editing Nginx configuration by hand or rerunning the entire VPS setup process.

One additional point: when your applications eventually run on different VPS instances, the Docker `edge` network cannot automatically connect those hosts. Nginx will need to route to a reachable private IP, service discovery mechanism, or load balancer instead.

Reference: [Nginx server names documentation](https://nginx.org/en/docs/http/server_names.html).

---

## 2. Why are there three workflows in CentralDevOps?

The three workflows have different operational responsibilities. They are separate entry points to automate infrastructure tasks, not three workflows that must run every time you deploy an application.

Also, distinguish these two layers:

- **GitHub Actions workflow:** decides when to run automation, which environment to target, and what credentials to use.
- **Ansible playbook:** defines the actual configuration operations to run against the machine.

Ansible playbooks support repeatable configuration and orchestration; roles let you group configuration into reusable modules.

Reference: [Ansible playbook documentation](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks.html).

### Workflow 1: `bootstrap-vps.yml`

**Purpose:** Bootstrap a fresh VPS and establish the initial trusted access path.

**When to use it:** You have created a new VPS and are preparing it for the first time.

Typical responsibilities:

- Connect through the initial account and SSH key supplied or configured during VPS creation.
- Create the intended administrative and deployment accounts.
- Install essential system packages and apply the initial security baseline.
- Configure SSH key authentication and carefully harden SSH.
- Set up the initial firewall rules.

**Flow:**

```text
Create VPS in provider dashboard
          ↓
Obtain initial SSH access
          ↓
Run bootstrap-vps.yml
          ↓
Create intended accounts and access
          ↓
Validate access before closing the old path
```

Be particularly careful when changing SSH settings. Verify that the new account and key work in a separate connection before disabling root login or password authentication. Otherwise, a mistake can lock you out of the machine.

### Workflow 2: `configure-vps.yml`

**Purpose:** Configure the machine's desired state by installing and maintaining services required by a particular VPS profile.

**When to use it:** After bootstrap, when installing services for the first time, or whenever the machine's intended configuration changes.

For example, a workflow input could select a server profile:

```text
configure-vps.yml
    ├── app
    ├── proxy
    ├── database
    └── all-in-one
```

The selected profile determines which Ansible roles to apply.

| Profile | Example roles |
|---|---|
| `app` | Common, users, SSH hardening, firewall, Docker, monitoring |
| `proxy` | Common, users, firewall, Docker, Nginx, monitoring |
| `database` | Common, users, firewall, PostgreSQL, backups, monitoring |
| `all-in-one` | A selected combination of the above |

**Flow:**

```text
Select environment and VPS profile
          ↓
Run configure-vps.yml
          ↓
Execute configure.yml
          ↓
Apply selected Ansible roles
          ↓
Install or update services
```

The playbook should be idempotent: running it repeatedly should converge to the desired configuration instead of duplicating resources or breaking the host.

### Workflow 3: `verify-vps.yml`

**Purpose:** Verify the server's health and configuration without trying to repair or reconfigure it.

**When to use it:** After bootstrap, after configuration changes, during troubleshooting, or as an on-demand infrastructure audit.

Typical checks include:

- SSH connectivity and expected accounts.
- Firewall rules and exposed ports.
- Docker availability and container health.
- Nginx configuration validity and service status.
- PostgreSQL availability where installed.
- Monitoring agent connectivity.
- Required network and application directories.
- Disk space and other basic resource checks.

**Flow:**

```text
Select target VPS
        ↓
Run verify-vps.yml
        ↓
Execute read-only checks
        ↓
Report PASS / FAIL per check
        ↓
Investigate failures if needed
```

It is useful to keep verification separate because you can run it without accidentally triggering a service installation or configuration change.

### How the three workflows fit together

#### First-time setup

`Provision VPS → bootstrap-vps.yml → configure-vps.yml → verify-vps.yml`

#### Change infrastructure

`Update Ansible roles/configuration → configure-vps.yml → verify-vps.yml`

#### Deploy an application

`Build image → deploy app → register/update its route → health check`

This should normally be handled by an application deployment workflow that invokes shared CentralDevOps deployment logic, rather than rerunning all three VPS workflows.

---

## 3. Do you really need three workflows?

Not necessarily. The separation is an operational design choice.

I would keep all three because infrastructure changes can be risky, and separate entry points make it easier to control which operation is running. In particular, production infrastructure workflows should reference the `Production` GitHub Environment so you can apply appropriate branch restrictions, approval requirements, and secret access controls. GitHub makes environment protection rules and secrets available to jobs that reference the environment after the applicable protection rules pass.

One refinement: **if your VPS SSH credentials are stored only in the CentralDevOps repository's environments, use a reusable deployment workflow in CentralDevOps as the entry point for application deployments.** A composite action alone runs inside the caller's job and does not automatically gain access to secrets stored in another repository. A reusable workflow can centralize deployment jobs while accessing the intended CentralDevOps environment; the calling application workflow can pass its application-specific configuration and secrets explicitly.

References:

- [GitHub deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [GitHub reusable workflow configurations](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations)

## Recommended implementation order

The first implementation I would build is `bootstrap-vps.yml`, followed by `configure-vps.yml` and `verify-vps.yml`. Prove you can reliably turn a fresh Ubuntu VPS into a secure, repeatably configured machine before automating application routing or horizontal scaling.
