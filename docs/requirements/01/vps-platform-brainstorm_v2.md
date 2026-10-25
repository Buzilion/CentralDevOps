# VPS Platform Bootstrap Decisions

## Summary

The VPS bootstrap playbook is an orchestration layer that runs the SSH, base, security, and Docker roles in sequence against `app_servers`. The first implementation targets Ubuntu 24.04 and keeps host access changes narrow: it adds an operator-provided public key, installs a minimal package baseline, enables AppArmor and auditd, and installs Docker Engine with the Compose plugin.

## Key Points

- Initial access to a fresh VPS uses its provider-created username and password. Bootstrap installs the separate `deploy` public key, verifies a new key-based session, then disables SSH password and keyboard-interactive authentication.
- The public key is supplied through the selected GitHub Environment variable: `STG_SSH_PUBLIC_KEY` or `PROD_SSH_PUBLIC_KEY`.
- The base role refreshes apt metadata and installs `ca-certificates`, `curl`, and `gnupg`. It does not perform a full upgrade or reboot.
- The security role installs and starts AppArmor and auditd. It does not change SSH, firewall, account, or OS-upgrade settings.
- The Docker role installs Docker Engine, Buildx, and the Compose plugin from Docker's official Ubuntu apt repository, enables Docker, and adds `ansible_user` to the `docker` group.
- The VPS login user is expected to have passwordless sudo. The GitHub workflow retains strict host-key checking and has syntax, check, and apply modes.

## Tradeoffs

- Adding a user to the `docker` group enables convenient Docker CLI access but grants effectively root-equivalent privileges.
- Keep the initial SSH password in a protected GitHub Environment secret only; the bootstrap run disables SSH password access after it verifies the deploy key.
- Automatic security updates are not configured; patch timing remains subject to the maintenance-window policy.
- Development runs locally on each developer workstation and is not a VPS inventory or bootstrap target. Staging and production are the only VPS environments.
- If staging and production map to the same physical VPS, they do not have host-level isolation and require one explicitly reviewed shared-host approval and credential policy.

## Open Questions

- Agree on a security-update maintenance schedule before automating package upgrades.
- Confirm the staging and production GitHub Environment credentials and known-hosts data identify their authorized VPS targets before a live run. The feedback draft records one active VPS for both environments; verify whether that shared-host arrangement is intended or provision separate hosts.
- Application endpoint checks, public entry points, and promotion gates remain outside this host-bootstrap implementation.

## Context

This note records implementation decisions clarified while using `vps-platform-brainstorm_v1.md` and inspecting the existing bootstrap workflow, roles, and inventory. It supplements rather than replaces the original product brainstorm.
