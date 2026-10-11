# 02 — Users, groups, ownership, and sudo

## Learning objectives

You can explain Linux identities and permission checks, use a normal administrative account instead of a persistent root shell, and reason about a future deployment identity without granting it unnecessary authority.

## Identities and privilege

Linux processes run with user and group identities. A process's effective identity controls many access checks. `root` (UID 0) can bypass most ordinary filesystem permission checks and administer the host; it is not a convenient default account for daily work.

Use a named administrator account for interactive administration and elevate individual commands with `sudo`. This reduces accidental damage, makes actions attributable, and supports policy such as requiring explicit elevation. `sudo` permission is still powerful administrative access; it is not a sandbox.

Inspect the current identity and privileges:

```sh
whoami
id
groups
sudo -l
```

`sudo -l` reports what the current account may run through sudo. If it requests a password, that is normally the invoking user's password, not a separate root password. Do not share passwords, private keys, or unredacted command histories.

## Users and groups

User and group records are commonly represented through `/etc/passwd`, `/etc/shadow`, and `/etc/group`, but use system tools rather than editing those files directly. Password hashes and account state belong in protected files; never copy their contents into a report.

Create or modify identities only after defining their purpose:

- **Administrator:** human-operated account with narrowly necessary sudo capability.
- **Deployment identity:** used by a deployment process or automation; normally not a general-purpose human login or unrestricted root account.
- **Service identity:** runs one service with access only to its own required files and resources.

These identities may be separate. Do not assume a dedicated deployment user is needed before understanding the delivery design. Never reuse the root account or a shared human account as an application service identity.

Commands such as `getent passwd USER`, `getent group GROUP`, `id USER`, and `groups USER` inspect account and group membership. `getent` uses configured system name services rather than assuming that every account is a literal line in one local file.

## How Unix mode bits work

For each file or directory, mode bits define read (`r`), write (`w`), and execute (`x`) access for the owner, owning group, and everyone else. For a regular file, execute means the file may be run (subject to other controls). For a directory, read lists names, execute/search permits traversal and lookup, and write permits changing directory entries when combined with the required search permission.

```sh
ls -l /path/to/file
stat -c '%A %a %U:%G %n' /path/to/file
```

An illustrative mode such as `640` means owner read/write, group read, and no access for others. `750` on a directory means owner full access, group read/search, and no access for others. Choose modes based on the intended principals, not by memorizing a single production number.

Use narrow changes:

```sh
chmod 640 /path/to/config
chown appuser:appgroup /path/to/data
```

Do not use `chmod 777` as a shortcut: it grants write access to every local user and can convert a minor mistake or compromised account into a larger compromise. Do not recursively change ownership of system or application trees unless you have verified the exact target and intended ownership.

### Special bits and ACLs

Set-user-ID/set-group-ID bits can cause a program to execute with a file's owner/group identity; set-group-ID on a directory can make new entries inherit its group. The sticky bit on a shared directory (commonly `/tmp`) restricts who can remove or rename entries. These behaviors are security-sensitive; avoid changing special bits without a specific, reviewed need.

Access Control Lists can add per-user or per-group rules beyond the three mode classes. If access seems inconsistent with `ls -l`, inspect with `getfacl PATH` if available. Do not install tools or change ACLs as an exploratory fix on a live host.

## `sudo` as a controlled boundary

Elevate only the command that needs it:

```sh
sudo systemctl status ssh
sudo apt update
```

Before running an elevated command, read its target and scope. `sudo` does not make a dangerous command safe, and shell redirection has its own privilege behavior (for example, `sudo command > /root/file` may still perform the redirect as the unprivileged shell).

Avoid persistent root shells for routine work. If one is necessary for a carefully controlled maintenance procedure, know how you entered it and exit it as soon as the procedure ends.

## A safe account-change sequence

When preparing an additional administrator, first confirm an alternate path to the server (provider console or documented recovery method). Create the account and grant only required privileges; install its authorized public key using a trusted process; open a second session; verify the account identity, sudo access, and ability to recover. Do not remove the existing working access until the replacement is proven in a separate session.

This lesson does not disable root login, alter SSH authentication policy, or choose firewall rules. Those decisions belong to the networking/security subject and must be coordinated with a tested recovery path.

## Knowledge check

1. What does `id` tell you that `whoami` does not?
2. Why is a deployment account not automatically a sudo administrator?
3. Why does directory execute permission matter when reading a file inside it?
4. What makes `chmod 777` an unsafe general-purpose fix?
5. Why must new access be tested in a second session before old access is removed?

## Practical checkpoint

Complete [Task 02 — Verify a least-privilege account model](../tasks/02-verify-a-least-privilege-account-model.md). The task verifies and documents accounts; it deliberately avoids changing SSH daemon policy.
