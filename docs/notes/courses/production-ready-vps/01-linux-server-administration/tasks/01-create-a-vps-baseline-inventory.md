# Task 01 — Create a VPS baseline inventory

## Outcome

Produce a dated, sanitized inventory that identifies the VPS operating-system baseline, current identity, storage layout, and initial resource state. You will use it to compare future changes and to avoid administering the wrong host.

## Prerequisites

- Authorized shell access to the intended VPS.
- A private place to store lab notes.
- Read [Lesson 01 — Inspecting Linux and its filesystems](../lessons/01-inspecting-linux-and-filesystems.md) and [Lesson 04 — Logs, storage, memory, and CPU](../lessons/04-logs-storage-memory-and-cpu.md).

## Procedure

1. Connect using the access path provided by your VPS administrator/provider. Do not change SSH daemon or firewall settings for this task.
2. Verify you are on the intended host:

   ```sh
   hostname
   whoami
   id
   date -Is
   ```

3. Record release, kernel, and architecture:

   ```sh
   cat /etc/os-release
   uname -r
   uname -m
   ```

4. Record filesystems and mounts:

   ```sh
   findmnt
   lsblk -f
   df -hT
   df -i
   ```

5. Record the initial health snapshot:

   ```sh
   uptime
   free -h
   systemctl --failed
   ```

6. In a private lab note, capture the date/time, OS release, kernel, architecture, login identity/groups, mount points with available space, inode use, memory/swap, load average, and failed-unit count. Note commands that were unavailable or permission-denied.
7. Sanitize a copy before sharing: remove public IPs, provider identifiers, hostnames, usernames if identifying, serials/UUIDs, and any unrelated process or log data.

## Acceptance criteria

- [ ] The inventory names the correct OS release and running kernel.
- [ ] It distinguishes mounted filesystem capacity from physical/virtual block devices.
- [ ] It records inode use as well as byte capacity.
- [ ] It identifies the account and groups used for the session.
- [ ] It has a timestamp and is stored somewhere private.
- [ ] You can explain each field and point out at least one caveat of a one-time snapshot.

## Troubleshooting and safety

- If `lsblk` or `findmnt` is missing, note it; do not install utilities solely to complete an inventory.
- If `sudo` is unavailable, record the limitation rather than switching to root through an undocumented route.
- Do not include `/etc/shadow`, private keys, environment files, or full process arguments in the inventory.
- Do not make changes based on this initial snapshot; first establish what the output means.

## Deliverable

A sanitized, dated baseline note retained privately. Keep raw command output only if needed and protect it as operational information.
