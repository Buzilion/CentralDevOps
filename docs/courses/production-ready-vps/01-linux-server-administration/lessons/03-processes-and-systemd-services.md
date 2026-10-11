# 03 — Processes and systemd services

## Learning objectives

You can distinguish a process from a service, inspect process identity and resource use, understand systemd's role, and gather service evidence before deciding whether an action is safe.

## Processes

A process is a running instance of a program with an identity (PID), parent relationship, credentials, open resources, and state. A process may be started interactively, by another process, by a scheduler, or by a service manager. A systemd service is a managed unit; it may start one or several processes over time, and its process IDs may change after a restart.

Useful inspection commands:

```sh
ps -eo pid,ppid,user,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head
pgrep -a -u "$USER" .
top
```

`ps` provides a snapshot; `top` refreshes interactively. Process arguments can include sensitive values if an application is configured badly, so avoid publishing unredacted output. The process list is not a health check: a process existing does not prove that the application is serving correctly.

Signals request actions from processes. `SIGTERM` asks a process to stop gracefully; `SIGKILL` forcibly ends it and cannot be caught or handled. Do not kill processes by guessed PID or broad name matching. Prefer the owning service manager and understand the impact before a stop or restart.

## systemd and units

On Ubuntu Server, systemd commonly initializes the host and manages services. A unit can represent a service, timer, mount, socket, target, and other resources. Unit files describe desired behavior and dependencies; systemd tracks state and provides logs.

Start with read-only inspection:

```sh
systemctl --failed
systemctl list-units --type=service --state=running
systemctl status SERVICE_NAME --no-pager
systemctl show SERVICE_NAME -p ActiveState -p SubState -p MainPID -p User
```

Use the installed unit name, which may not equal the package or product name. `status` provides recent context and the main PID; `show` exposes selected structured properties. A service can be `active` but unhealthy at the application level.

Typical operations include `start`, `stop`, `restart`, `reload`, `enable`, and `disable`, but each changes state:

- `start` and `stop` affect the current runtime state.
- `restart` stops and starts the service; active connections may be interrupted.
- `reload` asks a service to reread configuration if it supports that action.
- `enable` arranges for a unit to start at boot; it does not necessarily start it now.
- `disable` removes that boot-time enablement; it does not necessarily stop a running unit.

Do not restart SSH over your only remote connection. Do not restart a database or production application merely to see what happens. First understand the unit, users, dependencies, impact, recovery route, and change window.

## Troubleshoot in layers

When a unit is failing, proceed from observation to hypothesis:

1. `systemctl status UNIT` — current state, exit status, recent messages.
2. `journalctl -u UNIT --since '30 minutes ago' --no-pager` — relevant unit log records.
3. `systemctl show UNIT -p ExecStart -p User -p WorkingDirectory` — selected configuration context.
4. `ps` or `pgrep` — determine whether expected processes exist and which user owns them.
5. Inspect the configuration path and permissions only after identifying the path and service identity.
6. Check dependent services, storage availability, and recent package/configuration changes.

Do not paste secrets from environment files or command lines into evidence. If a log suggests credentials were printed, treat that as a possible exposure and follow the organization's secret-response process.

## systemd journal basics

```sh
journalctl -u SERVICE_NAME -n 100 --no-pager
journalctl -u SERVICE_NAME --since today --no-pager
journalctl -p warning..alert --since '1 hour ago' --no-pager
journalctl -k -b --no-pager
```

The journal stores messages from the system and services, subject to host configuration and retention. `-u` filters by unit; `-k` selects kernel messages; `-b` limits to the current boot. Logs may be incomplete if a service writes elsewhere or the journal is volatile/retained only briefly.

## Configuration and service lifecycle

Before editing a unit or its configuration, record the current state and locate the authoritative file. Package-provided unit files and administrator overrides have different lifecycle expectations. A change should have a clear owner, a minimal diff, a syntax/config validation step where supported, a planned activation action, and a rollback.

For this first subject, practice inspection, not custom unit authoring. Later deployment and automation subjects can build on a verified manual service model.

## Knowledge check

1. How can a service be active but still fail to serve requests?
2. What is the difference between `enable` and `start`?
3. Why is `SIGKILL` a poor first response to a stuck service?
4. What is the safe first sequence when `systemctl status` reports a failure?
5. Why is restarting SSH over the only session risky?

## Practical checkpoint

Complete [Task 04 — Diagnose a service and resource snapshot](../tasks/04-diagnose-a-service-and-resource-snapshot.md). Gather evidence from a low-risk unit; do not induce an outage.
