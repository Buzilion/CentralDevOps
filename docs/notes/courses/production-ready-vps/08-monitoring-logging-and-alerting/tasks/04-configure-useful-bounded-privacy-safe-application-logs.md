# Task 04 — Configure useful, bounded, privacy-safe application logs

## Outcome

Verify that operators can find and correlate meaningful application and proxy events while sensitive data is excluded and disk/remote retention is bounded.

## Prerequisites

- Read [Lesson 04 — Structured logs, correlation, and useful diagnostics](../lessons/04-structured-logs-correlation-and-useful-diagnostics.md) and [Lesson 07 — Monitoring security, privacy, access, and retention](../lessons/07-monitoring-security-privacy-access-and-retention.md).
- Complete Task 02 so Alloy is installed, running, and sending metrics to the selected Grafana Cloud stack.
- Have access to a test/staging deployment or an approved low-risk production validation window.

## Procedure

1. Inventory each relevant source: application stdout/stderr or files, reverse-proxy access/error logs, container runtime/journald, database logs if applicable, and remote log service. Identify the single owner of rotation/retention for each path.
2. Define the minimum useful schema: timestamp/timezone, service/environment, severity, event, release, request/correlation ID, safe result/error class, and duration where meaningful. Match the application's existing logging model and avoid unnecessary code changes.
3. Review the data protection policy and create an explicit deny list: credentials, tokens, cookies, request/response bodies, personal data not needed for operations, full connection strings, payment data, and untrusted raw headers/URLs.
4. Generate synthetic success and failure requests in the test/staging environment and inspect the emitted records at the source. Search for secrets, user-supplied strings, full headers, query parameters, stack traces containing sensitive values, and malformed or oversized events before forwarding them.
5. Verify proxy and app correlation behavior. Confirm an ID is generated or validated at a trusted boundary and can be used to find both relevant records. Confirm clock synchronization and a shared time basis.
6. Create a Grafana Cloud access-policy token with only `logs:write`, and store it in a protected file readable by Alloy and root. Configure Alloy's `loki.source.journal` to select only the required systemd units and `loki.write` to send them to the Cloud Logs endpoint, following Lesson 04. If logs are in Docker rather than journald, choose and document a supported source; do not mount the Docker socket without a security review.
7. Reload Alloy in the test/staging environment, repeat the synthetic success and failure requests, and inspect the resulting records in Grafana Cloud Logs/Explore. Confirm labels are bounded and useful, no unexpected journal units or duplicate streams are being sent, and source-side minimization/redaction works.
8. Set source rotation and retention, Alloy behavior during a destination outage, and Grafana Cloud retention before enabling production forwarding. For containers, inspect the logging driver and set documented size/file or service-retention bounds; for journald/files/remote storage, verify the corresponding cap and failure behavior. Avoid duplicate or conflicting rotation.
9. Estimate current and peak log volume, local journal retention, Cloud retention, and Alloy's behavior during a network interruption. Test rotation or expiration in a disposable target or using a supported dry-run; do not assume remote buffering is unlimited or durable.
10. Restrict Grafana Cloud log search/export access and document the Cloud destination, retention, deletion, and any Alloy processing. Never use real customer secrets as test data.

## Acceptance criteria

- [ ] An operator can filter representative events by service, time, severity, release, and request/correlation ID.
- [ ] Timestamps, severity, event names, and safe error classification are consistent enough to search and correlate.
- [ ] Synthetic success and failure records were inspected before and after collection.
- [ ] Alloy forwards only the approved log sources to Grafana Cloud Logs, using a logs-write-only token kept outside the configuration and repository.
- [ ] No credentials, tokens, cookies, sensitive bodies, or unnecessary personal data appear in the tested records.
- [ ] Untrusted correlation IDs/fields have bounded, validated handling; event size and log growth are capped.
- [ ] Rotation/retention has one clear owner and has been validated without deleting production evidence.
- [ ] Destination outage and local disk-pressure behavior are understood; monitoring failure cannot create unbounded storage growth.
- [ ] Access, remote storage location, retention, and deletion behavior are documented.

## Deliverable

A sanitized **logging configuration and validation note** with source inventory, Alloy pipeline, safe schema, redaction/minimization decisions, request-correlation test, tested journal/container rotation and Cloud retention limits, storage estimate, access boundary, and outstanding privacy risks.
