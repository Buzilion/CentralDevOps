# 06 — Actionable alerts, notification delivery, and escalation

## Learning objectives

You can design alerts around user impact and actionable risk, set bounded evaluation behavior, deliver notifications to a responsible person, and test the entire route including recovery and failure cases.

## Alert only when someone should act

An alert is a request for human attention. A useful alert answers: what is wrong, what is affected, how urgent is it, what evidence supports it, and what should the responder do next? If no one would take an action, the condition may belong on a dashboard or a periodic review rather than an immediate notification.

A practical alert set for one VPS might include:

- External HTTPS service unavailable for a sustained, defined interval.
- Application error rate or latency materially outside its agreed objective.
- Application process repeatedly restarting, failing readiness, or returning a sustained unhealthy result.
- Disk capacity or inode exhaustion projected within the response window; critical free-space conditions may require immediate action.
- Sustained memory pressure, OOM events, or a dependency failure that affects the core user path.
- Backup/restore-point age beyond the recovery objective, based on the previous course's verified backup signal.
- TLS certificate renewal failure or expiry approaching the time needed to recover it.
- Monitoring data or notification integration missing/stale when that creates a blind spot.

Avoid alerting on every CPU spike, single failed probe, informational log, or expected deploy restart. Alert thresholds should be based on the SLI/SLO, measured baseline, resource size/growth, and required response time. Use a duration or multi-sample condition to reject short noise when safe. Do not delay a critical low-disk or security signal solely to make the dashboard look quiet.

## Define severity and ownership

Severity should describe response urgency and impact, not the source technology. For example:

| Level | Meaning | Example response expectation |
|---|---|---|
| Critical | Service is unavailable or imminent loss requires immediate intervention | Acknowledge promptly; use the outage runbook |
| Warning | Reliability objective or safe operating margin is at risk but users may still be served | Review during the defined operating window |
| Informational | Change or condition needs awareness but not an urgent response | Record or review; do not page |

Choose names and response targets the actual team can meet. Every alert needs an owner or rotation, primary and backup route, and escalation if unacknowledged. A shared mailbox is not ownership if nobody monitors it. Specify quiet hours and maintenance suppression carefully; silence only the expected signal for a bounded, recorded window and never suppress external availability indefinitely.

## Make notifications useful and non-sensitive

Include concise service/environment identity, alert name and severity, first-seen time, current value and threshold, affected objective, dashboard/log/runbook links, and a suggested first diagnostic step. Avoid secret values, full log lines, customer data, private key material, or public message bodies with sensitive request details. Notification systems are another data store with their own membership and retention.

Deduplicate repeated evaluations into one incident with a clear start and recovery notification. Group related symptoms where possible—for example, an external outage plus app errors may be one incident, not a flood of separate messages. Preserve the triggering evidence and time window for investigation. Distinguish “resolved” from “no longer receiving data”; the latter may indicate a broken monitor.

## Test delivery, not just rule syntax

The alert path includes the metric/log source, evaluator, routing rule, integration credential, provider, recipient destination, and human response. A green “integration configured” state proves only part of it. Trigger a controlled test alert, confirm it arrives at the intended destination with safe content, acknowledge it, and confirm the recovery message. Test from a channel independent of the VPS where possible.

Test negative paths as well: stop or block a test exporter, use a non-production rule, or use the provider's built-in test facility to verify stale-data and integration failure handling. Do not deliberately stop a production dependency or fill production disk just to test alerts. Keep notification credentials least-privileged, rotate them through a documented process, and avoid putting them in repository files or screenshots.

## Tune without hiding incidents

Review alert history for false positives, missed detection, duplicate messages, delayed delivery, and alerts without a useful action. Adjust thresholds with a recorded reason. Track alert acknowledgment and time to useful diagnosis, not only notification count. After a real incident, update the SLI, rule, or runbook if evidence shows the signal failed.

Do not silence an alert permanently because it is noisy. Correct the underlying metric, threshold, dependency model, or maintenance behavior. When a signal must be muted for a maintenance operation, set an expiry and ensure another independent check remains active.

## Practical checkpoint

Complete [Task 06 — Route and rehearse actionable alerts](../tasks/06-route-and-rehearse-actionable-alerts.md) with a controlled test condition and a real recipient who can confirm receipt.

## Knowledge check

1. Why is “CPU above 80%” often not enough context for a useful alert?
2. What should an alert include so that the responder can begin safely?
3. Why should a monitor that stops sending data not automatically appear recovered?
4. Which parts of the alert chain are validated by a successful test message?

## References

- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
- [Prometheus documentation — Alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Prometheus documentation — Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
