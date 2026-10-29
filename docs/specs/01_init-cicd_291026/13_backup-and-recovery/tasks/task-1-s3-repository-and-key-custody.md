# Task 1: S3 repository and key custody

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Spec-level gate: specs 08, 11 and 12 checklists complete; BKP-04 interpretation accepted |
| Needs | Sumopod S3 account details and authorized Staging/Production operators |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Establish one encrypted Restic repository per Environment in the approved S3 bucket and verify key custody and provider capabilities before scheduled backups depend on it.

## Relevant files or references

- `roles/backup/`
- `docs/design/variables-and-secrets.md` §§3.2, 4.6–4.7, 7
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-03 to BKP-05)
- v5 design §13.2 and §17 items 2–3

## Proposed approach

1. Use `BACKUP_S3_ENDPOINT`, `BACKUP_S3_REGION` and `BACKUP_S3_BUCKET` from the selected GitHub Environment. Derive the repository prefix from the Environment in reviewed role code; do not accept a free-form repository path.
2. Verify Sumopod's current support for provider-side encryption, versioning and prefix-scoped access keys. Enable supported features and record unsupported features and the narrowest available credential scope. Never use account-wide administrative credentials.
3. Create a separate S3 access key and Restic repository password for each Environment. Generate a unique, high-entropy password of at least 32 characters per Environment; store the human recovery copy in the organization password manager, separate from S3 credentials and accessible to at least two authorized operators.
4. Confirm with the PRD owner that BKP-04's location separation applies to the human recovery copy. The scheduled host necessarily receives root-only operational copies of its own S3 key and Restic password; do not claim those runtime copies are physically separate.
5. Initialize and verify each repository using only its matching Environment credentials. Prove that the other Environment's Restic password cannot open it; do not use Production credentials for Staging tests.
6. Update the variables/secrets documentation with the actual provider capability results and any accepted access-scope limitation. Do not record secret values or account identifiers.

## Acceptance criteria

- Staging and Production have distinct Restic repositories, passwords and S3 credentials.
- Restic client-side encryption is enabled and wrong-password access fails.
- The S3 endpoint accepts a test snapshot and a repository check succeeds.
- Provider-side encryption, versioning and access-scope support are each recorded as enabled or unavailable based on evidence.
- The human recovery copy is available to at least two authorized operators and is not stored with S3 credential recovery material.
- The BKP-04 interpretation is accepted before the host receives operational secrets; any provider access-scope limitation is visible for Production review.

## Source reference

BKP-03 to BKP-05; parent PRD Q2; v5 §13.2 and §17 items 2–3.

## Verify

- Inspect the matching Environment configuration without printing secret contents.
- Create, check and restore a synthetic test snapshot; prove the other Environment password fails.
- Review sanitized provider evidence and password-manager access confirmation.
- Confirm no S3 secret or Restic password is committed, logged, copied to task summaries or placed in the repository/bucket as plaintext.

## Out of scope

Backup schedules, PostgreSQL exports, retention automation, database restore automation and Production go-live approval.
