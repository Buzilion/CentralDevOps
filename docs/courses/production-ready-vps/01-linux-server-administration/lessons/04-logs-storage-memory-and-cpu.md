# 04 — Logs, storage, memory, and CPU

## Learning objectives

You can make a first-pass resource assessment, distinguish common capacity symptoms, query host logs with useful time bounds, and collect evidence without disclosing sensitive data.

## Begin with a timestamped snapshot

```sh
date -Is
uptime
free -h
df -hT
df -i
lsblk -f
```

Capture this snapshot before making a change. It provides a baseline for later comparison. A single reading is not a trend: resource use varies with workload, and a quiet VPS can look healthy just before a scheduled task runs.

## CPU and load

`uptime` reports uptime and load averages over 1, 5, and 15 minutes. Load average is not CPU percentage; it counts runnable work and certain uninterruptible waits. Interpret it with vCPU count and workload. High load together with saturated CPU can mean CPU contention; high load without saturated CPU can point to I/O waits or other bottlenecks.

Use `top` for a live view and `ps` for a snapshot. Look for sustained patterns, not one transient spike. Do not terminate a process just because it is using CPU: identify its owner, role, and expected behavior first.

## Memory and swap

```sh
free -h
```

Linux uses otherwise idle RAM for caches, which can be reclaimed. The `available` column is generally more informative for rough capacity than treating all `used` memory as unrecoverable. Swap use is a signal to investigate alongside memory pressure and workload; it is not automatically an emergency, nor should high swap activity be ignored.

If memory pressure is suspected, inspect processes and relevant kernel/journal messages. An out-of-memory kill may leave a service down or restarting. Avoid memory stress tests on a production host.

## Filesystem blocks and inodes

```sh
df -hT
df -i
du -xhd1 /var 2>/dev/null | sort -h
```

- `df -hT` reports used and available data blocks by mounted filesystem.
- `df -i` reports inode use; a filesystem can run out of inodes while byte capacity remains.
- `du` estimates directory usage. `-x` stays on the same filesystem and avoids traversing other mounts; the example is read-only but may take time.

Do not run an unrestricted full-disk `du` repeatedly on a busy VPS. First identify the full mount in `df`, then inspect a bounded directory on that mount. Common growth areas include logs, package caches, temporary files, container data, and application data. Determine ownership and retention policy before deleting anything.

Never delete unfamiliar files in `/var/lib`, database directories, Docker storage, or logs to quickly free space. Deleting an open log file may not free disk blocks until the process closes it. Use the service's supported rotation/cleanup procedure after confirming the cause.

## Logs as evidence

```sh
journalctl -p warning..alert --since '1 hour ago' --no-pager
journalctl -k -b --no-pager
systemctl --failed
```

Make log queries time-bounded and relevant. Correlate timestamps with user reports and service changes. Logs can contain usernames, IP addresses, request data, or secrets. Share only the minimal redacted excerpt necessary, and store operational evidence privately.

Check available journal space and persistence when designing operations:

```sh
journalctl --disk-usage
```

Retention depends on configuration and available storage. Logs are not backups and should not be the only record of critical application data.

## A useful diagnosis pattern

1. State the symptom and when it began.
2. Capture `date -Is`, `uptime`, `free -h`, `df -hT`, and `df -i`.
3. Identify the affected service and inspect `systemctl status` and time-bounded logs.
4. Compare the evidence against a known-good baseline or previous observation.
5. Form one testable hypothesis; choose a low-risk, reversible check.
6. Record the result before making any remedial change.

This keeps troubleshooting evidence-led and prevents a well-intentioned cleanup from destroying data needed for diagnosis.

## Knowledge check

1. How can a filesystem be full even when `df -h` shows free bytes?
2. Why is high `used` memory not necessarily equivalent to low available memory?
3. What does `du -x` help prevent when investigating a directory?
4. Why should log queries be time-bounded and redacted?
5. Why is one CPU/load snapshot not sufficient to identify a capacity trend?

## Practical checkpoint

Complete [Task 04 — Diagnose a service and resource snapshot](../tasks/04-diagnose-a-service-and-resource-snapshot.md).
