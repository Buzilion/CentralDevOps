# Task 6: Disposable VPS proof

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 5 |

## Goal

Prove the full access transition and host-baseline assumptions on a disposable VPS before any Staging or Production host is hardened.

## Relevant files or references

- Update `docs/runbooks/bootstrap-vps.md`
- v5 design §§12.1, 15.1, 16 step 3
- Spec requirements H-01 to H-13; Decisions D3, D4, D6

## Proposed approach

1. Create a disposable VPS manually and temporarily add it as a clearly identified test alias in the Staging inventory. Generate a disposable-only admin key pair; temporarily set its private key as the Staging `ANSIBLE_SSH_PRIVATE_KEY` secret and commit only its public key for the test host. Set Staging `VPS_INITIAL_ACCESS_PASSWORD` to this host's temporary provider password, one host at a time. Verify its SSH fingerprint against the Sumopod console and commit/use only the confirmed pin. Never add it to Production inventory.
2. Follow the runbook using the normal bootstrap workflow with `target_environment=Staging` and the disposable alias. Verify the first login, account separation, updates, firewall, admin public key, fresh admin-key login, SSH hardening, and fresh post-hardening admin login.
3. Exercise the failure gate by making the admin-key proof fail. Confirm the hardening phase does not run and provider access remains available.
4. Test unknown host and mismatched host key failures; both must occur before unintended access or key acceptance.
5. Test SSH source restriction when a stable source exists. If it is not compatible with the runner, record the host-specific exception and the remediation trigger.
6. Measure physical RAM and platform service memory use. Confirm or lower the reserve/budget values in inventory; record the evidence for spec 06.
7. Install a temporary, disposable-only deploy test public key for `cdo-deploy`; verify both `cdo-admin` and `cdo-deploy` can establish fresh key-based sessions. Enable the delivered fail2ban/equivalent role, observe both paths through the test window, and confirm neither is blocked. Remove the temporary deploy key afterward. If not safe, leave the role disabled and keep the spec blocked pending a safe policy.
8. After successful independent admin-key verification, remove the temporary password secret. Replace/remove the disposable admin-key secret, remove its public key, alias, and host pin from Staging inventory, and prepare a new admin key before bootstrapping the real Staging host. Do not reuse the disposable host's password or key. Destroy the disposable VPS only after evidence is captured and no access-path investigation remains.

## Acceptance criteria

- The complete successful transition is recorded, including a verified independent second login; this is the prerequisite evidence for INF-16. The test host is never confused with the actual Staging service host and is removed from inventory after the test.
- The forced-failure case proves SSH hardening is gated.
- Host-key mismatch and invalid-target tests fail closed.
- The base firewall exposes no PostgreSQL, app, or Docker API port.
- Admin and deploy identities are distinct; deploy cannot sudo or access Docker.
- Source restriction outcome, measured memory reserve/budget, and brute-force-protection outcome are documented.
- Temporary password, admin, and deploy test credentials are removed; no secret value is recorded.

## Verify

Record timestamp, operator, host alias, commit SHA, workflow run URL, phase outcomes, observed ports, memory figures, and any exception in the runbook evidence table. Do not record credentials or private key material.

## Out of scope

Hardening Staging or Production before this proof passes.
