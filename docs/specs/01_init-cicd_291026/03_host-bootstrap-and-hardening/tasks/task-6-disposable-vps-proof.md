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

1. Use a disposable VPS in Staging by default. For the user-authorized empty VPS labeled `buz-prod-1`, use the Production inventory alias `prd-disposable-01` with `bootstrap_disposable: true`; keep the host free of service data. Generate a disposable-only admin key pair, put only its public half in the selected Environment inventory, and set its private half as that Environment's `ANSIBLE_SSH_PRIVATE_KEY` secret. Set that Environment's `VPS_INITIAL_ACCESS_PASSWORD` to the host's temporary provider password, one host at a time. Verify the SSH fingerprint against the Sumopod console and commit/use only the confirmed pin. Production runs must remain on `release/*` and pass the required reviewer gate.
2. Follow the runbook with the corresponding Environment and exact disposable alias. Verify the first login, account separation, updates, firewall, admin public key, fresh admin-key login, SSH hardening, and fresh post-hardening admin login.
3. Exercise the failure gate by making the admin-key proof fail. Confirm the hardening phase does not run and provider access remains available.
4. Test unknown host and mismatched host key failures; both must occur before unintended access or key acceptance.
5. Test SSH source restriction when a stable source exists. If it is not compatible with the runner, record the host-specific exception and the remediation trigger.
6. Measure physical RAM and platform service memory use. Confirm or lower the reserve/budget values in inventory; record the evidence for spec 06.
7. The disposable-only workflow phase generates a temporary Ed25519 key for `cdo-deploy`, verifies fresh `cdo-admin` and `cdo-deploy` sessions before enabling fail2ban, then probes both paths every minute for the 120-second test window. It removes the temporary deploy key afterward. If either path fails, the workflow attempts to disable and remove fail2ban before removing the test key; use the Sumopod console if either cleanup phase cannot connect, and keep the spec blocked until the host is confirmed safe.
8. After successful independent admin-key verification, remove the temporary password secret. Replace/remove the disposable admin-key secret, remove its public key, alias, and host pin from the selected inventory, and do not reuse the disposable password or key. Destroy a standalone disposable VPS after evidence is captured and no access-path investigation remains. For the user-authorized future-Production VPS, reimage or otherwise restore a clean Ubuntu Server 24.04 host before Production service use, then configure it with a fresh Production admin key and a normal service alias.

## Acceptance criteria

- The complete successful transition is recorded, including a verified independent second login; this is the prerequisite evidence for INF-16. The test host is never treated as a service host while flagged disposable and is removed from the disposable inventory entry after the test.
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
