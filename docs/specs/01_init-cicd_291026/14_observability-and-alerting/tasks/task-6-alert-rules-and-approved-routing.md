# Task 6: Alert rules and approved routing

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Tasks 2, 3, and 5 |
| Needs | Staging metrics/logs/probes, and owner-approved alert recipient/channel/escalation details |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Implement and rehearse every required alert rule while ensuring notifications are sent only to an approved, accountable route.

## Relevant files or references

- `monitoring/grafana/alert-rules/`
- `monitoring/grafana/synthetic-checks/`
- `docs/runbooks/observability-and-alerting.md`
- OBS-03, OBS-04, OBS-05, OBS-08; PRD Q5; operational feedback v2 §7

## Proposed approach

1. Implement the spec thresholds: disk/inodes at least 85% for 15 minutes; 3 long-lived-container restarts in 10 minutes; unhealthy container for 5 minutes; certificate expiry under 21 days; newest good backup older than 8 hours; app 5xx rate at least 5% over 5 minutes with at least 20 requests; missing host telemetry for 5 minutes; and route failure for 3 consecutive one-minute probes.
2. Group alerts only by bounded Environment, host, app, and severity labels. Ensure no-data states for host heartbeat and backup freshness fire rather than resolve.
3. Store reviewed alert expressions in the repository and apply them through the approved Grafana Cloud operator workflow.
4. Keep contact points/routes unconfigured until the owner confirms the primary, backup/escalation recipient, channel, and routing behavior. Do not infer or copy an address from notes or use an unapproved test destination.
5. Once approval is recorded, route every required alert to the accountable primary and documented escalation path. Confirm whether reboot-pending notifications share that route; do not add reboot notification behavior here.
6. Exercise each alert in Staging with synthetic values or a controlled disposable host; record rule firing and delivery separately.

## Acceptance criteria

- All OBS-03 alert rules and the OBS-04 route-unavailable alert use the exact spec thresholds.
- A missing/stale host heartbeat or backup success metric fires; missing data is never interpreted as healthy.
- Each alert fires and clears correctly in Staging.
- Delivery is proven to the approved primary and escalation/backup path; without owner approval, leave this task unchecked and report it blocked.
- No recipient address, credential, tenant ID, or sensitive host detail is stored in the repository or task summary.

## Source reference

OBS-03 to OBS-05, OBS-08; PRD Q5; v5 §13.1; spec 07 certificate metric; spec 13 backup status contract.

## Verify

- Test below/at/above each threshold with deterministic Staging fixtures.
- Test a stopped collector and a failed external route independently.
- Confirm every required rule receives an approved notification and escalation behavior, without triggering Production.
- Inspect alert definitions and summaries for unapproved contact information or secret values.

## Out of scope

Choosing a recipient without owner approval, reboot notification implementation, Production fault injection, and replacing the selected observability provider.
