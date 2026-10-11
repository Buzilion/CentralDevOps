# Production VPS Engineering Roadmap

## Goal

Turn a fresh VPS into a **secure, reliable, observable, and maintainable production environment**, then deploy the existing `CustomerBuilderEngine-Application` GitHub repository to it.

The guiding principle:

> Understand the manual process first, automate the repeatable parts second, and verify that the automation works third.

This helps prevent infrastructure that works only because an AI-generated playbook happens to succeed, without understanding what it changed or how to troubleshoot it.

## 1. Subjects to learn

### 1. Linux server administration

**Purpose:** Understand how the operating system, users, processes, files, permissions, and services work.

Learn:
- Linux filesystem, ownership, permissions, and `sudo`
- Users and groups; root versus a dedicated deployment user
- Processes, systemd services, logs, disk, memory, and CPU
- Package management and security updates
- SSH access and basic troubleshooting

**Hands-on outcome:** Administer a fresh Ubuntu VPS without relying on a root shell for everything.

### 2. Networking, DNS, and firewall security

**Purpose:** Understand how a user reaches the application and which network connections should be allowed.

Learn:
- Public IP, private IP, ports, TCP, and HTTP/HTTPS
- DNS records and domain configuration
- UFW or another host firewall
- SSH hardening, key-based authentication, and brute-force protection
- Loopback, binding addresses, and internal Docker networks

**Hands-on outcome:** Only intended services are exposed to the internet. SSH is restricted, and the application and database do not expose unnecessary ports.

### 3. Docker and container operations

**Purpose:** Package and run the application consistently.

Learn:
- Images, containers, Dockerfiles, and image registries
- Volumes, networks, port mappings, and environment variables
- Docker Compose for multi-container applications
- Health checks, restart policies, resource limits, and logging
- Image versioning, upgrades, rollback, and container cleanup

**Hands-on outcome:** Run the application through a reproducible deployment definition rather than a series of manually remembered commands.

### 4. Infrastructure automation with Ansible

**Purpose:** Configure the VPS in a repeatable, reviewable way.

Learn:
- Inventory, playbooks, tasks, handlers, roles, and variables
- Idempotency: rerunning a playbook should converge on the intended state
- Templates, file permissions, secrets, and privilege escalation
- SSH connectivity from your control machine or CI runner
- Ansible Vault or a suitable external secret manager
- Configuration drift and safe changes

**Hands-on outcome:** One command can configure a new VPS to your documented baseline, and rerunning it does not break the server.

### 5. CI/CD with GitHub Actions

**Purpose:** Move source code from your repository to production safely.

Learn:
- Workflow triggers, jobs, steps, runners, and artifacts
- Testing, building, and container image publishing
- GitHub Container Registry or another image registry
- SSH authentication and GitHub Actions secrets
- Environment protection, deployment approvals, and concurrency
- Automated deployment, post-deployment verification, and rollback

**Hands-on outcome:** A deliberate GitHub release triggers a predictable deployment without requiring you to SSH into the server and deploy manually.

### 6. Reverse proxy, HTTPS, and application serving

**Purpose:** Serve the application to real users.

Learn:
- Nginx or Caddy as a reverse proxy
- Domain routing and HTTPS certificates
- HTTP headers, request limits, and timeouts
- TLS renewal and redirect configuration
- Static assets, API routing, and WebSocket support if needed

**Hands-on outcome:** Users access the application through a domain over HTTPS, while internal services remain private.

### 7. Data persistence, backup, and recovery

**Purpose:** Prevent a deployment, disk failure, or accidental deletion from becoming permanent data loss.

Learn:
- Persistent Docker volumes and database storage
- Backup scheduling, retention, and off-site storage
- PostgreSQL dumps or appropriate database-native backups, if applicable
- Restore testing and recovery procedures
- Migration safety and backward-compatible releases
- Recovery Point Objective (RPO) and Recovery Time Objective (RTO)

**Hands-on outcome:** Recover the application's important data on a clean environment, not just confirm that a backup file exists.

### 8. Monitoring, logging, and alerting

**Purpose:** Detect failures and investigate problems before users report them.

Learn:
- VPS CPU, RAM, disk usage, network, and uptime
- Application health and readiness endpoints
- Structured application logs and Docker logs
- Metrics, dashboards, and alert thresholds
- External uptime checks and notifications
- Log retention and avoiding sensitive information in logs

**Hands-on outcome:** Know whether the server and application are healthy, receive alerts for important failures, and trace the cause of a problem.

### 9. Production operations and reliability

**Purpose:** Operate the application after the first successful deployment.

Learn:
- Health checks, restart behavior, and failure diagnosis
- Graceful shutdown and deployment downtime
- Rolling updates or blue-green deployment where justified
- Resource capacity, disk exhaustion, and dependency failures
- Incident response, rollback, and operational runbooks
- Security patching, dependency updates, and access reviews

**Hands-on outcome:** Safely update the application, diagnose failures, recover service, and maintain the VPS over time.

## 2. Recommended implementation order

### Phase 1 — Inspect the VPS and establish a secure baseline

**Topics:** Linux, SSH, firewall, users.

- Inspect the operating system.
- Create a non-root administrative user.
- Configure SSH keys.
- Disable password-based SSH and root login where appropriate.
- Configure the firewall and apply updates.
- Keep a tested recovery path before restricting access.

### Phase 2 — Prepare the application runtime

**Topics:** Docker, Docker Compose, secrets.

- Install Docker using its official installation instructions.
- Configure permissions securely.
- Learn to start, stop, inspect, and troubleshoot containers.
- Determine the application's runtime requirements from the repository before finalizing the Compose configuration.

### Phase 3 — Deploy the application manually once

**Topics:** Build, configuration, networking.

- Get the app running with a known version and correct environment variables.
- Verify that it works locally on the VPS.
- Understand which port it listens on.
- Do not expose it publicly until the network configuration is ready.

### Phase 4 — Make it accessible securely

**Topics:** DNS, reverse proxy, HTTPS.

- Point a domain to the VPS.
- Configure the reverse proxy and TLS.
- Verify that public traffic reaches the correct application.
- Check that internal ports are not exposed.

### Phase 5 — Add persistence, backups, and monitoring

**Topics:** Data safety, observability, alerts.

- Configure persistent storage.
- Automate backups to a separate location.
- Test restoring backups.
- Add resource monitoring, application health checks, and alert notifications.

### Phase 6 — Automate the VPS configuration

**Topics:** Ansible, idempotency, configuration management.

- Convert the successful manual configuration into Ansible roles and playbooks.
- Test them against the existing VPS.
- Ideally, test against a disposable fresh VPS too.

### Phase 7 — Automate application delivery

**Topics:** GitHub Actions, registry, deployment, rollback.

- Build and test the application in GitHub Actions.
- Publish a versioned image.
- Deploy through a restricted SSH-based mechanism or a deployment runner.
- Verify health after deployment.
- Establish a rollback procedure.

### Phase 8 — Practice failure and recovery

**Topics:** Incident response, troubleshooting, reliability.

Test what happens when:
- The application crashes.
- The disk fills up.
- A deployment fails.
- A database backup needs restoring.

Document the recovery steps.

## 3. Target architecture

A reasonable starting architecture for a single-VPS application is intentionally simple. Kubernetes and a complex multi-server setup are not necessary for the initial deployment.

```text
Users
  |
  v
DNS + VPS firewall
  |  Allow only required inbound ports
  v
Nginx or Caddy
  |  HTTPS termination and reverse proxy
  v
Application container
  |  Private Docker network + health checks
  v
Database / persistent storage
  (only if required by the application)

Supporting operations:
- Ansible: provisioning and server configuration
- GitHub Actions: build, publish, and deploy
- Monitoring: metrics, logs, alerts, uptime
- Off-site backups: independent recovery copies
```

Important distinctions:

- **Ansible manages the server's desired state.** GitHub Actions manages the application delivery workflow. Keep those responsibilities separate.
- **Monitoring and backups are not optional finishing touches.** Implement them before treating the application as production-ready.

## 4. Subjects to defer

| Subject | Why to defer it |
|---|---|
| Kubernetes | Adds orchestration complexity that a single VPS does not initially need. |
| Terraform | Useful for reproducibly creating cloud infrastructure, but Ansible can cover OS configuration. Start with your VPS provider's provisioning process. |
| Multi-server high availability | A single VPS remains a single point of failure regardless of how well configured it is. |
| Advanced observability stacks | Start with useful health checks, resource metrics, logs, and actionable alerts. |
| Complex blue-green deployments | First establish reliable versioned deployments and rollback. |

These subjects are not unimportant. They have a lower priority than securing, operating, monitoring, and recovering your first server.

## 5. Production-readiness checklist

Use this as the definition of done rather than considering a successful HTTP response sufficient.

### Security
- [ ] SSH uses keys and root login is appropriately restricted.
- [ ] Firewall allows only necessary inbound traffic.
- [ ] Secrets are not committed to Git or baked into images.
- [ ] Application and database ports are not publicly exposed unnecessarily.
- [ ] Security updates and access reviews have a defined process.

### Deployment
- [ ] Application runs with a pinned, identifiable release.
- [ ] Docker Compose configuration is version-controlled.
- [ ] Application restarts appropriately after a crash or reboot.
- [ ] HTTPS and domain routing work correctly.
- [ ] Failed deployments can be rolled back.

### Reliability
- [ ] Persistent data survives container recreation.
- [ ] Backups run automatically and are stored off-site.
- [ ] A backup has been restored successfully in a test.
- [ ] Disk, memory, and CPU capacity are monitored.
- [ ] Application health and external uptime are checked.

### Operations
- [ ] Logs can be inspected during a failure.
- [ ] Important failures trigger actionable alerts.
- [ ] Ansible can configure a fresh server repeatably.
- [ ] GitHub Actions deploys through restricted credentials.
- [ ] Recovery and deployment procedures are documented.

## 6. First step: inspect the application repository

Before writing Ansible roles or creating deployment workflows, determine what `CustomerBuilderEngine-Application` actually requires.

The application stack determines whether you need Node.js, .NET, PostgreSQL, Redis, background workers, scheduled jobs, or other infrastructure. Do not install services just because they are common in production.

Inspect:
- `README.md` and deployment documentation
- Application entry points and project files
- `Dockerfile` and Docker Compose files, if present
- Environment variable examples and configuration
- Database dependencies and migration procedures
- Build, test, and startup commands
- Existing GitHub Actions workflows

**First milestone:** Document the runtime requirements and draw the intended deployment architecture before changing the VPS.

Once that is clear, proceed with the secure Linux baseline, configure the runtime, and deploy manually. Then turn the working setup into Ansible automation and GitHub Actions.

This sequence teaches both how production infrastructure works and how to automate it without losing control over what the automation does.
