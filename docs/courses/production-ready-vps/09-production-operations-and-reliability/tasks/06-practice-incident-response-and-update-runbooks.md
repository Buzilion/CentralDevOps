# Task 06 — Practice incident response and update runbooks

## Outcome

Demonstrate that an operator can coordinate a bounded incident scenario, find the right procedure, make a controlled decision, and prove service recovery.

## Prerequisites

- Complete Tasks 01–05 and review [Lesson 06 — Incident response, decision-making, and operational runbooks](../lessons/06-incident-response-and-operational-runbooks.md).
- Have a current service contract, failure diagnosis matrix, monitoring/alert route, deployment runbook, and recovery procedure.
- Obtain approval for the exercise and use a non-production scenario where practical.

## Procedure

1. Choose a bounded scenario relevant to the architecture, such as a staging application health failure, a simulated dependency error, or a provider-generated test alert. State what is not being tested.
2. Write an exercise plan with owner, participants, scope, expected impact, start/end, safety limits, abort condition, independent communication/recovery path, and evidence location.
3. Give the scenario to a responder who did not author the relevant runbook if possible. Record the simulated impact time, alert/detection, acknowledgment, diagnosis, decision, mitigation, and validated recovery times.
4. Have the responder locate the service owner, release identity, dashboards/logs, safe first checks, and escalation path without coaching where practical.
5. Require the responder to state evidence and uncertainty before changing state. For any simulated rollback/restore decision, identify data and compatibility consequences and the person authorized to approve them.
6. Verify recovery through the relevant user-facing operation and fresh independent monitoring evidence. Do not accept an alert clearing by itself.
7. Review confusing, missing, unsafe, stale, or inaccessible instructions. Create corrective actions with owner and due date.
8. Remove test settings, verify ordinary alerts and public checks remain enabled, and update the off-host runbook with the review date.

## Acceptance criteria

- [ ] The scenario is authorized, bounded, reversible, and includes an explicit abort condition.
- [ ] A responder can find the correct service information, logs/signals, contact, and procedure.
- [ ] Timeline captures detection, acknowledgment, diagnosis, mitigation, and recovery with timestamps where measurable.
- [ ] Decisions distinguish observed facts from assumptions and identify required approvals.
- [ ] Recovery is verified at the user-facing boundary and with fresh monitoring samples.
- [ ] Runbook gaps have assigned owners/due dates; test configuration is removed.
- [ ] Exercise report contains no credentials, sensitive payloads, or unnecessary infrastructure details.

## Deliverable

A sanitized **incident exercise report and updated operational runbook** stored outside the VPS.
