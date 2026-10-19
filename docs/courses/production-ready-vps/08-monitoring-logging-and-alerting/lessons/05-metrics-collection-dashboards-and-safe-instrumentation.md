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

## Use Alloy to send metrics to Grafana Cloud

The course's default path runs Grafana Alloy on the VPS as a package-managed systemd service. The `prometheus.exporter.unix` component collects Linux host metrics without exposing a separate exporter port; `prometheus.scrape` gathers them locally inside Alloy, and `prometheus.remote_write` sends them to Grafana Cloud Metrics. Use the metrics endpoint and instance ID from the Grafana Cloud stack. The following illustrates the component wiring; replace the placeholders, create the token file, and review the generated or customized configuration before enabling it:

```alloy
local.file "metrics_token" {
  filename  = "/etc/alloy/secrets/grafana-cloud-metrics-token"
  is_secret = true
}

prometheus.exporter.unix "host" {
  include_exporter_metrics = true
}

prometheus.scrape "host" {
  targets         = prometheus.exporter.unix.host.targets
  scrape_interval = "60s"
  forward_to      = [prometheus.remote_write.cloud.receiver]
}

prometheus.remote_write "cloud" {
  external_labels = {environment = "production"}

  endpoint {
    url = "https://<your-metrics-host>/api/prom/push"

    basic_auth {
      username = "<your-metrics-instance-id>"
      password = local.file.metrics_token.content
    }
  }
}
```

The token file must be readable by the Alloy service account and root only. Create a Grafana Cloud access-policy token with the minimum `metrics:write` scope; never paste it into this configuration, Git, or a screenshot. For applications that expose metrics, add a separate `prometheus.scrape` component for a loopback/private target and forward it to the same Cloud receiver. Keep the exporter and application endpoint off public interfaces.

If a metric needs filtering or label normalization, place `prometheus.relabel` between the scrape and remote-write components and verify the resulting series in Grafana Cloud. For logs, `loki.process` can parse or filter records before `loki.write`. Keep transformations small, bounded, and documented; they do not replace preventing sensitive data at the source.

Grafana Cloud's Linux Server integration can provide guided setup, prebuilt dashboards, and alerting when available on the account. If using it, inspect the generated Alloy configuration and avoid collecting the same host or logs twice with a second manual pipeline. Whether using the guided integration or a reviewed custom configuration, use Grafana Cloud's metrics and logs backends rather than installing a time-series database and Grafana UI on the VPS.

For the Linux package, the default Alloy configuration file is `/etc/alloy/config.alloy`; the service stores component state under `/var/lib/alloy/data`. Protect that state directory and monitor disk use, especially while Cloud is unreachable. After editing a configuration, reload Alloy and inspect its systemd status and journal logs. Keep outbound HTTPS access to the Cloud endpoints working, but do not open an inbound exporter port. Restrict Alloy's own HTTP/UI interface to a trusted local/private path.

Scrape intervals, Cloud retention, ingestion limits, label count, and Alloy's local state all affect resource use and cost. Record the expected overhead and verify it under real conditions. Treat absent samples as missing data, not zero. In Grafana Cloud, verify that `up` and the expected host metrics have recent samples; create an alert for missing/stale telemetry rather than silently displaying a healthy zero. Compare metrics and logs using synchronized time, stable service identity, and release metadata.

## Build a dashboard for decisions

A starting operational dashboard should have a top-level row for user-facing availability, request/error rate, and latency; a second row for application health and key dependencies; and a host row for CPU/load, memory pressure, filesystem capacity and growth, and network/restart context. Show units, relevant time window, service/environment, and thresholds. Include links to diagnostic logs and the runbook when the platform supports them.

Avoid one giant dashboard with unlabeled panels. Use explicit titles such as “External HTTPS success, last 1 hour” instead of “Uptime.” Explain whether request latency is measured at the app, reverse proxy, or external probe. Mark planned maintenance or deploys rather than editing away evidence. Provide a short range for incident diagnosis and a longer range for capacity/trend review.

Validate each panel with a known value, controlled event, or independent command. Check that the displayed timezone, unit conversion, aggregation, filters, and time range are correct. Confirm stale-data behavior when the agent stops or collection is interrupted. A green panel with no recent samples is not green health.

## Instrumentation should be proportionate and safe

Add instrumentation at meaningful boundaries, such as the HTTP server and essential background work. Do not make application success depend on telemetry export. Keep metric exposition and library dependencies current and compatible with the inspected runtime. Test that metrics are updated on both success and failure and that labels are constrained.

For a first VPS, the Alloy-to-Grafana-Cloud path gives the operator a managed metrics/logs destination and dashboard without hosting a database or Grafana UI on the monitored machine. Keep application instrumentation small and add traces only when a concrete diagnostic need justifies their cost and complexity.

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
- [Grafana Alloy — `prometheus.exporter.unix`](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.exporter.unix/)
- [Grafana Alloy — `prometheus.scrape`](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.scrape/)
- [Grafana Alloy — `prometheus.relabel`](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.relabel/)
- [Grafana Alloy — `prometheus.remote_write`](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.remote_write/)
- [Grafana Alloy — `loki.process`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.process/)
- [Grafana Cloud — Monitor a Linux server](https://grafana.com/docs/learning-journeys/linux-server-integration/)
