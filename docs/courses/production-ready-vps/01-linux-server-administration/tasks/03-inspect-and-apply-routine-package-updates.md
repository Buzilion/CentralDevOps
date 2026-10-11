# Task 03 — Inspect and apply routine package updates

## Outcome

Demonstrate the difference between refreshing package metadata and applying upgrades. Review proposed changes, apply only an approved routine update set, and verify the host afterward.

## Prerequisites

- Read [Lesson 05 — Packages and security maintenance](../lessons/05-packages-and-security-maintenance.md).
- Sudo access and a maintenance window.
- Provider console/recovery access.
- Confirmed backup/recovery approach suitable for the VPS workload. If the host has no important data yet, record that explicitly.

## Procedure

1. Confirm the target host and record a timestamp, release, uptime, failed services, and basic resource snapshot.
2. Refresh package metadata:

   ```sh
   sudo apt update
   ```

   Record whether repositories refreshed successfully. Stop and investigate repository, signature, or connectivity errors; do not bypass trust checks.

3. Review candidates and available changes:

   ```sh
   apt list --upgradable
   apt-cache policy PACKAGE_NAME
   ```

   Use `apt-cache policy` for packages relevant to the review. Identify held-back packages or planned removals before proceeding.

4. If this is a disposable learning VPS or the maintenance has been approved, apply routine upgrades:

   ```sh
   sudo apt upgrade
   ```

   Read the proposed actions and confirm only if they match the planned scope. Do not run a distribution release upgrade or `full-upgrade` as an unexamined substitute.

5. Record what was upgraded and any reboot recommendation. If a reboot is needed, schedule it only after verifying console access and service impact; do not reboot just to complete the exercise.
6. After the change, compare:

   ```sh
   date -Is
   uptime
   systemctl --failed
   df -hT
   free -h
   ```

   Confirm SSH remains usable and any known baseline services are in their expected state.

## Acceptance criteria

- [ ] You can explain why `apt update` alone does not upgrade installed packages.
- [ ] Repository errors were resolved rather than ignored or bypassed.
- [ ] Proposed changes/removals were reviewed before confirmation.
- [ ] A reboot decision was recorded and made deliberately.
- [ ] Post-update access, failed units, and resource state were checked.
- [ ] The evidence records the date, outcome, and any follow-up without exposing host-specific data.

## Stop conditions

Stop before applying upgrades if the host is production-critical without a change window, the repository signature is invalid, unexpected packages would be removed, recovery access is unverified, or package operations report errors you do not understand. Capture the error and seek an approved resolution; do not hide it with forced options.

## Deliverable

A sanitized maintenance record listing metadata refresh status, reviewed package changes, upgrades applied (or why none were applied), reboot decision, and post-change verification.
