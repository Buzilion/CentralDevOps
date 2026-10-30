# Infrastructure Contracts and Invariants (v1)

| Item | Value |
|---|---|
| Status | Draft for review |
| Created | 2026-10-29 |
| Parent PRD | [`prd-v1.md`](../prd/01_init-cicd_291026/prd-v1.md) |
| Scope | Technical integration rules and non-negotiable constraints for the v1 platform |

This document defines how application repositories, GitHub Actions, Ansible, VPS hosts, Docker Compose, Nginx, PostgreSQL, GHCR, backups and monitoring exchange data and divide responsibility. It is the integration contract for the parent PRD and its nine module PRDs; it does not replace their detailed requirements or runbooks.

The parent PRD and module PRDs are drafts for review. In this document, **MUST** and **MUST NOT** describe the intended v1 contract. Any unresolved conflict is called out in section 10; it is not permission to weaken a security boundary.

## 1. Topology and trust boundaries

The initial deployment has one manually created Ubuntu/Sumopod VPS for `Staging` and a separate VPS for `Production`. Each is initially an all-in-one host for apps, Nginx, PostgreSQL and monitoring. VPS creation stays manual because Sumopod has no provisioning API.

```text
App repository (unprivileged GitHub Actions)
  build(source_ref) --> GHCR image digest + provenance
  deploy(target_environment, image_ref)
    --> age-sealed runtime env + Compose file + route manifest
    --> request-bound OIDC proof + dispatch-only GitHub App token
                                |
                                v
CentralDevOps GitHub Actions (ref allowed by selected Environment)
  authorize --> Production approval when required --> policy checks
                                |
                                v
Environment-specific VPS (restricted deploy SSH identity)
  Docker Compose app --> edge network --> Nginx --> public HTTPS
                    \--> db network --> PostgreSQL
  host pulls exact digest from GHCR; Restic sends encrypted backups to S3
  host monitoring collector sends telemetry to Grafana Cloud
```

The app's workflow requests a deployment; it never connects to a VPS. The privileged deployment runs in CentralDevOps after request authorization. A reusable workflow running in the caller's app-repository context is not a substitute for this boundary.

## 2. End-to-end request contract

Each app repository has exactly two manual workflows, `build` and `deploy`; neither automatically starts the other.

1. **Build.** An operator manually selects `source_ref`. The app workflow checks out that ref, runs tests, builds and pushes the image to its GHCR package, and records the full digest reference. A failed test prevents the push. Provenance links the digest to the app repository, workflow and commit. A `sha-<full-commit>` tag may be published for convenience, but is never a deployment input.
2. **Request.** The app's separate manual deploy workflow accepts exactly `target_environment` (`Staging` or `Production`) and `image_ref` (`ghcr.io/<OWNER>/<IMAGE>@sha256:<64 hex>`). It rejects a tag or malformed digest before dispatch. It reads app runtime values from that app's matching GitHub Environment, seals the runtime environment file, Compose file and route manifest to that Environment's `age` public key, and obtains an OIDC identity proof whose audience binds the Environment, image reference and sealed bundle. The dispatch-only GitHub App token dispatches the central workflow. The app name is derived centrally from the identity proof; it is not a request parameter. Requests exceeding the approximately 65 KB dispatch payload limit are rejected before dispatch.
3. **Authorize.** CentralDevOps runs deployment workflows only from refs allowed by the selected Environment: any branch for `Staging` and `release/*` for `Production`. Before any Environment or secret is used, it verifies the dispatch identity and OIDC token signature, issuer and expiry; recomputes the bound audience; maps the token repository to a registered app; checks the expected app `deploy.yml`, allowed ref and matching Environment claim; validates the digest against that app's registered image repository; and rejects a previously used source `run_id` and `run_attempt`. The dispatch token and OIDC proof are independent required proofs.
4. **Approve and select.** A verified `Production` request waits for approval in the CentralDevOps `Production` Environment before its secrets are made available. The selected Environment determines the inventory, registry row and credentials. The declared Environment, registry entry, inventory and resolved target host must agree; otherwise the run fails before deployment.
5. **Preflight.** CentralDevOps verifies required provenance (always for Production), decrypts the bundle only in a restricted temporary location, validates its manifest and fully rendered Compose configuration, and checks that runtime keys exactly match the manifest and contain no reserved keys. These checks happen before the host is changed. The central run fails on any invalid input; secret material is masked, never printed, and never uploaded as an artifact.
6. **Deploy and route.** The central deploy job connects with the restricted deploy identity, pulls the exact digest, and runs only the root-owned server-side scripts with validated arguments. It replaces the app, waits for its health check (90 seconds by default), then activates the route. An optional release command, when supported, runs before replacement. Route changes are serialized across apps.
7. **Report.** The central run records the result and the app run waits for it, fails when it fails, and links to the central run. Runtime environment contents are never included in summaries.

## 3. Component contracts and responsibility

| Boundary | Authoritative inputs | Output | Responsibility and ownership |
|---|---|---|---|
| App build -> GHCR | App source at `source_ref`, tests, Dockerfile and app-owned build configuration | Published image, immutable digest, provenance and metadata-only artifact | App team owns source and build workflow. It does not deploy or receive server credentials. |
| App deploy -> CentralDevOps | The two request inputs, app Environment values, Compose file, manifest, Environment `age` public key and dispatch App credentials | Sealed bundle, request-bound OIDC proof, dispatch and central-run result | App team owns app runtime values and request invocation. Shared sealing/dispatch/polling logic is owned by CentralDevOps and pinned by commit SHA. |
| CentralDevOps Actions -> VPS | Authorized request, selected Environment, registry, inventory and Environment-scoped credentials | Validated deployment, route result and deployment record | CentralDevOps owns authorization, approval gates, policy checks, deployment and audit trail. It is the only deployment path with VPS access. |
| Ansible -> VPS | Selected Environment, on-demand operation, inventory-derived targets, profile and optional validated host/group limit | Bootstrap/configuration result or read-only PASS/FAIL verification | CentralDevOps owns playbooks, roles and inventories. On a fresh host, bootstrap first connects with the provider username and temporary password, then uses the admin SSH key after installation; later operations use that key, never the deploy identity. |
| Docker Compose -> app services | Sealed app Compose file, requested digest, centrally supplied runtime values, registry limits and platform networks | Running app services and container health | The app authors its Compose file; CentralDevOps validates the fully rendered result; root-owned host scripts execute it. |
| CentralDevOps -> Nginx | Registry domain allow-list, app route manifest, healthy backend and DNS precondition | Validated HTTP-01 and HTTPS route configuration | CentralDevOps owns the trusted route template, generated files, validation and reload. An app cannot write Nginx configuration. |
| CentralDevOps -> PostgreSQL | Registry database setting, app identity and app-supplied `DB_PASSWORD` | One database and login role per enabled app, reachable on the private `db` network | The platform owns the instance, database and role lifecycle. The app owns its schema and migrations. |
| VPS -> GHCR | Exact digest and a host-installed read-only package credential | Pulled image matching the requested digest | The app build publishes packages; the VPS pulls them. App repositories never hold the host pull token. |
| VPS -> backup and monitoring services | Per-Environment backup and monitoring configuration and least-privilege credentials | Encrypted off-host backups, telemetry and alerts | CentralDevOps configures the host agents. Restic/S3 and Grafana Cloud are external services; credentials and data remain Environment-isolated. |

## 4. Configuration ownership and source of truth

| Configuration or data | Source of truth | Owner and constraints |
|---|---|---|
| Host address, SSH port, provider-supplied initial SSH username, role groups, private address, capacity budget and pinned SSH host keys | Reviewed per-Environment Ansible inventory and host-key file | Platform owner. The username is a per-host fact; the initial password is not stored in inventory or as a GitHub variable. Never hard-code host facts in workflows. Every SSH session uses strict host-key checking; a fresh key scan over the same connection is not trusted. |
| App source repository, GHCR image repository, allowed refs, provenance requirement, allowed domains, placement, upstream mode/port, resource ceilings and database settings | Reviewed `apps/<app>/<env>.yml` registry entry | Platform owner, reviewed through code ownership. The registry controls placement and policy; app input cannot override it. |
| Requested domain, service name, container port, health path, TLS preference, required runtime keys and optional release command | App-owned per-Environment route manifest | App team. The manifest cannot set placement, resource limits, allowed refs or image repository. Requested domains must be registered for that app and Environment. |
| App service definition and runtime keys/values | App `compose.yml`, manifest and app repository's matching GitHub Environment | App team. Secrets stay in the app Environment and travel only in the sealed bundle. No secrets in committed Compose files, image layers, build arguments or labels. |
| Temporary provider initial-access password, admin SSH key, deploy SSH key, `age` private key, GHCR pull token, backup and monitoring credentials | CentralDevOps `Staging` or `Production` Environment as appropriate | Platform owner. The initial password is used only for bootstrap and removed after the second key-based login succeeds. Other values are Environment-scoped and distinct where required. The admin key and initial password are never referenced by deployment jobs; app repositories never receive server credentials or the GHCR pull token. |
| Dispatch App credentials | Organization secrets restricted to selected app repositories, or app Environment secrets | App-side request only. The App has only the required Actions dispatch permission; no PAT or shared dispatch secret is used. |
| Nginx route files and TLS configuration | CentralDevOps trusted template and generated host configuration | Platform-owned. App manifests request a route but never supply proxy directives. |
| Per-app database and role | Central deployment plus the environment's PostgreSQL instance | Platform-owned lifecycle; no app uses a PostgreSQL superuser. App migrations are app-owned and backward-compatible with the previous release. |
| Workflow logic, policy validators and host deploy scripts | Reviewed CentralDevOps repository code | Platform owner. Changes to `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`, `.github/CODEOWNERS` and `.github/rulesets/**` require code-owner review before merging to `main` or `release/*`; both branch patterns require the same pull-request, approval and status-check protections. Third-party actions and shared actions are pinned to reviewed commit SHAs. |

CI validates registry and manifest schemas, rejects duplicate domain claims and duplicate host-port claims, and sums app memory limits per placement host against the capacity budget in inventory. A registry change that exceeds the budget fails before merge; capacity is reviewed again when the fourth app is onboarded.

GitHub variable and secret names use `SCREAMING_SNAKE_CASE` with an ownership prefix: `ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_` or `MONITORING_`. The same name is used in both Environments, with the Environment supplying its value. Do not use `STAGING_`, `PRODUCTION_`, `GITHUB_` or generic names such as `TOKEN` and `KEY`. Credentials are secrets; ordinary configuration belongs in variables or reviewed files.

## 5. Infrastructure operations contract

Infrastructure workflows run on demand only, from CentralDevOps, and reject dispatches made by the deployment-dispatch GitHub App identity. Production infrastructure changes require approval before using Production credentials.

| Operation | Inputs | Required behavior and result |
|---|---|---|
| Bootstrap | Selected Environment and a fresh VPS whose provider-supplied username is in inventory and password is in the temporary `VPS_INITIAL_ACCESS_PASSWORD` Environment secret | Connects first with the provider username and password; creates separate named admin and deploy accounts, applies OS updates and a base firewall, then installs the admin public key. After a second, independent key-based login succeeds, SSH hardening disables root and password login and the initial password secret is deleted. If the check fails, the run stops without hardening or removing the working access path. |
| Configure | Selected Environment, one profile (`app`, `proxy`, `database`, `monitoring` or `all-in-one`), optional inventory-validated host/group limit and optional dry run | Uses only the selected Environment's inventory. Unknown or cross-Environment limits fail before SSH. Dry run makes no host changes. A second configure run on unchanged inputs reports no changes. |
| Verify | Selected Environment and host, group or whole-environment scope | Read-only; changes nothing. Reports PASS/FAIL per check for access/users, firewall, Docker/Compose and networks, Nginx, certificate expiry, PostgreSQL listeners, deploy scripts and sudoers, monitoring, disk/inodes and backup age. Any failed check fails the run. |

Admin and deploy identities are separate. The deploy account is unprivileged, is not in the `docker` group, and can invoke only the root-owned `centraldevops-deploy` and `centraldevops-route` scripts through sudo with validated arguments. It cannot change those scripts, run arbitrary sudo commands or use Docker directly. Deploy SSH sessions and sudo executions are attributable in host logs.

Before hardening any Staging or Production host, a successful second-login path must have been recorded on a disposable VPS.

## 6. Security and runtime invariants

### Environment and identity isolation

- Exactly two GitHub Environments exist in CentralDevOps and each app repository: `Staging` and `Production`. Each Environment maps to its corresponding VPS; there is no Environment per VPS. The two environments have separate hosts, inventories, deployment/decryption credentials and encrypted backup repositories.
- A request for one Environment cannot resolve to the other Environment's inventory, host, key or registry entry. Mismatches fail closed before the deploy stage.
- CentralDevOps `Staging` accepts runs from any branch without approval; CentralDevOps `Production` accepts only protected `release/*` runs and requires approval for deployments and infrastructure changes. App Production Environments allow only `main` or approved release branches and do not add a second reviewer gate by default.
- GitHub Actions permissions are least-privilege. Untrusted values are strictly validated, never interpolated directly into shell commands. The dispatch GitHub App identity is rejected by infrastructure workflows.
- No PAT, provider initial-access password, deploy SSH key, admin key, registry pull token or plaintext runtime secret is stored in an app repository. No secret is printed, written to an artifact, committed, passed as a plaintext workflow input or baked into an image.

### Network exposure

- Public host ports are limited to TCP 80 and 443, plus SSH only as permitted by the access policy. SSH is key-only; root and password login are refused after the independent access check, and source restrictions are applied where practical.
- **PostgreSQL MUST NOT have a public port.** It listens only on localhost and the `db` network gateway; port 5432 is admitted only from the `db` subnet. Apps connect over that network (or a later private address); administrators use an SSH tunnel.
- **The Docker API MUST NOT be publicly exposed.** Do not enable a public TCP Docker listener. App containers MUST NOT mount the Docker socket. The deploy identity is not Docker-equivalent.
- Initial `docker_edge` deployments publish no app container ports. Nginx and app containers communicate on the shared `edge` network; database-enabled apps additionally use `db`. The `edge` and fixed-subnet `db` networks exist before app deployment.

### Image and Compose policy

- Every deployment uses a full `ghcr.io/<OWNER>/<IMAGE>@sha256:<64 hex>` reference. Tags, including `latest` and `sha-<commit>`, are never deployment inputs. Production additionally requires verified provenance for the registered app repository and workflow.
- The app container's rendered Compose image must equal the requested digest. Other service images must be digest- or explicitly version-pinned. The host pulls with a read-only GHCR credential stored root-only on the host.
- Policy is applied to the **fully rendered** Compose configuration, including interpolation and overrides. Reject privileged mode, added capabilities, device access, host PID/IPC/network modes, user-namespace changes or weakening security options; Docker socket mounts; bind mounts outside `/opt/apps/<app>/<environment>/`; published ports; networks other than the app's own default, `edge` and `db` (with `db` only when enabled in the registry); an unpinned service image; a routed service without a health check; missing or over-limit CPU/memory limits; and any `env_file` other than `.env`.
- Each app has registry-owned CPU and memory ceilings. Durable app data belongs in declared volumes, PostgreSQL or object storage, never a container writable layer. Containers run non-root where the app allows it.
- The runtime environment contains exactly the keys declared in the manifest, with no extras or reserved names. App input must not supply platform-owned keys such as `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `IMAGE_REF`, `EDGE_ALIAS` or any `CENTRALDEVOPS_*` key. The platform supplies the `DB_*` connection fields except `DB_PASSWORD`, which the app supplies from its own secret. Each app has its own database and role.
- CentralDevOps never runs app schema migrations. Apps own migrations and must keep them backward-compatible; an explicitly declared release command is the only central deployment hook and must complete before replacement.

### Proxy and TLS

- A domain's DNS A/AAAA records are created manually and must resolve to the proxy's public IP before its first certificate request. A mismatch fails with a clear error and makes no certificate request.
- Routes are rendered from a trusted template and allow-listed registry data. Health must pass before route activation. New domains use HTTP-01 on port 80, then validated HTTPS configuration; HTTP redirects to HTTPS, modern TLS is required, and HSTS is enabled only after a domain is verified. Certificate-issuance tests use the CA staging endpoint.
- Certificates renew automatically, with Nginx configuration validated before a renewal reload. Verification reports FAIL and alerting fires for certificates with fewer than 21 days remaining.
- Validate Nginx configuration before every reload. If validation fails, restore the last known-good file, do not reload, fail the deployment and leave other apps' routes serving. An unchanged route produces no file rewrite and no reload. Proxy edits and reloads are serialized across apps.

## 7. Deployment failure and rollback contract

| Failure point | Required result |
|---|---|
| Invalid identity, Environment, replay, image reference or required provenance | Reject before using Environment secrets or contacting a VPS. |
| Invalid manifest, Compose policy or runtime key set | Fail before changing host state. Do not start the app with a partial or untrusted configuration. |
| Optional release command fails | Abort before replacing the running release; the current release and route remain untouched. |
| New container health check fails | Fail the deployment and restore the previous release automatically. Do not change the route. If this is the first deployment, leave the app stopped. |
| Nginx configuration validation fails | Fail the deployment, restore the last known-good route file, do not reload Nginx, and preserve other apps' routes. |
| HTTPS smoke test fails after route activation | Fail the run and report the failure. Whether this failure rolls back the app and route is an unresolved PRD question (Q8); do not claim rollback is guaranteed until Q8 is decided. |

Server-side locks serialize deployments of the same app and Environment and prevent two apps from editing or reloading Nginx simultaneously. GitHub Actions concurrency is not the correctness lock: a pending run may be replaced, so host-side locking is required. Brief deployment interruption is accepted; blue/green deployment is out of scope.

Rollback of a completed release is performed by running the deploy operation again with the previous known-good digest. Every authorized deployment attempt, successful or failed, has a secret-free record containing app, Environment, requested and previous digest, source commit, source run, central run URL, UTC time and result. The record is stored on the host and included in off-host backups. Pre-authorization rejections remain auditable in the central Actions run and never bypass authorization to write to a host.

## 8. Database, backups and observability

- Each Environment has one shared PostgreSQL instance with a separate database and login role per app. The platform idempotently creates the database and role when enabled in the registry and applies the app's `DB_PASSWORD`; no app receives superuser access. After a host reboot, PostgreSQL must listen on the `db` network gateway and apps must reconnect.
- PostgreSQL accepts password authentication using a modern hash, and its firewall admits 5432 only from the `db` subnet. PostgreSQL databases and global objects are backed up off-host at least every six hours. Persistent app data is backed up at least daily unless stored in object storage; configuration and deployment records are backed up after each deployment.
- Restic writes to one client-side encrypted repository per Environment in Sumopod S3, with a unique high-entropy password per Environment. The recovery copy is held separately from S3 credentials in the organization password manager and is accessible to at least two authorized operators. S3 credentials are least-privilege.
- A backup-age alert fires when the newest good backup is older than eight hours. Recovery targets are RTO 4 hours and RPO 12 hours. A timed Staging restore must pass within four hours before Production go-live and at least quarterly thereafter.
- The last known-good digest for each app must be recoverable without the VPS from app run history and off-host deployment records, so a rebuilt host can redeploy the recorded digest.
- A least-privilege collector runs on every VPS and sends host, container, proxy, database, certificate, app and backup signals to Grafana Cloud. An external uptime probe, independent of the VPS, detects host or route failure. Host-down and backup-age alerts are mandatory before Production.
- The recovery runbook creates a replacement VPS manually, updates DNS or reassigns the IP, bootstraps and configures it, restores PostgreSQL and durable app data, redeploys each app by its recorded digest, then verifies and smoke-tests the environment.

## 9. Evolution and deployment boundaries

The initial topology uses `docker_edge` on a single all-in-one host per Environment. Hostnames and addresses are inventory data, and app placement is registry data; workflows must not hard-code either. A later split of app, proxy, database or monitoring roles is intended to change inventory and registry placement, not workflow logic.

`private_ip` routing and separate hosts are future capabilities, not permission to expose arbitrary app ports in v1. The current Compose policy rejects published ports. Any future private backend must be explicitly specified and reviewed: its port must be centrally allocated and unique per host, bound only to a private address, and admitted by the firewall only from the proxy host. Until the registry schema and Compose policy express that exception consistently, use `docker_edge` only.

The following remain out of scope for this contract: Kubernetes or another orchestrator, blue/green rollout, automated VPS creation, automated DNS management, wildcard certificates, a dedicated database container per app, central execution of application migrations, and untrusted third-party apps.

## 10. Open decisions that affect the contract

| Decision | Current safe rule | Source |
|---|---|---|
| Rollback after an HTTPS smoke-test failure | The run fails and reports the failure. Rollback of an already activated route is not defined; resolve before treating this case as production-safe. | Parent PRD Q8; RTE-07 |
| `private_ip` routing versus the no-published-ports Compose rule | V1 uses `docker_edge` with no published app ports. Do not enable `private_ip` until the policy/schema discrepancy is resolved and the private-only binding and firewall rules are testable. | RTE-02, REG-05, REG-08 |
| Production DNS TTL for VPS recovery | Decide and document the TTL/recovery-IP strategy before Production; the current four-hour TTL can consume the whole RTO. | Parent PRD Q3; BKP-13 |
| Per-host capacity budget | Declare a host budget in inventory and enforce the aggregate app-memory limit before onboarding another app. Reference VPS sizes are estimates, not budgets. | Parent PRD Q7; INF-20, REG-07 |
| Sumopod S3 versioning and provider-side encryption | Record provider support and enable these protections where available; client-side Restic encryption remains mandatory. | Parent PRD Q2; BKP-05 |

An open decision never relaxes the current network, identity, digest, secret-handling or Environment-isolation invariants. When a required value or decision is missing, fail closed and block the affected deployment or go-live gate.

## 11. Source documents

- [Parent PRD](../prd/01_init-cicd_291026/prd-v1.md)
- [Infrastructure provisioning, configuration and verification](../prd/01_init-cicd_291026/infrastructure-v1.md)
- [Environments, access control and secrets](../prd/01_init-cicd_291026/access-and-secrets-v1.md)
- [Application build and deployment request](../prd/01_init-cicd_291026/app-release-v1.md)
- [Central deployment](../prd/01_init-cicd_291026/central-deployment-v1.md)
- [Registry, manifest, Compose policy and onboarding](../prd/01_init-cicd_291026/registry-and-policy-v1.md)
- [Routing and TLS](../prd/01_init-cicd_291026/routing-and-tls-v1.md)
- [Shared database](../prd/01_init-cicd_291026/database-v1.md)
- [Backup and disaster recovery](../prd/01_init-cicd_291026/backup-and-recovery-v1.md)
- [Observability and alerting](../prd/01_init-cicd_291026/observability-v1.md)
- [GitHub variables and secrets](variables-and-secrets.md)
