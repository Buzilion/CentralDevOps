# Spec 14: Observability and Alerting

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 14 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation gated on completion of specs 05 and 13 |
| Depends on | `05_host-verification` and `13_backup-and-recovery` (each checklist must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `observability-v1.md` (`OBS`), `infrastructure-v1.md` (`INF`), `routing-and-tls-v1.md` (`RTE`), `database-v1.md` (`DB`), `backup-and-recovery-v1.md` (`BKP`), `central-deployment-v1.md` (`DEP`), and `access-and-secrets-v1.md` (`SEC`) in `docs/prd/01_init-cicd_291026/` |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§6.3, 8; `docs/design/naming-and-repository-conventions.md` §§7–8; `docs/design/variables-and-secrets.md` §§3.2, 4.8, 7; v5 design §§6.2–6.3, 13.1, 15.6 and 16 step 11; operational feedback v2 §7 |

## What

Deliver Grafana Cloud observability for every Staging and Production VPS: a least-privilege Grafana Alloy collector, host/container/proxy/database/application/backup signals, shared dashboards, required alert rules, an external HTTPS probe, quota tracking, role-scoped verification, and an operations runbook.

The collector and probe must remain independent failure signals. A stopped collector must not make its own health look good, and a powered-off VPS or failed public route must still be detected outside that VPS. Telemetry must not become another path for runtime secrets, request contents, or host credentials to leave the platform.

## Context and sequencing

- Do not implement this spec until every task and acceptance item in specs 05 and 13 is complete. Spec 13 itself depends on specs 08, 11, and 12; drafting spec 14 does not bypass any roadmap gate.
- Grafana Cloud is the selected observability platform. Each VPS sends its own Environment's telemetry using that Environment's least-privilege credential. No collector may use a token or endpoint from the other Environment.
- Spec 05 owns the single read-only `verify-vps.yml` operation and role-check contract. Add the monitoring check to that operation; do not create a second host-verification workflow.
- Spec 07 owns certificate issuance and already defines `centraldevops_certificate_expiry_days{domain="..."}` in `/var/lib/centraldevops/metrics/certificate-expiry.prom`. Consume that signal; do not create a second certificate-expiry authority.
- Spec 13 owns backup execution and the root-owned, secret-free `/var/lib/centraldevops/backups/status.json` with per-class success state. This spec reads that document through spec 13's read-only interface and derives the monitoring metric; do not create a second backup-status authority or require monitoring credentials.
- The project feedback says not to enable alert destinations until the recipient and routing configuration are approved. This spec intentionally contains no recipient addresses or unapproved notification settings. Missing approval is a blocked acceptance item, not a successful alert-delivery test.
- The v5/spec 04 material uses both `monitoring_agent` and `collector` for role names, while the naming convention and spec 05 verifier name `monitoring_agent`. This spec uses `roles/monitoring_agent` as the canonical Ansible role that configures Alloy. Before implementation, reconcile the spec 04 profile wording so there is one unambiguous role and every VPS profile receives the required collector configuration; do not create duplicate collectors.
- The parent design resolves Q10 conditionally: use the Grafana Cloud free plan only when its quotas and features cover the forecast; otherwise upgrade the plan or reduce ingestion before Production go-live.

## Requirements

| ID | Priority | Statement | Source |
|---|---|---|---|
| OBS-01 | Must | Every VPS sends metrics and logs to Grafana Cloud through the selected Environment's least-privilege credential. Both Environments report independently. | OBS PRD OBS-01; v5 §13.1 |
| OBS-02 | Must | Signals are visible and queryable by Environment and, where applicable, host and app: CPU, RAM, disk and inode use, container health/restarts, Nginx errors, certificate expiry, PostgreSQL availability/connections, HTTP availability/latency/5xx, and backup age. | OBS PRD OBS-02; v5 §13.1 |
| OBS-03 | Must | Alert rules cover disk pressure, restart loops, failed container health, certificate expiry under 21 days, newest good backup older than 8 hours, elevated 5xx rate, and host down. Each rule is rehearsed in Staging and reaches an approved recipient. | OBS PRD OBS-03; v5 §13.1 |
| OBS-04 | Must | An uptime probe outside the VPS and outside its collector checks public HTTPS routes and raises an alert when a route is unavailable. Collector loss is separately detected by a missing-telemetry/heartbeat alert. | OBS PRD OBS-04; v5 §13.1 |
| OBS-05 | Must | Host-down and backup-age alerts are active in Production and supported by the Grafana Cloud plan in use. | OBS PRD OBS-05; v5 §§13.1, 17 #10 |
| OBS-06 | Must | Estimate metric, log, and probe usage before go-live; monitor plan quotas; compare measured usage after the first full month; upgrade or reduce volume before quotas impair required signals. | OBS PRD OBS-06; v5 §§13.1, 17 #10 |
| OBS-07 | Must | Container logs needed to diagnose a failed rollout are queryable centrally without logging in to the VPS, while secret-bearing configuration and request contents remain excluded. | OBS PRD OBS-07; v5 §15.6; SEC-12 |
| OBS-08 | Should | Each alert has an accountable primary recipient and a documented escalation/backup path. Alert destinations are enabled only after their owner approves the recipient, channel, and routing configuration. | OBS PRD OBS-08; PRD Q5; operational feedback v2 §7 |

OBS-09 (separate dashboard per app) is a Could requirement and is not included. The app-health dashboard in this spec is shared and uses an app selector.

## Design

### Collector, credentials, and host boundary

- Configure Grafana Alloy through the canonical `roles/monitoring_agent` role on every VPS. Pin the reviewed package/version and verify its checksum before installation. Run it as a hardened systemd service with only the host access needed by its configured sources.
- Use Environment-scoped, non-secret variables for the provider's metrics/logs endpoints and tenant identifiers, and the existing `MONITORING_GRAFANA_CLOUD_TOKEN` as an Environment secret. The token is unique per Environment and limited to the write scopes required for metrics and logs. Do not place endpoint values, tenant identifiers, or token values in this spec, dashboards, committed configuration, command arguments, or summaries.
- Metrics and logs may have different Grafana Cloud endpoints and tenant identifiers. The implementation task must use signal-specific `MONITORING_` variable names where required and update `docs/design/variables-and-secrets.md`; do not assume one generic endpoint works for both signals. Distributed traces are not an OBS-01–08 requirement and remain disabled unless separately approved and included in the quota estimate.
- Pass the Environment secret to Ansible using the repository's secret-handling convention. Store the resulting host credential in a root-owned, non-deploy-readable file with restrictive permissions; do not put it in process arguments, service logs, metrics, or a deploy-readable location. A failure to configure the selected Environment's credentials is an explicit failure, never a fallback to another Environment.
- Exporters and health endpoints are loopback-only or on the existing private Docker networks. Do not add a public listener, put `cdo-deploy` in the Docker group, expose a Docker socket to app containers, or let the collector read deployment/runtime environment files. If Docker metrics require privileged access, use a root-controlled adapter that exposes only the required metrics to Alloy.
- Extend the existing role-scoped verifier with a read-only monitoring check. It verifies the collector service, required local sources, and a successful remote-write/ingestion signal without displaying the credential. A missing, stale, malformed, or indeterminate signal is not PASS.

The metrics/logs configuration contract is:

| Configuration | Kind and scope | Handling |
|---|---|---|
| `MONITORING_METRICS_ENDPOINT` | Variable, CentralDevOps Environment | Approved Grafana metrics endpoint; values are not committed. |
| `MONITORING_METRICS_INSTANCE_ID` | Variable, CentralDevOps Environment | Approved metrics tenant/account identifier; values are not committed. |
| `MONITORING_LOGS_ENDPOINT` | Variable, CentralDevOps Environment | Approved Grafana logs endpoint; values are not committed. |
| `MONITORING_LOGS_INSTANCE_ID` | Variable, CentralDevOps Environment | Approved logs tenant/account identifier; values are not committed. |
| `MONITORING_GRAFANA_CLOUD_TOKEN` | Secret, CentralDevOps Environment | Environment-specific, least-privilege write token; never printed or committed. |

If the selected stack uses the same endpoint or identifier for both signals, the values may match while the signal-specific names keep the contract explicit. Contact points and alert routes are managed separately from these ingestion credentials and are not enabled until Q5 is approved.

### Signals and ownership

| Signal | Source and labels | Contract |
|---|---|---|
| CPU, RAM, disk, and inodes | Host metrics; `environment`, inventory host alias | Report all required host filesystems. Ignore transient container filesystems and pseudo-filesystems. Disk or inode usage at the alert threshold is also a monitoring verification failure. |
| Container health and restarts | Docker/container metrics; `environment`, host alias, stable app/container identity | Include long-lived platform/app containers. Exclude one-off release-command containers from restart-loop alerts. Never export container environment values or labels containing secrets. |
| Nginx errors and HTTP request metrics | Nginx logs/counters; `environment`, app slug, status class | Use a platform-owned structured format. Do not send request bodies, query strings, full request targets, client IPs, cookies, authorization headers, or arbitrary request headers. HTTP latency and 5xx calculations must remain available per app. |
| Certificate expiry | Spec 07's textfile metric and path | Consume `centraldevops_certificate_expiry_days{domain="..."}`. A host with no registry-expected route/certificate has no expiry failure. |
| PostgreSQL availability and connections | A local exporter using a dedicated read-only monitoring identity; `environment`, host alias | Use the PostgreSQL statistics-monitoring capability only. Do not expose an exporter publicly, log SQL parameters, collect query text, or grant database mutation privileges. |
| HTTP route availability | Independent external HTTPS probe; `environment`, app slug | Probe each registered public route at a bounded interval. Store status/latency only; do not retain response bodies or send authentication material. |
| Backup age | Read-only view of spec 13's status document; `environment`, host alias | Derive `centraldevops_backup_last_success_timestamp_seconds` from the newest verified success across the required backup classes, using the same definition as spec 13's verifier. The status document remains the only source of truth; a failed attempt must not advance its last-success time. |
| Container logs | Allow-listed Docker stdout/stderr and sanitized Nginx error logs; bounded labels above | Logs needed for rollout diagnosis are centrally queryable. Do not scrape `.env` files, runtime configuration, PostgreSQL statements, arbitrary host files, or secret-bearing process metadata. |

Use only bounded labels: `environment`, `host`, `app`, `container`, `service`, and low-cardinality status/severity fields where needed. Never label metrics with request IDs, user IDs, client IPs, full URLs, query strings, or unbounded error text.

### Log minimization and secret redaction

- Configure Nginx access logs at source with only the fields needed for app, status, and latency metrics. Omit the full request target and client address rather than relying on downstream redaction.
- Collect only explicitly approved application/container and Nginx log sources. Drop or redact common credential fields and token patterns before remote write; do not collect headers, request bodies, cookies, or container environment metadata.
- Application owners must not log runtime secrets. Use synthetic canary values in tests and inspect the resulting Grafana logs, labels, dashboard queries, and collector output. Any canary match fails the test and blocks rollout of that pipeline.
- Do not upload decrypted bundles, runtime env files, private keys, provider tokens, or host access credentials. Keep log detail sufficient to diagnose a failed deployment without recording the secret-bearing input that deployment consumed.

### Dashboards and external probes

- Store reviewed dashboard definitions and alert expressions under `monitoring/grafana/` in the repository. The platform overview covers host resources, container health/restarts, Nginx errors, certificate expiry, PostgreSQL availability/connections, backup age, and telemetry/quota health.
- Provide one reusable app-health dashboard with an `environment` and `app` selector for HTTP availability, latency, 5xx rate, relevant container health, and sanitized logs. Do not create an individually forked dashboard for every app in this spec.
- Apply dashboard and alert definitions to Grafana Cloud through the approved operator workflow. Do not install a Grafana administration credential on a VPS or reuse the ingestion token for administrative API access.
- Use Grafana Cloud Synthetic Monitoring from a probe location outside the target VPS and its network. Probe each registry-approved public HTTPS route and validate TLS. If the selected plan cannot provide the required external probe/alert features, Production acceptance is blocked until the plan is upgraded or an independently approved probe is selected.
- A route probe failure is evaluated independently from Alloy. A missing collector heartbeat for five minutes raises the host-down signal even when the external route remains reachable; a failed external route probe raises a route-unavailable alert even when the collector is healthy.

### Alert policy and thresholds

| Alert | Condition | Notes |
|---|---|---|
| Disk pressure | Disk use **or** inode use is at least 85% for 15 minutes on a required host filesystem. | The verifier fails at a current reading of 85% or more; only alert firing waits for 15 minutes. |
| Container restart loop | A long-lived container restarts at least 3 times in a rolling 10-minute window. | Exclude one-off release-command containers; group by stable app/container identity. |
| Container unhealthy | A required container remains `unhealthy` for 5 minutes. | Missing or unknown health data is not healthy. |
| Certificate expiry | A registry-expected certificate has fewer than 21 days remaining. | Preserve spec 07's threshold and metric; no expected certificate is not an alert. |
| Backup age | The latest successful backup is older than 8 hours, or its success metric is missing when a scheduled backup is expected. | Preserve the BKP-07/OBS-03 threshold. A failed backup never refreshes the success timestamp. |
| Elevated app 5xx | At least 5% of app responses are 5xx over 5 minutes, with at least 20 requests in the window. | Low-volume windows still show their samples but do not create a percentage alert from a tiny denominator. |
| Host down | Collector heartbeat/telemetry is absent for 5 minutes. | This also detects a stopped collector; an external route probe independently detects a host outage. |
| Route unavailable | Any registered external HTTPS probe fails 3 consecutive one-minute checks. | This covers route failure even if host telemetry is still arriving. |

The host verifier reports current disk/inode measurements and returns FAIL at or above 85%; it does not wait for the alert's 15-minute persistence window. That window reduces transient alert noise only. A missing or malformed source is FAIL, not a zero-use value. Alert rules must be tested with synthetic Staging data; do not intentionally trigger a Production alert.

### Recipients and escalation (PRD Q5)

- Alert rules may be defined and validated without a notification destination. Do not create or enable a contact point/route until the platform owner has explicitly approved the accountable primary recipient, backup/escalation recipient, channel, and routing behavior.
- Keep recipient values in the Grafana Cloud managed contact-point configuration, not in this spec, the repository, dashboard labels, logs, or task summaries. Do not infer a recipient from feedback notes or use an unapproved address for a test.
- Once approved, every required alert must reach an accountable primary and the documented escalation/backup path in the Staging rehearsal. If the approved route is unavailable, the alert task and go-live gate remain blocked; never record a rule-only test as successful delivery.
- Confirm whether reboot-pending notifications share the approved route before configuring them. Reboot notification behavior itself is outside this spec.

### Grafana Cloud plan and quota tracking (PRD Q10)

- Start with the free plan only if its signal, alerting, external-probe, retention, and ingestion quotas cover the full forecast. If any required feature or quota is insufficient, select a suitable paid plan or reduce ingestion before Production go-live; do not silently drop mandatory telemetry.
- Before go-live, create `docs/observability/ingestion-estimate.md` using the selected inventories and registry, expected app/log volume, collection intervals, active metric series, external probe schedule, and plan retention/limits. State assumptions and the selected plan's fit without recording credentials or tenant values.
- Track current metrics, logs, probe, and alert-rule usage against the selected plan. Use a Grafana Cloud usage view where available and otherwise retain a dated monthly portal review. Compare the estimate with actual usage after the first full month and record the upgrade/reduction decision.
- Keep labels bounded, avoid verbose/debug log ingestion by default, and reduce unnecessary sources before increasing retention. Do not claim a quota is covered based only on a successful test push.

### Runbook and acceptance boundary

Create `docs/runbooks/observability-and-alerting.md`. It explains the dashboards, alert meaning and response, missing-data behavior, collector/token recovery, external-probe behavior, backup/certificate signals, quota review, safe log use, and how to diagnose a failed rollout from centrally collected logs. It contains no endpoint values, tenant IDs, recipient addresses, credentials, or sensitive host details.

Run acceptance on Staging only. Exercise each alert with synthetic fixtures or a controlled disposable host, verify the approved notification route, stop the collector to prove heartbeat loss is detected, and make a public route unavailable only in an approved test window. Demonstrate that a failed rollout can be diagnosed centrally without logging in to the VPS. Production fault injection is out of scope.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Use Grafana Cloud and Alloy, with `roles/monitoring_agent` as the single canonical host role. | Add a second collector role or send data to another provider by default | Grafana Cloud is selected in the PRD; one role avoids profile drift and duplicate agents. | Yes |
| D2 | Use separate signal-specific Environment variables when metrics and logs have different endpoints/tenant IDs; keep the ingest token Environment-scoped and least-privilege. | Assume one endpoint/ID or reuse an administrative token | The signals may have separate provider connection details; environment separation limits credential blast radius. | Yes |
| D3 | Set the disk/inode alert to 85% for 15 minutes and make the read-only verifier fail at a current reading of 85% or more; define explicit restart, health, and 5xx conditions here. | Leave every alert threshold unspecified | Spec 05 delegates its pressure threshold to spec 14, and alerts need testable acceptance criteria. | Yes |
| D4 | Use external HTTPS probes plus a separate five-minute telemetry-heartbeat check. | Depend on collector metrics alone | A collector cannot report its own outage; external probes remain independent of the host and agent. | Yes |
| D5 | Treat recipient/channel approval as a go-live gate and keep alert destinations unconfigured until confirmed. | Infer a recipient/channel or route alerts to an unapproved address | Project feedback explicitly requires approval before any alert route is enabled. | Yes |
| D6 | Choose the Grafana Cloud plan by forecast and measured usage; use Free only when all required features and quotas fit. | Assume the free plan is sufficient | App count and actual log volume are not fixed; quota fit must be demonstrated. | Yes |
| D7 | Keep tracing and separate per-app dashboards out of this spec; provide a shared app-selector dashboard. | Expand to unrequested telemetry and per-app dashboard maintenance | Traces are not in OBS-01–08 and OBS-09 is Could. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Staging and Production never share a collector credential or endpoint selection. | Inspect Environment mapping and use synthetic credentials to prove cross-Environment configuration fails. |
| Collector loss and public route failure are observable independently. | Stop the Staging collector and separately fail a controlled public route; verify the corresponding signals fire. |
| A missing or stale backup signal cannot appear healthy. | Remove/age the synthetic success timestamp and verify the backup-age alert fires after the defined threshold. |
| Certificate and backup thresholds remain exactly 21 days and 8 hours. | Test values immediately below/at/above each threshold using fixtures. |
| Runtime secrets, request contents, and access credentials are absent from telemetry. | Search canary values across logs, labels, dashboards, and task evidence; any match fails acceptance. |
| No collector/exporter adds a public host listener or deploy-user Docker access. | Inspect firewall/listeners, service permissions, Docker groups, and sudo rules. |
| No alert is considered delivered until an owner-approved recipient route passes rehearsal. | Verify approved contact-point ownership and record a sanitized delivery result. |
| The selected Grafana Cloud plan can carry the forecast and required features. | Review the dated ingestion estimate and plan quotas before Production go-live; compare against the first full month. |

## Error behavior

| Situation | Behavior |
|---|---|
| Spec 05 or 13 checklist is incomplete or absent. | Keep this spec blocked; do not configure a service host or bypass the dependency gate. |
| Environment endpoint, identifier, or token is missing or malformed. | Fail configure before remote collection; do not use the other Environment's values or emit credentials. |
| Grafana Cloud rejects authentication or remote write fails. | Report a sanitized failure and fail monitoring verification; do not report the collector healthy based only on a running process. |
| Collector source or signal is missing, stale, or malformed. | Report FAIL or fire the corresponding no-data alert; never substitute a zero or success-shaped default. |
| A log redaction/canary test finds a secret or request-only field. | Block the pipeline change, remove the unsafe source/field, and rerun the test before any Staging rollout. |
| A Grafana Cloud plan cannot support the mandatory signals, alerts, or external probes. | Do not pass the quota/production gate; upgrade the plan, reduce ingestion, or obtain approval for an independent probe. |
| No owner-approved recipient and escalation route exists. | Do not enable a contact point or claim alert delivery; keep OBS-03/OBS-08 delivery acceptance blocked. |
| The backup success marker is missing when a scheduled backup is expected or older than 8 hours. | Fire the backup-age alert; do not infer success from a running Restic process or an attempted backup. |
| A route probe returns TLS, DNS, timeout, or non-expected HTTP failure. | Raise route-unavailable after the configured consecutive failures and retain only sanitized status/latency evidence. |

## Testing strategy

- Run repository workflow/name checks, Ansible syntax/lint, and focused role/config tests for the pinned collector, secret-file permissions, systemd hardening, check-mode safety, and idempotence.
- Use synthetic host/container/log fixtures to test CPU/RAM/disk/inode queries, restart counts, health state, sanitized Nginx metrics, label bounds, secret redaction, and failed/unknown source handling.
- Test PostgreSQL metrics through the dedicated read-only identity; confirm no public exporter, SQL mutation privilege, query text, or secret-bearing parameter is collected.
- Test the spec 07 certificate metric and spec 13 backup-success metric at threshold boundaries. A failed backup must leave the prior timestamp unchanged.
- Validate dashboard JSON and alert definitions; confirm every required signal is queryable by Environment and app selector. Check that unknown/missing metrics do not display as healthy.
- Exercise all required alert conditions in Staging with synthetic values. Verify both rule evaluation and delivery to the approved primary/escalation route; if recipient approval is absent, mark delivery acceptance blocked rather than passed.
- Stop the Staging collector and confirm the heartbeat alert fires. Fail a controlled Staging HTTPS route and confirm the external probe raises route-unavailable independently of collector state.
- Use a canary secret and inspect collector logs, Grafana logs/labels, dashboards, and task evidence. Never copy the canary value into test output or a summary.
- Before Production, review the plan-fit estimate and confirm host-down/backup-age alerts are active. After the first full month, record actual-versus-estimated usage and any plan/log-volume change.
- Record sanitized commands, run URLs, commit IDs, host aliases, outcomes, and date in each task summary. Never record endpoint/tenant values, recipient addresses, secrets, or sensitive host details.

## Deliverables

```text
roles/monitoring_agent/                         # pinned Alloy configuration and role-scoped verify
roles/nginx/                                     # sanitized access/error telemetry integration
roles/postgresql/                                # read-only exporter integration
roles/backup/                                    # spec 13-owned backup-age metric contract
playbooks/configure.yml                          # ensure every relevant profile configures the agent
playbooks/verify.yml                             # extend spec 05's role-scoped checks
monitoring/grafana/dashboards/
monitoring/grafana/alert-rules/
monitoring/grafana/synthetic-checks/
monitoring/tools/tests/
docs/observability/ingestion-estimate.md
docs/runbooks/observability-and-alerting.md
docs/specs/01_init-cicd_291026/14_observability-and-alerting/
```

Spec 07 owns certificate metric production; spec 13 owns `/var/lib/centraldevops/backups/status.json` and the backup-age source data. Alloy reads the status through the spec 13 read-only interface and derives the metric without writing to the backup document. The implementation must integrate those contracts rather than duplicate their authoritative state.

## Out of scope

- Backup scheduling, Restic credentials, restore implementation, and restore drills (spec 13).
- Certificate issuance, route rendering, and TLS remediation (spec 07).
- A second verification workflow or host remediation from `verify-vps.yml` (spec 05).
- App-owned dashboards per app (OBS-09 Could), distributed tracing, log-based security analytics, and automated Production fault injection.
- Alert destinations until recipient/channel/escalation details are approved by the accountable owner.
