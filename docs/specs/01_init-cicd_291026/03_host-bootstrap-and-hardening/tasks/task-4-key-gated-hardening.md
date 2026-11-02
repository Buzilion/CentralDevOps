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
4. After the admin key works on port 22, configure key-only SSH with both `Port 22` and `Port 4671`; disable root, password, and keyboard-interactive login. Validate the complete candidate sshd configuration and both effective ports before reloading.
5. Open a fresh admin-key connection on port 4671. Only after it succeeds, use a separate 4671 session to finalize sshd to port 4671 only and remove the UFW 22 rule; validate/reload and prove another fresh 4671 connection.
6. Keep the Sumopod console recovery procedure explicit in the runbook. Do not introduce an untested automatic rollback that could conceal a failed access transition.

## Acceptance criteria

- Admin-key proof uses a new process/SSH connection, not the initial provider session.
- A failed proof demonstrably skips all sshd hardening and leaves provider password access available.
- Successful proof permits hardening, and a new admin-key connection succeeds afterwards.
- Failed initial proof prevents hardening and leaves provider port 22 usable.
- The transitional effective sshd listener set is exactly `{22, 4671}`; final sshd listens on 4671 only.
- Port 22 is not closed until a fresh admin-key login on 4671 has succeeded; finalization itself runs over 4671.
- Root and password/keyboard-interactive authentication are refused after successful hardening.
- sshd config validation failure leaves the existing configuration active.

## Verify

On the disposable VPS, run the success path and an induced key-proof failure. Capture phase results without logging secrets; confirm current access paths after each case.

## Out of scope

Workflow Environment approval configuration, actual Production use, fail2ban, and runtime service setup.
