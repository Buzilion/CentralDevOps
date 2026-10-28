# Monitoring, Logging, and Alerting — Course Checklist

Complete this subject after **Linux Server Administration**, **Networking, DNS, and Firewall Security**, **Docker and Container Operations**, **Infrastructure Automation with Ansible**, **CI/CD with GitHub Actions**, **Reverse Proxy, HTTPS, and Application Serving**, and **Data Persistence, Backup, and Recovery**. Base every signal on the inspected application and its actual runtime contract. This module's default telemetry path uses Grafana Alloy as a systemd agent on the VPS and Grafana Cloud for managed metrics, logs, dashboards, and alert evaluation. Application instrumentation and notification destinations still depend on the actual service and account capabilities.

Monitoring is an operational control, not a dashboard installation exercise. Decide what failures matter, collect the minimum signals needed to detect and diagnose them, alert a reachable owner, and prove the complete path with safe tests. Public availability checks must run outside the monitored VPS; an Alloy agent on that VPS cannot report a host outage. Keep monitoring private, budget resources on a single VPS, and never publish secrets, personal data, raw production records, or identifying infrastructure details in course evidence.

## Lessons

- [ ] [01 — Observability signals, service objectives, and monitoring boundaries](lessons/01-observability-signals-service-objectives-and-monitoring-boundaries.md)
- [ ] [02 — VPS health: CPU, memory, storage, network, and capacity](lessons/02-vps-health-cpu-memory-storage-network-and-capacity.md)
- [ ] [03 — Application health, readiness, and external uptime checks](lessons/03-application-health-readiness-and-external-uptime-checks.md)
- [ ] [04 — Structured logs, correlation, and useful diagnostics](lessons/04-structured-logs-correlation-and-useful-diagnostics.md)
- [ ] [05 — Metrics collection, dashboards, and safe instrumentation](lessons/05-metrics-collection-dashboards-and-safe-instrumentation.md)
- [ ] [06 — Actionable alerts, notification delivery, and escalation](lessons/06-actionable-alerts-notification-delivery-and-escalation.md)
- [ ] [07 — Monitoring security, privacy, access, and retention](lessons/07-monitoring-security-privacy-access-and-retention.md)
- [ ] [08 — Failure exercises, troubleshooting, and operational handoff](lessons/08-failure-exercises-troubleshooting-and-operational-handoff.md)

## Hands-on tasks

- [ ] [Task 01 — Define service signals, ownership, and measurable objectives](tasks/01-define-service-signals-ownership-and-measurable-objectives.md)
- [ ] [Task 02 — Monitor VPS resources and establish a capacity baseline](tasks/02-monitor-vps-resources-and-establish-a-capacity-baseline.md)
- [ ] [Task 03 — Verify application health locally and from outside the VPS](tasks/03-verify-application-health-locally-and-externally.md)
- [ ] [Task 04 — Configure useful, bounded, privacy-safe application logs](tasks/04-configure-useful-bounded-privacy-safe-application-logs.md)
- [ ] [Task 05 — Build an operational dashboard and validate its signals](tasks/05-build-an-operational-dashboard-and-validate-its-signals.md)
- [ ] [Task 06 — Route and rehearse actionable alerts](tasks/06-route-and-rehearse-actionable-alerts.md)
- [ ] [Task 07 — Run a monitoring failure exercise and publish the runbook](tasks/07-run-a-monitoring-failure-exercise-and-publish-the-runbook.md)

## Subject completion gate

- [ ] A service inventory names each critical component and its dependencies; each signal has a source, owner, and known blind spot; unknowns are explicit.
- [ ] Availability, latency, and recovery expectations are measurable, have an agreed observation window, and distinguish user impact from machine symptoms.
- [ ] Alloy is installed and enabled as a systemd service, collects the selected host metrics, and sends fresh samples to Grafana Cloud over outbound HTTPS; its local UI and any scrape endpoints are not publicly reachable.
- [ ] CPU, memory, disk space and inodes, network/listener state, host uptime, and application health are visible in Grafana Cloud with timestamps and useful context.
- [ ] Application health checks distinguish process liveness from readiness, avoid leaking internal details, and have tested behavior when a dependency is unavailable.
- [ ] At least one public availability check runs from outside the VPS and validates the intended hostname, HTTPS certificate, and expected application response.
- [ ] Selected application/systemd logs reach Grafana Cloud Logs through Alloy, are searchable and time-correlated, and have bounded collection, access, retention, and tested privacy controls.
- [ ] Grafana Cloud dashboards show service-level and host-level signals with units, ranges, and caveats; every displayed signal has been exercised or independently verified.
- [ ] Grafana Cloud alert rules and notification policies have an owner, actionable context, severity, response expectation, deduplication/recovery behavior, and a tested delivery path.
- [ ] Monitoring and alert delivery do not rely exclusively on the VPS being monitored; loss of telemetry and stale data are detectable.
- [ ] Grafana Cloud endpoints, narrowly scoped write credentials, Alloy's local interface, logs, metric labels, dashboards, and notification destinations are protected; retention and deletion behavior are documented.
- [ ] A safe failure exercise proves detection, notification, diagnosis, recovery, and evidence capture without deliberately exhausting production resources or exposing private data.
- [ ] A dated, sanitized runbook explains routine checks, alert response, access, known blind spots, recovery, and escalation; monitoring costs and VPS resource impact are understood.

## Exit criteria

The operator can answer whether the application is available to a user, whether the VPS has sufficient headroom, and what changed when service degraded. Important failures reach a person through a verified notification path, while dashboards and logs support investigation without exposing sensitive data. Monitor loss, stale data, and notification failures are considered explicitly. Proceed to **Production Operations and Reliability** only after the end-to-end signal-to-action path has been exercised and the runbook has been reviewed.
