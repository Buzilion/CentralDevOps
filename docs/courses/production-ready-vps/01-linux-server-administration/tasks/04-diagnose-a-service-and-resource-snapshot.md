# Task 04 — Diagnose a service and resource snapshot

## Outcome

Produce an evidence-based health note for one low-risk, existing systemd service and the host's current CPU/load, memory, storage, inode, and log state—without inducing an outage.

## Prerequisites

- Read [Lesson 03 — Processes and systemd services](../lessons/03-processes-and-systemd-services.md) and [Lesson 04 — Logs, storage, memory, and CPU](../lessons/04-logs-storage-memory-and-cpu.md).
- Authorized shell and sudo access if required.

## Procedure

1. Choose a low-risk unit already present on the VPS (for example, a time synchronization service if installed). Do **not** use SSH, a database, or the production application as a restart exercise.
2. Record a timestamp and inspect current unit state:

   ```sh
   systemctl status UNIT_NAME --no-pager
   systemctl show UNIT_NAME -p ActiveState -p SubState -p MainPID -p User
   ```

3. Inspect a bounded amount of relevant log data:

   ```sh
   journalctl -u UNIT_NAME --since '1 hour ago' -n 100 --no-pager
   ```

   If access is denied or the unit has no journal entries, record that fact; do not dump unrelated system logs.

4. Capture a resource snapshot:

   ```sh
   uptime
   free -h
   df -hT
   df -i
   ps -eo pid,ppid,user,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head
   ```

5. Write a short diagnosis with **observations**, **interpretation**, and **unknowns** separated. For example, “`/` has 30% available” is an observation; “disk is not currently at capacity” is a limited interpretation; “growth rate is unknown from one snapshot” is an unknown.
6. If the service is failed or the host shows pressure, do not restart, kill, or delete files. Note a next safe diagnostic step and the evidence that would justify it.

## Acceptance criteria

- [ ] The selected service was inspected without changing its state.
- [ ] Status and time-bounded logs are recorded or their absence/permission limitation is explained.
- [ ] CPU/load, memory, filesystem blocks, and inodes are covered.
- [ ] Observations are distinguished from interpretation and unknowns.
- [ ] No unredacted process arguments, secrets, or unrelated logs are included.
- [ ] No service restart, process kill, or data deletion was performed.

## Deliverable

A sanitized one-page service/resource health note with timestamp, commands, findings, limitations, and the next evidence-led diagnostic step.
