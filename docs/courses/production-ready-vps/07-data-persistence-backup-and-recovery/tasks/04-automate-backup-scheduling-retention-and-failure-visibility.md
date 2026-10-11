# Task 04 — Automate backup scheduling, retention, and failure visibility

## Outcome

Run the tested backup process on a schedule aligned with the approved RPO, retain enough usable history, and make failed or overdue backups discoverable by an operator.

## Prerequisites

- Complete [Task 03 — Protect and retrieve an encrypted off-site copy](03-protect-and-retrieve-an-encrypted-off-site-copy.md).
- Read [Lesson 05 — Scheduling, retention, and backup verification](../lessons/05-scheduling-retention-and-backup-verification.md).
- Have a validated backup procedure, least-privileged identity, protected credentials, remote destination, and approved retention requirements.

## Procedure

1. Select the VPS/provider scheduler appropriate to the actual backup method (for example, a systemd service/timer, managed provider job, or existing supported scheduler). Use a dedicated service identity and explicit paths/environment; do not depend on an interactive root shell.
2. Set the schedule from the maximum tolerable gap between successful usable restore points. Include capture and remote-transfer duration. If the objective needs transaction-log archiving or a different method, do not pretend a less frequent job meets it.
3. Ensure capture, artifact validation, encryption, remote transfer, and remote verification all contribute to the job's final success/failure result. A failed stage must not report success or delete the only known-good point.
4. Configure retention from RPO, detection delay, data-change history, privacy requirements, and storage capacity. Confirm that cleanup cannot remove required base backups, incremental dependencies, or transaction logs.
5. Review the cleanup tool's preview/dry-run against a test repository. Confirm the minimum retained points and that an unverified replacement does not displace the previous known-good point.
6. Run the configured scheduled unit/job through its normal invocation path. Inspect identity, enabled/next-run state, exit result, logs, remote object, and last successful verified restore-point age.
7. In a disposable configuration or staging destination, create a controlled failure (such as denying the test destination) and prove the job exits unsuccessfully and produces the expected operator-visible signal. Do not disable or damage the production backup path to simulate failure.
8. Define the threshold and owner for an overdue backup or failed job. The next monitoring subject can implement alert delivery; until then, document the current review mechanism and its limitations.
9. Record schedule, service identity, retention rule, capacity estimate, failure test, last-success interpretation, and how to safely pause or repair the job.

## Acceptance criteria

- [ ] The active job uses the intended least-privileged identity and explicit, protected configuration.
- [ ] The actual schedule can meet the approved RPO based on successful verified restore points, not just timer frequency.
- [ ] Every required stage propagates failure; incomplete or empty artifacts do not replace a known-good copy.
- [ ] Retention rules preserve a tested recovery chain and comply with required retention/deletion policy.
- [ ] Normal execution is proven through the installed scheduler and a remote artifact check.
- [ ] A safe failure simulation produces a non-success result and visible, actionable evidence.
- [ ] Job logs and records do not expose credentials, keys, or user data.

## Deliverable

A sanitized **backup operations record** containing the scheduler/unit, cadence, RPO comparison, retention and capacity notes, normal/failure execution evidence, and current overdue/failure owner.
