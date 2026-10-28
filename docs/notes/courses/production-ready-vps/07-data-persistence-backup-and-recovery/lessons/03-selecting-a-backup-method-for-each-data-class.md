# 03 — Selecting a backup method for each data class

## Learning objectives

You can select a practical backup and restore method for each inventoried data class, identify method limitations, and verify that the exact artifact is readable before relying on it.

## Match method to data and recovery goal

There is no universal backup command. Choose a method based on the source-of-truth owner, change rate, size, consistency requirement, retention period, portability, expected restore time, and operator skill. A design is incomplete until it names a restore path and has tested that path.

| Data or system | Candidate method | Important caveat |
|---|---|---|
| Small/medium SQL database | Engine-native logical export | Validate roles, extensions, encodings, ownership, and restore duration; some cluster-wide objects are outside a single-database dump. |
| Large or point-in-time database recovery | Engine-supported base backup plus transaction-log archive | Requires compatible software, a complete log chain, capacity, retention planning, and replay drills. |
| User-uploaded files | Versioned/encrypted object copy or filesystem-aware archive | Preserve required names, metadata, permissions, and a consistent relationship with database references. |
| Configuration | Version-controlled declarative files plus a separate protected secret recovery path | Publicly storing secrets or relying on a lost VPS `.env` file defeats recovery and confidentiality. |
| Managed database/object store | Provider-native backup/export plus independent recovery plan | Confirm account-level deletion protection, region/failure boundaries, retention, exportability, and restore time. |
| Rebuildable images/cache | Rebuild from pinned source/artifacts where feasible | Verify the artifact and toolchain are still obtainable; do not back up disposable cache by default. |

Logical exports are often straightforward to inspect and move between compatible systems, but can be slow to restore at scale. Physical backups can restore larger datasets more quickly but are less portable and demand engine-specific care. Snapshots can be fast but may preserve corruption or deletion, and are not necessarily application-consistent. Use layered methods only when each layer has a clear recovery purpose.

## Example: PostgreSQL logical backup

For a PostgreSQL deployment where a logical database backup meets the size and recovery objectives, an illustrative command is:

```sh
pg_dump --format=custom --file=/secure/staging/appdb.dump --dbname=appdb
```

Use a protected PostgreSQL service definition or another approved credential mechanism rather than placing a password in the command. Check the command's exit status, expected artifact existence and size, then run the matching restore tool against a new, empty test database. A valid-looking file is not proof that it can be read or restored. Include global roles or other cluster objects separately when the application needs them. Confirm that the dump format and client/server versions are compatible with the planned restore target.

For point-in-time recovery, follow the database version's documentation for base backups and WAL archiving; a logical dump does not automatically provide point-in-time replay. Retain a tested base backup and every required log segment for the target recovery interval.

## Example: file and upload backup

First determine whether files can change during capture and whether the app stores checksums, metadata, ownership, or paths in the database. Prefer a documented application export, object-store versioning, or a snapshot/quiesce procedure that gives a consistent set. If using an archive, test listing and extracting it as the intended restore identity and compare representative file metadata. Avoid archiving temporary uploads or caches unless their recovery value is established.

## Split the process into observable stages

A dependable job distinguishes:

1. **Capture** — use the supported database/application/filesystem method.
2. **Local validation** — verify exit status, artifact presence, plausible size, and format-specific readability.
3. **Protection** — encrypt before or during transfer with a supported tool and restricted identities.
4. **Transfer** — send to a different failure and access boundary.
5. **Remote verification** — confirm expected object identity/size/checksum or repository status and retention.
6. **Restore sampling** — regularly retrieve, decrypt, and restore in isolation.

Keep failures visible. A script that logs an error and exits successfully, uploads an empty file, overwrites the only prior good backup, or reports success before remote verification creates false confidence. Preserve at least one known-good restore point while generating and checking its replacement.

## Capacity and restore performance

Estimate full and incremental backup size, database growth, file growth, transfer bandwidth, compression/encryption overhead, and retained versions. Compression helps some data and hurts or offers little value on data already compressed. Deduplication can reduce stored bytes while increasing dependency on repository metadata and correct tooling. Measure a representative restore at expected scale; do not extrapolate from a tiny test database.

## Practical checkpoint

Complete [Task 02 — Produce and validate a consistent application backup](../tasks/02-produce-and-validate-a-consistent-application-backup.md). The artifact must be a real candidate for restore, not only a screenshot of a successful command.

## Knowledge check

1. What does a single-database `pg_dump` not necessarily cover?
2. Why should restore speed influence backup-method choice?
3. Why must the previous known-good backup remain available until its replacement is verified?
4. What evidence demonstrates that an artifact is readable, and what stronger evidence demonstrates that it is useful?

## References

- [PostgreSQL — `pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html)
- [PostgreSQL — Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [MySQL — Backup and Recovery](https://dev.mysql.com/doc/refman/8.4/en/backup-and-recovery.html)
