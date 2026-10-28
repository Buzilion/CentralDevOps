# Module PRD: Observability and Alerting (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `OBS` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

Seeing the health of each VPS and each app, and being told when something needs action, including when the VPS itself is down. Grafana Cloud is the decided platform.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| OBS-01 | A collector on every VPS sends metrics and logs to Grafana Cloud using a least-privilege credential held as an Environment secret. | Both Staging and Production hosts report metrics and logs. | §3, §4.4, §13.1 |
| OBS-02 | The following are monitored: CPU, RAM, disk and inode usage, container restarts and health, Nginx errors, certificate expiry, PostgreSQL availability and connections, HTTP availability, latency and 5xx rate per app, and backup age. | Each signal is visible and queryable for each Environment. | §13.1 |
| OBS-03 | Alerts exist for: disk pressure, restart loops, failed health, certificate expiry under 21 days, newest good backup older than 8 hours, elevated 5xx rate and host down. | Each alert is triggered once in a Staging rehearsal and reaches its recipient. | §13.1 |
| OBS-04 | An external uptime probe, independent of the VPS and its collector, detects a VPS or route being down and raises an alert. | Powering off a Staging VPS or stopping its collector raises the host-down alert. | §13.1 |
| OBS-05 | The host-down alert and the backup-age alert are mandatory and are covered by the Grafana Cloud plan in use. | Both alerts are active in Production before go-live. | §13.1, §17 #10 |
| OBS-06 | Expected log and metric ingestion is estimated before go-live and measured afterwards. Usage is watched against the plan's quotas, and the plan is upgraded or the log volume reduced when needed. | An estimate exists before go-live and a measured comparison after the first full month. | §13.1, §17 #10 |
| OBS-07 | Container logs are available centrally, so a failed rollout can be diagnosed without logging in to the VPS. | In a Staging failure exercise, the cause is found from central logs. | §15.6 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| OBS-08 | Alert recipients and escalation are defined, so that an alert always reaches an accountable person. | A list of recipients per alert exists and a rehearsal confirms delivery. | §13.1 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| OBS-09 | A dashboard per app shows its health, latency, error rate and resource usage against its limits. | Each onboarded app has a dashboard. | §13.1 |
