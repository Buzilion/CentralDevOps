# 02 — Persistence boundaries and consistency

## Learning objectives

You can trace where application state is written, explain the difference between persistence and backup, and choose a capture point that produces a restorable, internally consistent copy.

## Trace writes end to end

Follow representative user actions and background jobs from the application process to durable storage. For each write, identify the container path, its host mount or remote service, the owning identity, and what survives container replacement, VPS reboot, host loss, and accidental deletion. Confirm the effective runtime configuration rather than relying only on a Compose file that may differ from what is deployed.

The earlier Docker subject demonstrates that a named volume can outlive a container. That is a persistence property, not a disaster-recovery property. A volume on the same VPS shares its disk, host, administrator credentials, and many failure modes with the application. A host snapshot can also be coupled to the same provider account or deletion permissions. Recovery copies must cross the failure boundary they are intended to survive.

## Consistency is more than copying bytes

A backup must represent a state the application can use. Copying files while they are changing can capture a mixture of old and new content. For a database, the raw data directory may contain pages, write-ahead logs, or engine metadata that must be captured together using the engine's supported procedure. Never copy a live database directory with a generic file-copy command and assume the result is safe.

Common consistency strategies include:

- **Database-native logical backup:** The database engine reads a transactionally consistent view and serializes selected schemas or objects. This is portable and useful for many small/medium workloads, but restore may be slower and database-specific features or roles may require separate handling.
- **Database-native physical/base backup:** Captures engine files in a documented, recoverable form. It can restore large databases faster, but is coupled to engine version, platform, and a correct transaction-log chain.
- **Filesystem or provider snapshot:** Captures a point-in-time block/file view. Consistency may be only crash-consistent unless the database is quiesced or the engine coordinates a snapshot. Verify the provider's semantics and the database's documented procedure.
- **Application quiesce or maintenance mode:** Temporarily stops or queues writes while related files and database state are captured. This can provide a simple consistent boundary but causes downtime and must handle interrupted jobs safely.
- **Application-level export:** Uses an application's supported export mechanism to include related entities and files. It may be the only correct option for complex application state, but its completeness and restore behavior must be verified.

For multiple state stores, either coordinate a shared point-in-time capture or document a procedure that brings them into a compatible state. A database-native dump at one time and an uncoordinated file archive at another time may not be mutually consistent.

## Database examples are conditional

Use the actual engine's supported backup documentation and match it to the deployed version. For PostgreSQL, `pg_dump` creates a logical backup of one database; cluster-wide roles and tablespaces may need separate treatment. A custom-format dump can be inspected and restored with `pg_restore`. Physical base backups plus WAL archiving serve a different purpose and require a complete, ordered archive and recovery configuration. For MySQL, `mysqldump --single-transaction` provides a consistent view for transactional engines such as InnoDB, but does not make every storage engine or concurrent schema change safe. These are examples, not assumptions about this application.

Pass credentials using the database's supported protected mechanism (for example, a permissions-restricted client service file or secret manager). Avoid passwords in command-line arguments, shell history, process listings, logs, or evidence.

## Proving the actual persistence boundary

Test the application's own state in a disposable environment: create a clearly identifiable record or file, recreate only the application container using the documented deployment procedure, and verify that state remains. This proves the application writes to the intended persistent service or mount. It does not prove that a backup exists, that the VPS can be replaced, or that the data can be recovered from an independent copy.

Before a destructive experiment, establish how to identify the correct project, volumes, database, and test data. Never run a volume prune or broad teardown with a production dataset merely to see what happens. Preserve the normal rollback path and keep the experiment isolated.

## Consistency acceptance

For every backed-up data class, record the capture method, consistency guarantee, time boundary, required companion data, and restore command/procedure. If a guarantee is unknown, label it unknown and do not call the artifact production-ready. A checksum detects some transfer or storage corruption; it does not prove database consistency or application correctness.

## Practical checkpoint

Use the state inventory from [Task 01](../tasks/01-inventory-state-and-define-recovery-objectives.md) to choose and demonstrate the data paths and consistency boundary in [Task 02 — Produce and validate a consistent application backup](../tasks/02-produce-and-validate-a-consistent-application-backup.md).

## Knowledge check

1. Which failure modes does a Docker named volume survive, and which does it not?
2. Why is a file-level copy of a live database directory unsafe by default?
3. What additional state might be required beside a database dump?
4. What does a successful container-recreation persistence test prove—and not prove?

## References

- [Docker documentation — Volumes](https://docs.docker.com/engine/storage/volumes/)
- [PostgreSQL documentation — Backup and Restore](https://www.postgresql.org/docs/current/backup.html)
- [PostgreSQL documentation — `pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html)
- [MySQL documentation — Backup and Recovery Methods](https://dev.mysql.com/doc/refman/8.4/en/backup-methods.html)
