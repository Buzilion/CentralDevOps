# Task 3: Bootstrap baseline

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 2 |

## Goal

Implement the provider-credential phase that creates the separate account identities and a minimal safe host baseline, without disabling the existing access method.

## Relevant files or references

- Create `playbooks/bootstrap.yml`
- Create roles `common`, `users`, `firewall`, and `fail2ban`; keep fail2ban out of the initial-access playbook and disabled by default until the disposable-host test passes
- `docs/design/infrastructure-contracts-and-invariants.md` §§4–6
- v5 design §§6.1, 12.1
- Spec sections: Bootstrap and hardening sequence; SSH source restriction policy

## Proposed approach

1. Implement the initial phase using the provider username and password only for the target in the selected inventory.
2. Create `cdo-admin` and `cdo-deploy`. Grant `cdo-admin` passwordless sudo for Ansible `become`; set `cdo-deploy` password login disabled and do not grant it sudo, `docker` group membership, or the admin key.
3. Apply OS package updates and enable automatic security updates. Avoid making a reboot or lockout decision implicitly; report when a reboot is required and keep it an operator-controlled step.
4. On a fresh/reset host, bootstrap connects through port 22. Configure UFW default-deny inbound and temporarily allow SSH on both 22 and 4671 before enabling the firewall; also allow TCP 80/443, permit required outbound traffic, and never open PostgreSQL/app/Docker API ports. Keep port 22 open until a fresh admin-key login on 4671 is proven. Finalization removes the UFW 22 rule over the verified 4671 session.
5. Install the Environment's admin public key, without changing sshd root/password policy in this task.
6. Use `no_log` for secret-bearing tasks; never echo connection secrets or pass them in a command-line argument.
7. Implement D3's source allowlist rule and exception recording. Do not apply an allowlist that blocks the selected runner; do not claim GitHub-hosted runner egress is static.

## Acceptance criteria

- Accounts, package state, firewall, and public-key installation converge idempotently.
- `cdo-admin` can use Ansible privilege escalation; `cdo-deploy` is not privileged and has no Docker access.
- The existing provider login remains usable after the first phase.
- The initial provider connection and admin-key proof use port 22. The base UFW rules preserve both ports during transition; finalization removes port 22 after 4671 access is proven.
- No SSH hardening task can run in the initial phase.
- Ansible output, logs, and artifacts contain no credential values.

## Verify

Run syntax and lint checks, then use an isolated disposable test host. Assert account/group/sudo state, firewall rules, public-key presence, provider-login continuity, and no secret in captured logs.

## Out of scope

Admin-key proof, sshd hardening, fail2ban activation, production hosts, and Docker setup.
