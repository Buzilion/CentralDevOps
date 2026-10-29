# Task 3: Persistent data and deployment backups

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Task 1; specs 06, 11 and 12 checklists complete |
| Needs | Validated registry/Compose fixtures and a disposable Staging app |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Back up approved durable app data daily and capture each finalized deployment record and non-secret deployed configuration off-host.

## Relevant files or references

- `roles/backup/`
- Spec 06 `registry-and-compose-policy/spec.md` for approved persistent paths
- Spec 11 `deployment-records-and-run-summaries` task for the host record contract
- Spec 12 `app-deploy-request/spec.md` for immutable digest recovery
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-02, BKP-12, BKP-14)

## Proposed approach

1. Derive backup sources only from the validated registry and Compose persistent-volume contract. Back up those host mounts at least daily; never infer durable data from a container writable layer or accept an arbitrary path from app input.
2. After spec 11 finalizes each authorized host deployment record, capture that record and the matching non-secret deployed configuration in a Restic snapshot. Include failed and interrupted host attempts with their truthful result; a pre-authorization rejection that never reaches a host has no host record.
3. Include the sanitized DEP-14 fields needed to identify the last successful digest and correlate its source app run. Preserve failed attempts without replacing a prior successful digest as the recovery target.
4. Exclude runtime `.env`/`compose.env` files, decrypted request bundles, age keys, SSH keys, S3 credentials, Restic passwords and monitoring tokens. Recreate runtime configuration only through the app's matching GitHub Environment and normal authorized deploy flow.
5. Treat an upload failure as an observable backup failure without rewriting a deployment result or claiming that the record is already off-host. Retain the host record for a later successful capture.

## Acceptance criteria

- Approved persistent data is snapshotted at least daily and can be restored with its test marker intact.
- A finalized deployment record and non-secret deployed configuration appear in the off-host repository after both successful and failed host deployment attempts.
- The off-host record supports recovery of the latest successful full image digest without the lost host.
- No container writable layer is a backup source.
- Synthetic runtime-secret canaries, credentials and decrypted bundles do not appear in snapshots, logs, status files, artifacts or summaries.

## Source reference

BKP-02, BKP-12, BKP-14; DEP-14; REL-13; v5 §§9.4, 13.2 and 13.4.

## Verify

- Compare configured sources with registry/Compose fixtures and reject an unapproved path.
- Run a daily-data snapshot and restore its marker into an isolated location.
- Complete a success and failure deployment fixture; confirm both records are backed up and only the successful record supplies the recovery digest.
- Canary-scan test logs, artifacts and restored snapshots for synthetic secret values.

## Out of scope

Moving uploads to object storage (BKP-16), changing the deployment-record schema, backing up container writable layers or storing app runtime secrets as a recovery source.
