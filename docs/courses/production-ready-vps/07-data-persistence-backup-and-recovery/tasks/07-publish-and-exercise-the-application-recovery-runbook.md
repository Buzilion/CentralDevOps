# Task 07 — Publish and exercise the application recovery runbook

## Outcome

Publish an operator-ready recovery procedure independent of the VPS and exercise the decision path with a short tabletop or staging drill.

## Prerequisites

- Complete Tasks 01–06.
- Read [Lesson 08 — Recovery workflow, incident decisions, and operational evidence](../lessons/08-recovery-workflow-incident-decisions-and-operational-evidence.md).
- Have an approved, access-controlled location for operational documentation outside the VPS.

## Procedure

1. Assemble the data inventory, recovery contract, backup job details, off-site access path, successful restore drill, and migration rehearsal into a concise runbook. Link to authoritative procedures rather than copying secret-bearing configuration.
2. Document symptom triage and decision points for host loss, database loss/corruption, accidental deletion, failed backup, and suspected compromise. Include stop conditions where evidence is inadequate or the selected restore point may contain the incident.
3. List roles/owners, emergency access path, provider/account dependencies, tool/engine versions, restore-point selection rule, key-recovery process, resource prerequisites, restore order, validation checks, traffic-switch approval, and cleanup process.
4. State measured RPO/RTO and any exclusions alongside the objectives. Include exact accepted limitations and open actions; do not promise an untested recovery time.
5. Store the runbook in a versioned, access-controlled location that remains reachable if the VPS is down. Verify a second authorized operator can find it and understand the recovery access process without receiving a secret in the document.
6. Run a tabletop with a second operator: give them one scenario (for example, VPS disk loss or accidental deletion) and ask them to select the right response, restore point, approvals, and validation. Alternatively, perform a safe staging drill without public traffic.
7. Record missed steps and update the runbook. Confirm the changes are versioned and an owner/date is assigned to future review.

## Acceptance criteria

- [ ] Runbook is reachable independently of the production VPS and includes version/date/owner.
- [ ] Each scenario has a decision path, recovery order, validation, approval, and stop/escalation condition.
- [ ] Restore identity and encryption-key recovery are documented without exposing credentials or keys.
- [ ] Measured RPO/RTO are distinguished from goals and include measurement boundaries/exclusions.
- [ ] A second operator successfully follows the tabletop or staging procedure and gaps are recorded.
- [ ] Recovery steps preserve unaffected copies and never restore over production during the exercise.
- [ ] Runbook and evidence contain no secrets, private keys, or actual database/file contents.

## Deliverable

An approved, versioned **application recovery runbook** and a sanitized tabletop/staging exercise record with open actions and review owner.
