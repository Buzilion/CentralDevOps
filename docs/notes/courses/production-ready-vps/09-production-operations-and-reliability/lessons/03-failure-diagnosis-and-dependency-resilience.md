# 03 — Failure diagnosis and dependency resilience

## Learning objectives

You can move from a user symptom to evidence across the request path, classify likely failure boundaries, avoid premature remediation, and make dependency failures visible without creating retry storms.

## Diagnose from observed impact, not assumptions

When a report arrives, establish what is failing before changing the system:

1. Record the start time, affected users/operations, scope, and whether the symptom is ongoing.
2. Reproduce or verify the user-facing behavior from an independent location when possible.
3. Check recent releases, configuration changes, scheduled work, provider events, and reboots.
4. Compare reverse-proxy, application, dependency, host, and external-monitor evidence for the same time window.
5. Check telemetry freshness and whether clocks are sufficiently synchronized to correlate events.
6. Form one or more hypotheses and identify what evidence would confirm or disprove each.
7. Choose the lowest-risk mitigation that limits impact; preserve evidence before a restart, cleanup, or restore.
8. Verify recovery at the boundary that users experienced and watch for recurrence.

Symptoms are facts; causes are hypotheses until supported by evidence. A deployment preceding a failure is an important lead, not proof. A 200 response from the process does not prove a database-backed operation works. A green internal check does not prove DNS, TLS, or the public proxy path works.

## Follow the dependency chain

Draw a request path that reflects the application actually deployed, such as:

```text
User -> DNS / network -> TLS proxy -> application -> database / external service
                                      |             |
                                      +-- logs      +-- persistence / queue
```

For each dependency, record what the application does when it is slow, unavailable, misconfigured, or returning malformed data. Include DNS resolution, certificates, persistent storage, image registry, backup storage, notification provider, and deployment credentials where relevant. The outage boundary may be different from the runtime boundary: a registry outage may not affect the running release but may block a rollback.

Use timeouts for network calls and bound retries. Exponential backoff with jitter can reduce synchronized retries, but must be paired with a maximum elapsed time and an appropriate user or job outcome. Retrying a non-idempotent operation can create duplicate writes; make such operations idempotent or use an explicit idempotency key where the application supports it. Do not retry forever, amplify traffic to a struggling dependency, or silently convert failure into fake success.

## Separate immediate mitigation from diagnosis

Mitigation aims to reduce current impact; diagnosis explains why it occurred. Safe mitigation may be a controlled rollback, temporary traffic reduction, disabling a non-critical feature, or restoring a dependency after verifying its state. A restart can be reasonable when the process is demonstrably stuck and restart behavior is understood, but it can erase volatile evidence or interrupt work. Deleting data, rebuilding storage, changing firewall rules, or restoring a backup has larger consequences and requires explicit checks and authorization.

Prefer commands and procedures that inspect before they modify. Capture relevant timestamps, release IDs, restart history, resource trends, and sanitized logs. Keep an incident timeline so several operators do not repeat risky actions or contradict one another.

## Plan for degraded dependencies

The application should fail visibly and predictably when an essential dependency is unavailable. Decide whether requests should fail fast, return a clear temporary error, queue work, or expose a limited degraded mode. Preserve queued work safely, bound queue growth, and define how it drains after recovery. Do not claim a critical operation succeeded if it was only accepted locally and then lost.

Document which dependencies are critical to startup, readiness, and each user-facing operation. This supports useful health checks and incident triage without making every optional integration a global outage.

## Practical checkpoint

Complete [Task 03 — Build a failure diagnosis matrix](../tasks/03-build-failure-diagnosis-matrix.md) and exercise at least one safe scenario.

## Knowledge check

1. Why is a recent deployment a lead rather than a confirmed root cause?
2. What makes unbounded retries dangerous during a dependency outage?
3. Why should a rollback path include registry availability?
4. Which evidence should be preserved before restarting a service?

## References

- [Google SRE Book — Managing Critical State](https://sre.google/sre-book/managing-critical-state/)
- [Google SRE Book — Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
