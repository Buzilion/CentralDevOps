# 04 — SSH hardening and brute-force defense

## Learning objectives

You can harden OpenSSH without relying on a single fragile setting, validate the effective server configuration, and preserve a tested recovery path while changing remote access.

## Threat model and layered controls

SSH is an administrative control plane, not an application endpoint. Internet-facing SSH attracts password guessing and automated probes. A nonstandard port may reduce background noise, but it is not a meaningful substitute for authentication and access controls.

Use multiple layers:

- Prefer public-key authentication; protect the private key on the trusted client and never copy it into a repository or the VPS.
- Disable password authentication only after a second key-authenticated session succeeds.
- Disallow direct root login; use a named administrative account with controlled `sudo`.
- Restrict allowed accounts with `AllowUsers` or an appropriate group if the operational model is understood.
- Limit network reachability at the provider firewall and UFW; use a stable administrator source range when practical.
- Add monitored brute-force controls, such as a correctly configured Fail2ban SSH jail, where appropriate.

If a source IP changes frequently, a fixed source allowlist can lock you out. Decide how to recover before applying such a restriction. The provider console and a second verified session are important independent paths.

## OpenSSH configuration on Ubuntu

Ubuntu typically supports drop-in files under `/etc/ssh/sshd_config.d/`; the main file may include them. Read the effective configuration and inspect the existing files before adding a drop-in. OpenSSH generally uses the first obtained value for a keyword, so the order of `Include` directives and existing definitions matters.

Relevant directives include:

```text
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin no
MaxAuthTries 4
```

These are example target values, not instructions to paste without checking. `AllowUsers` can reduce which accounts may log in, but an incorrect list can deny all access. Do not disable other authentication methods until you understand whether the host uses PAM, account policy, or provider-managed access.

After an edit, check syntax and effective values before reloading:

```sh
sudo sshd -t
sudo sshd -T | grep -E '^(pubkeyauthentication|passwordauthentication|permitrootlogin|maxauthtries|port) '
```

When `Match` blocks are present, effective values can depend on user and source address; `sshd -T -C ...` can evaluate a connection context. Review the OpenSSH manual for the installed version. Keep the current session open, reload rather than terminating the service where supported, then validate a **new** session from the intended client. Check the actual systemd unit name with `systemctl status ssh` or `systemctl status sshd`; Ubuntu commonly uses `ssh`.

## Brute-force defenses

A strong key-based login policy sharply reduces password-guessing risk, but repeated attempts still generate noise and can consume resources. Network restrictions and rate limiting reduce exposure. A log-based tool such as Fail2ban can temporarily ban addresses after repeated failures; it does not make weak credentials safe, and a ban can affect legitimate administrators behind shared or changing IPs.

Before enabling a jail, confirm the package supports the VPS's logging backend and SSH port. Configure the `sshd` jail through the distribution's supported local override, validate it with `fail2ban-client -t`, enable the service, and confirm `fail2ban-client status sshd` shows the jail monitoring the expected source. Do not test by intentionally failing repeated logins from your only administrative address. Review ban logs and ensure the recovery procedure can remove a mistaken ban from a trusted console.

## Avoid accidental lockout

Use this change sequence:

1. Confirm the provider console/recovery method is available and authorized.
2. Confirm the intended user has a working key login and required `sudo` access.
3. Keep the current SSH session open; use a second terminal for validation.
4. Make one policy change at a time; run `sshd -t` before reload.
5. Open a fresh session after reload and verify account, host, key, and privilege.
6. Only then remove obsolete access or close the previous path.

Do not log or share private keys. Verbose SSH client output and server logs may contain usernames, addresses, and hostnames; redact them before sharing evidence.

## Knowledge check

1. Why is moving SSH to a different port not sufficient hardening?
2. Why validate a new connection after reloading `sshd`?
3. What can go wrong if you use `AllowUsers` without testing?
4. How does Fail2ban differ from key-based authentication and firewall filtering?

## Practical checkpoint

Complete [Task 04 — Harden SSH and prove a safe second login](../tasks/04-harden-ssh-and-prove-a-safe-second-login.md).
