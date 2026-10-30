# Spec 03: Host Bootstrap and Hardening

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 03 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation is gated by spec 01 |
| Depends on | `01_foundation-and-access` |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/infrastructure-v1.md` (`INF`); `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`) |
| Design | `docs/design/naming-and-repository-conventions.md` §§3, 7–8; `docs/design/variables-and-secrets.md` §§1–4, 9–10; `docs/design/infrastructure-contracts-and-invariants.md` §§4–6; v5 design §§4.2–4.4, 5.1, 6.1, 12.1, 15.1, 16 step 3 |

## What

Create the reviewed foundation for a new Ubuntu VPS: per-Environment Ansible inventories and pinned SSH host keys, a one-host-at-a-time bootstrap operation, and a staged transition from the provider's temporary password to independent admin-key access. Bootstrap creates separate `cdo-admin` and `cdo-deploy` accounts, applies updates and a base firewall, and installs the admin public key. SSH root and password login are disabled only after a fresh key-based login succeeds. The transition is proven on a disposable VPS before it is used on either real Environment.

This spec does not configure Docker, application runtime, proxy, database, monitoring, or deployment services. It creates no VPS through an API; VPS creation remains a manual Sumopod-console operation.

## Context and sequencing

- The roadmap requires spec 01 to be fully checked off before spec 03 implementation starts. Its checklist must be complete before any task here is executed.
- The roadmap's `Depends on` entry for spec 03 is spec 01. Follow the roadmap's numeric order as well: spec 02 establishes the dispatch App identity. Task 5 cannot be accepted until that identity is proven and its numeric actor ID is available; if it is not, fail closed rather than omit the rejection check.
- The initial host OS target is Ubuntu Server 24.04 LTS. Confirm Sumopod offers this image before provisioning; do not silently substitute another release.
- Environments are exactly `Staging` and `Production`; each has a separate VPS and inventory. Host aliases follow `<env>-<purpose>-<number>`, for example `stg-aio-01` and `prd-aio-01`.
- `VPS_INITIAL_ACCESS_PASSWORD` is a temporary CentralDevOps Environment secret for one target VPS at a time. The provider username is an inventory fact. Never put the password in a workflow input, inventory, variable, file, log, or artifact.
- Production's GitHub Environment approval must happen before the job that receives Production secrets starts. Every SSH connection, including the first password-based one, uses a host-key pin verified against the independent provider-console fingerprint.
- Do not add fabricated host facts or sample host-key material. Add real host inventory only when a host is provisioned and its facts and key have been independently verified.

## Requirements

| ID | Statement | Source |
|---|---|---|
| H-01 | An operator can bootstrap exactly one fresh VPS in the selected Environment using the provider username from that Environment's inventory and the temporary `VPS_INITIAL_ACCESS_PASSWORD` secret. The operation creates distinct `cdo-admin` and `cdo-deploy` accounts, applies OS updates and a base firewall, and installs the admin public key. | INF-01, SEC-03 |
| H-02 | The bootstrap operation only accepts `Staging` or `Production`, derives its inventory from the selected GitHub Environment, and rejects an unknown host before opening SSH. It cannot reach a host from the other Environment. | INF-01, INF-07, INF-08 |
| H-03 | The first SSH connection uses a committed, reviewed host-key pin and strict checking. The pin is obtained and verified out of band; a fresh `ssh-keyscan` result from the same connection is never trusted. | INF-09 |
| H-04 | A separate SSH process proves that the admin account accepts its installed public key before any hardening task runs. If this check fails, the workflow stops, leaves provider password access enabled, and does not request removal of the temporary password secret. | INF-02, SEC-03 |
| H-05 | Only after H-04 passes does hardening disable root SSH and password/keyboard-interactive authentication. The `cdo-admin` key remains usable and can perform Ansible privilege escalation; `cdo-deploy` remains separate and unprivileged. | INF-02, INF-10, INF-13 |
| H-06 | On Ubuntu Server 24.04 LTS, the base UFW firewall defaults to deny unsolicited inbound traffic and permits only the inventory-declared SSH port plus TCP 80/443. PostgreSQL, app ports, and the Docker API are not opened. Automatic security updates are enabled. | INF-10 |
| H-07 | Inventories, playbooks, roles, and workflows contain no hostnames or addresses that bypass the selected inventory. Each host's address, provider username, SSH port, role groups, private address, and capacity budget are inventory facts. | INF-07, INF-08 |
| H-08 | Every SSH session uses strict host-key checking against `inventories/<environment>/known_hosts`. A mismatched or missing key fails closed. | INF-09 |
| H-09 | Infrastructure operations run on demand only, reject the dispatch GitHub App identity established by spec 02, and require the selected Environment's protections. Production approval precedes access to Production credentials. | INF-14, INF-15 |
| H-10 | The initial-access password is removed from the selected Environment after the independent admin-key login is verified. The operator records the result without recording credentials. | SEC-03 |
| H-11 | No actual Staging or Production service host is hardened until the same bootstrap and access-transition sequence has passed on a disposable VPS and its evidence is recorded. | INF-16 |
| H-12 | A fail2ban (or equivalent) role is delivered disabled by default and enabled on configured hosts only after a disposable-host test demonstrates that it does not block the `cdo-admin` or `cdo-deploy` access paths. | INF-19 |
| H-13 | Every inventory host declares physical RAM and an app-memory budget, with the reserved capacity for platform services accounted for. | INF-20 |

## Deliverables

```text
ansible.cfg
requirements.yml
inventories/
  staging/
    hosts.yml
    known_hosts
    group_vars/all.yml
    host_vars/<host-alias>.yml
  production/                       # same layout
playbooks/bootstrap.yml
roles/
  common/
  users/
  firewall/
  ssh_hardening/
  fail2ban/
.github/workflows/bootstrap-vps.yml
docs/runbooks/bootstrap-vps.md
```

Only files needed for bootstrap and the host baseline are created. Later specs add their own roles and playbooks. Inventory files may start with empty role groups; do not commit fabricated host facts or sample host-key material. `group_vars/all.yml` may contain public keys, never private keys.

## Design

### Inventory and trust

- Keep the two inventory roots fixed at `inventories/staging/hosts.yml` and `inventories/production/hosts.yml`. Trusted workflow code maps the exact Environment choice to its fixed path during secret-free preflight; the Environment-bound job confirms its `ANSIBLE_INVENTORY_PATH` matches that path. The operator cannot supply a path.
- Use one required host alias for bootstrap, not a group or arbitrary Ansible pattern. Validate it as an exact host in the selected inventory and pass it as the sole limit. Reject wildcard syntax, groups, multiple hosts, and aliases not in that inventory before any network operation.
- Keep host-specific facts in `host_vars/<alias>.yml`: `ansible_host`, `ansible_port` when non-default, provider-supplied initial username, stable admin/deploy usernames (`cdo-admin`, `cdo-deploy`), host purpose, physical memory, capacity budget, and any SSH source-policy exception. Do not put passwords, private keys, or secret values there.
- Store the per-Environment admin public key in reviewed inventory data; install only the public key. Admin and deploy keys are distinct. Creation of the deploy public key and its authorized-key restrictions can be completed by the later deploy-runtime spec; this bootstrap must not grant the deploy user admin privileges.
- Before adding a `known_hosts` entry, compare the candidate key's fingerprint with the fingerprint shown in the Sumopod console over an independent channel. Commit only the verified public host key in the selected Environment's file, keyed to the endpoint OpenSSH uses (including `[host]:port` for a non-default port). A workstation `ssh-keyscan` may collect a candidate key but is never itself a trust source; never run it in the workflow to establish trust.
- Configure Ansible/OpenSSH to use the selected `known_hosts` file with `StrictHostKeyChecking=yes`; do not fall back to global or automatically accepted keys. The same policy applies to both login phases.

### Bootstrap and hardening sequence

The workflow performs distinct phases against the same single inventory host:

1. **Preflight:** validate the Environment and exact host alias against the fixed inventory path mapped from the exact Environment choice, ensure the pin exists, install the pinned Ansible/collection dependencies, and reject dispatches from the spec-02 deployment App identity. Preflight must not connect to a host or expose Environment credentials.
2. **Initial access:** the protected Environment-bound job connects using the inventory's provider username and the Environment's temporary password. Create `cdo-admin` with passwordless sudo for Ansible `become`, and create `cdo-deploy` without sudo or Docker access. Apply operating-system updates and the base firewall, then install the admin public key. Do not change SSH authentication policy in this phase.
3. **Independent proof:** end the initial connection and start a fresh Ansible/SSH process using `cdo-admin` and `ANSIBLE_SSH_PRIVATE_KEY`. Require successful authentication and a non-privileged remote identity check. This must be a separate connection, not a task that assumes the first session can become the admin account.
4. **Credential cleanup:** after phase 3 succeeds, promptly tell the operator to delete `VPS_INITIAL_ACCESS_PASSWORD` from the selected GitHub Environment. The workflow does not receive repository-administration permissions to delete it. If phase 3 fails, leave the secret in place until access is recovered and the key check succeeds.
5. **Hardening:** only when phase 3 succeeds, run the SSH hardening role. Set key authentication on; disable root, password, and keyboard-interactive login; validate the candidate sshd configuration before reload; then establish a new admin-key connection to verify it remains usable.
6. **Brute-force protection:** deliver the fail2ban/equivalent role disabled by default. Enable it only after Task 6 proves on the disposable VPS that the policy leaves the admin and deploy SSH paths usable. Re-check the admin path after activation; the disposable test also uses and then removes a temporary deploy test key. Do not harden Staging or Production if the test does not pass.

Do not pass either secret as a workflow dispatch input, command-line argument, generated inventory, artifact, or log output. Mask secrets before use; mark secret-bearing Ansible tasks `no_log`; do not enable shell tracing. The initial password must not be copied to a runner file. If the Ansible connection implementation requires a temporary key file, create it from the admin key only with restrictive permissions, remove it in an unconditional cleanup step, and never upload it. If hardening fails after the independent key proof, use the Sumopod console recovery path; do not retain the initial password as a substitute for recovery.

### Workflow contract

`.github/workflows/bootstrap-vps.yml` is `workflow_dispatch` only and has:

| Input | Contract |
|---|---|
| `target_environment` | Required choice with exact values `Staging` or `Production`; selects the corresponding GitHub Environment and its inventory path/secrets. |
| `target_host` | Required host alias; exact-match validated against the selected inventory before any SSH connection. |

- No profile, inventory path, SSH username, address, or password is operator-selectable.
- Require the workflow ref to be permitted by the selected Environment: any branch for `Staging`, and `release/*` only for `Production`. Reject an invalid Environment/ref combination before the Environment-bound job or any SSH connection.
- Bind the credential-using job to `environment: ${{ inputs.target_environment }}` so Production waits for its required approval before secrets are available. The preflight job has no Environment association; it uses only the fixed input-to-inventory mapping committed in workflow/repository code. Before SSH, the credential-using job fails unless `ANSIBLE_INVENTORY_PATH` for its selected Environment equals the mapped path.
- Make the credential-using job depend on successful preflight and skip it on any failed or invalid preflight result. It checks out the same reviewed commit and installs the exact pinned Ansible dependencies on its own runner before SSH; do not assume jobs share a workspace or installed tools.
- Use `permissions: contents: read` only, pinned checkout action, pinned Ansible/collections, and a supported Ubuntu runner. Do not grant `actions: write` or use `GITHUB_TOKEN` to remove secrets.
- Reject the dispatch App actor resolved by spec 02 before host access. If that identity has not been established, fail closed rather than skipping the check.
- Pass workflow values to scripts through environment variables, validate strict allowlists, and never interpolate dispatch inputs directly into shell.
- Reference `VPS_INITIAL_ACCESS_PASSWORD` only in the initial-access step and `ANSIBLE_SSH_PRIVATE_KEY` only in the independent-proof and hardening steps. Both are scoped to the selected GitHub Environment and are passed only to the steps that need them.
- Add `ANSIBLE_SSH_PRIVATE_KEY` and `VPS_INITIAL_ACCESS_PASSWORD` to the spec-01 name catalog as secrets introduced by this spec if not already present. The deploy workflow's forbidden-reference policy must continue to prohibit both.

### SSH source restriction policy (PRD Q9)

Require SSH source allowlisting at the provider or host firewall whenever there is a stable, known operator/VPN CIDR that also permits the chosen automation runner to connect. GitHub-hosted runner egress is not stable; do not encode a stale runner IP or claim that a user-only allowlist protects automation that cannot use it. If no stable source range is available, document the exception per host and retain key-only SSH after bootstrap, a temporary password only during the initial phase, and tested brute-force protection. Revisit source restriction if the runner/network architecture changes. Never make a firewall change that strands the current session before a verified alternate path exists.

### Capacity policy (PRD Q7)

Use the following initial conservative planning budgets for `capacity_budget_mib`; inventory also records physical RAM. These are app-workload ceilings after reserving memory for platform services:

| Environment | Reference physical RAM | Platform reserve | Initial app budget |
|---|---:|---:|---:|
| Production | 4096 MiB | 1536 MiB | 2560 MiB |
| Staging | 2048 MiB (estimate) | 1024 MiB | 1024 MiB |

The first disposable VPS and the first Staging host must be measured after the platform baseline is installed. If the reserve is insufficient for observed service use, lower the app budget before registry capacity enforcement; do not increase it based solely on nominal provider RAM. Production sizing remains the PRD reference, and the Staging size remains an estimate until confirmed. The memory limits and headroom are reviewed with spec 06, which implements the capacity check.

### Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Bootstrap exactly one inventory host per run. | Allow group or wildcard targets | The Environment password is temporary and may differ per VPS; exact host selection limits the initial credential's blast radius. | Yes |
| D2 | Use separate initial-password, admin-key proof, and hardening phases with fresh SSH connections. | One play/session with privilege escalation | A successful provider login does not prove that the installed admin key works. The hardening gate must be observable and fail closed. | Yes |
| D3 | Require stable SSH source allowlisting when it is compatible with the automation egress; otherwise record a per-host exception and retain key-only controls. | Assume GitHub-hosted runner IPs are static; block SSH from all sources | Runner egress is not stable, while blocking it would prevent the workflow from connecting. | Yes |
| D4 | Start with 2560 MiB Production and 1024 MiB Staging app budgets, with 1536/1024 MiB platform reserves. | Treat all provider RAM as app capacity; wait for spec 06 | These explicit conservative ceilings can be measured and lowered before capacity enforcement. They are planning values, not a claim that the Staging estimate is confirmed. | Yes |
| D5 | The operator removes the initial password secret after successful admin-key proof; the workflow has no secret-administration permission. | Grant workflow `actions: write` and self-delete | Keeping credential cleanup outside the privileged job avoids granting broad administration permission and makes the human cleanup auditable. | Yes |
| D6 | Enable fail2ban or equivalent only after the disposable-host access-path test passes; deliver the role disabled by default. | Enable during the first bootstrap by default | A premature ban can block the only working automation path; this follows INF-19. | Yes |
| D7 | Name the automation accounts `cdo-admin` and `cdo-deploy`; grant only `cdo-admin` passwordless sudo for infrastructure automation. | Generic `admin`/`deploy` usernames; require a sudo password | The names match the environment-specific SSH key identities and align the bootstrap contract with spec 04. Unattended Ansible needs a separate privileged admin identity; the deploy account remains unprivileged. | Yes |
| D8 | Target Ubuntu Server 24.04 LTS. | Accept any provider image version | Pinning the OS release makes Ansible module support, package state, and later Docker installation reproducible. | Yes |
| D9 | Use UFW for the base host firewall, default-deny inbound with only the required ports admitted. | Provider firewall only; hand-written iptables | UFW is the Ubuntu host firewall interface; keep provider-level filtering as an additional control where available. | Yes |

### Invariants

| Invariant | How to check |
|---|---|
| No bootstrap run can resolve a host outside the selected Environment inventory. | Negative test with an alias that exists only in the other inventory; preflight fails before the connection step. |
| No initial password or private key is in inventory, workflow input, log, artifact, or tracked file. | Catalog/name checker and secret-scan tests; inspect a canary run's logs and artifacts. |
| SSH host-key checking is strict for both phases. | Inspect effective Ansible/OpenSSH configuration and run a disposable-host test with an intentionally mismatched pin; connection fails. |
| Hardening cannot run after an unsuccessful admin-key proof. | Force the proof phase to fail on a disposable host; assert the hardening phase is skipped and password access still works. |
| Every hardened host retains admin-key access and refuses root/password SSH. | Fresh post-hardening login tests using admin key and negative tests for root/password login. |
| Deploy identity is distinct and cannot sudo or access Docker; admin has the expected automation privilege. | `id cdo-deploy`, `sudo -l -U cdo-deploy`, `id cdo-admin`, `sudo -n true` as `cdo-admin`, and group-membership checks on the disposable host. |
| No actual Staging or Production service host is hardened before disposable-host evidence is recorded. | Runbook evidence gate and checklist; no service-host execution until Task 6 is accepted. |
| Host budget accounts for platform reserve. | Inventory values and documented measurement evidence; validate `capacity_budget_mib <= physical_memory_mib - reserve_mib`. |

### Error behavior

| Situation | Behavior |
|---|---|
| Spec 01 checklist is not fully complete. | Do not execute this spec's tasks; report the unmet dependency. |
| Spec-02 dispatch App identity is not yet proven or available to the workflow. | Fail closed; do not omit the actor rejection or start host access. |
| Environment is invalid, host alias is absent/ambiguous, or host pin is missing. | Fail preflight before credentials are accessed or SSH is attempted. |
| Host key differs from the committed pin. | Fail closed; do not scan and trust a replacement. Verify the key through the provider console and review the pin change separately. |
| Provider login or bootstrap phase fails. | Stop without changing SSH authentication policy. Preserve the existing access path and report the failing phase without exposing credential material. |
| Admin key login fails. | Stop before hardening; leave provider password access available and retain the temporary secret until the cause is fixed and verification succeeds. |
| sshd config validation fails or post-hardening key login fails. | Fail the run and use the provider console recovery path. Do not report the host ready; record and resolve the incident before retrying. |
| Production approval is not granted. | Credential-using job does not start and no Production secret is available to it. |
| SSH source restriction would block the selected runner. | Do not apply it blindly; record the exception and rely on the controls in D3 pending a compatible network path. |

## Testing strategy

- Validate both inventory files with `ansible-inventory --list`; assert no fixture address, placeholder key, password, or private-key material has been committed.
- Run `ansible-playbook --syntax-check` for `playbooks/bootstrap.yml` and `ansible-lint` against the bootstrap playbook and roles.
- Test workflow YAML with the repository's pinned `actionlint`/`zizmor` checks and the spec-01 naming checker. Confirm a negative fixture for `deploy-app.yml` still rejects both bootstrap-only secrets.
- Test host selection using the chosen inventory: a known host passes; unknown, wildcard, group, malformed, and other-Environment-only aliases fail before SSH.
- On a disposable VPS, test each transition: provider login, account creation, firewall, admin public key, a fresh admin-key login, SSH hardening, a fresh post-hardening admin login, and negative root/password login.
- On a disposable VPS, force the admin-key verification to fail and confirm hardening is skipped and the provider path remains usable.
- Test host-key mismatch failure; test SSH source allowlisting if a stable CIDR is available; test the documented exception otherwise.
- Enable fail2ban only after verifying the `cdo-admin` and `cdo-deploy` paths are not blocked, then observe both paths during the test window.
- Record physical RAM, platform service memory use, reserve, and budget for the disposable and first Staging host. Revise budgets downward if measurements require it.
- Test Production approval behavior without running the playbook: verify the credential-using job is gated by the Production Environment.
- Record evidence without credential values. A successful independent admin-key proof triggers operator removal of `VPS_INITIAL_ACCESS_PASSWORD`; if that proof fails, retain the secret until recovery and a successful proof.

## Out of scope

- VPS creation, snapshots, or provider API automation.
- `configure-vps.yml`, Docker/Compose, networks, `deploy_runtime`, Nginx, Certbot, PostgreSQL, backup and monitoring roles, and `verify-vps.yml`; later specs own these.
- Registry schema and capacity enforcement; spec 06 consumes the inventory budget.
- Separate-host profiles and WireGuard.
- App deploy workflow, deploy key, and app-facing GitHub Environments.
- Production rollout before the disposable-host proof and later go-live gates.
