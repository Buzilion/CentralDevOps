# Task 02 — Verify a least-privilege account model

## Outcome

Document which identity you use for administration, the administrative privilege mechanism, and the intended distinction between a human administrator and application/service identities. Verify current access; do not alter SSH daemon policy in this task.

## Prerequisites

- Read [Lesson 02 — Users, groups, ownership, and sudo](../lessons/02-users-groups-permissions-and-sudo.md).
- Working authorized shell access.
- Provider-console/recovery access documented if you intend to make any account changes.

## Procedure

1. Capture the current interactive identity:

   ```sh
   whoami
   id
   groups
   sudo -l
   ```

2. If you are authorized to inspect another known account, query it without reading credential files:

   ```sh
   id ACCOUNT
   getent passwd ACCOUNT
   ```

   Do not dump `/etc/shadow` or copy password hashes.

3. Inspect ownership/mode on a few paths already relevant to the host:

   ```sh
   ls -ld /etc /var /home /root
   stat -c '%A %a %U:%G %n' /etc/os-release
   ```

4. In a private note, classify each relevant identity as human administrator, deployment identity (if already provisioned), service identity, or unknown. Record purpose, group memberships, sudo scope, and evidence. Do not infer purpose from a username alone.
5. State which identity should administer the VPS and what a future deployment identity should be allowed to do. If no deployment account exists yet, record it as a design decision for a later deployment subject—not as a reason to create a privileged account now.
6. If you have explicit authorization and need to create an administrator as part of the initial setup, first verify provider console access. Follow the provider/Ubuntu-supported account and authorized-key procedure. Keep the existing access open, test the new login and required sudo access in a separate session, and stop if verification fails. Do not disable existing access or change SSH policy in this task.

## Acceptance criteria

- [x] The current account and group memberships are known.
- [ ] The scope of `sudo` access is recorded, or the lack of access is documented.
- [ ] Human administration is distinguished from application/service runtime identity.
- [ ] No shared password, key material, hash, or sensitive account database content is in the evidence.
- [ ] If an account was created, it was verified in a separate session before any old access was changed.
- [ ] The proposed deployment identity has only the permissions its future deployment design will require.

## Safety and rollback

This task can be completed read-only. Prefer that path on an existing server. Account and key changes can lock you out; make no access-removal change without an independent recovery route and verified replacement session. If a new account is misconfigured, keep the known-good session open and use it or the provider console to correct the issue.

## Deliverable

A short account/privilege matrix and verification note stored privately. Do not commit real usernames or host details to a public repository.
