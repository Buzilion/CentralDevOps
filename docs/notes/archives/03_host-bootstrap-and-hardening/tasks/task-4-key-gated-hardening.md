# Task 4: Key-gated SSH hardening

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 3 |

## Goal

Make the independent admin-key connection an explicit, mandatory gate before disabling root and password SSH access.

## Relevant files or references

- Update `playbooks/bootstrap.yml`
- Create role `roles/ssh_hardening/`
- `docs/design/variables-and-secrets.md` §4.1
- v5 design §§6.1, 12.1
- Spec sections: Bootstrap and hardening sequence, Invariants, Error behavior

## Proposed approach

1. Implement a separate admin-key proof phase that establishes a fresh SSH connection to the same exact host, with strict host-key checking and the `cdo-admin` account.
2. Require an authenticated remote command that confirms the connection is the intended admin user, not merely a successful local key parse.
3. Gate every hardening task on successful completion of that proof. A failed proof must fail the play and skip all hardening changes.
4. Configure key-only SSH: enable public key authentication; disable root, password, and keyboard-interactive login. Validate the candidate sshd configuration before applying it and reload only after validation.
5. After hardening, open a fresh SSH connection with the admin key and verify the host refuses root/password login.
6. Keep the Sumopod console recovery procedure explicit in the runbook. Do not introduce an untested automatic rollback that could conceal a failed access transition.

## Acceptance criteria

- Admin-key proof uses a new process/SSH connection, not the initial provider session.
- A failed proof demonstrably skips all sshd hardening and leaves provider password access available.
- Successful proof permits hardening, and a new admin-key connection succeeds afterwards.
- Root and password/keyboard-interactive authentication are refused after successful hardening.
- sshd config validation failure leaves the existing configuration active.

## Verify

On the disposable VPS, run the success path and an induced key-proof failure. Capture phase results without logging secrets; confirm current access paths after each case.

## Out of scope

Workflow Environment approval configuration, actual Production use, fail2ban, and runtime service setup.
