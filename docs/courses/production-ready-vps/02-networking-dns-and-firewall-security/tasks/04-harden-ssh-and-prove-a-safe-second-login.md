# Task 04 — Harden SSH and prove a safe second login

## Outcome

Enforce key-based, non-root administrative SSH access, verify the effective daemon policy, and enable monitored brute-force defense without risking an untested lockout.

## Prerequisites

- Read [Lesson 04 — SSH hardening and brute-force defense](../lessons/04-ssh-hardening-and-brute-force-defense.md).
- Completed Task 03 or otherwise have a verified SSH firewall rule.
- A working key-authenticated administrative account with `sudo`, an open existing SSH session, and provider recovery access.

## Procedure

1. From the client, confirm the intended account and key can open a new session. Verify `whoami`, `id`, and `sudo -v`. Do not copy private-key material to the server.
2. Inspect `/etc/ssh/sshd_config` and included drop-in files. Confirm how the current OpenSSH version handles `Include` order, PAM, `Match` blocks, and existing authentication settings.
3. Add a narrowly scoped local drop-in only if necessary to reach the intended policy: public-key authentication enabled, password authentication disabled, direct root login disabled, and a reasonable `MaxAuthTries`. Add an account allowlist only if you have verified the exact login name and recovery account.
4. Validate before reload:

   ```sh
   sudo sshd -t
   sudo sshd -T | grep -E '^(pubkeyauthentication|passwordauthentication|permitrootlogin|maxauthtries|port) '
   ```

5. Keep the current session open. Reload the actual SSH unit only after syntax validation, then use a second terminal to reconnect with the intended key. Confirm `sudo` still works before closing the original session.
6. If Fail2ban is appropriate, confirm its package and logging backend, configure its SSH jail using a supported local override, run `sudo fail2ban-client -t`, enable it, and verify `sudo fail2ban-client status sshd`. Do not deliberately trigger bans from your only admin address.
7. Record recovery steps for removing an accidental ban or restoring a known-good SSH configuration using the provider console.

## Acceptance criteria

- [ ] A fresh key-based login succeeds for the intended non-root account.
- [ ] The effective configuration confirms password login is disabled and direct root login is disabled, unless a documented platform constraint prevents it.
- [ ] `sshd -t` passes before and after the change, and the active service is healthy.
- [ ] `sudo` works in the new session and provider recovery access remains available.
- [ ] If Fail2ban is enabled, its SSH jail is active and monitoring the correct backend/port; otherwise, the rationale is recorded.
- [ ] No private key, password, token, recovery code, or raw authentication log is included in evidence.

## Deliverable

A private SSH hardening record with sanitized effective settings, test outcome, brute-force control status, and a credential-free lockout recovery procedure.
