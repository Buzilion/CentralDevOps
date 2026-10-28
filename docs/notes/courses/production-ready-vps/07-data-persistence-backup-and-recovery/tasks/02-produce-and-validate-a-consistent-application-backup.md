# Task 02 — Produce and validate a consistent application backup

## Outcome

Create a protected candidate backup for each important data class using a documented consistency method, then prove the artifacts are readable without disturbing production.

## Prerequisites

- Complete [Task 01 — Inventory state and define measurable recovery objectives](01-inventory-state-and-define-recovery-objectives.md).
- Read [Lesson 02 — Persistence boundaries and consistency](../lessons/02-persistence-boundaries-and-consistency.md) and [Lesson 03 — Selecting a backup method for each data class](../lessons/03-selecting-a-backup-method-for-each-data-class.md).
- Use a disposable/staging dataset or an approved low-risk backup window. Do not use a destructive test on live state.

## Procedure

1. Select a test target that represents the actual application storage layout. Confirm free space, access controls, owner, and an isolated staging directory with permissions appropriate for the data.
2. Follow the engine/application's version-specific backup procedure. For a database, use its supported logical export, physical backup, provider snapshot, or coordinated quiesce method as selected in the inventory. Do not copy a live database data directory as a generic file backup.
3. Capture each coupled data class at a compatible boundary. If uploads and database references cannot be captured atomically, document and use the planned quiesce/snapshot/application-export procedure.
4. Use protected credentials. Do not put passwords, tokens, encryption keys, or connection strings in command-line arguments, shell history, environment dumps, logs, or evidence.
5. Check the capture process exit status. Verify expected artifact identity, time, plausible nonzero size, permissions, format, and any engine/tool integrity check. Preserve the previous known-good artifact until the replacement passes validation.
6. Use the native listing or inspection tool to read the artifact. In an isolated test target, restore a small representative backup or database dump to a new empty location and confirm the engine accepts it. Do not restore over an existing database.
7. Record tool/engine versions, capture time boundary, consistency method, validation results, duration, and any exclusions. Redact real row contents, credentials, and identifying infrastructure details.
8. Before removing temporary plaintext artifacts, confirm that a validated backup remains in the approved protected location; do not treat the staging files as the only recovery copy. Securely remove the temporary files according to the data-handling policy.

## Acceptance criteria

- [ ] Every required durable data class has a captured artifact or a documented provider-native equivalent.
- [ ] The capture method matches the data consistency requirement; unsupported live file copying is not used.
- [ ] Commands report failure honestly, and the expected artifact is nonempty, correctly permissioned, and readable by its recovery tool.
- [ ] At least one isolated native restore/read test succeeds without writing to production.
- [ ] Database and companion files are tied to a documented time boundary or coordinated capture.
- [ ] The prior known-good copy was not deleted before the new copy was validated.
- [ ] Evidence excludes secrets and real application data.

## Deliverable

A sanitized **backup method and artifact validation record** with data-class coverage, capture timestamp, consistency boundary, tool versions, integrity/read test, size/duration, and remaining restore limitations.
