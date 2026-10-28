# 07 — Monitoring security, privacy, access, and retention

## Learning objectives

You can identify sensitive data and privileged interfaces in a monitoring design, restrict access and transport, set defensible retention and deletion behavior, and protect evidence used during incident response.

## Observability systems can be sensitive systems

Metrics can reveal hostnames, software versions, process names, resource patterns, deployment schedules, filesystem mounts, route names, and failure timing. Logs can contain user identifiers, IP addresses, query strings, exception content, and accidental credentials. Dashboards can reveal infrastructure topology and operational status. Treat the whole telemetry plane as production data, not as harmless debugging output.

Create an inventory of data collected, its purpose, source, destination, sensitivity, access groups, retention, deletion method, and any processors or third parties. Minimize collection at the application boundary: preventing a secret from being emitted is safer than relying on later redaction. Review proxy access logs, app logs, tracing attributes, metric labels, crash reports, and alert payloads together.

## Restrict interfaces and credentials

Do not expose dashboards, exporters, admin APIs, log search, or collector endpoints to the public Internet by default. Place them behind a private network, VPN, authenticated reverse proxy, or provider access controls. Allow only required sources at both host and provider firewalls. A private bind address alone is not proof: inspect actual listeners and test from an external network.

Use named accounts, least privilege, multi-factor authentication where available, and separate read-only dashboard access from rule/credential administration. Remove access promptly when roles change. Avoid shared root/admin credentials and public “viewer” links for production data. Record who can export or delete telemetry.

Store API tokens and notification secrets in a suitable secret store or protected service configuration with minimal file permissions; do not commit them to Git, bake them into images, include them in command-line arguments visible to other users, or print them during tests. Rotate credentials and verify that old values no longer work. Restrict agent privileges and do not grant broad Docker socket, host PID, or host filesystem access without a documented reason.

For Grafana Cloud, create stack-scoped Access Policy tokens with only the write scopes Alloy needs (normally `metrics:write` for metrics and `logs:write` for logs). Prefer separate tokens so each can be rotated independently; never give the agent dashboard-administration, data-read, or organization-wide permissions. Store the token in a protected file and load it with Alloy's `local.file` component marked `is_secret = true`, rather than embedding it in `config.alloy`. The Cloud endpoint and instance/tenant username are not the token, but still sanitize them from general-purpose evidence.

The Linux Alloy package runs as a systemd service. Its local HTTP/UI interface should stay on a trusted local/private address; verify the actual listener and do not bind it to `0.0.0.0` or open its port in the firewall. The Unix exporter is collected within Alloy and does not need a public listener. Alloy needs outbound HTTPS to the Cloud endpoints, not inbound access from Grafana Cloud. For journal collection, review the broad read access granted by journal groups; for Docker collection, treat access to the Docker socket as host-level privilege.

Use encrypted transport for remote telemetry and follow the provider's supported authentication model. For self-hosted dashboards, protect session cookies, TLS, updates, and backups just as for other production services. Monitoring agents and exporters are code running on the host; update them and limit their permissions.

## Retention, deletion, and integrity

Choose retention based on incident diagnosis, capacity, privacy obligations, and the service's recovery needs. High-resolution metrics can often have shorter retention than rolled-up trends; logs may need a shorter window than audit records. Retention must have a measurable maximum and include any remote copy, backup, export, and notification archive. Verify provider defaults and account-level lifecycle policies rather than assuming data expires automatically.

Estimate ingestion volume and storage growth. Apply rotation, size caps, and backpressure at the source so an outage or error loop cannot fill the VPS. Define what happens when remote collection is unavailable: bounded local buffering, controlled loss, or alternate delivery. Do not allow telemetry pressure to make the application unavailable.

Deletion should cover primary storage, replicas, backups, exported files, and provider retention as far as the service permits. Document limits and delayed expiration honestly. For incident evidence, preserve only what is needed, restrict access, and apply an approved retention hold instead of copying entire databases or log archives into an informal folder.

## Privacy-safe evidence and incident sharing

Before attaching screenshots, logs, or query results to tickets or course records, inspect and redact tokens, cookies, IP addresses when sensitive, customer content, internal DNS names, unique host identifiers, and exact private endpoint values. Prefer synthetic data and aggregate metrics. Keep raw evidence inside the approved restricted system; sanitized records should describe finding, time, release, effect, and action without reproducing sensitive payloads.

Check the monitoring vendor's data location, processors, export, access, breach notification, and deletion terms where relevant. If telemetry leaves the VPS, confirm that the transfer is permitted and authenticated. Reassess the data inventory when new labels, log fields, probes, or integrations are introduced.

## Practical checkpoint

Use [Task 04 — Configure useful, bounded, privacy-safe application logs](../tasks/04-configure-useful-bounded-privacy-safe-application-logs.md) and [Task 06 — Route and rehearse actionable alerts](../tasks/06-route-and-rehearse-actionable-alerts.md) to verify access, content, retention, and credential handling across the signal path.

## Knowledge check

1. Why should a metrics endpoint be protected even if it contains no credentials?
2. What systems and copies must be considered when setting telemetry retention?
3. Why is source-side data minimization preferable to redaction after collection?
4. Which privileged access can an unrestricted Docker socket grant to a monitoring container?

## References

- [OWASP Cheat Sheet Series — Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [NIST SP 800-92 — Guide to Computer Security Log Management](https://csrc.nist.gov/pubs/sp/800/92/final)
- [Prometheus documentation — Security model](https://prometheus.io/docs/operating/security/)
- [Grafana Cloud — Access Policies](https://grafana.com/docs/grafana-cloud/security-and-account-management/authentication-and-permissions/access-policies/)
- [Grafana Alloy — `local.file`](https://grafana.com/docs/alloy/latest/reference/components/local/local.file/)
- [Grafana Alloy — Configure Alloy on Linux](https://grafana.com/docs/alloy/latest/configure/linux/)
