# 08 — Failure exercises, troubleshooting, and operational handoff

## Learning objectives

You can investigate an alert from user symptom to component evidence, exercise the monitoring path safely, distinguish recovery from symptom removal, and hand over a runbook that another operator can use.

## Follow evidence across the request path

Start from the reported symptom and the time it began. Confirm whether the failure is current and user-visible; compare external probes from more than one check interval and validate DNS/TLS/public routing. Then compare application health, request/error/latency metrics, host resource trends, service restart/deploy history, dependency state, and logs for the same time window and release.

A disciplined order prevents risky guesswork:

1. Confirm scope, impact, start time, and whether the alert is still firing.
2. Check the independent external probe and current user-facing behavior.
3. Review recent deploys, configuration changes, provider events, and restarts.
4. Compare application and host signals; look for saturation, missing data, or dependency failures.
5. Search sanitized logs by service, time, release, and correlation ID.
6. Follow the runbook's least-risk mitigation, preserve necessary evidence, and verify user recovery.
7. Record cause, decisions, actual recovery time, and follow-up work.

Do not infer cause from correlation alone. A deploy at the same time as an error increase is a lead to verify, not proof. Avoid restarting services or deleting data before checking whether an operation is still in progress or whether the action destroys useful evidence.

## Alert detection time and recovery evidence

Measure the delay from a controlled or observed fault to detection, notification, human acknowledgment, and validated recovery. Each interval reveals a different weakness: slow polling, alert evaluation delay, broken routing, unavailable responders, or an unclear mitigation. Keep the original timestamps and state what is excluded.

After mitigation, verify the application from the user-facing boundary and check that the key SLI returns to its expected behavior. “Alert cleared” may mean only that samples stopped arriving or a threshold was crossed briefly. Confirm healthy, fresh samples and a successful external request. Continue monitoring for recurrence and delayed effects.

Capture sanitized evidence: alert identity, time window, release, affected SLI, relevant host trend, safe event IDs, action, and validation. Do not copy raw logs, customer records, secrets, or screenshots with exposed infrastructure details into general-purpose notes.

## Exercise safely

Use a staging target, test rule, provider test function, or reversible low-risk condition. Examples include firing a dedicated test alert, checking a synthetic endpoint that deliberately returns a known test status, or exercising an isolated test service restart. Do not fill a production filesystem, kill the production database, inject live customer failures, or disable the only alert channel as an unannounced test.

Define an exercise plan: owner, expected result, start/end, affected component, safety limit, rollback/stop condition, and where evidence will be stored. Confirm normal service health and a working out-of-band communication path first. Test both firing and recovery, duplicate suppression, stale telemetry, and the human's ability to locate the correct runbook. For any production exercise, obtain appropriate authorization, announce it, and keep the blast radius small.

For the Alloy/Grafana Cloud path, a safe staging exercise is to stop Alloy on a test VPS or disable a test scrape target, then confirm Grafana Cloud reports missing data and the no-data alert fires while the independent public uptime check continues. Restart Alloy or restore the test target, then verify that fresh metrics/logs resume before the alert resolves. Do not stop the only production collector as an unannounced test. If using a non-production token or configuration, remove it after the exercise.

## Maintain an operational runbook

A useful runbook contains:

- Service and environment scope, owner, support hours, and escalation contacts.
- Links to external availability checks, dashboards, logs, deployment history, and provider status.
- Alloy installation/version, configuration path, service status and log commands, Cloud metrics/logs endpoint identity, and the safe credential-retrieval/rotation process (never token values).
- Alert meanings, severity, thresholds, expected response, and maintenance/silence rules.
- Safe first checks and commands or UI paths, with expected healthy and unhealthy results.
- Restart, rollback, capacity, certificate, dependency, and communication procedures appropriate to the actual application.
- Access prerequisites and approved secret-retrieval path, never secret values.
- Validation criteria, evidence handling, known blind spots, monitoring/notification failure path, and last review date.

Keep procedures specific enough for another operator but avoid embedding credentials or commands that destroy data without a confirmation step. Link to the existing deployment and recovery procedures instead of maintaining conflicting copies. Rehearse the runbook when the architecture changes and periodically when team readiness matters.

During a live incident, an operator handoff must transfer context, not just a runbook link: state the current impact and last verified time, actions tried and their results, unresolved risks or approvals, the next owner, and the next update time. The receiving operator should acknowledge responsibility.

## Treat telemetry failures as incidents too

Alert on collection gaps, stale samples, failed integrations, and unavailable dashboards only where they create a material blind spot. Grafana Cloud dashboards remain outside the VPS failure boundary, but Alloy cannot forward while the VPS or its network is unavailable. Document an alternate way to check public service behavior if Grafana Cloud is unavailable, and the VPS provider-console/recovery path if the host itself is unreachable.

An alert platform that cannot notify anyone is not operational. Periodically confirm recipients, escalation, credential expiry, provider quotas, and integration health. Monitor the monitoring path without creating an infinite alert loop.

## Practical checkpoint

Complete [Task 07 — Run a monitoring failure exercise and publish the runbook](../tasks/07-run-a-monitoring-failure-exercise-and-publish-the-runbook.md). Review results with the service owner and keep all evidence sanitized.

## Knowledge check

1. Why is alert resolution not by itself proof that service recovered?
2. Which steps distinguish a symptom from a verified root cause?
3. Name two safe ways to test alert delivery without disrupting production.
4. If the VPS is unreachable, which monitoring path should still detect the outage, and what fallback should an operator use if Grafana Cloud is unavailable?

## References

- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Google SRE Book — Being On-Call](https://sre.google/sre-book/being-on-call/)
- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
