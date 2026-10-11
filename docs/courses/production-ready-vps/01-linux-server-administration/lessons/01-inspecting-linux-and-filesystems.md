# 01 — Inspecting Linux and its filesystems

## Learning objectives

After this lesson, you can establish what operating system and kernel a VPS is running, navigate the filesystem safely, identify mounted filesystems, and explain how the filesystem layout affects operations.

## The mental model

Linux presents processes with a unified directory tree rooted at `/`. A path such as `/var/log/syslog` names a location in that tree; it does not imply that the data lives on one physical disk. Filesystems can be mounted at directories, so `/`, `/boot`, or `/var` may be backed by different devices or storage layers. Containers add namespaces and mounts, but their host still has this underlying model.

The kernel manages hardware, processes, memory, devices, and filesystems. A distribution combines the kernel with user-space tools, package management, defaults, and support policy. Knowing the actual distribution and release is more reliable than assuming from a VPS provider's product label.

## Inspect before changing anything

Run these read-only checks as the initial login user:

```sh
hostnamectl
cat /etc/os-release
uname -a
id
pwd
```

`/etc/os-release` identifies the distribution and release; `uname` identifies the running kernel. `id` shows the effective user and groups. Record the release, architecture, kernel, and login account in a private lab record, not in a public issue or Git commit.

If a command is missing, first confirm the OS and consult its manual or package documentation. Do not paste an unreviewed remote installation script into a root shell to obtain a convenience tool.

## A useful filesystem map

| Path | Typical purpose | Operational note |
|---|---|---|
| `/` | Root of the directory tree | Check its mount and available space. |
| `/etc` | Host-wide configuration | Changes can alter service behavior; preserve permissions and review diffs. |
| `/home` | Human users' home directories | Not necessarily suitable for service-owned application data. |
| `/root` | Root user's home directory | Private administrative area; ordinary users should not need access. |
| `/var` | Variable state such as logs, caches, spool, and databases | Can grow independently and fill a disk. |
| `/var/log` | System and service logs | Logs help diagnosis but need retention and privacy controls. |
| `/usr` | Installed programs and shared read-only software data | Usually managed by the package manager; do not hand-edit package files. |
| `/tmp` | Temporary files | May be cleaned automatically and may be memory-backed. Never treat it as durable storage. |
| `/run` | Volatile runtime state, often recreated at boot | PID files and sockets here are not persistent application data. |
| `/dev` | Device nodes exposed to the system | Not ordinary disk files. |
| `/proc`, `/sys` | Kernel and process information interfaces | Virtual filesystems; values are observations or controls, not persistent files. |

This is a convention, not a guarantee that each path has its own disk or that every distribution lays out every optional directory identically. Use mount inspection to learn what this particular server does.

## Navigate and inspect safely

```sh
pwd
ls -la /
ls -ld /etc /var /home /root
stat /etc/os-release
findmnt /
findmnt --target /var
lsblk -f
df -hT
```

- `ls -ld` reports the directory itself, rather than listing its contents.
- `stat` reports metadata such as owner, mode, size, and modification time.
- `findmnt` shows mount points and their sources/options.
- `lsblk -f` relates block devices to filesystem types and labels.
- `df -hT` reports filesystem capacity in human-readable units and filesystem type.

Use `namei -l /path/to/file` to inspect permissions on each path component when a file is inaccessible. A user needs execute/search permission on every directory in a path, not just permission on the final file.

Avoid recursive ownership or permission commands until you know exactly what path they will affect. A typo in `chown -R` or `rm -rf`, especially when running as root, can damage the whole host. Prefer read-only inspection and narrowly scoped changes.

## Mounts, capacity, and persistence

A VPS may expose a virtual disk, partitions, LVM, encrypted storage, or provider-managed volumes. `lsblk`, `findmnt`, and `df` answer different questions: device topology, current mount relationships, and space available to filesystems. No single command is a complete storage map.

Application data must live on storage whose lifecycle and backup policy are understood. Temporary directories, container writable layers, and `/run` are not a substitute for persistent storage. Later course subjects cover application volumes and backups; for now, learn where the host's filesystems are and which one is approaching capacity.

## Common misreadings

- A large virtual disk does not mean `/` has that much usable space; inspect the mounted filesystem and its allocation.
- `df` showing free space does not rule out inode exhaustion; compare with `df -i` (covered in the resource lesson).
- A file's owner and mode do not reveal every access rule if ACLs are in use. `getfacl` can show ACLs when the tool is installed.
- Paths under `/proc` and `/sys` are not durable config files.
- A VPS snapshot may help with rollback but is not automatically an independent, tested backup.

## Knowledge check

1. Why can `/var` fill even when `/home` has free space?
2. Which command shows mount relationships, and which shows available filesystem capacity?
3. Why should `/tmp` not be used for important application data?
4. What does `namei -l` help diagnose?

## Practical checkpoint

Complete [Task 01 — Create a VPS baseline inventory](../tasks/01-create-a-vps-baseline-inventory.md). Explain each recorded field and redact identifying information from any evidence you share.
