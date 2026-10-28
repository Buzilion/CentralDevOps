# 05 — Packages and security maintenance

## Learning objectives

You can explain the Debian/Ubuntu package lifecycle, inspect pending changes before applying them, and plan routine updates without mistaking an update command for a complete maintenance policy.

## What the package manager does

On Ubuntu, APT resolves packages from configured repositories and tracks installed package state. Repository trust, release support, and package provenance matter: installing a package is granting its code the ability to run with the package's assigned privileges.

Useful read-only queries:

```sh
apt-cache policy PACKAGE_NAME
apt list --upgradable
dpkg-query -W -f='${binary:Package}\t${Version}\n'
```

The inventory command can be large; filter locally and avoid publishing a complete system inventory if it reveals operational details.

## Update is not upgrade

```sh
sudo apt update
apt list --upgradable
```

`apt update` refreshes the local package index from configured repositories. It does **not** upgrade installed packages. Review available changes, then apply upgrades intentionally:

```sh
sudo apt upgrade
```

APT may ask for confirmation, report packages held back, or require a broader dependency-changing operation. Read the proposed actions. Do not automatically agree to a removal or distribution release upgrade without understanding the impact. `apt full-upgrade` can install or remove packages to resolve dependency transitions; it is a separate decision, not a routine synonym for `upgrade`.

Avoid piping arbitrary shell scripts from the internet into `sudo`. Prefer the operating system's documented repository and signature-verification process. Do not install a package merely because a lesson command references an optional tool.

## A safe routine maintenance window

1. Verify provider console/recovery access and identify the maintenance window.
2. Confirm backups appropriate to the host's state; a provider snapshot alone may not meet recovery needs.
3. Record the OS release, uptime, failed units, and resource baseline.
4. Refresh package metadata, inspect candidate upgrades and removals, and understand any held packages.
5. Apply approved updates; observe errors instead of hiding them.
6. Check whether a reboot is recommended/required, and schedule one deliberately.
7. After changes, verify the host is reachable, expected services are active, and resource/service checks are normal.
8. Record what changed and any follow-up needed.

Kernel and core-library updates can require a reboot or service restart. A VPS that has received packages but is still running an old kernel may not yet be using the patched kernel. Check the provider's recovery options before rebooting a remote system.

## Automatic updates and policy

Automatic security updates can reduce exposure, but automation does not replace ownership or verification. Understand which origins and package types are enabled, how reboots are handled, how failures are reported, and who responds. Do not enable unattended reboot behavior on a production service without deciding the availability and recovery policy.

Package updates alone do not cover application dependencies, container images, secrets, SSH policy, firewall rules, backups, or monitoring. Those have dedicated subjects in this roadmap.

## Support lifecycle

Confirm that the VPS release is still supported and has an upgrade path. Do not mix a major distribution-release upgrade into a routine patch session. Plan it separately, with tested backups, compatibility review, maintenance window, provider console access, and a rollback/rebuild strategy.

## Knowledge check

1. What does `apt update` do, and what does it not do?
2. Why inspect proposed removals before confirming an upgrade?
3. Why might an updated kernel still not be the kernel currently running?
4. What must be defined before enabling automatic reboot behavior?
5. Why are host package updates not a complete security program?

## Practical checkpoint

Complete [Task 03 — Inspect and apply routine package updates](../tasks/03-inspect-and-apply-routine-package-updates.md).
