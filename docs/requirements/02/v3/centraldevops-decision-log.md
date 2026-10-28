# CentralDevOps — v3 Decision Log

## 1. Confirmed decisions (from the clarification round)

| # | Question | Decision | Consequence in v3 |
|---|---|---|---|
| 1 | Deployment execution model | **Centralized execution from the start**: app dispatches a request to a CentralDevOps workflow; CentralDevOps holds all server credentials | New `deploy-app.yml`, `request-deploy` action, OIDC-bound requests, sealed runtime bundle (design §7–8) |
| 2 | Secret naming | **Identical names in both environments**, values scoped by GitHub Environment, subsystem prefixes | `STAGING_`/`PRODUCTION_` prefixed names removed; org-level secrets limited to the dispatch App (design §4) |
| 3 | GitHub plan | Environment secrets/variables tested and working on the org repos | Plan risk closed; documented as an assumption |
| 4 | Topology | Start all-in-one, **design the contract for a separate proxy from day one** | `upstream_mode` (`docker_edge`/`private_ip`), inventory groups, registry placement (design §6.4, §10) |
| 5 | Host targeting | **Central registry** `apps/<app>/<env>.yml` maps app to inventory groups; manifest holds only the route | Registry schema, domain allow-list, capacity check (design §9) |
| 6 | DNS / TLS | Other DNS provider, **Let's Encrypt HTTP-01** | No DNS API token; no wildcard certificates; port 80 must be public; DNS pre-check before issuance (design §10) |
| 7 | PostgreSQL | **One shared instance per environment**, per-app DB and role, with a documented path to per-app containers | `postgresql` role, `db` network, `DB_*` contract (design §11) |
| 8 | Rollout | Simple Compose replace; blue/green documented later | Design §14 |
| 9 | Provider / scale | **Sumopod**; up to **6 apps** in 6 months; **RTO 4 h, RPO 12 h** | 6-hourly DB backups, 8 h backup-age alert, timed restore drill, capacity ceilings (design §2, §13) |

## 2. Decisions made by the designer (please confirm or override)

| # | Decision | Rationale |
|---|---|---|
| A | Request authentication uses **GitHub OIDC with an audience bound to a hash of the request**, not a shared secret or PAT | A cross-repo dispatch token cannot prove *which* app is calling. OIDC claims prove repository, workflow file, ref, environment and run |
| B | App `compose.yml`, manifest and runtime env travel in **one age-encrypted bundle** | Avoids any CentralDevOps read credential for app repos; the bundle is bound to the OIDC proof |
| C | **Production approval lives in the CentralDevOps `Production` Environment**; app Production approval is optional | CentralDevOps holds the server credentials, so it is the single control point |
| D | Compose policy is enforced centrally on the rendered config | Centralized execution of an app-supplied Compose file is privileged; policy is required |
| E | Deployment history is mirrored to GitHub Deployments and off-host backups | Needed so a lost VPS can be redeployed within the 4 h RTO |
| F | Staging and Production are separate VPS instances | Environment isolation |
| G | Each placement group must resolve to exactly one host in v3 | Keeps the first implementation simple; relaxed in the multi-host phase |
| H | Host key pins are committed in `inventories/<env>/known_hosts`, not secrets | They are public data and should be reviewed |
| I | DB backups every 6 h | Half the 12 h RPO, tolerates one failed run |

## 3. Changes from v2

| Area | v2 | v3 |
|---|---|---|
| Deployment execution | Composite action in the app job; SSH deploy key in app repos | Cross-repo dispatch to a CentralDevOps workflow; app repos hold no server credential |
| Reusable-workflow secret claim | Called workflow would use CentralDevOps environment secrets | **Corrected:** a called reusable workflow runs in the caller's context; central execution needs a workflow in CentralDevOps |
| Secret names | `STAGING_DEPLOY_SSH_KEY`, `PRODUCTION_DEPLOY_SSH_KEY` (org) | Identical names per Environment (`DEPLOY_SSH_PRIVATE_KEY`) |
| App-to-host mapping | `DEPLOY_HOST`, `DEPLOY_USER` variables in app environments | Central registry + inventory groups |
| Domain ownership | Declared in app manifest, "validate uniqueness" | Registry allow-list; manifest may only select an allocated domain |
| Compose safety | Advice on ports and networks | Enforced policy (privileged, host mounts, ports, networks, limits, healthcheck) |
| Deploy identity | "Likely in docker group initially" | Non-docker-group user, sudo-limited root-owned scripts |
| TLS | Certbot or other ACME, DNS-01 optional | HTTP-01 with webroot and a defined activation sequence |
| Database | Containerized per app or dedicated VPS | Shared PostgreSQL with per-app DB/role; defined network, listener ordering, migration path |
| Recovery | Generic backup/restore guidance | RTO 4 h / RPO 12 h with timed budget, drill requirement, backup-age alert |
| Capacity | Not addressed | Mandatory limits and registry capacity check for 6 apps |
| Concurrency | App-level group | Per app/env group for convenience; server-side `flock` for correctness; note on pending-run cancellation |
| Inventory | Environment inventories | Same, plus groups for all-in-one hosts, `private_ip`, capacity budget, `known_hosts` |
| Build | Digest in summary | Adds provenance attestation and optional central verification |
| Provisioning, DNS API | Mentioned | Deferred; not needed for HTTP-01 |

## 4. Open items still needing your input or a spike

| # | Item | Needed before |
|---|---|---|
| 1 | **Spike**: cross-repo dispatch with GitHub App, OIDC custom audience, claim contents, and the reusable-workflow secret behaviour in your org | Building `deploy-app.yml` |
| 2 | **Sumopod capabilities** (private network, firewall, snapshots, S3-compatible storage, API, reserved IP, console) | Backup design, split-host plans |
| 3 | Backup tool and off-host destination; custody of the encryption key | Backup role |
| 4 | Migration approach per app (`release_command` vs start-up) | First app with a database |
| 5 | `require_attestation` for Production | Build workflow design |
| 6 | Whether to build the GitHub Deployment status feature now (needs a small App with `deployments: write` on app repos) or rely on server and backup records initially | Deploy workflow |
| 7 | VPS sizing for each environment | Registry capacity budget |
| 8 | DNS provider name and TTL policy | DR plan |
| 9 | Grafana Cloud plan limits vs 6 apps | Monitoring role |
| 10 | Confirm designer decisions A–I above | Implementation start |
