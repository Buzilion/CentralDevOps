# Task 07 — Run a monitoring failure exercise and publish the runbook

## Outcome

Prove that an operator can detect and investigate one realistic failure, receive and acknowledge its alert, restore verified service, and use an up-to-date runbook without unsafe production experimentation.

## Prerequisites

- Complete Tasks 01–06 and review [Lesson 08 — Failure exercises, troubleshooting, and operational handoff](../lessons/08-failure-exercises-troubleshooting-and-operational-handoff.md).
- Have an application/service owner approve scope, participant, environment, time, safety limit, and evidence handling.
- Have an independent communication and recovery path; do not use production for destructive tests.

## Procedure

1. Choose one low-risk exercise, such as a provider-generated test alert, a reversible test endpoint failure in staging, a stopped test exporter, or a simulated notification integration failure. State what the exercise does not test.
2. Write an exercise plan with owner, expected detection, affected boundary, start/end time, success criteria, stop condition, rollback, and communication channel. Confirm normal service status and current monitoring before starting.
3. Have a responder who did not configure the test receive and acknowledge the alert. Start a clock at the defined simulated impact and record detection, delivery, acknowledgment, diagnosis, mitigation, and validated recovery timestamps.
4. Follow the runbook without coaching where practical. Verify the public/user-facing check and fresh application/host signals after recovery; do not treat alert-clearing alone as success.
5. Record the diagnosis chain: user symptom, external probe, deploy/change history, application health/metrics, host signal, log evidence, action, and how the cause was confirmed. Redact sensitive values and preserve only the minimum evidence.
6. Review any delay, missing alert, confusing dashboard, unsafe step, incorrect assumption, or unnecessary exposure. Assign each corrective action an owner and due date.
7. Finalize the runbook with service scope, contacts/escalation, dashboards/logs/status links, alert meanings, first safe checks, rollback/recovery references, monitoring-failure alternative, access/secret path, validation criteria, known blind spots, and review date.
8. Remove test configuration and temporary credentials; confirm ordinary alerts and public checks remain enabled. Store the sanitized exercise report and runbook in the approved restricted documentation location.

## Acceptance criteria

- [ ] The exercise was authorized, bounded, reversible, and did not intentionally exhaust production resources or disrupt real users.
- [ ] A responder other than the rule author could locate the relevant dashboard, logs, and runbook from the alert.
- [ ] Detection, delivery, acknowledgment, diagnosis, mitigation, and validated recovery timestamps are recorded.
- [ ] Recovery was independently checked through the relevant user-facing path and fresh signals.
- [ ] The evidence is sanitized and does not include credentials, personal data, raw payloads, or exposed private infrastructure identifiers.
- [ ] Any alert miss, delay, unsafe procedure, blind spot, or objective gap has an owner and due date.
- [ ] The runbook includes a way to check service when primary monitoring or the VPS is unavailable.
- [ ] Test artifacts are removed, production coverage is restored, and the runbook has a named owner and review date.

## Deliverable

A dated, sanitized **monitoring exercise report and operational runbook** with scope, timestamps, signal-to-action evidence, recovery validation, deviations, owners/due dates, escalation, monitoring failure fallback, and review cadence.
