# 04 — Off-site backup architecture, encryption, and access

## Learning objectives

You can design a backup destination that survives the failures it is meant to address, explain the purpose and limits of 3-2-1, protect copies against unauthorized access and deletion, and maintain a recoverable encryption-key path.

## Separate failure and credential boundaries

A backup on the same VPS does not protect against VPS loss, disk failure, host compromise, or an operator deleting the wrong directory. A second directory or Docker volume on the same disk is not an independent copy. Send at least one recoverable copy to a separate provider, account, region, or physical location appropriate to the threat model. Prefer a destination that cannot be altered or erased using the production VPS's ordinary credentials.

The 3-2-1 heuristic means keeping three total copies of important data, including the primary copy, on two kinds of storage, with one copy off-site. It helps prompt independence, but it does not specify consistency, encryption, retention, restore testing, or access control. Three synchronized replicas can all receive accidental deletion or ransomware-encrypted files. Treat it as a design prompt, not a completion certificate.

Consider immutable/object-lock retention, versioning, delayed deletion, or a separate backup account for protection from compromise and mistakes. Understand each provider's minimum retention, legal hold, lifecycle, and early-deletion charges. Immutability can preserve bad or sensitive data too; combine it with tested recovery and an explicit retention/deletion policy.

## Encryption and key recovery

Backups often contain complete user records, tokens, password hashes, uploaded documents, or other sensitive data. Encrypt in transit and at rest. If the destination's encryption key is solely controlled by the same compromised VPS or account, an attacker with production access may be able to decrypt or delete the copies.

Client-side encryption keeps plaintext out of the storage provider's view, but shifts responsibility to the key owner. Store the recovery key or key-encryption material in a separate, access-controlled, documented location with an authorized recovery procedure. Test access using a controlled drill. If the key is lost, an intact backup can be permanently useless; if it is broadly available, backup confidentiality is weakened. Do not put a long-lived key in a container image, repository, shell history, task evidence, or the same backup set it is meant to unlock.

Use a well-maintained backup tool and follow its documented repository, key, and credential practices. Avoid inventing custom encryption pipelines without a compelling reason and tested failure handling. Decide how new keys, rotations, revocation, and old retained backups will work before changing key material.

## Least privilege and separate identities

Use a dedicated backup identity rather than broad administrator credentials. Give the VPS only the rights needed to create or append backup objects. Keep deletion, lifecycle changes, key administration, and restore access separate where practical. Restore credentials may be read-only and held by a different operator from the scheduled writer. Restrict access to the destination by account, path/prefix, network policy, and retention controls supported by the provider.

Record who can initiate, retrieve, decrypt, delete, and restore backups. Use multi-factor authentication for human accounts and document the emergency access path. Test that normal application credentials cannot erase all historical copies. Reassess access whenever a host is rebuilt, an operator leaves, or a key is rotated.

## Retention, privacy, and cost

Retain enough independent restore points to recover from delayed detection, corruption, and accidental deletion. The retention window must be longer than the plausible time between an incident and detection; legal or business requirements may impose additional periods. Longer retention increases storage cost and the amount of sensitive data retained. Apply deletion requests and retention obligations deliberately across snapshots, object versions, database logs, and replicated copies.

Estimate capacity using measured change rates and the actual tool's deduplication/compression behavior. Check that lifecycle rules do not expire a base backup before its dependent transaction logs or break an incremental chain. Periodically verify the oldest and newest expected restore points.

## Practical checkpoint

Complete [Task 03 — Protect and retrieve an encrypted off-site copy](../tasks/03-protect-and-retrieve-an-encrypted-off-site-copy.md). Prove the independent retrieval and decryption path without including secrets or real data in evidence.

## Knowledge check

1. Which failures are not addressed by a backup stored beside the production database?
2. How can ransomware affect three synchronized copies?
3. What operational risk does client-side encryption create?
4. Why should scheduled backup credentials not also have unrestricted historical deletion rights?

## References

- [CISA — StopRansomware Guide](https://www.cisa.gov/stopransomware/ransomware-guide)
- [restic documentation](https://restic.readthedocs.io/en/stable/)
- [NIST SP 800-34 Rev. 1 — Contingency Planning Guide](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final)
