# Task 2: Host, container, and proxy telemetry

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Task 1 |
| Needs | Configured Staging Alloy and completed spec 04/06/07 telemetry sources |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Collect the host, container, Nginx, and app request signals while keeping logs and labels bounded and secret-safe.

## Relevant files or references

- `roles/monitoring_agent/`
- `roles/nginx/`
- `playbooks/configure.yml`
- `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` (disk/inode report)
- `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md`
- `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md`
- OBS-02, OBS-03, OBS-07; SEC-12

## Proposed approach

1. Collect CPU, memory, disk, and inode measurements for the required inventory filesystems. Ignore transient container filesystems and pseudo-filesystems.
2. Collect long-lived container health and restart signals with stable `environment`, host, app, and container identity. Do not export container environment values or secret-bearing labels.
3. Extend the platform-owned Nginx log format to provide app/status/latency data without request bodies, full request targets, query strings, client addresses, cookies, authorization headers, or arbitrary request headers.
4. Collect only approved app stdout/stderr and sanitized Nginx errors. Apply source-level minimization and downstream redaction before remote write; do not collect `.env` files, runtime configuration, or PostgreSQL statement logs.
5. Add synthetic canary tests, bounded-label checks, per-app 5xx/latency queries, and tests for missing or malformed source data.

## Acceptance criteria

- Host resource measurements and long-lived container health/restarts are visible per Environment and host.
- Nginx/app metrics provide per-app request availability, latency, and 5xx data using bounded labels.
- No request body, query string, client IP, cookie, authorization header, runtime environment value, or canary secret appears in uploaded logs or labels.
- The collector does not open a public port, and `cdo-deploy` remains outside the Docker group.
- Unknown/missing metrics are represented as missing or failed, never as zero usage or healthy.

## Source reference

OBS-02, OBS-03, OBS-07; SEC-12; HV-06; v5 §§6.3, 13.1, 15.6; spec 07's trusted Nginx templates.

## Verify

- Run focused role and log-pipeline tests with safe fixtures and synthetic canary values.
- Query host/container metrics by Environment and verify stable app identity in Nginx metrics.
- Inspect the resulting Grafana logs and labels for disallowed fields; do not print the canary value in test output.
- Confirm resource, container, and Nginx failures produce missing/failed signals rather than healthy defaults.

## Out of scope

PostgreSQL, certificate, and backup metrics; dashboards; notification routing; and application changes to their own logging behavior.
