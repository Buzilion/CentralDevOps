# 05 — Metrics collection, dashboards, and safe instrumentation

## Learning objectives

You can select metrics that answer operational questions, understand collection and label costs, build a dashboard for both service health and host diagnosis, and verify that displayed data is current and correctly interpreted.

## Metrics express numeric behavior over time

A metric is a named numeric measurement with a type, unit, timestamp, and optional dimensions (often called labels or tags). Use metrics for rates, durations, saturation, and trends; use logs for event details. Naming and units matter. A latency metric in milliseconds that is displayed as seconds can lead to dangerous decisions.

Common metric types include:

- **Counter:** only increases, such as total requests or errors. Derive a rate over a defined window; a process restart resets in-memory counters, so the collector must handle resets correctly.
- **Gauge:** a current value that can increase or decrease, such as available memory or queue depth.
- **Histogram or distribution:** observations grouped into buckets or a distribution, often used for request duration and size. Check how the chosen backend computes quantiles and aggregates buckets; percentiles from pre-aggregated local quantiles generally cannot be combined accurately.

Useful application metrics often include request count by bounded route group and outcome, request duration, active work or queue depth if applicable, dependency failures, and process restarts. Start with a few that can answer “is it working?” and “what is saturated?” Do not instrument every function or database query on a small application without a diagnostic need.

## Control dimensions, cardinality, and privacy

Metric labels create separate time series. Use bounded values such as service, environment, release channel, method, coarse route template, and result class. Do not label metrics with raw URL paths containing IDs, user identifiers, request IDs, IP addresses, email addresses, exception messages, SQL text, or arbitrary query parameters. A route label should be a template such as `/customers/{id}`, not `/customers/849213`.

High-cardinality labels can overwhelm memory, storage, query performance, and cost. They can also reveal personal data. Before adding a label, estimate its value count and identify whether it is controlled by input. Logs may carry a validated correlation ID under access controls; metric labels should remain low-cardinality.

Expose metrics only to the intended collector over loopback, private networking, or a tightly restricted source allowlist. Keep the endpoint unauthenticated only when the network boundary itself is sufficient and documented; otherwise use the collector's supported secure transport/authentication. Never publish a metrics endpoint on a public interface just because it returns no passwords.

## Choose a collection topology

Metrics can be collected by a provider agent, a hosted service, or a self-managed collector. A pull collector periodically scrapes an endpoint; a push agent sends data to a remote service. Select based on reachability, reliability, credential model, cost, retention, and failure boundaries. For a single VPS, avoid running a resource-heavy time-series database unless you have a clear need and capacity plan.

Keep collection separate from the service's critical request path. A metrics exporter should not block application requests when its backend is unreachable. Local buffering must have bounded size and a defined drop/backoff policy. Scrape intervals, metric retention, and label count all affect resource use. Record the expected overhead and verify it under real conditions.

Treat absent samples as missing data, not zero. Show sample age or collection health, and handle counter resets and exporter restarts. Compare metrics and logs using synchronized time, stable service identity, and release metadata.

## Build a dashboard for decisions

A starting operational dashboard should have a top-level row for user-facing availability, request/error rate, and latency; a second row for application health and key dependencies; and a host row for CPU/load, memory pressure, filesystem capacity and growth, and network/restart context. Show units, relevant time window, service/environment, and thresholds. Include links to diagnostic logs and the runbook when the platform supports them.

Avoid one giant dashboard with unlabeled panels. Use explicit titles such as “External HTTPS success, last 1 hour” instead of “Uptime.” Explain whether request latency is measured at the app, reverse proxy, or external probe. Mark planned maintenance or deploys rather than editing away evidence. Provide a short range for incident diagnosis and a longer range for capacity/trend review.

Validate each panel with a known value, controlled event, or independent command. Check that the displayed timezone, unit conversion, aggregation, filters, and time range are correct. Confirm stale-data behavior when the agent stops or collection is interrupted. A green panel with no recent samples is not green health.

## Instrumentation should be proportionate and safe

Add instrumentation at meaningful boundaries, such as the HTTP server and essential background work. Do not make application success depend on telemetry export. Keep metric exposition and library dependencies current and compatible with the inspected runtime. Test that metrics are updated on both success and failure and that labels are constrained.

For a first VPS, a simple provider dashboard plus external uptime and useful runtime logs may be adequate. Add a dedicated metrics collector or Grafana/Prometheus-compatible stack only when it improves diagnosis enough to justify operating, securing, backing up, and upgrading it.

## Practical checkpoint

Complete [Task 05 — Build an operational dashboard and validate its signals](../tasks/05-build-an-operational-dashboard-and-validate-its-signals.md). The deliverable must identify each panel's source, unit, interpretation, and known blind spot.

## Knowledge check

1. Why are raw request IDs poor metric labels even when they are useful in a log?
2. What must an operator know before interpreting a request-latency panel?
3. Why should metric export failure not block ordinary application requests?
4. How can a panel distinguish zero from missing or stale samples?

## References

- [Prometheus documentation — Metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Prometheus documentation — Instrumentation practices](https://prometheus.io/docs/practices/instrumentation/)
- [Prometheus documentation — Naming](https://prometheus.io/docs/practices/naming/)
