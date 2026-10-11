# Task 04 — Configure useful, bounded, privacy-safe application logs

## Outcome

Verify that operators can find and correlate meaningful application and proxy events while sensitive data is excluded and disk/remote retention is bounded.

## Prerequisites

- Read [Lesson 04 — Structured logs, correlation, and useful diagnostics](../lessons/04-structured-logs-correlation-and-useful-diagnostics.md) and [Lesson 07 — Monitoring security, privacy, access, and retention](../lessons/07-monitoring-security-privacy-access-and-retention.md).
- Have access to a test/staging deployment or an approved low-risk production validation window.

## Procedure

1. Inventory each relevant source: application stdout/stderr or files, reverse-proxy access/error logs, container runtime/journald, database logs if applicable, and remote log service. Identify the single owner of rotation/retention for each path.
2. Define the minimum useful schema: timestamp/timezone, service/environment, severity, event, release, request/correlation ID, safe result/error class, and duration where meaningful. Match the application's existing logging model and avoid unnecessary code changes.
3. Review the data protection policy and create an explicit deny list: credentials, tokens, cookies, request/response bodies, personal data not needed for operations, full connection strings, payment data, and untrusted raw headers/URLs.
4. Generate synthetic success and failure requests. Inspect actual emitted records at the source and after collection. Search for secrets, user-supplied strings, full headers, query parameters, stack traces containing sensitive values, and malformed or oversized events.
5. Verify proxy and app correlation behavior. Confirm an ID is generated or validated at a trusted boundary and can be used to find both relevant records. Confirm clock synchronization and a shared time basis.
6. Configure a single intentional collection path. For containers, inspect the logging driver and set documented size/file or service-retention bounds; for journald/files/remote storage, verify the corresponding cap and failure behavior. Avoid duplicate or conflicting rotation.
7. Estimate current and peak log volume, disk/remote retention, local buffering during a network interruption, and the result when the destination is unavailable. Test rotation or expiration in a disposable target or using a supported dry-run.
8. Restrict log search/export access and document location, retention, deletion, and any remote processor. Never use real customer secrets as test data.

## Acceptance criteria

- [ ] An operator can filter representative events by service, time, severity, release, and request/correlation ID.
- [ ] Timestamps, severity, event names, and safe error classification are consistent enough to search and correlate.
- [ ] Synthetic success and failure records were inspected before and after collection.
- [ ] No credentials, tokens, cookies, sensitive bodies, or unnecessary personal data appear in the tested records.
- [ ] Untrusted correlation IDs/fields have bounded, validated handling; event size and log growth are capped.
- [ ] Rotation/retention has one clear owner and has been validated without deleting production evidence.
- [ ] Destination outage and local disk-pressure behavior are understood; monitoring failure cannot create unbounded storage growth.
- [ ] Access, remote storage location, retention, and deletion behavior are documented.

## Deliverable

A sanitized **logging configuration and validation note** with source inventory, safe schema, redaction/minimization decisions, request-correlation test, tested rotation/retention limits, storage estimate, access boundary, and outstanding privacy risks.
