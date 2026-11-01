# VPS Bootstrap and Hardening Runbook

## Scope and gates

This runbook applies only to one fresh Ubuntu Server 24.04 LTS VPS in the selected `Staging` or `Production` GitHub Environment. Provision the VPS manually in Sumopod; this repository does not create hosts through a provider API.

The user confirmed on 2026-10-31 that their Sumopod Ubuntu target is 24.04 and available to connect. On 2026-11-01, the user authorized using the empty VPS labeled `buz-prod-1` as the disposable proof target before it carries Production service data. It is represented by the alias `prd-disposable-01`. The user reported that the pinned Ed25519 fingerprint `SHA256:BrLzSX6Y4gni6cfc8HvHYJMsTuWzw8zOskxg5dBQqAc` matches the Sumopod console; the live initial-access SSH session accepted the committed pin. The first disposable run also confirmed Ubuntu 24.04 and observed 3723 MiB physical RAM. The 1536 MiB reserve and 2048 MiB app budget remain provisional until platform baseline use is measured.

Do not run the protected workflow until all of these are true:

- The selected inventory has the exact host alias, its reviewed host facts, a public admin key, the capacity facts, and a verified `known_hosts` pin.
- The selected Environment's `ANSIBLE_SSH_PRIVATE_KEY` represents an unencrypted private key matching the reviewed inventory public key. Prefer setting it as `base64:` followed by the single-line Base64 encoding of the exact key file; the runner decodes it to bytes before validation. The protected job checks this before making any SSH connection.
- The Staging or Production Environment has `ANSIBLE_INVENTORY_PATH` set to its matching fixed inventory path: `inventories/staging/hosts.yml` for Staging, `inventories/production/hosts.yml` for Production. Set it with the GitHub CLI or repository settings; never accept an operator-supplied path.
- The dispatch App numeric actor ID has been proven by spec 02 and recorded in `deployment/tools/bootstrap_inventory.py` (`350767931`). Preflight rejects that actor before binding an Environment.
- Until disposable-host proof is recorded, only a host with a `disposable` alias purpose and boolean `bootstrap_disposable: true` passes target validation. For `buz-prod-1`, dispatch the Production environment using `prd-disposable-01`; Production still requires a `release/*` ref and its required reviewer approval. Record the proof commit in `DISPOSABLE_VPS_PROOF_COMMIT` before allowing service-host targets.
- Production approval and `release/*` deployment-branch protection remain enabled.
- The initial password secret is set only for the target VPS and the admin private-key secret belongs to the selected Environment.

The Production inventory contains the user-authorized `prd-disposable-01` candidate with 3723 MiB RAM observed during the first live run, a provisional 1536 MiB reserve, and a provisional 2048 MiB app budget. The Staging inventory remains empty. A read-only audit using `aldoawp` confirmed the fixed inventory-path variable and required secret names in both Environments; no secret values were accessed by that audit. The live target and host-key checks passed, but the independent admin-key login failed. Before retrying, review the new key-pair preflight and keep the initial password secret available until admin access is proven.

## GitHub Environment protection audit

Read-only metadata was checked using `aldoawp` on 2026-11-01; no Environment settings were changed and no secret values were accessed.

- `Production` has a required reviewer, accepts `release/*`, and has administrator bypass disabled.
- `Staging` has the fixed required-reviewer gate, allows self-review and administrator bypass, and has no branch restriction.
- Staging has `ANSIBLE_INVENTORY_PATH=inventories/staging/hosts.yml`; Production has `ANSIBLE_INVENTORY_PATH=inventories/production/hosts.yml`. Both Environments contain the secret names `VPS_INITIAL_ACCESS_PASSWORD` and `ANSIBLE_SSH_PRIVATE_KEY`. Secret values were not accessed, and their correctness for the host remains an operator confirmation.

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
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/manage-deploy-test-key.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/prove-deploy-key.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/enable-fail2ban-test.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/disable-fail2ban-test.yml
ansible-lint \
  playbooks/bootstrap.yml \
  playbooks/prove-admin-key.yml \
  playbooks/harden-ssh.yml \
  playbooks/manage-deploy-test-key.yml \
  playbooks/prove-deploy-key.yml \
  playbooks/enable-fail2ban-test.yml \
  playbooks/disable-fail2ban-test.yml \
  roles/
```

The first install is controller-only. Do not set provider credentials or connect to a VPS while validating syntax or inventories.

## Adding a host and verifying its SSH pin

1. Provision the host manually and confirm its Ubuntu Server 24.04 LTS image and initial SSH username in the Sumopod console.
2. Generate a new environment-specific Ed25519 admin key pair on a trusted workstation. Commit only its public half to that Environment's `group_vars/all.yml`; set `ANSIBLE_SSH_PRIVATE_KEY` in the matching GitHub Environment to `base64:` plus a single-line Base64 encoding of the complete unencrypted private-key file. For example, from WSL/Linux, pipe `{ printf 'base64:'; base64 -w0 "$HOME/.ssh/cdo-admin"; }` to `gh secret set ANSIBLE_SSH_PRIVATE_KEY --repo Buzilion/CentralDevOps --env Production`. The workflow also accepts raw private-key text for compatibility. Base64 is encoding, not encryption; treat the value as the private key. The workflow rejects a passphrase-protected key because it has no passphrase secret. Do not reuse the disposable VPS key on a service host.
3. Use the host alias format `<environment-code>-<purpose>-<two-digit-number>`, such as `stg-aio-01`. Add the exact alias to only its own `hosts.yml` and add a corresponding `host_vars/<alias>.yml` with `ansible_host`, `provider_username`, optional non-default `ansible_port`, `physical_memory_mib`, `platform_reserve_mib`, `capacity_budget_mib`, and either `ssh_source_cidrs` or a documented `ssh_source_policy_exception`. For the user-authorized Production proof target, use `prd-disposable-01` and set `bootstrap_disposable: true`; do not use that alias for Production services.
4. Measure physical RAM and reserve enough for the platform services. The initial reference values are Staging 2048/1024/1024 MiB (physical/reserve/app budget) and Production 4096/1536/2560 MiB. Lower the budget when measurements require it; the validator rejects a budget above physical memory minus reserve or the environment reference ceiling.
5. From an operator-controlled workstation, collect a candidate host key with `ssh-keyscan` if needed. Use `ssh-keygen -lf` to inspect its fingerprint and compare it with the independently displayed fingerprint in the Sumopod console. A scan is only a way to collect a candidate; it is not a trust source. Add the candidate to the selected `known_hosts` file only after the fingerprints match. For non-default SSH ports, use the exact OpenSSH endpoint format `[host]:port`.
6. Require a stable SSH source allowlist only when it permits the selected runner to connect. GitHub-hosted runner egress is not stable. If no compatible stable CIDR exists, leave the host's CIDR list empty and record the per-host exception and its remediation trigger. Never apply a rule that strands the active access path.
7. Review the inventory change. Do not commit provider passwords, private keys, placeholder addresses, or unverified host-key material.

The secret-free preflight validates the fixed Environment-to-inventory mapping, exact host membership, alias format, public admin key, source-policy decision, RAM budget, and the host-key pin before any SSH command. It does not scan for or accept a new host key. After Environment approval and before any SSH connection, a separate local check derives the public key from `ANSIBLE_SSH_PRIVATE_KEY` and compares it with the selected inventory key; a mismatch fails before host mutation. Before any mutating role runs, the bootstrap playbook also checks the observed memory against the configured reserve and application budget.

## Bootstrap sequence

Dispatch `.github/workflows/bootstrap-vps.yml` with only:

- `target_environment`: exactly `Staging` or `Production`
- `target_host`: one exact alias from that Environment's inventory

The workflow rejects non-branch refs, rejects Production refs outside `release/*`, and checks the dispatch App actor before its Environment-bound job. The preflight job has no Environment association or credentials. The credential job rechecks the Environment's `ANSIBLE_INVENTORY_PATH` against the fixed code mapping; Production approval occurs before the job can receive secrets.

Before the SSH phases, the Environment-bound job validates the private/public admin-key pair locally. It writes the private key to a runner temporary file, derives only its public half, compares the key type and material with the selected inventory value, and removes the file. An invalid, mismatched, unreadable, or passphrase-protected key stops the workflow before the VPS is changed.

If this check fails, do not retry initial access yet. Verify the public half of the private key you stored in the selected Environment and compare it with `bootstrap_admin_public_key`; update the secret or reviewed inventory key so they are a matching pair. If a valid key passes Ubuntu `ssh-keygen` locally but fails when supplied as a multiline secret, store the same file with the `base64:` prefix described above. Never paste or log the private key or its Base64 form.

The phases run in separate Ansible processes with SSH multiplexing disabled:

1. **Initial access:** use the provider username from `host_vars` and the selected Environment's `VPS_INITIAL_ACCESS_PASSWORD`. Create `cdo-admin` with the explicit home `/home/cdo-admin` and `cdo-deploy`, update packages, enable automatic security updates, and apply UFW. Install the admin public key at `/home/cdo-admin/.ssh/authorized_keys` and read it back to assert that the reviewed key is present before ending this phase. SSH authentication policy is unchanged. Ansible tasks using the initial connection are marked `no_log`; the password is read from the step environment and is never passed in argv or written to a runner file.
2. **Independent admin-key proof:** after the provider session ends, use the `cdo-admin` key in a new SSH process and assert the remote identity is exactly `cdo-admin`. Password and keyboard-interactive methods are disabled for this proof.
3. **Credential cleanup:** only after that proof succeeds, the workflow displays an operator notice to remove `VPS_INITIAL_ACCESS_PASSWORD` from the selected Environment. If the proof fails, the workflow stops before this notice and before hardening.
4. **SSH hardening:** the hardening playbook performs its own fresh admin-key identity check before running the hardening role. The role writes the SSH drop-in, validates the complete effective sshd configuration and required effective settings, and reloads SSH only after validation. If validation fails, it restores the prior drop-in and fails without reporting a successful reload.
5. **Post-hardening proof:** a new Ansible/SSH process confirms `cdo-admin` key access again. If it fails, do not report the host ready; use the Sumopod console recovery procedure and investigate before retrying.
6. **Disposable-only fail2ban proof:** for an explicitly flagged disposable alias, the workflow generates a temporary Ed25519 key for `cdo-deploy`, installs it without recording the private key, and proves fresh admin and deploy sessions before enabling fail2ban. It then verifies the SSH jail is active and probes both access paths every minute for the 120-second policy window. The temporary deploy key is removed at the end. If a probe fails, the workflow attempts to disable/remove fail2ban and remove the test key; if cleanup cannot connect, use the Sumopod console to confirm fail2ban is stopped and the key is removed. Successful testing leaves fail2ban active only on the disposable host; the default remains disabled for all normal bootstrap runs.

`run_bootstrap_phase.py` writes the admin private key only to a runner temporary file with owner-only permissions and removes it in an unconditional cleanup path. The local key-pair check passes neither secret value to its `ssh-keygen` child process; Ansible receives only a temporary file path during SSH phases. Do not enable shell tracing or upload runner files.

The base UFW policy allows the configured SSH port, TCP 80/443, and outbound traffic; it denies other unsolicited inbound traffic. It does not open PostgreSQL, application, or Docker API ports. A reboot-required marker is reported for an operator-controlled reboot; bootstrap never reboots automatically.

## Disposable VPS proof and cleanup

The first Production attempt on `release/test-bootstrap` ([run 41277668347](https://github.com/Buzilion/CentralDevOps/actions/runs/41277668347)) passed the protected preflight and connected to `prd-disposable-01` with the committed host-key pin. Initial bootstrap completed with 21 successful tasks and 10 changes; the admin-key installation task reported `changed`, the Ubuntu 24.04 check passed, and Ansible observed 3723 MiB RAM. The fresh `cdo-admin` login then failed as unreachable. The task's `no_log` setting censored the SSH error, so the exact authentication cause cannot be established from that run. The operator has since confirmed the private/public key pair and reports finding an empty `authorized_keys` file, but the account/home path inspected is not yet confirmed. If it is `/home/cdo-admin/.ssh/authorized_keys`, the key-placement step is the likely cause; the current fix branch now sets that path explicitly and verifies the key before continuing. No credential-cleanup notice or SSH-hardening phase ran. Keep `VPS_INITIAL_ACCESS_PASSWORD` in the selected Environment and do not treat this host as ready. The host is now mutated by the successful initial-access phase. The 1536 MiB reserve and 2048 MiB app budget remain provisional until platform baseline use is measured.

After PR #13 was merged, four later dispatches on `release/test-bootstrap` (runs 41294676263, 41295964087, 41296203909, and 41296528648) failed in the local admin-key validation step with `admin SSH private key is unreadable, invalid, or passphrase-protected`. The bootstrap and SSH steps were skipped, so these runs made no VPS changes and did not test the `authorized_keys` path. The operator confirms the key pair is correct; because this workflow requires an unencrypted OpenSSH private key, a passphrase-protected key or unsupported private-key encoding remains a likely explanation. The new follow-up code reports this case explicitly without logging the key.

Use a separate temporary admin key for the proof, and record only sanitized evidence. For the user-authorized `buz-prod-1` candidate, the Production workflow must run from `release/*` and pass the required reviewer gate:

1. Recheck that the provider-console fingerprint and committed host-key pin match before dispatch. The user reported a match on 2026-11-01; repeat the comparison if the host is reprovisioned or its SSH host key changes.
2. Run the workflow for `target_environment=Production` and `target_host=prd-disposable-01`; verify provider access, account/group/sudo state, updates, UFW exposure, admin-key login, successful hardening, post-hardening admin login, and refusal of root/password/keyboard-interactive access.
3. Force the admin-key proof to fail. Confirm the hardening role does not run and provider access remains available.
4. Try an unknown target, an alias from the other Environment, an invalid alias pattern, and a mismatched host key. Each must fail before an unintended SSH connection or key acceptance.
5. Record whether a stable runner-compatible SSH source CIDR exists; otherwise record the host-specific exception and remediation trigger.
6. Measure physical RAM and platform service memory use. Confirm or lower the reserve and budget and record the evidence for spec 06.
7. Let the disposable-only workflow phase generate and install a temporary deploy key, verify fresh admin and deploy sessions, enable fail2ban, and probe both paths every minute for the 120-second policy window. The workflow removes the test key and attempts fail2ban rollback if a probe fails. Confirm the final service and key state from the run output; if rollback or key removal cannot connect, use the Sumopod console and keep the spec blocked.
8. After successful independent admin-key verification, remove the temporary password secret. Remove the disposable admin-key secret, test public key, alias, host facts, and host pin. Because the user intends to use this VPS for Production later, reimage or restore it to a clean Ubuntu Server 24.04 state before service use, then add it under a normal Production service alias with a fresh Production admin key. Do not reuse the disposable password or key. Record the tested commit and evidence, then set `DISPOSABLE_VPS_PROOF_COMMIT` to that full 40-character commit SHA in a reviewed change; until that change is reviewed, service-host bootstrap remains blocked.

## GitHub Environment audit

Read-only GitHub metadata was checked on 2026-11-01. No Environment setting was changed and no secret value was requested.

- The repository has exactly `Staging` and `Production`.
- `Production` has a required reviewer, administrator bypass disabled, and a `release/*` deployment-branch policy.
- `Staging` has the fixed required-reviewer gate and no branch restriction. Self-review and administrator bypass are allowed in the current GitHub configuration.
- The read-only audit using `aldoawp` confirmed `ANSIBLE_INVENTORY_PATH` values `inventories/staging/hosts.yml` and `inventories/production/hosts.yml`, plus the required secret names in both Environments. No secret values were accessed.

## Evidence log

Record one row after each real disposable-host run. Never record passwords, private keys, or secret values.

| Date/time | Operator | Host alias | Commit SHA | Workflow run URL | Phase outcomes | Observed inbound ports | Physical RAM / reserve / budget | Source-policy result or exception |
|---|---|---|---|---|---|---|---|---|
| 2026-11-01 05:45 UTC | workflow_dispatch | `prd-disposable-01` | `fe7ed018b5dccd973a1326b0e42c0fd4c5a13edc` | [41277668347](https://github.com/Buzilion/CentralDevOps/actions/runs/41277668347) | Preflight, pinned SSH, and initial bootstrap passed; key-install task reported changed; fresh `cdo-admin` login failed; operator later reported an empty authorized_keys file (account/home not confirmed); cleanup/hardening not reached | Not externally scanned; UFW tasks completed | 3723 / 1536 / 2048 MiB (reserve/budget provisional) | Documented exception; no stable runner CIDR |
| 2026-11-01 09:47 UTC | workflow_dispatch | `prd-disposable-01` | `7ec83ea273cc3c2e94e615e1ca5e8944250ff45b` | [41294676263](https://github.com/Buzilion/CentralDevOps/actions/runs/41294676263) | Admin private-key preflight failed before SSH; no VPS changes | N/A (no SSH) | N/A (preflight only) | N/A (no SSH) |
| 2026-11-01 10:06 UTC | workflow_dispatch | `prd-disposable-01` | `7ec83ea273cc3c2e94e615e1ca5e8944250ff45b` | [41295964087](https://github.com/Buzilion/CentralDevOps/actions/runs/41295964087) | Admin private-key preflight failed before SSH; no VPS changes | N/A (no SSH) | N/A (preflight only) | N/A (no SSH) |
| 2026-11-01 10:09 UTC | workflow_dispatch | `prd-disposable-01` | `7ec83ea273cc3c2e94e615e1ca5e8944250ff45b` | [41296203909](https://github.com/Buzilion/CentralDevOps/actions/runs/41296203909) | Admin private-key preflight failed before SSH; no VPS changes | N/A (no SSH) | N/A (preflight only) | N/A (no SSH) |
| 2026-11-01 10:13 UTC | workflow_dispatch | `prd-disposable-01` | `7ec83ea273cc3c2e94e615e1ca5e8944250ff45b` | [41296528648](https://github.com/Buzilion/CentralDevOps/actions/runs/41296528648) | Admin private-key preflight failed before SSH; no VPS changes | N/A (no SSH) | N/A (preflight only) | N/A (no SSH) |

## Acceptance audit

Acceptance audit updated on 2026-11-01. The first release-branch run passed the target and host-key checks, verified Ubuntu 24.04 and 3723 MiB RAM, and completed the initial-access play. Its fresh `cdo-admin` login failed and `no_log` hid the SSH error. Four later runs failed before SSH because the key-validation step could not load the Environment private key with an empty passphrase; initial access was skipped. The operator confirms the key pair is correct and reports an empty authorized_keys file, but has not confirmed that it is cdo-admin's actual home. The follow-up branch writes and verifies the key at an explicit path and reports passphrase errors clearly. Local validation on Windows with Python 3.12 used fixtures under `TestRepo-Application`; 52 tests ran, 49 passed, and 3 platform-specific integration tests were skipped. The GitHub name checker, YAML parsing for changed files, and `git diff --check` passed. PR CI run [41298016405](https://github.com/Buzilion/CentralDevOps/actions/runs/41298016405) passed both checks; `workflow-lint` includes actionlint, zizmor, Ansible inventory/syntax/lint, and Linux integration tests. A reviewed, Production-approved rerun remains necessary; no secret values were accessed from the local CLI. The Production reserve and app budget remain provisional, and Task 6/7 acceptance is incomplete.

| Requirement | Local status | Evidence or remaining gate |
|---|---|---|
| H-01 | LIVE PARTIAL | Initial access completed (21 tasks, 10 changes); the key-install task reported changed, but the operator later reported an empty authorized_keys file (account/home path unconfirmed). The fresh admin-key proof failed, so the host is not ready and the temporary password must remain. |
| H-02 | LIVE PASS FOR SELECTED TARGET | The protected release run validated the fixed Production inventory and exact `prd-disposable-01` target before connecting; Staging isolation negative cases remain untested live. |
| H-03 | LIVE PASS FOR PINNED KEY | The initial SSH connection succeeded with strict checking and the committed Production host-key pin; mismatched-pin negative cases remain local-only. |
| H-04 | BLOCKED | The initial independent `cdo-admin` proof failed as unreachable. Four later runs stopped before SSH because the private key could not be loaded with an empty passphrase. The operator confirms the key pair is correct; verify whether the GitHub secret is passphrase-protected and confirm the exact cdo-admin authorized_keys path. Explicit placement/read-back validation and passphrase diagnostics passed PR CI; review and a protected rerun remain. Keep the initial password secret. |
| H-05 | BLOCKED | The proof gate correctly prevented SSH hardening; post-hardening login and root/password refusal tests were not run. |
| H-06 | LIVE PARTIAL | UFW tasks completed during bootstrap; effective inbound exposure and outbound policy have not been independently audited. |
| H-07 | LIVE PASS FOR SELECTED TARGET | The production address, provider username, alias, and Environment mapping were used from the fixed inventory. Staging separation remains locally tested; no cross-Environment live attempt was made. |
| H-08 | LIVE PASS FOR VALID PIN | The pinned host key was accepted during initial access. Missing/mismatched pin rejection remains covered only by local fixtures. |
| H-09 | LIVE PARTIAL | Production dispatch from `main` was rejected by the `release/*` rule ([run 41277470379](https://github.com/Buzilion/CentralDevOps/actions/runs/41277470379)); the subsequent release run reached the protected credential job. Staging reviewer behavior remains as previously audited. |
| H-10 | BLOCKED | The workflow stopped before the password-removal notice. Keep `VPS_INITIAL_ACCESS_PASSWORD` configured until an independent admin-key proof succeeds. |
| H-11 | LOCAL PASS; LIVE BLOCKED | The tested host is explicitly disposable. Service-host bootstrap remains blocked until disposable acceptance evidence is recorded and `DISPOSABLE_VPS_PROOF_COMMIT` is reviewed. |
| H-12 | LOCAL GATE READY; LIVE BLOCKED | Fail2ban remains out of initial bootstrap and disabled by default. Its admin/deploy access-path test and rollback behavior have not run on the VPS. |
| H-13 | LIVE PARTIAL | Ansible observed 3723 MiB and the configured reserve-plus-budget guard passed. The reserve 1536 MiB and app budget 2048 MiB remain provisional until platform baseline use is measured. |
