# Task 06 — Route and rehearse actionable alerts

## Outcome

Deliver a controlled alert to a responsible human, prove acknowledgement and recovery behavior, and verify that alert text gives a safe, actionable starting point.

## Prerequisites

- Read [Lesson 06 — Actionable alerts, notification delivery, and escalation](../lessons/06-actionable-alerts-notification-delivery-and-escalation.md) and [Lesson 07 — Monitoring security, privacy, access, and retention](../lessons/07-monitoring-security-privacy-access-and-retention.md).
- Complete Tasks 01–05 and have an approved primary and backup recipient.
- Use a test rule, staging target, or Grafana Cloud's built-in notification test facility.

## Procedure

1. Select a small set of alerts with a defined owner and action: public application unavailability, sustained objective breach, resource exhaustion risk, stale/failed backup signal, and telemetry/notification blind spot as applicable.
2. Create and manage the rules in Grafana Cloud Alerting so evaluation does not depend on the monitored VPS. For each rule, record the Cloud data source/query, threshold, evaluation interval, persistence/delay, severity, response expectation, recipient, deduplication key, no-data/error behavior, recovery condition, and runbook link. Tie numeric limits to approved objectives or the measured host baseline.
3. Configure grouping and maintenance suppression. Require an expiry for mutes and retain independent checks for core service availability. Ensure missing telemetry is not treated as a cleared alert.
4. Review the notification body for safe service identity, first-seen time, current value/threshold, impact, dashboard/log/runbook link, and first safe diagnostic action. Remove tokens, raw logs, personal data, and private infrastructure details.
5. Trigger the test through Grafana Cloud's notification test facility, a dedicated synthetic condition, or a non-production rule. Confirm receipt by the intended recipient through the actual configured destination; record delivery and acknowledgment times.
6. Resolve the test condition and confirm the recovery notification, deduplication, and final alert state. Verify that recovery represents fresh healthy samples rather than loss of telemetry.
7. Test a stale-data or integration-failure path safely. Confirm the team can distinguish “service healthy” from “monitoring blind.” Verify the backup/secondary route if one is required.
8. Remove test rules/conditions, rotate any temporary credential if used, confirm production rules are enabled, and review false-positive/alert-storm behavior before finalizing.

## Acceptance criteria

- [ ] Each production alert maps to a user-impacting failure or a documented operational action and has an owner.
- [ ] Severity, evaluation behavior, response expectation, deduplication, recovery, and runbook link are explicit.
- [ ] A controlled alert reaches the actual recipient; receipt and acknowledgment are confirmed and timed.
- [ ] Alert evaluation and notification routing are managed in Grafana Cloud or another independent service, not solely on the VPS being monitored.
- [ ] Recovery is delivered and based on fresh, healthy data; telemetry loss does not appear as service recovery.
- [ ] Stale signal or integration failure is detectable through a safe test or documented provider verification.
- [ ] Notification content contains enough context to begin diagnosis and contains no secret, customer data, or unnecessary internal detail.
- [ ] Maintenance silences are bounded, expire, and do not remove all independent coverage.
- [ ] Temporary test configuration is removed and alert credentials are stored and permissioned appropriately.

## Deliverable

A sanitized **alert catalog and delivery test record** listing rule purpose, threshold source, severity/owner, response path, tested firing and recovery times, blind spots, and corrective actions.
