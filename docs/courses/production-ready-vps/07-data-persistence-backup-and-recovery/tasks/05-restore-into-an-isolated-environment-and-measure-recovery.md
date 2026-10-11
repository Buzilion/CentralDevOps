# Task 05 — Restore into an isolated environment and measure recovery

## Outcome

Recover a selected encrypted off-site point into a clean, isolated target, validate usable application data, and compare measured RPO/RTO with the approved objectives.

## Prerequisites

- Complete [Task 04 — Automate backup scheduling, retention, and failure visibility](04-automate-backup-scheduling-retention-and-failure-visibility.md).
- Read [Lesson 06 — Restore testing and recovery validation](../lessons/06-restore-testing-and-recovery-validation.md).
- Have a disposable VPS, isolated staging environment, or approved recovery target with adequate space and access. Do not use production as the restore target.

## Procedure

1. Schedule and announce the exercise. Define the simulated outage time, the incident lead, stop conditions, permitted data, test network, and method to prevent outbound email, billing, webhooks, or scheduled jobs.
2. Start the RTO clock at the agreed recovery declaration point. Provision a clean target or record which provisioning time is excluded. Confirm it cannot receive public traffic accidentally.
3. Select a specific remote restore point. Record its identity and timestamp; retrieve it using the documented recovery identity, verify integrity, and recover the encryption key through its separate documented path.
4. Restore database and companion files using the documented tool/version/order. Keep all data in the isolated target. Capture safe command results; redact credentials and record values.
5. Validate storage state: engine restore/consistency result, required schema or migration version, representative non-sensitive record checks, required file presence, and cross-references where safe.
6. Start the matching application release with external side effects disabled and traffic disconnected. Verify readiness, read expected recovered state, and run a safe representative operation.
7. Stop the RTO clock only when the agreed validation criteria pass. Record completion time, last recovered data point, data age/loss relative to simulated incident, restore duration, and exclusions.
8. Compare observed RPO/RTO with objectives. For every miss or manual workaround, record a corrective action and owner. Do not revise the recorded measurement to make it pass.
9. Securely dispose of temporary restored data and credentials according to policy. Preserve only sanitized evidence and the required approved recovery artifact.

## Acceptance criteria

- [ ] The selected copy was independently retrieved and decrypted, not read only from a production cache.
- [ ] Restore completed on a clean, isolated target without writing to production.
- [ ] Database/file consistency and application-level validation criteria passed.
- [ ] External side effects and public traffic were disabled during the drill.
- [ ] Actual RPO and RTO, start/stop definitions, selected restore point, and exclusions are recorded.
- [ ] Objective misses and recovery blockers have an owner and next action.
- [ ] Temporary sensitive restored data was securely cleaned up and no real data is in evidence.

## Deliverable

A dated, sanitized **restore drill report** with restore-point identity/time, tool versions, validation results, measured RPO/RTO, deviations, and remediation actions.
