# VPS Bootstrap and Hardening Runbook

## Scope and gates

This runbook applies only to one fresh Ubuntu Server 24.04 LTS VPS in the selected `Staging` or `Production` GitHub Environment. Provision the VPS manually in Sumopod; this repository does not create hosts through a provider API.

The user confirmed on 2026-10-31 that their Sumopod Ubuntu target is 24.04 and available to connect. On 2026-11-01, the user authorized using the empty VPS labeled `buz-prod-1` as the disposable proof target before it carries Production service data. It is represented by the alias `prd-disposable-01`. The user reported that the pinned Ed25519 fingerprint `SHA256:BrLzSX6Y4gni6cfc8HvHYJMsTuWzw8zOskxg5dBQqAc` matches the Sumopod console. The inventory records 3723 MiB physical RAM as user-reported; the pre-mutation Ansible check must confirm it. The 1536 MiB reserve and 2048 MiB app budget are provisional until baseline use is measured.

Do not run the protected workflow until all of these are true:

- The selected inventory has the exact host alias, its reviewed host facts, a public admin key, the capacity facts, and a verified `known_hosts` pin.
- The Staging or Production Environment has `ANSIBLE_INVENTORY_PATH` set to its matching fixed inventory path: `inventories/staging/hosts.yml` for Staging, `inventories/production/hosts.yml` for Production. Set it with the GitHub CLI or repository settings; never accept an operator-supplied path.
- The dispatch App numeric actor ID has been proven by spec 02 and recorded in `deployment/tools/bootstrap_inventory.py` (`350767931`). Preflight rejects that actor before binding an Environment.
- Until disposable-host proof is recorded, only a host with a `disposable` alias purpose and boolean `bootstrap_disposable: true` passes target validation. For `buz-prod-1`, dispatch the Production environment using `prd-disposable-01`; Production still requires a `release/*` ref and its required reviewer approval. Record the proof commit in `DISPOSABLE_VPS_PROOF_COMMIT` before allowing service-host targets.
- Production approval and `release/*` deployment-branch protection remain enabled.
- The initial password secret is set only for the target VPS and the admin private-key secret belongs to the selected Environment.

The Production inventory contains the user-authorized `prd-disposable-01` candidate with user-reported 3723 MiB RAM, a provisional 1536 MiB reserve, and a provisional 2048 MiB app budget. No live target validation or baseline measurement has been recorded. The Staging inventory remains empty. Do not dispatch until the target facts are verified and the selected Environment's required variables and secrets are available.

## GitHub Environment protection audit

Read-only metadata was checked on 2026-11-01; no Environment settings were changed and no secret values were accessed.

- `Production` has a required reviewer, accepts `release/*`, and has administrator bypass disabled.
- `Staging` has the fixed required-reviewer gate, allows self-review and administrator bypass, and has no branch restriction.
- GitHub denied access to the Environment variable/secret name-list endpoints. The user reports that the required configuration is complete, but this CLI identity could not verify the presence of `ANSIBLE_INVENTORY_PATH`, `VPS_INITIAL_ACCESS_PASSWORD`, or `ANSIBLE_SSH_PRIVATE_KEY`; no secret values were accessed.

## Pinned controller and local checks

The selected toolchain is recorded in [spec 03](../specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md#pinned-controller-baseline). Bootstrap runs on the GitHub-hosted `ubuntu-24.04` controller; Ansible is not supported as a Windows controller.

From the repository root on Ubuntu:

```bash
python3 -m venv .ansible-venv
. .ansible-venv/bin/activate
python -m pip install --disable-pip-version-check --no-input -r requirements-dev.txt
ansible-galaxy collection install \
  --requirements-file requirements.yml \
  --collections-path ./.ansible/collections

ansible --version
ansible-galaxy collection list
ansible-config dump --only-changed
ansible-inventory --inventory inventories/staging/hosts.yml --list
ansible-inventory --inventory inventories/production/hosts.yml --list
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/bootstrap.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/prove-admin-key.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/harden-ssh.yml
ansible-lint playbooks/bootstrap.yml playbooks/prove-admin-key.yml playbooks/harden-ssh.yml roles/
```

The first install is controller-only. Do not set provider credentials or connect to a VPS while validating syntax or inventories.

## Adding a host and verifying its SSH pin

1. Provision the host manually and confirm its Ubuntu Server 24.04 LTS image and initial SSH username in the Sumopod console.
2. Generate a new environment-specific Ed25519 admin key pair on a trusted workstation. Commit only its public half to that Environment's `group_vars/all.yml`; set the private half as `ANSIBLE_SSH_PRIVATE_KEY` in the matching GitHub Environment. Do not reuse the disposable VPS key on a service host.
3. Use the host alias format `<environment-code>-<purpose>-<two-digit-number>`, such as `stg-aio-01`. Add the exact alias to only its own `hosts.yml` and add a corresponding `host_vars/<alias>.yml` with `ansible_host`, `provider_username`, optional non-default `ansible_port`, `physical_memory_mib`, `platform_reserve_mib`, `capacity_budget_mib`, and either `ssh_source_cidrs` or a documented `ssh_source_policy_exception`. For the user-authorized Production proof target, use `prd-disposable-01` and set `bootstrap_disposable: true`; do not use that alias for Production services.
4. Measure physical RAM and reserve enough for the platform services. The initial reference values are Staging 2048/1024/1024 MiB (physical/reserve/app budget) and Production 4096/1536/2560 MiB. Lower the budget when measurements require it; the validator rejects a budget above physical memory minus reserve or the environment reference ceiling.
5. From an operator-controlled workstation, collect a candidate host key with `ssh-keyscan` if needed. Use `ssh-keygen -lf` to inspect its fingerprint and compare it with the independently displayed fingerprint in the Sumopod console. A scan is only a way to collect a candidate; it is not a trust source. Add the candidate to the selected `known_hosts` file only after the fingerprints match. For non-default SSH ports, use the exact OpenSSH endpoint format `[host]:port`.
6. Require a stable SSH source allowlist only when it permits the selected runner to connect. GitHub-hosted runner egress is not stable. If no compatible stable CIDR exists, leave the host's CIDR list empty and record the per-host exception and its remediation trigger. Never apply a rule that strands the active access path.
7. Review the inventory change. Do not commit provider passwords, private keys, placeholder addresses, or unverified host-key material.

The secret-free preflight validates the fixed Environment-to-inventory mapping, exact host membership, alias format, public admin key, source-policy decision, RAM budget, and the host-key pin before any SSH command. It does not scan for or accept a new host key. Before any mutating role runs, the bootstrap playbook also checks the observed memory against the configured reserve and application budget.

## Bootstrap sequence

Dispatch `.github/workflows/bootstrap-vps.yml` with only:

- `target_environment`: exactly `Staging` or `Production`
- `target_host`: one exact alias from that Environment's inventory

The workflow rejects non-branch refs, rejects Production refs outside `release/*`, and checks the dispatch App actor before its Environment-bound job. The preflight job has no Environment association or credentials. The credential job rechecks the Environment's `ANSIBLE_INVENTORY_PATH` against the fixed code mapping; Production approval occurs before the job can receive secrets.

The phases run in separate Ansible processes with SSH multiplexing disabled:

1. **Initial access:** use the provider username from `host_vars` and the selected Environment's `VPS_INITIAL_ACCESS_PASSWORD`. Create `cdo-admin` and `cdo-deploy`, update packages, enable automatic security updates, apply UFW, and install the admin public key. SSH authentication policy is unchanged. Ansible tasks using the initial connection are marked `no_log`; the password is read from the step environment and is never passed in argv or written to a runner file.
2. **Independent admin-key proof:** after the provider session ends, use the `cdo-admin` key in a new SSH process and assert the remote identity is exactly `cdo-admin`. Password and keyboard-interactive methods are disabled for this proof.
3. **Credential cleanup:** only after that proof succeeds, the workflow displays an operator notice to remove `VPS_INITIAL_ACCESS_PASSWORD` from the selected Environment. If the proof fails, the workflow stops before this notice and before hardening.
4. **SSH hardening:** the hardening playbook performs its own fresh admin-key identity check before running the hardening role. The role writes the SSH drop-in, validates the complete effective sshd configuration and required effective settings, and reloads SSH only after validation. If validation fails, it restores the prior drop-in and fails without reporting a successful reload.
5. **Post-hardening proof:** a new Ansible/SSH process confirms `cdo-admin` key access again. If it fails, do not report the host ready; use the Sumopod console recovery procedure and investigate before retrying.

`run_bootstrap_phase.py` writes the admin private key only to a runner temporary file with owner-only permissions and removes it in an unconditional cleanup path. It removes the secret value from the child process environment and gives Ansible only the temporary file path. Do not enable shell tracing or upload runner files.

The base UFW policy allows the configured SSH port, TCP 80/443, and outbound traffic; it denies other unsolicited inbound traffic. It does not open PostgreSQL, application, or Docker API ports. A reboot-required marker is reported for an operator-controlled reboot; bootstrap never reboots automatically.

## Disposable VPS proof and cleanup

No disposable VPS proof has been run. The user has made the empty `buz-prod-1` VPS available for the test and reports that required configuration is complete. The Production inventory candidate is present, but its capacity values remain marked as examples, the provider-console fingerprint comparison is not recorded here, and Environment variable/secret metadata is inaccessible to this CLI identity. No workflow dispatch or SSH connection has been attempted.

Use a separate temporary admin key for the proof, and record only sanitized evidence. For the user-authorized `buz-prod-1` candidate, the Production workflow must run from `release/*` and pass the required reviewer gate:

1. Recheck that the provider-console fingerprint and committed host-key pin match before dispatch. The user reported a match on 2026-11-01; repeat the comparison if the host is reprovisioned or its SSH host key changes.
2. Run the workflow for `target_environment=Production` and `target_host=prd-disposable-01`; verify provider access, account/group/sudo state, updates, UFW exposure, admin-key login, successful hardening, post-hardening admin login, and refusal of root/password/keyboard-interactive access.
3. Force the admin-key proof to fail. Confirm the hardening role does not run and provider access remains available.
4. Try an unknown target, an alias from the other Environment, an invalid alias pattern, and a mismatched host key. Each must fail before an unintended SSH connection or key acceptance.
5. Record whether a stable runner-compatible SSH source CIDR exists; otherwise record the host-specific exception and remediation trigger.
6. Measure physical RAM and platform service memory use. Confirm or lower the reserve and budget and record the evidence for spec 06.
7. Temporarily add a disposable-only deploy public key to `cdo-deploy`, verify fresh key sessions for both accounts, then enable fail2ban and observe both access paths through the test window. Remove the deploy test key. If either account is blocked or the test is inconclusive, leave fail2ban disabled.
8. After successful independent admin-key verification, remove the temporary password secret. Remove the disposable admin-key secret, test public key, alias, host facts, and host pin. Because the user intends to use this VPS for Production later, reimage or restore it to a clean Ubuntu Server 24.04 state before service use, then add it under a normal Production service alias with a fresh Production admin key. Do not reuse the disposable password or key. Record the tested commit and evidence, then set `DISPOSABLE_VPS_PROOF_COMMIT` to that full 40-character commit SHA in a reviewed change; until that change is reviewed, service-host bootstrap remains blocked.

## GitHub Environment audit

Read-only GitHub metadata was checked on 2026-11-01. No Environment setting was changed and no secret value was requested.

- The repository has exactly `Staging` and `Production`.
- `Production` has a required reviewer, administrator bypass disabled, and a `release/*` deployment-branch policy.
- `Staging` has the fixed required-reviewer gate and no branch restriction. Self-review and administrator bypass are allowed in the current GitHub configuration.
- GitHub returned HTTP 403 for Environment variable/secret-name listing. The presence of `ANSIBLE_INVENTORY_PATH` and bootstrap secrets was not verified.

## Evidence log

Record one row after each real disposable-host run. Never record passwords, private keys, or secret values.

| Date/time | Operator | Host alias | Commit SHA | Workflow run URL | Phase outcomes | Observed inbound ports | Physical RAM / reserve / budget | Source-policy result or exception |
|---|---|---|---|---|---|---|---|---|

## Acceptance audit

Local audit updated on 2026-11-01. All 36 Python unit tests passed with one Ansible CLI integration test skipped on Windows; the fixtures used `CENTRALDEVOPS_TEST_TMPDIR` under the local `TestRepo-Application` clone, which remained clean. The workflow naming checker, actionlint 1.7.12, zizmor 1.31.1, YAML parsing (17 files), and `git diff --check` passed. Ansible syntax-check and ansible-lint could not run because this Windows controller has no Linux distribution. The local Production candidate passed the Python inventory, capacity, and pin-syntax checks; the user reported that the pinned host-key fingerprint matches the independent Sumopod console fingerprint. Host RAM is user-reported at 3723 MiB, while reserve and budget remain provisional pending live baseline validation. The spec-02 checklist is complete and the actor ID is pinned. No VPS, Environment secret value, or provider credential was accessed. No live dispatch or SSH connection was attempted; this feature branch is not a published `release/*` ref.

| Requirement | Local status | Evidence or remaining gate |
|---|---|---|
| H-01 | BLOCKED | Bootstrap roles and phases are implemented; end-to-end account, update, firewall, and public-key convergence needs the disposable VPS. |
| H-02 | LOCAL PASS; LIVE BLOCKED | Fixed inventory mapping and exact alias/target checks have fixture tests; the `prd-disposable-01` candidate passes local Python validation. Environment variables could not be audited, and this feature branch is not an eligible published `release/*` ref. |
| H-03 | USER CONFIRMED; LIVE BLOCKED | Strict checking and committed-pin lookup are configured and tested with generated fixture keys. The user reported an exact Ed25519 SHA256 fingerprint match against the Sumopod console; no live SSH handshake has been attempted. |
| H-04 | BLOCKED | Separate proof process and hardening gate are implemented; successful and forced-failure transitions need the disposable VPS. |
| H-05 | BLOCKED | Key-only SSH role and fresh post-hardening proof are implemented; login/refusal behavior needs the disposable VPS. |
| H-06 | BLOCKED | UFW policy is implemented; effective rules and service behavior need the disposable VPS. |
| H-07 | LOCAL PASS; LIVE BLOCKED | The Production candidate's address and provider username remain in its host vars; workflow and runner use fixed inventory mappings. The Staging inventory remains separate and empty. |
| H-08 | USER CONFIRMED; LIVE BLOCKED | Missing/mismatched pin fixtures fail closed; the user reported the configured Production pin matches the provider-console fingerprint. A live strict-SSH handshake remains untested. |
| H-09 | LOCAL PASS; LIVE PARTIAL | The proved actor ID is rejected; Production approval and `release/*` were verified, and the fixed Staging reviewer gate is active. Environment variables/secrets could not be audited; no protected workflow run was dispatched. |
| H-10 | BLOCKED | The workflow requests operator cleanup only after independent proof; no Environment password was set or removed. |
| H-11 | LOCAL PASS; LIVE BLOCKED | Service-host targets are rejected until a disposable proof commit is recorded. The user-authorized Production candidate is flagged disposable; no host has been accessed. |
| H-12 | BLOCKED | Fail2ban is disabled by default; enabling it safely requires the disposable-host access-path observation. |
| H-13 | LOCAL PASS; LIVE BLOCKED | Inventory capacity validation checks the declared reserve and environment ceiling, and the initial playbook checks observed RAM before any roles run. Physical RAM is user-reported at 3723 MiB; reserve 1536 MiB and budget 2048 MiB remain provisional until live baseline validation. |
