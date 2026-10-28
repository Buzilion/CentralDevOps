# 05 — Scheduling, retention, and backup verification

## Learning objectives

You can turn a tested backup procedure into a scheduled job with explicit failure behavior, select retention that supports the recovery objectives, verify both local and remote copies, and determine when an operational signal is a warning rather than proof of recoverability.

## Derive the schedule from RPO

Choose backup frequency from the approved RPO and the real maximum gap between **successful, usable restore points**. A job scheduled hourly does not meet an hourly RPO if it routinely runs for three hours, fails silently, or uploads only after the data is already too old. Include backup duration, transfer delay, remote confirmation, and detection delay in the design. If a required RPO cannot be met by a periodic full backup, evaluate incrementals or database-native transaction-log archiving and account for their added recovery dependencies.

Measure duration, source size, remote size, and success time across representative runs. Check capacity against growth and retention. Avoid overlapping runs unless the backup tool and database procedure explicitly support it; overlapping jobs can create load, inconsistent snapshots, or confusing cleanup.

## Make the job observable and fail honestly

Run the procedure under a dedicated, least-privileged identity with a controlled environment and explicit working directory. Protect temporary directories and credentials. Use absolute paths where appropriate; never depend on an interactive shell's profile or an administrator's unlocked session.

The job should expose each stage—capture, local validation, encryption, transfer, remote verification, and retention—so an operator can find where it failed. A non-zero exit status, useful service log, and a last-success timestamp are basic requirements. Preserve sufficient logs to diagnose failures without printing secrets, backup contents, or user data. Schedule output and errors to a location that remains available when the network destination is down.

A systemd service and timer are one Linux option; cron, a managed-backup service, or a provider's scheduler may also be appropriate. Verify the actual deployed scheduler, service identity, timezone, enabled state, previous execution result, and next run. An enabled timer is not evidence that its job succeeds. Invoke the exact service in a controlled test and inspect its result rather than testing only the command in an administrator shell.

Monitoring and alert delivery are covered in the next course subject. For this subject, define the signal and its owner now: for example, an alert or review trigger when the most recent independently verified restore point is older than the maximum permitted RPO, when destination capacity is low, or when a job exits unsuccessfully. A backup that fails without reaching anyone is not an operational control.

## Retention must preserve recoverable chains

Define retention from business, privacy, regulatory, detection, and recovery needs. A simple daily/weekly/monthly rotation may be a useful starting shape, not a universal policy. Keep enough history to recover from corruption discovered after several days; retain point-in-time logs for the intended replay period. For incremental or deduplicated systems, confirm that expiration preserves all bases, indexes, metadata, and objects needed by retained restore points.

Test cleanup against a disposable repository or a dry-run mode first. Protect minimum recovery points and avoid a retention run that deletes the only known-good copy before a replacement is verified. Confirm lifecycle rules in the destination account as well as local cleanup jobs; two independent cleanup layers can expire the chain earlier than intended.

## Verification levels

Evidence has increasing strength:

1. Scheduler is active and the job exited successfully.
2. A new artifact or remote snapshot has expected identity, timestamp, and plausible size.
3. The encrypted repository/object can be listed and integrity-checked by the expected backup tool.
4. Data can be retrieved and decrypted using the documented recovery identity and key path.
5. The artifact restores in isolation and the application validates.

Levels 1–4 are valuable, but only the last proves the end-to-end recovery path for the tested sample. Define how often to reach that level based on RTO, data change, and risk. Capture tool versions and restore prerequisites so an artifact does not depend on software that has disappeared.

## Practical checkpoint

Automate the already proven method—not an untested script—in [Task 04 — Automate backup scheduling, retention, and failure visibility](../tasks/04-automate-backup-scheduling-retention-and-failure-visibility.md).

## Knowledge check

1. Why does a successful scheduler exit not prove an application can be recovered?
2. What must be checked before enabling a retention rule for incremental backups?
3. Why should the job's last-success age be compared with RPO?
4. Which backup stage should remain observable if off-site storage is unreachable?

## References

- [systemd.timer documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [restic documentation — Forget and Prune](https://restic.readthedocs.io/en/stable/060_forget.html)
