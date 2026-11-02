# Task 6: Disposable VPS proof

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 5 |

## Goal

Prove the full access transition and host-baseline assumptions on a disposable VPS before any Staging or Production host is hardened.

## Relevant files or references

- Update `docs/runbooks/bootstrap-vps.md`
- Verify the SSH jail settings delivered by `roles/fail2ban/` and its disposable-proof playbook
- Exercise `playbooks/finalize-ssh-port.yml` after the fresh 4671 admin-key proof
- v5 design §§12.1, 15.1, 16 step 3
- Spec requirements H-01 to H-13; Decisions D3, D4, D6

## Proposed approach

1. Use a disposable VPS in Staging by default. For the user-authorized empty VPS labeled `buz-prod-1`, use the Production inventory alias `prd-disposable-01` with `bootstrap_disposable: true`; keep the host free of service data. For a fresh/reset host, expect initial SSH on port 22 and ensure the provider firewall permits 4671 before dispatch. Generate a disposable-only admin key pair, put only its public half in the selected Environment inventory, and set the raw private-key file contents as that Environment's `ANSIBLE_SSH_PRIVATE_KEY` secret. Set that Environment's `VPS_INITIAL_ACCESS_PASSWORD` to the host's temporary provider password, one host at a time. Re-verify the reset host fingerprint against the Sumopod console; pin the verified key for both port 22 and `[host]:4671`. Production runs must remain on `release/*` and pass the required reviewer gate.
2. Follow the runbook with the corresponding Environment and exact disposable alias. Verify the first login and admin-key proof on port 22, temporary dual-listener sshd/UFW behavior, a fresh admin-key login on 4671, finalization to sshd/UFW 4671 only, and another fresh 4671 login. Then close provider-firewall port 22 and verify 4671 remains reachable while 22 is closed.
3. Exercise the failure gate by making the admin-key proof fail. Confirm the hardening phase does not run and provider access remains available.
4. Test unknown host and mismatched host key failures; both must occur before unintended access or key acceptance.
5. Test SSH source restriction when a stable source exists. If it is not compatible with the runner, record the host-specific exception and the remediation trigger.
6. Measure physical RAM and platform service memory use. Confirm or lower the reserve/budget values in inventory; record the evidence for spec 06.
7. After port finalization and provider-firewall cleanup, the disposable-only workflow phase generates a temporary Ed25519 key for `cdo-deploy`, verifies fresh `cdo-admin` and `cdo-deploy` sessions before enabling Fail2ban, and verifies the loaded SSH jail uses port 4671, `maxretry=2`, `findtime=1h`, and `bantime=1d`. Probe both paths every minute for the 120-second test window. It removes the temporary deploy key afterward. If either path fails, the workflow attempts to disable and remove Fail2ban before removing the test key; use the Sumopod console if either cleanup phase cannot connect, and keep the spec blocked until the host is confirmed safe.
8. After successful independent admin-key verification, remove the temporary password secret. Replace/remove the disposable admin-key secret, remove its public key, alias, and host pin from the selected inventory, and do not reuse the disposable password or key. Destroy a standalone disposable VPS after evidence is captured and no access-path investigation remains. For the user-authorized future-Production VPS, reimage or otherwise restore a clean Ubuntu Server 24.04 host before Production service use, then configure it with a fresh Production admin key and a normal service alias.

## Acceptance criteria

- The complete successful transition is recorded, including a verified independent second login; this is the prerequisite evidence for INF-16. The test host is never treated as a service host while flagged disposable and is removed from the disposable inventory entry after the test.
- The forced-failure case proves SSH hardening is gated.
- Host-key mismatch and invalid-target tests fail closed.
- The base firewall exposes no PostgreSQL, app, or Docker API port.
- Final SSH uses TCP 4671 only; port 22 is not listening, not allowed by UFW, and removed from the provider firewall after the final 4671 proof.
- Admin and deploy identities are distinct; deploy cannot sudo or access Docker.
- Source restriction outcome, measured memory reserve/budget, and brute-force-protection outcome are documented.
- Temporary password, admin, and deploy test credentials are removed; no secret value is recorded.

## Verify

Record timestamp, operator, host alias, commit SHA, workflow run URL, phase outcomes, observed ports, memory figures, and any exception in the runbook evidence table. Do not record credentials or private key material.

## Out of scope

Hardening Staging or Production before this proof passes.
