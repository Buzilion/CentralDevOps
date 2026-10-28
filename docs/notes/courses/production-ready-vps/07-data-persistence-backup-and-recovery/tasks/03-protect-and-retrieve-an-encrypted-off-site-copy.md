# Task 03 — Protect and retrieve an encrypted off-site copy

## Outcome

Store an encrypted, retrievable copy outside the VPS's failure and normal credential boundary, and demonstrate that an authorized recovery path can retrieve and decrypt it.

## Prerequisites

- Complete [Task 02 — Produce and validate a consistent application backup](02-produce-and-validate-a-consistent-application-backup.md).
- Read [Lesson 04 — Off-site backup architecture, encryption, and access](../lessons/04-off-site-backup-architecture-encryption-and-access.md).
- Have authorization to use a separate backup destination/account and establish its retention, privacy, and cost settings.

## Procedure

1. Choose a destination outside the VPS disk and its ordinary administrator credentials. Document which failures it protects against and which correlated risks remain.
2. Create a dedicated backup identity scoped to the smallest practical destination path and write operations. Separate routine upload rights from historical deletion, lifecycle changes, key administration, and restore access where feasible.
3. Select a supported encryption approach. If client-side encryption is used, store the recovery key separately under approved access control. Write down the authorized key-recovery procedure without writing the key itself.
4. Transfer the validated backup using the intended production identity and mechanism. Protect transfer in transit; enforce destination-side encryption/access/retention controls as applicable.
5. From a clean or separate recovery client, authenticate with the documented restore identity, locate the expected object/repository snapshot, retrieve it, and run the supported integrity/list operation.
6. Prove that the authorized recovery process can decrypt/read the retrieved copy without using the production VPS's local cache or credentials. Use a disposable copy and restricted target path.
7. Verify that routine production credentials cannot erase every historical recovery point. Test permission boundaries with a safe read/permission check, not a destructive delete.
8. Record destination class, identity/permission summary, encryption/key recovery method, retention configuration, object identity, integrity result, and retrieval duration. Do not include secret/key values or real data.

## Acceptance criteria

- [ ] At least one validated recovery copy resides outside the VPS disk and ordinary host access boundary.
- [ ] The copy is encrypted in transit and at rest; encryption ownership and key recovery are documented.
- [ ] Routine upload credentials have no unnecessary broad read/delete/admin permissions.
- [ ] An independent authorized client retrieves and reads/decrypts the expected copy.
- [ ] The remote copy is verified by its native tool or appropriate integrity metadata.
- [ ] The destination and retention survive the stated host-loss scenario; remaining common-mode risks are written down.
- [ ] Evidence contains no keys, credentials, or backup contents.

## Deliverable

A sanitized **off-site recovery access record** describing the destination boundary, restricted identities, retention/encryption controls, recovery-key path, retrieval test, and open risks.
