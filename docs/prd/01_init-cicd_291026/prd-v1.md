# PRD: CentralDevOps — Central CI/CD and VPS Platform (v1)

| Item | Value |
|---|---|
| Project folder | `docs/prd/01_init-cicd_291026/` |
| Version / status | v1, draft for review |
| Created | 2026-10-29 |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (v5; "§" references in this PRD and the module PRDs point to it) |
| Owner | CentralDevOps repository owner |

---

## 1. Summary

CentralDevOps is the central repository that provisions, configures, verifies and deploys applications onto VPS hosts, one environment at a time. It gives every application repository the same two-step release path (build an image, then request a deployment) and keeps all server credentials and infrastructure code in one reviewed place. The first release covers two environments, `Staging` and `Production`, each on its own Sumopod VPS running Docker Compose, with a shared PostgreSQL database, Nginx and HTTPS routing, off-host encrypted backups, and Grafana Cloud monitoring. It must carry up to **6 applications within 6 months** and meet **RTO 4 hours and RPO 12 hours**.

## 2. Problem Statement

- The team currently runs two internal apps and expects more, including a high-traffic storefront later. It needs to set up a VPS and deploy an app quickly and repeatably; doing this by hand for each app and environment is slow, inconsistent and hard to audit.
- A deployment path that puts server credentials into each app repository multiplies the places a leaked key can cause a server compromise. GitHub's reusable workflows run in the caller's repository, so they cannot give apps access to credentials held centrally; a different trust design is required.
- Deploying mutable image tags means the running software cannot be proven to be what was built and tested.
- Six apps will share two VPS hosts. Without enforced per-app limits, domain ownership, database isolation and a vetted Compose policy, one app can exhaust memory, claim another app's hostname or break the proxy for all.
- Sumopod offers no VPS snapshots and no API, so a lost VPS can only be recovered from code and off-host backups. Without a rehearsed recovery path, the 4-hour RTO and 12-hour RPO are not credible.

This matters now because the platform must be in place before the app count grows from two toward six, and the earlier design iterations (v1–v4) left the deployment model, key custody and backup tool open; v5 closes them.

## 3. Goals

| # | Goal | Measurable outcome |
|---|---|---|
| G1 | One standard release path for every app | Every app deploys through the same build and deploy operations; 100% of deployments use an immutable image digest. |
| G2 | Server credentials stay central | 0 deploy SSH keys or server admin credentials in any app repository. |
| G3 | Controlled, authenticated deployments | 100% of deployment requests are proven to come from the registered app repository, workflow, ref and Environment; any mismatch or replay is rejected. Production deployments require approval. |
| G4 | Repeatable hosts | Any host is rebuilt from code (bootstrap, then configure) and passes verification; a second configure run changes nothing. |
| G5 | Safe shared hosting for up to 6 apps | Each app has its own database and role, resource ceilings and allowed domains; the sum of limits never exceeds a host's budget. |
| G6 | Safe failure | A failed deployment never leaves the running route changed; the previous release is restored automatically when the health check fails. |
| G7 | Recoverability | RTO 4 hours and RPO 12 hours, proven by a timed restore drill on Staging before Production go-live and at least quarterly afterwards. |
| G8 | Visibility | Host-down, backup-age, certificate-expiry, health and error-rate conditions raise alerts that reach an accountable person. |
| G9 | Cheap onboarding | A new app is onboarded by a registry pull request plus app-repository files, with 0 changes to CentralDevOps workflows. |
| G10 | Room to grow | Splitting proxy, database or app hosts later requires only inventory and registry changes, not rewritten workflows. |

## 4. Out of Scope

- Kubernetes, Docker Swarm or any orchestrator (deferred until a measurable need appears).
- Blue/green or zero-downtime rollout. A few seconds of interruption per deployment is accepted; blue/green is a documented later phase.
- Automated VPS creation or IaC provisioning. Sumopod has no API; VPSs are created manually in its console.
- VPS snapshots (not offered by Sumopod).
- Automated DNS management and DNS-based certificate validation. DNS records are created manually at Masterweb; certificates use HTTP-01 only (no wildcard certificates).
- Running a split proxy, database or app host, load balancing, and one app on several hosts. The contract is designed for them from day one but they are not delivered in the first release (tracked as Could requirements).
- A dedicated database container per app or a managed database. The migration path is documented, not delivered.
- Running schema migrations. Migrations are owned by each app.
- Application source code, tests, Dockerfiles and application-level instrumentation (owned by the app teams).
- GitHub Deployments status integration (deferred; Actions run history is the deployment history for now).
- Dev environment and autoscaling or surge scaling for the future storefront. Only `Staging` and `Production` exist in this release.
- Hosting apps of untrusted third parties. All apps are first-party; same-host blast radius is an accepted risk.

## 5. Target Users

| User | Context | Main needs |
|---|---|---|
| Platform owner / DevOps operator (the repository owner) | Builds and operates CentralDevOps; initial Production approver; creates VPSs at Sumopod | Bootstrap, configure and verify hosts; review registry changes; rehearse recovery; rotate secrets |
| App developer / maintainer (up to 6 apps) | Owns an app repository, its Compose file, route manifest and runtime secrets | Build an image, deploy it to Staging and Production with no server access, see the result in their own run |
| Deployment approver | Owner first; the deployment team later | Approve Production deployments knowing exactly which app, digest and host are targeted |
| Recovery operators (at least two) | Respond to loss of a VPS or data | Access to the backup recovery password and a runbook that meets the 4-hour RTO |
| On-call recipient of alerts | Receives monitoring alerts | Actionable alerts, including when a VPS is completely down |
| End users of the apps (indirect) | Reach apps over HTTPS | Reliable, secure, available services |

## 6. Functional Requirements

Functional requirements span nine distinct domains, so they are owned by the module PRDs below. Each module lists Must, Should and Could requirements with acceptance criteria. Priority meaning: **Must** = required before Production go-live; **Should** = required before the capability it supports is relied on (for example, before app 2 or before a drill); **Could** = later phase, contract only.

| Module PRD (full path) | Prefix | Scope |
|---|---|---|
| `docs/prd/01_init-cicd_291026/infrastructure-v1.md` | `INF` | Bootstrap, configure and verify hosts; inventories; host security baseline; restricted deploy runtime |
| `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` | `SEC` | Environments, naming, secrets, approvals, code ownership, rotation |
| `docs/prd/01_init-cicd_291026/app-release-v1.md` | `REL` | App build to GHCR, immutable digest, attestation, deployment request |
| `docs/prd/01_init-cicd_291026/central-deployment-v1.md` | `DEP` | Request authentication, authorization, deployment, rollback, records |
| `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` | `REG` | App registry, route manifest, Compose policy, capacity check, onboarding |
| `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md` | `RTE` | DNS precondition, Nginx routes, HTTPS certificates, placement contract |
| `docs/prd/01_init-cicd_291026/database-v1.md` | `DB` | Shared PostgreSQL, per-app isolation, connection contract, migrations |
| `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` | `BKP` | Off-host encrypted backups, key custody, restore drills, disaster recovery |
| `docs/prd/01_init-cicd_291026/observability-v1.md` | `OBS` | Monitoring, alerts, external uptime probe, quota control |

### End-to-end flow (context for all modules)

```text
App: build (source_ref) -> image digest
App: deploy (Staging|Production, image_ref) -> sealed request + identity proof + authenticated dispatch
CentralDevOps: authorize -> (Production approval) -> deploy -> policy -> health -> route -> smoke test -> record
App run: waits for the central run and reports its result
```

## 7. Non-Functional Requirements

| ID | Category | Requirement | Threshold |
|---|---|---|---|
| NFR-01 | Recovery | Recovery time for a lost environment VPS | **RTO ≤ 4 h**, shown by a timed drill; time budget excluding DNS TTL is about 2 h 15 min to 2 h 45 min (§13.3) |
| NFR-02 | Recovery | Maximum data loss | **RPO ≤ 12 h**; database backups at most every 6 h; alert when newest good backup is older than 8 h |
| NFR-03 | Recovery | Restore drill cadence | Before Production go-live, then at least quarterly |
| NFR-04 | Availability | Deployment interruption | Brief (seconds) accepted; no zero-downtime requirement |
| NFR-05 | Availability | Failed deployment | Route unchanged and previous release restored in 100% of failed health checks |
| NFR-06 | Performance | Typical deployment time per app, from central run start to recorded result, excluding approval wait | ≤ 5 min (derived from the recovery budget of 6 apps × 5 min); health check wait defaults to 90 s and is configurable |
| NFR-07 | Scalability | Apps per environment | Up to 6 apps within 6 months on one VPS per environment; sum of app memory limits ≤ host budget; sizing reviewed at 4 apps |
| NFR-08 | Scalability | Reference host sizes | Production 2 vCPU / 4 GB RAM / 60 GB SSD; Staging estimated 1 vCPU / 2 GB / 20 GB |
| NFR-09 | Scalability | Topology change | Splitting proxy, database or app hosts needs 0 workflow rewrites |
| NFR-10 | Security | Credential custody | 0 deploy SSH keys or admin credentials in app repositories; deploy key and decryption key stored per Environment only in CentralDevOps; the provider-issued initial VPS password is a temporary Environment secret used only by bootstrap and removed after admin key login is verified, while its username is a per-host inventory fact |
| NFR-11 | Security | Request authentication | Two independent proofs per request; 100% of mismatched, tampered, expired or replayed requests rejected |
| NFR-12 | Security | Secret handling | 0 plaintext secrets in logs, artifacts, workflow inputs, image layers or committed files (canary-tested) |
| NFR-13 | Security | Network exposure | Only ports 80 and 443 public (SSH per access policy); 0 public database, app or Docker API ports |
| NFR-14 | Security | Least privilege | Deploy identity is not root-equivalent and can run only the two deploy scripts; admin and deploy identities and keys are separate |
| NFR-15 | Security | Supply chain | 100% of deployments by digest; 100% of Production deployments have verified provenance; third-party actions pinned to commit SHAs |
| NFR-16 | Security | Encryption | Backups encrypted client-side with a per-environment password; HTTP redirects to HTTPS; modern TLS |
| NFR-17 | Security | Change control | 100% of changes to `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`, `.github/CODEOWNERS` and `.github/rulesets/**` code-owner reviewed before merging into protected `main` or `release/*`; both branch patterns require pull requests, approval and required checks and block force-push/deletion; Production deployments and infrastructure changes approved |
| NFR-18 | Reliability | Idempotency | Second consecutive configure run: 0 changes; unchanged route: 0 rewrites and 0 reloads |
| NFR-19 | Reliability | Safe change | No SSH hardening applied without a proven independent admin-key login; a failed proxy validation never reloads or breaks another route |
| NFR-20 | Reliability | Certificate validity | 0 expired certificates; verification flags certificates with fewer than 21 days left |
| NFR-21 | Observability | Detection | Host-down and backup-age alerts mandatory and tested; external uptime probe independent of the VPS |
| NFR-22 | Auditability | Deployment traceability | 100% of deployments have a record (app, Environment, digest, previous digest, commit, source run, central run URL, time, result) stored on the host and in off-host backups |
| NFR-23 | Maintainability | Naming and configuration | 100% of variables and secrets follow the naming rules; per-host facts only in inventory or registry |
| NFR-24 | Compliance / operations | Third-party limits | Certificate-authority rate limits respected (DNS pre-check, staging endpoint for tests); Grafana Cloud quota usage tracked |
| NFR-25 | Accessibility | End-user accessibility | Not applicable: the platform has no end-user interface |

## 8. Success Metrics

| # | Metric | Target |
|---|---|---|
| M1 | Deployments using an immutable digest | 100% |
| M2 | Apps onboarded | Up to 6 within 6 months, each with 0 CentralDevOps workflow changes |
| M3 | Timed restore drill result | ≤ 4 h before Production go-live and each quarter |
| M4 | Backup freshness | Newest good backup ≤ 8 h old at all times; no backup gap > 6 h without an alert |
| M5 | Credential exposure | 0 deploy keys in app repositories; 0 secret leaks in the canary test |
| M6 | Deployment duration | ≤ 5 min typical, excluding approval wait (proposed target) |
| M7 | Failed-deploy safety | 100% of failed health checks leave the previous release serving |
| M8 | Host conformance | 100% of hosts PASS verification after each configure run |
| M9 | Certificate health | 0 expired certificates; all with ≥ 21 days remaining at verification |
| M10 | Mandatory alerts rehearsed | 100% of OBS-03 alerts triggered and received during a Staging rehearsal |
| M11 | Capacity | Sum of memory limits ≤ declared budget on every host |

### Production go-live gates

Production is not ready until all of the following are recorded:

1. The throwaway-app acceptance test has passed (DEP-20).
2. Hardening has been proven safe on a disposable VPS (INF-16).
3. A deployment has passed on Staging, with a rehearsed rollback (REL-13, DEP-12).
4. The S3 backup endpoint is verified and a timed restore drill has passed within 4 hours (BKP-08, BKP-10).
5. Host-down and backup-age alerts are active (OBS-05) and DNS TTL handling for recovery is decided (BKP-13).

## 9. Assumptions & Constraints

**Decided constraints** (from design v5):

| Area | Decision |
|---|---|
| Runtime | Docker Compose on one all-in-one Ubuntu VPS per environment; `Staging` and `Production` are separate VPS instances |
| Automation | GitHub Actions and Ansible, run from CentralDevOps |
| Provider | Sumopod VPS (private network, firewall, console; no snapshots, no API); Sumopod S3 object storage for backups |
| Registry and release identity | GHCR, deploy by immutable digest |
| Deployment model | Privileged deployment runs in CentralDevOps via authenticated cross-repository dispatch; request authenticated by a dispatch-only GitHub App and a request-bound GitHub OIDC token; runtime secrets travel in an `age`-sealed bundle |
| Routing and TLS | Nginx; DNS at Masterweb (domains registered at exabytes.co.id); Let's Encrypt HTTP-01 |
| Database | One shared PostgreSQL per environment, per-app database and role |
| Backups | Restic to the Sumopod S3 bucket, per-environment repository, client-side encryption |
| Monitoring | Grafana Cloud with a collector on each VPS |

**Assumptions and known limits:**

- Environment secrets and variables work on the current GitHub Free plan for the organisation's repositories (confirmed; to be noted in the README so a change is noticed).
- Dispatch payloads are limited to about 65 KB, so the sealed bundle must fit within that limit (REL-12).
- GitHub-hosted runner source addresses are not stable, so SSH source restrictions on the deploy key cannot rely on addresses.
- GitHub keeps only one pending run per concurrency group, so correctness relies on server-side locking, not workflow concurrency.
- HTTP-01 needs port 80 public, supports no wildcard certificates and needs one certificate per domain.
- Let's Encrypt limits failed validations and certificate issuance; this affects recovery of many domains at once.
- Docker published ports can bypass host firewall rules; the Compose policy therefore forbids them.
- The A/AAAA TTL is currently 14,400 s (4 h), equal to the whole RTO.
- Apps are stateless or keep durable data in volumes, the database or object storage; apps own backward-compatible migrations.
- The dispatch GitHub App's `actions: write` permission could dispatch any CentralDevOps workflow. This residual risk is accepted and mitigated (infrastructure workflows reject the App identity, Production needs approval, OIDC proof is required for every deployment).
- The companion documents `centraldevops-deployment-contract.md` and `centraldevops-decision-log.md` are still at v3 and do not yet reflect v4 or v5.

## 10. Open Questions

| # | Question | Needed before | Source |
|---|---|---|---|
| Q1 | Does Sumopod's private network connect separate VPS instances? Are IPv6, static or reserved IPs and outbound restrictions available? (Currently unconfirmed.) | Split-host design, DR plan | §10.1, §17 #2 |
| Q2 | Does Sumopod S3 support provider-side encryption and versioning? | BKP-05 | §13.2 |
| Q3 | DNS TTL policy for recovery: lower the production A/AAAA TTL to 300–600 s beforehand, or keep the recovery IP the same? | Production go-live (BKP-13) | §13.3 |
| Q4 | Number of monthly backup copies to retain, and the retention period of deployment records beyond the GitHub Actions run history. | BKP-06 | §13.2 |
| Q5 | Who receives alerts, by which channel, and what is the escalation path? | OBS-03, OBS-08 | §13.1 |
| Q6 | When the deployment team is assigned, does it replace the owner as Production approver or join the owner (single or double approval)? | SEC-18 | §4.1 |
| Q7 | What is the per-host capacity budget (reserve for OS, Docker, Nginx, PostgreSQL, collector) and how many apps does each VPS host? Is the Staging sizing estimate confirmed? | REG-07 | §2, §9.3 |
| Q8 | If the post-deployment HTTPS smoke test fails, should the deployment roll back or only report failure? The design only specifies rollback for health check failures. | RTE-07 | §8.3, §8.4 |
| Q9 | What is the rule for restricting SSH by source IP or VPN ("where practical")? | INF-10 | §12.1 |
| Q10 | Which Grafana Cloud plan is required once measured usage is known, and what are the expected ingestion volumes of the apps? | OBS-06 | §13.1 |
| Q11 | What is the fallback if an app's sealed bundle exceeds the ~65 KB dispatch limit? | REL-12 | §7.2 |
| Q12 | Update the v3 companion documents (deployment contract schemas, workflow skeletons, decision log) to v5 before the design and spec stage? | Design/spec stage | Header of design v5 |

## 11. Glossary

| Term | Meaning |
|---|---|
| Environment | A GitHub Environment, `Staging` or `Production`, holding that environment's variables, secrets and approval rules |
| Digest reference (`image_ref`) | `ghcr.io/OWNER/IMAGE@sha256:<64 hex>`; the immutable identity of a release |
| Registry | The reviewed `apps/<app>/<env>.yml` files in CentralDevOps that decide placement, domains, limits and policy per app |
| Manifest | The app's `deploy/<env>.yml` file declaring only the route it wants |
| Sealed bundle | The `age`-encrypted package of runtime env, Compose file and manifest sent from an app to CentralDevOps |
| Attestation | Signed provenance linking a digest to its repository, workflow and commit |
| RTO / RPO | Recovery time objective (4 h) / recovery point objective (12 h) |
| All-in-one | One VPS acting as app, proxy and database host |
