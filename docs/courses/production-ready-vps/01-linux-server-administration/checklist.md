# Linux Server Administration — Course Checklist

Complete this subject before moving to **Networking, DNS, and Firewall Security**. Work on a non-production VPS, or arrange a provider console/recovery path before changing accounts or packages. Keep evidence sanitized: do not commit IP addresses, hostnames, usernames, logs containing personal data, or credentials.

## Lessons

- [ ] [01 — Inspecting Linux and its filesystems](lessons/01-inspecting-linux-and-filesystems.md)
- [ ] [02 — Users, groups, ownership, and sudo](lessons/02-users-groups-permissions-and-sudo.md)
- [ ] [03 — Processes and systemd services](lessons/03-processes-and-systemd-services.md)
- [ ] [04 — Logs, storage, memory, and CPU](lessons/04-logs-storage-memory-and-cpu.md)
- [ ] [05 — Packages and security maintenance](lessons/05-packages-and-security-maintenance.md)
- [ ] [06 — SSH access and recovery basics](lessons/06-ssh-access-and-recovery-basics.md)

## Hands-on tasks

- [ ] [Task 01 — Create a VPS baseline inventory](tasks/01-create-a-vps-baseline-inventory.md)
- [ ] [Task 02 — Verify a least-privilege account model](tasks/02-verify-a-least-privilege-account-model.md)
- [ ] [Task 03 — Inspect and apply routine package updates](tasks/03-inspect-and-apply-routine-package-updates.md)
- [ ] [Task 04 — Diagnose a service and resource snapshot](tasks/04-diagnose-a-service-and-resource-snapshot.md)
- [ ] [Task 05 — Prove SSH access and document recovery](tasks/05-prove-ssh-access-and-document-recovery.md)

## Subject completion gate

- [ ] I can explain the purpose of `/etc`, `/var`, `/home`, `/root`, `/tmp`, and `/run`.
- [ ] I can distinguish a user, a group, a file owner, a process, and a systemd service.
- [ ] I can explain why directory permissions differ from file permissions and why `chmod 777` is not a normal fix.
- [ ] I can inspect a service and its logs without restarting a critical service blindly.
- [ ] I can distinguish full filesystem space from exhausted inodes and identify memory or CPU pressure.
- [ ] I understand that `apt update` refreshes package metadata; it does not install upgrades.
- [ ] I can verify which SSH account/key I am using and can name a recovery route that does not depend on the current SSH session.
- [ ] I have completed all five tasks and retained sanitized evidence of their acceptance criteria.

## Exit criteria

You are ready to continue when every lesson and task is checked, the exit criteria above are true, and you can explain the commands and their output in your own words. SSH/firewall hardening, Docker installation, and application deployment belong to later subjects; do not improvise those changes as part of this baseline.
