# Task 5: Independent uptime probes

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Task 1 |
| Needs | Staging public route, approved probe location outside the VPS, and confirmation that the selected Grafana Cloud plan supports the required probe |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Detect public route failures independently of the VPS and its Alloy collector.

## Relevant files or references

- `monitoring/grafana/synthetic-checks/`
- `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md`
- `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md`
- OBS-04, OBS-05, RTE-03, RTE-07

## Proposed approach

1. Configure Grafana Cloud Synthetic Monitoring from a probe location outside the target VPS and its network.
2. Create one HTTPS check per registry-approved public app route. Derive targets from reviewed registry/route data; do not accept arbitrary hostnames or credentials in probe configuration.
3. Validate TLS and record only sanitized status and latency. Do not store response bodies, request credentials, cookies, or sensitive host details.
4. Evaluate a route as unavailable after three consecutive failed one-minute checks. Keep route probes independent from the VPS collector and define the collector-heartbeat alert separately in task 6.
5. Confirm the selected plan covers probe count, evaluation, and notification features. If it does not, block Production readiness until an approved independent probe or suitable plan is available.

## Acceptance criteria

- Every registered Staging route has an external HTTPS probe with TLS validation.
- A controlled route failure is detected without relying on Alloy or host-local monitoring.
- Probe records contain only bounded Environment/app labels, status, and latency.
- Probe configuration has no arbitrary target, credential, or response-body capture.
- The documented plan supports the required probe behavior; unsupported capability is an explicit blocker.

## Source reference

OBS-04, OBS-05; RTE-03, RTE-07; v5 §§10.2, 13.1.

## Verify

- Test a passing Staging route and a controlled failing route in an approved test window.
- Stop the collector while leaving the route available; confirm the probe continues to report independently.
- Inspect probe definitions and results for unapproved targets, credentials, response bodies, or sensitive host data.
- Verify TLS failures and repeated HTTP/timeout failures are reported as unavailable.

## Out of scope

Host-side collectors, alert contact-point approval, Production fault injection, and DNS record changes.
