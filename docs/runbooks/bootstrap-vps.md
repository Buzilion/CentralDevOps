# VPS Bootstrap and Hardening Runbook

## Scope and gates

This runbook applies only to one fresh Ubuntu Server 24.04 LTS VPS in the selected `Staging` or `Production` GitHub Environment. Provision the VPS manually in Sumopod; this repository does not create hosts through a provider API.

The user confirmed on 2026-10-31 that their Sumopod Ubuntu target is 24.04 and available to connect. On 2026-11-01, the user authorized using the empty VPS labeled `buz-prod-1` as the disposable proof target before it carries Production service data. It is represented by the alias `prd-disposable-01`. The user reset the VPS on 2026-11-02; it is reachable on SSH port 22, and the provider firewall permits port 4671. Any fingerprint or live pin verification from before the reset is historical and must not be trusted for the reset host. Re-verify the current fingerprint in the provider console before updating either known-hosts endpoint or connecting. The earlier image confirmed Ubuntu 24.04 and observed 3723 MiB physical RAM; the 1536 MiB reserve and 2048 MiB app budget remain provisional until platform baseline use is measured.

Do not run the protected workflow until all of these are true:

- The selected inventory has the exact host alias, `bootstrap_initial_ssh_port: 22`, final `ansible_port: 4671`, `bootstrap_managed_ssh_port: 4671`, its reviewed host facts, a public admin key, capacity facts, and current independently verified host-key pins for both endpoints.
- The selected Environment's `ANSIBLE_SSH_PRIVATE_KEY` contains `base64:` followed by a single-line Base64 encoding of the complete unencrypted private-key file, and matches the reviewed inventory public key. The controller requires this format, decodes and normalizes CRLF to LF, and validates it before SSH.
- For a fresh/reset host, port 22 must accept the provider's initial SSH login and the provider firewall must permit TCP 4671. The workflow temporarily configures sshd/UFW for both ports, proves a fresh admin-key login on 4671, then finalizes sshd/UFW to 4671 only. Already-managed hosts remain on 4671 and must not be moved back to 22.
- After final sshd/UFW finalization and a fresh 4671 admin-key login, the operator removes provider-firewall TCP 22 and verifies externally that 4671 is reachable and 22 is closed. Provider firewall settings are not managed by Ansible.
- The Staging or Production Environment has `ANSIBLE_INVENTORY_PATH` set to its matching fixed inventory path: `inventories/staging/hosts.yml` for Staging, `inventories/production/hosts.yml` for Production. Set it with the GitHub CLI or repository settings; never accept an operator-supplied path.
- The dispatch App numeric actor ID has been proven by spec 02 and recorded in `deployment/tools/bootstrap_inventory.py` (`350767931`). Preflight rejects that actor before binding an Environment.
- Until disposable-host proof is recorded, only a host with a `disposable` alias purpose and boolean `bootstrap_disposable: true` passes target validation. For `buz-prod-1`, dispatch the Production environment using `prd-disposable-01`; Production still requires a `release/*` ref and its required reviewer approval. Record the proof commit in `DISPOSABLE_VPS_PROOF_COMMIT` before allowing service-host targets.
- Production approval and `release/*` deployment-branch protection remain enabled.
- Because the VPS was reset after the prior password-secret cleanup, set `VPS_INITIAL_ACCESS_PASSWORD` in Production to the current provider initial-access password before the run. The workflow consumes it only for the port-22 initial-access phase; remove it again after a fresh `cdo-admin` key login on port 22 succeeds.
- The admin private-key secret belongs to the selected Environment and contains only the `base64:`-prefixed encoding of the unencrypted private-key file.

The Production inventory contains the user-authorized `prd-disposable-01` candidate with 3723 MiB RAM observed on the previous image, a provisional 1536 MiB reserve, and a provisional 2048 MiB app budget. The Staging inventory remains empty. A read-only audit using `aldoawp` confirmed the fixed inventory-path variable and required secret names in both Environments; no secret values were accessed. Because the VPS was reset, the previous host-key pin and earlier access evidence do not establish trust for the current image. Update both host-key endpoints only after comparing the new key fingerprint with the provider console.

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
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/finalize-ssh-port.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/manage-deploy-test-key.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/prove-deploy-key.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/enable-fail2ban-test.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/disable-fail2ban-test.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/enable-fail2ban.yml
ansible-playbook --inventory inventories/staging/hosts.yml --syntax-check playbooks/disable-fail2ban.yml
ansible-lint \
  playbooks/bootstrap.yml \
  playbooks/prove-admin-key.yml \
  playbooks/harden-ssh.yml \
  playbooks/finalize-ssh-port.yml \
  playbooks/manage-deploy-test-key.yml \
  playbooks/prove-deploy-key.yml \
  playbooks/enable-fail2ban-test.yml \
  playbooks/disable-fail2ban-test.yml \
  playbooks/enable-fail2ban.yml \
  playbooks/disable-fail2ban.yml \
  roles/
```

The first install is controller-only. Do not set provider credentials or connect to a VPS while validating syntax or inventories.

## Adding a host and verifying its SSH pin

1. Provision the host manually and confirm its Ubuntu Server 24.04 LTS image and initial SSH username in the Sumopod console.
2. Generate a new environment-specific Ed25519 admin key pair on a trusted workstation. Commit only its public half to that Environment's `group_vars/all.yml`; set `ANSIBLE_SSH_PRIVATE_KEY` to `base64:` followed by a single-line Base64 encoding of the complete unencrypted private-key file. For example, from WSL/Linux: `{ printf 'base64:'; base64 -w0 "$HOME/.ssh/cdo-admin-production"; } | gh secret set ANSIBLE_SSH_PRIVATE_KEY --repo Buzilion/CentralDevOps --env Production`. Do not pass the secret with `--body`, print it, or store raw private-key text in the secret. Base64 is encoding, not encryption; treat the encoded value as the private key. The runner decodes it, normalizes CRLF to LF, and rejects values without the `base64:` prefix. The workflow rejects a passphrase-protected key because it has no passphrase secret. Do not reuse the disposable VPS key on a service host.
3. Use the host alias format `<environment-code>-<purpose>-<two-digit-number>`, such as `stg-aio-01`. Add the exact alias to only its own `hosts.yml` and add a corresponding `host_vars/<alias>.yml` with `ansible_host`, `bootstrap_initial_ssh_port: 22`, final `ansible_port: 4671`, `provider_username`, `physical_memory_mib`, `platform_reserve_mib`, `capacity_budget_mib`, and either `ssh_source_cidrs` or a documented `ssh_source_policy_exception`. Set `bootstrap_managed_ssh_port: 4671` in the Environment's group variables. For fresh/reset hosts, keep provider TCP 22 available for initial access and permit provider TCP 4671 before bootstrap. For the user-authorized Production proof target, use `prd-disposable-01` and set `bootstrap_disposable: true`; do not use that alias for Production services.
4. Measure physical RAM and reserve enough for the platform services. The initial reference values are Staging 2048/1024/1024 MiB (physical/reserve/app budget) and Production 4096/1536/2560 MiB. Lower the budget when measurements require it; the validator rejects a budget above physical memory minus reserve or the environment reference ceiling.
5. After a reset, collect a candidate host key from port 22 with `ssh-keyscan -p 22` if needed. Use `ssh-keygen -lf` to inspect its fingerprint and compare it with the fingerprint displayed independently in the Sumopod console. A scan is only a candidate, not a trust source. After the fingerprint matches, add the same verified host key under both `host` (initial port 22) and `[host]:4671` in the selected `known_hosts` file. Once sshd is listening on 4671, confirm the key served there matches the verified fingerprint. Never trust a new key based only on the scan.
6. Require a stable SSH source allowlist only when it permits the selected runner to connect. GitHub-hosted runner egress is not stable. If no compatible stable CIDR exists, leave the host's CIDR list empty and record the per-host exception and its remediation trigger. Never apply a rule that strands the active access path.
7. Review the inventory change. Do not commit provider passwords, private keys, placeholder addresses, or unverified host-key material.

The secret-free preflight validates the fixed Environment-to-inventory mapping, exact host membership, alias format, initial port 22 and final port 4671, both host-key pins, public admin key, source-policy decision, and RAM budget before any SSH command. It does not scan for or accept a new host key. After Environment approval and before any SSH connection, a separate local check decodes the `base64:`-prefixed `ANSIBLE_SSH_PRIVATE_KEY` value, derives the public key, and compares it with the selected inventory key; a mismatch fails before host mutation. Before any mutating role runs, the bootstrap playbook also checks the observed memory against the configured reserve and application budget.

## Bootstrap sequence

Dispatch `.github/workflows/bootstrap-vps.yml` with only:

- `target_environment`: exactly `Staging` or `Production`
- `target_host`: one exact alias from that Environment's inventory

The workflow rejects non-branch refs, rejects Production refs outside `release/*`, and checks the dispatch App actor before its Environment-bound job. The preflight job has no Environment association or credentials. The credential job rechecks the Environment's `ANSIBLE_INVENTORY_PATH` against the fixed code mapping; Production approval occurs before the job can receive secrets.

Before the SSH phases, the Environment-bound job validates the private/public admin-key pair locally. It writes the private key to a runner temporary file, derives only its public half, compares the key type and material with the selected inventory value, and removes the file. An invalid, mismatched, unreadable, or passphrase-protected key stops the workflow before the VPS is changed.

If this check fails, do not retry initial access yet. Verify that the Environment secret uses the exact `base64:` prefix and a single-line encoding of the complete unencrypted private-key file. Derive the public key from the original local key file and compare it with `bootstrap_admin_public_key`; update the secret or reviewed inventory key so they are a matching pair. The controller reports malformed Base64, mismatched keys, and passphrase-protected keys before SSH. Never paste or log the private key or its encoded value.

The phases run in separate Ansible processes with SSH multiplexing disabled:

1. **Initial access on port 22:** use the provider username from `host_vars` and the selected Environment's `VPS_INITIAL_ACCESS_PASSWORD`. Create `cdo-admin` with the explicit home `/home/cdo-admin` and `cdo-deploy`, update packages, enable automatic security updates, and apply UFW rules allowing both 22 and 4671. Install the admin public key at `/home/cdo-admin/.ssh/authorized_keys` and read it back to assert that the reviewed key is present. SSH authentication policy is unchanged. Ansible tasks using the initial connection are marked `no_log`; the password is never passed in argv or written to a runner file.
2. **Independent admin-key proof on port 22:** after the provider session ends, use the `cdo-admin` key in a new SSH process on port 22 and assert the remote identity is exactly `cdo-admin`. Password and keyboard-interactive methods are disabled for this proof.
3. **Credential cleanup:** only after that proof succeeds, the workflow displays an operator notice to remove `VPS_INITIAL_ACCESS_PASSWORD` from the selected Environment. If the proof fails, the workflow stops before this notice and before hardening.
4. **Dual-listener hardening:** the hardening playbook performs its own fresh admin-key identity check on 22. The role writes a key-only SSH drop-in with `Port 22` and `Port 4671`, validates the complete effective sshd configuration and both listeners, then reloads SSH only after validation. If validation fails, it restores the prior drop-in.
5. **First 4671 proof:** start a new SSH process using the `cdo-admin` key on port 4671 and verify identity. If it fails, stop; sshd/UFW still preserve port 22. Do not finalize or claim the host is ready.
6. **Port finalization:** over a fresh 4671 admin-key connection, configure sshd with `Port 4671` only, validate and reload, remove the managed UFW rule for port 22, then prove a new 4671 login. If SSH config validation fails, the previous dual-listener drop-in is restored and UFW 22 remains. After the final 4671 proof succeeds, manually remove the provider-firewall TCP 22 rule and verify externally that 4671 works and 22 does not.
7. **Disposable-only Fail2ban proof:** after port finalization and provider-firewall cleanup, for an explicitly flagged disposable alias, generate a temporary Ed25519 key for `cdo-deploy`, install it without recording the private key, and prove fresh admin/deploy sessions before enabling Fail2ban. Verify the SSH jail is active on 4671 with `bantime=1d`, `findtime=1h`, and `maxretry=2`; probe both access paths every minute for the 120-second policy window. Remove the temporary deploy key afterward. If a probe fails, attempt Fail2ban rollback and test-key removal; if cleanup cannot connect, use the Sumopod console. Successful testing leaves Fail2ban active only on the disposable host.
8. **Managed-host Fail2ban activation:** after the disposable proof commit is recorded, each non-disposable host enables the same policy in a separate exact-host phase after hardening and a fresh admin-key proof. Verify a fresh admin login after activation; if activation or proof fails, attempt to stop/disable Fail2ban and remove the managed jail. If rollback cannot reconnect, use the Sumopod console. Fail2ban remains disabled by default; do not activate service hosts while the proof gate is unset.

`run_bootstrap_phase.py` writes the admin private key only to a runner temporary file with owner-only permissions and removes it in an unconditional cleanup path. The local key-pair check passes neither secret value to its `ssh-keygen` child process; Ansible receives only a temporary file path during SSH phases. Do not enable shell tracing or upload runner files.

The initial UFW policy allows SSH TCP 22 and 4671, TCP 80/443, and outbound traffic while default-denying other unsolicited inbound traffic. Port 22 remains open until the fresh 4671 key proof passes; finalization removes the UFW 22 rule. The operator then closes provider-firewall port 22. PostgreSQL, application, and Docker API ports are not opened. A reboot-required marker is reported for an operator-controlled reboot; bootstrap never reboots automatically.

## Disposable VPS proof and cleanup

The first Production attempt on `release/test-bootstrap` ([run 41277668347](https://github.com/Buzilion/CentralDevOps/actions/runs/41277668347)) passed the protected preflight and connected to `prd-disposable-01` with the then-committed host-key pin. Initial bootstrap completed with 21 successful tasks and 10 changes; the admin-key installation task reported `changed`, the Ubuntu 24.04 check passed, and Ansible observed 3723 MiB RAM. The fresh `cdo-admin` login then failed as unreachable. The task's `no_log` setting censored the SSH error, so the exact authentication cause cannot be established from that run. The operator later confirmed the private/public key pair and reported finding an empty `authorized_keys` file, but the inspected account/home path was not confirmed. No credential-cleanup notice or SSH-hardening phase ran. The host has since been reset; these results and the prior pin do not describe the current image. The 1536 MiB reserve and 2048 MiB app budget remain provisional until platform baseline use is measured.

After PR #13 was merged, four later dispatches on `release/test-bootstrap` (runs 41294676263, 41295964087, 41296203909, and 41296528648) failed in the local admin-key validation step with `admin SSH private key is unreadable, invalid, or passphrase-protected`. The bootstrap and SSH steps were skipped, so these runs made no VPS changes and did not test the `authorized_keys` path. These runs predate the reset and do not establish current host state. The key must remain unencrypted; current controller code reports parse/passphrase errors without logging the key.

Use a separate temporary admin key for the proof, and record only sanitized evidence. The reset invalidates prior live host-key verification. For the user-authorized `buz-prod-1` candidate, the Production workflow must run from `release/*` and pass the required reviewer gate:

1. Re-verify the reset VPS host-key fingerprint in the provider console. Compare a port-22 candidate key with the independent console fingerprint, then update both the port-22 hostname and `[host]:4671` known-host entries. Do not rely on the pre-reset fingerprint or committed pin.
2. Confirm initial SSH on port 22 and provider-firewall access to 4671. Set `bootstrap_initial_ssh_port: 22`, final `ansible_port: 4671`, and the selected Environment's initial password secret. Run the protected Production workflow from `release/*`; verify provider access, account/group/sudo state, updates, UFW allowing both ports, and the admin-key proof on 22.
3. Confirm sshd is temporarily key-only on both 22 and 4671; prove a fresh admin-key login on 4671. Finalize sshd/UFW to 4671 only over that fresh 4671 connection and prove another new admin-key login. If the first 4671 proof fails, leave both listeners and the port-22 firewall rule available.
4. After the final 4671 proof, manually close provider-firewall TCP 22. From an authorized external network verify that 4671 is reachable and 22 is closed; do not mark acceptance until this is confirmed.
5. Force the initial admin-key proof to fail. Confirm dual-listener hardening and port finalization do not run and provider port 22 remains available.
6. Try an unknown target, an alias from the other Environment, an invalid alias pattern, and a missing/mismatched pin for either endpoint. Each must fail before an unintended SSH connection or key acceptance.
7. Record whether a stable runner-compatible SSH source CIDR exists; otherwise record the host-specific exception and remediation trigger. Measure physical RAM and platform service memory use, confirm or lower the reserve/budget, and record the evidence for spec 06.
8. After port finalization and provider-firewall cleanup, let the disposable-only workflow generate and install a temporary deploy key, verify fresh admin and deploy sessions on 4671, enable Fail2ban, confirm `bantime=1d`, `findtime=1h`, `maxretry=2` and the SSH jail port, then probe both paths every minute for the 120-second policy window. The workflow removes the test key and attempts Fail2ban rollback if a probe fails. Confirm final service/key state; use the Sumopod console if rollback or key removal cannot connect.
9. After successful independent admin-key verification, remove the temporary password secret. Remove the disposable admin-key secret, test public key, alias, host facts, and both host-key pins. Before future Production service use, configure the VPS under a normal Production service alias with a fresh Production admin key. Do not reuse disposable credentials. Record the tested commit and evidence, then set `DISPOSABLE_VPS_PROOF_COMMIT` to that full 40-character commit SHA in a reviewed change; until then, service-host bootstrap remains blocked.

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

## Pre-reset acceptance audit (historical)

The successful run and failed attempts below occurred before the 2026-11-02 VPS reset; they do not prove the reset image's host key, access paths, listeners, firewall, or account state. The earlier confirmed fingerprint must be rechecked through the provider console. The current staged 22-to-4671 workflow and post-reset proof have not yet been run. No secret values were accessed by the local CLI. The Production reserve and app budget remain provisional, and Task 6/7 acceptance is incomplete.

| Requirement | Local status | Evidence or remaining gate |
|---|---|---|
| H-01 | PRE-RESET ONLY; RESET PROOF PENDING | Historical initial access ran on the prior image, but the host has since been reset. Re-run the complete staged bootstrap and verify account/key state on the current image. |
| H-02 | PRE-RESET PASS; RESET RUN PENDING | The protected release run validated the exact Production target before connecting on the prior image. Re-run preflight and staged bootstrap against the reset image; Staging isolation negative cases remain untested live. |
| H-03 | RESET PIN PENDING | The old image accepted its committed pin, but reset may have rotated the host key. Re-verify out-of-band and pin both port-22 and `[host]:4671` endpoints before dispatch. |
| H-04 | RESET PROOF PENDING | The prior image's independent admin-key proof failed. Re-run the port-22 initial proof on the reset image; if it fails, stop before hardening and retain/recover initial access. |
| H-05 | BLOCKED | The proof gate correctly prevented SSH hardening; post-hardening login and root/password refusal tests were not run. |
| H-06 | STAGED CODE; RESET PROOF PENDING | First bootstrap allows both ports, proves 4671 before finalization, and removes 22 from sshd/UFW. The operator must close provider port 22 after final 4671 proof; the reset image has not run this flow. |
| H-07 | RESET PORT TRANSITION PENDING | Inventory declares initial 22 and managed 4671. Verify both phases on the reset image. |
| H-08 | RESET PINS PENDING | Both endpoints are required in preflight. Re-verify the current host key through the console; the old pin does not establish trust after reset. |
| H-09 | LIVE PARTIAL | Production dispatch from `main` was rejected by the `release/*` rule ([run 41277470379](https://github.com/Buzilion/CentralDevOps/actions/runs/41277470379)); the subsequent release run reached the protected credential job. Staging reviewer behavior remains as previously audited. |
| H-10 | RESET CREDENTIAL LIFECYCLE PENDING | Configure the reset VPS's initial-access secret for the protected run, then remove it only after a fresh admin-key proof on port 22 succeeds. No secret values were accessed. |
| H-11 | LOCAL PASS; LIVE BLOCKED | The tested host is explicitly disposable. Service-host bootstrap remains blocked until disposable acceptance evidence is recorded and `DISPOSABLE_VPS_PROOF_COMMIT` is reviewed. |
| H-12 | CODE GATE IMPLEMENTED; LIVE BLOCKED | Fail2ban remains disabled by default. The 1d/1h/two-retry policy and exact-host activation path require disposable-host proof on port 4671 before service-host use. |
| H-13 | PRE-RESET PARTIAL | Ansible observed 3723 MiB on the previous image and the reserve-plus-budget guard passed. Recheck capacity on the reset image; the 1536 MiB reserve and 2048 MiB app budget remain provisional. |
