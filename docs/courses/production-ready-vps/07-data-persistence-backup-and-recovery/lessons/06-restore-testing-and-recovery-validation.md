# 06 — Restore testing and recovery validation

## Learning objectives

You can restore a protected copy into a clean, isolated target, validate the recovered data and application behavior, measure actual RPO/RTO, and preserve production state while testing.

## A restore drill is the proof

A backup's usefulness is established by recovery, not by its filename, size, green dashboard, or successful upload. Restore testing discovers missing keys, permissions, roles, database extensions, compatible software, dependent files, network access, undocumented steps, and unrealistic recovery estimates. Plan the exercise as a routine operation with an owner, scope, stop conditions, and safe target.

Use a clean VPS, disposable environment, or isolated network and database—not the live production database or its volume. Keep the restored target private. Use test credentials and prevent restored email, payment, webhook, or job processing from affecting real users or external systems. Restored data may be sensitive; restrict access, avoid copying it to personal machines, and securely dispose of the test target under the organization's data policy.

## Recovery sequence

Write a recovery order based on the application's dependencies. A common sequence is:

1. Declare scope and incident time; preserve relevant production evidence and avoid changes that could overwrite the best recovery point.
2. Provision a clean compatible target and install the documented recovery tools.
3. Retrieve the selected remote restore point and its companion files/logs. Verify identity and integrity.
4. Obtain the encryption key and credentials through the separately documented recovery path. Never place secrets in the exercise record.
5. Restore configuration safely, then database and files in the order required by their consistency boundary.
6. Apply any required database recovery/replay and ensure schema and application release compatibility.
7. Keep public traffic disconnected. Validate data and application behavior using non-sensitive checks.
8. Record decisions, failures, elapsed times, and the restore point's timestamp; clean up the isolated target safely.

Actual recovery can differ for a database provider or backup tool. Use the engine's supported restore commands and preserve the original artifact until the restored result has passed checks.

## Validate useful state, not just a green process

Define checks before restoring. Verify the expected database/schema and migration version, representative record counts or stable identifiers, data relationships, and required uploaded files. Use synthetic records where possible and do not place personal data in evidence. Start the application with external side effects disabled. Check a health/readiness path, a read of expected state, and a safe application operation that demonstrates restored state can be used.

Database-level checks such as successful `pg_restore` or engine consistency checks are necessary but do not establish that the whole application is correct. Conversely, an HTTP 200 from the homepage does not prove that older user data, permissions, uploads, or relationships were recovered. Include checks at both storage and application layers.

## Measure RPO and RTO

Record the incident simulation time, last known-good point, newest recovered data point, and validation completion time. The time difference between incident and recoverable state is observed data loss; compare it to RPO. The elapsed interval from declared start to validated service is observed RTO; state what was excluded, such as waiting for a human approval or VPS provisioning.

If a drill misses an objective, record the actual figure and a corrective action—do not adjust the measured result. Repeated drills with realistic data volume reveal throughput, capacity, and operational bottlenecks.

## Common restore failures

- The backup exists but cannot be decrypted because the key is lost or inaccessible.
- The database dump omits roles, extensions, cluster settings, or external dependencies.
- Transaction-log segments or incremental bases have expired.
- The target's engine version, filesystem layout, UID/GID, or available disk space is incompatible.
- Uploads and database references represent different times.
- The application starts but uses a newer or older schema incompatibly.
- Restored background jobs send email, trigger billing, or overwrite an external source of truth.
- Recovery procedures rely on a credential or human who is unavailable during an incident.

Treat every failure as a design defect or explicit limitation to resolve, not as a reason to claim success from the parts that worked.

## Practical checkpoint

Complete [Task 05 — Restore into an isolated environment and measure recovery](../tasks/05-restore-into-an-isolated-environment-and-measure-recovery.md).

## Knowledge check

1. Why must a restore target be isolated from production and external side effects?
2. Which tests demonstrate both database integrity and application usefulness?
3. How do you calculate observed RPO and RTO during an exercise?
4. What must happen to real restored data and credentials after the drill?

## References

- [PostgreSQL documentation — Restoring a Dump](https://www.postgresql.org/docs/current/backup-dump.html#BACKUP-DUMP-RESTORE)
- [PostgreSQL documentation — Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [NIST SP 800-34 Rev. 1 — Contingency Planning Guide](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final)
