# VPS Platform Bootstrap Decisions

## Summary

The VPS bootstrap playbook is an orchestration layer that runs the SSH, base, security, and Docker roles in sequence against `app_servers`. The first implementation targets Ubuntu 24.04 and keeps host access changes narrow: it adds an operator-provided public key, installs a minimal package baseline, enables AppArmor and auditd, and installs Docker Engine with the Compose plugin.

## Key Points

- Initial SSH access remains username/password-based; the SSH role adds the supplied public key for the existing `ansible_user` without changing sshd settings or disabling password authentication.
- The public key is supplied through the selected GitHub Environment variable: `DEV_SSH_PUBLIC_KEY`, `STG_SSH_PUBLIC_KEY`, or `PROD_SSH_PUBLIC_KEY`.
- The base role refreshes apt metadata and installs `ca-certificates`, `curl`, and `gnupg`. It does not perform a full upgrade or reboot.
- The security role installs and starts AppArmor and auditd. It does not change SSH, firewall, account, or OS-upgrade settings.
- The Docker role installs Docker Engine, Buildx, and the Compose plugin from Docker's official Ubuntu apt repository, enables Docker, and adds `ansible_user` to the `docker` group.
- The VPS login user is expected to have passwordless sudo. The GitHub workflow retains strict host-key checking and has syntax, check, and apply modes.

## Tradeoffs

- Adding a user to the `docker` group enables convenient Docker CLI access but grants effectively root-equivalent privileges.
- Public-key installation enables later key-based access, but password authentication remains enabled until a separately reviewed SSH-hardening change.
- Automatic security updates are not configured; patch timing remains subject to the maintenance-window policy.
- Development and staging intentionally share a VPS, so separate workflow environments do not provide host-level isolation.

## Open Questions

- Agree on a security-update maintenance schedule before automating package upgrades.
- Confirm each GitHub Environment's credentials and known-hosts data identify the authorized shared development/staging VPS before a live run.
- Application endpoint checks, public entry points, and promotion gates remain outside this host-bootstrap implementation.

## Context

This note records implementation decisions clarified while using `vps-platform-brainstorm_v1.md` and inspecting the existing bootstrap workflow, roles, and inventory. It supplements rather than replaces the original product brainstorm.
