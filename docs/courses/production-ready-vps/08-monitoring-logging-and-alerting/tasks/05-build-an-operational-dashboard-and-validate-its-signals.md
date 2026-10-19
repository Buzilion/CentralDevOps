# Task 05 — Build an operational dashboard and validate its signals

## Outcome

Give an operator one concise view that distinguishes user-visible service health from internal resource condition and helps start a diagnosis without pretending that a green panel proves everything is healthy.

## Prerequisites

- Read [Lesson 05 — Metrics collection, dashboards, and safe instrumentation](../lessons/05-metrics-collection-dashboards-and-safe-instrumentation.md).
- Complete Tasks 01–04, or document why an application metric/log source is not available yet.
- Use an access-controlled dashboard or provider view; do not publish a public dashboard.

## Procedure

1. Build the operational dashboard in the Grafana Cloud stack's managed Grafana instance. Confirm that the Cloud Metrics and Logs data sources are available and review any prebuilt Linux Server integration dashboards before creating duplicate panels. Record the relevant stack plan, retention, access, and cost assumptions.
2. Add a top-level public availability/synthetic result with probe freshness and a recent time window. Use the independent probe from Task 03 and state exactly which hostname, protocol, probe location, status/content condition, and latency are measured. Do not substitute Alloy's local host metrics for public availability.
3. Add application error/request/latency signals from Grafana Cloud Metrics when the runtime can provide them. Document whether duration is measured at proxy, app, or external client, and use bounded route/result dimensions only.
4. Add Alloy-collected host CPU/load, available memory or pressure, disk bytes and inodes for relevant filesystems, and restart/dependency context. Include the units and thresholds established in Task 02 and verify the series have recent samples.
5. Add Grafana Cloud Logs queries or links for the corresponding approved sources and runbook, filtered by service and time. Ensure no panel or link includes sensitive query values or credentials.
6. For each panel, document source, collection interval, aggregation, unit, interpretation, threshold, owner, stale-data behavior, and known blind spot. Remove decorative metrics that cannot guide an operator.
7. Validate each panel against a local command, Cloud source, synthetic event, or known controlled test. Check time zone, units, current/stale behavior, filters, and aggregation. Confirm that missing Alloy data is not displayed as zero or healthy. Do not induce production load or create a disk exhaustion event.
8. Review access permissions, dashboard sharing/export behavior, data retention, and monitoring resource cost. Test the alternate status path if the dashboard service is unavailable.

## Acceptance criteria

- [ ] User-visible availability and internal VPS/application diagnosis appear as distinct signal groups.
- [ ] The dashboard is hosted in Grafana Cloud and shows fresh metrics/logs from the expected Alloy and external-probe sources.
- [ ] All panels have meaningful title, unit, source, time window, freshness, and interpretation.
- [ ] Data has been cross-checked or exercised; no panel is accepted solely because a line is displayed.
- [ ] Missing/stale samples are visibly different from zero or healthy state.
- [ ] Metric labels are bounded and do not contain request IDs, user identifiers, raw URLs, IPs, or arbitrary input.
- [ ] Dashboard access is restricted to the intended users and no public link exposes production telemetry.
- [ ] The displayed thresholds match the documented contract and capacity baseline, with an action linked for alert-level conditions.
- [ ] An independent route to determine service status exists if the dashboard or VPS is unavailable.

## Deliverable

An access-controlled **Grafana Cloud operational dashboard** plus a sanitized panel inventory that documents source, units, freshness, interpretation, validation evidence, blind spots, and owner.
