# CentralDevOps

## Purpose

CentralDevOps is designed to provide shared CI/CD workflows and infrastructure automation for application repositories. It centralizes deployment policy and privileged release execution; deployments use immutable image digests rather than mutable tags.

## Environments

The target model is exactly two GitHub Environments, not one per VPS. The following settings match the API audit completed on 2026-10-31:

| Environment | Configured behavior |
|---|---|
| `Staging` | Requires repository-owner review (self-review allowed); accepts runs from any branch. |
| `Production` | Requires repository-owner approval without administrator bypass; accepts runs from `release/*` branches. |

In the design, each Environment maps to its corresponding deployment target. The current API audit confirms the Staging reviewer gate with no branch restriction and the Production `release/*` gate without administrator bypass. See the [GitHub Environments runbook](docs/runbooks/github-environments.md).

## Documentation

- **Requirements:** [Parent PRD](docs/prd/01_init-cicd_291026/prd-v1.md) · [Access and secrets PRD](docs/prd/01_init-cicd_291026/access-and-secrets-v1.md)
- **Design:** [Naming and repository conventions](docs/design/naming-and-repository-conventions.md) · [Variables and secrets](docs/design/variables-and-secrets.md) · [Infrastructure contracts and invariants](docs/design/infrastructure-contracts-and-invariants.md) · [Source design (v5)](docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md)
- **Specifications:** [Spec roadmap](docs/specs/01_init-cicd_291026/00_spec-roadmap.md) · [Foundation and access spec](docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md)
- **Operations:** [GitHub Environments apply and audit runbook](docs/runbooks/github-environments.md) · [VPS bootstrap runbook](docs/runbooks/bootstrap-vps.md)

## Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `Lint` | Pull requests and pushes to `main` | Checks workflow security and syntax, inventory and Ansible configuration, naming rules, and Python tests. |
| `Bootstrap VPS` | Manual dispatch | Bootstraps one fresh or reset Ubuntu Server 24.04 VPS in the selected GitHub Environment. |

### Bootstrap a VPS

Use the [VPS bootstrap runbook](docs/runbooks/bootstrap-vps.md) for the full phase-by-phase procedure, recovery guidance, and disposable-host requirements. Follow these setup steps in order. The workflow does not provision VPS instances or manage the provider firewall.

1. **Provision the VPS and choose its Environment.** Create one Ubuntu Server 24.04 VPS in the provider console. Record its address, initial SSH username, and initial password. Keep provider-firewall TCP 22 open for initial access and allow TCP 4671 before starting the workflow. Bootstrap one VPS at a time in either the existing `Staging` or `Production` Environment; do not create an Environment per host.

2. **Prepare the environment-specific admin key.** Generate a separate, unencrypted Ed25519 key pair for each Environment on a trusted workstation. The private key must be unencrypted for unattended use; only its public half belongs in the repository. Add that public key as `bootstrap_admin_public_key` in `inventories/<environment>/group_vars/all.yml`. The private half will be stored as an Environment secret in step 4.

3. **Add and review the inventory entry.** Configure only the selected Environment's inventory:

   | File | Required information |
   |---|---|
   | `inventories/<environment>/hosts.yml` | Add the exact host alias under its inventory group. Use that same alias later as `target_host`. |
   | `inventories/<environment>/host_vars/<alias>.yml` | Set `ansible_host`, final `ansible_port: 4671`, `bootstrap_initial_ssh_port: 22`, `provider_username`, observed `physical_memory_mib`, `platform_reserve_mib`, `capacity_budget_mib`, and either `ssh_source_cidrs` or a documented `ssh_source_policy_exception`. Set `bootstrap_disposable: true` only for an authorized disposable proof host. |
   | `inventories/<environment>/group_vars/all.yml` | Set the matching `bootstrap_admin_public_key` and `bootstrap_managed_ssh_port: 4671`. The admin public key must match the private-key secret configured in step 4. |
   | `inventories/<environment>/known_hosts` | Pin the host keys for both the initial port-22 endpoint and `[host]:4671`. First compare the fingerprint with the one shown independently in the provider console. `ssh-keyscan` output is only a candidate; never trust it without that comparison. |

   Use the naming and capacity rules in the runbook. Do not commit provider passwords, private keys, placeholder addresses, or unverified host keys. The workflow enables strict host-key checking, so a missing or mismatched pin stops the run before SSH.

4. **Configure the selected GitHub Environment.** In repository **Settings → Environments → Staging or Production**, set the Environment variable `ANSIBLE_INVENTORY_PATH` to the fixed path for that Environment:

   | Environment | `ANSIBLE_INVENTORY_PATH` |
   |---|---|
   | `Staging` | `inventories/staging/hosts.yml` |
   | `Production` | `inventories/production/hosts.yml` |

   Set the variable in the selected Environment's **Variables** section, or use GitHub CLI:

   ```sh
   gh variable set ANSIBLE_INVENTORY_PATH --repo Buzilion/CentralDevOps --env Staging --body "inventories/staging/hosts.yml"
   gh variable set ANSIBLE_INVENTORY_PATH --repo Buzilion/CentralDevOps --env Production --body "inventories/production/hosts.yml"
   ```

   The workflow reads this path from the selected Environment and rejects a mismatch. It is not a workflow-dispatch input. The workflow also loads the checked-in `ansible.cfg` and installs the pinned Ansible controller and collections on its runner; operators do not need to configure an Ansible executable path to dispatch it.

   Add these **Environment secrets** to the same selected Environment:

   - `ANSIBLE_SSH_PRIVATE_KEY`: the complete unencrypted private key encoded as `base64:` followed by one line of Base64. Prefer piping it directly to `gh` so it is not printed or placed in shell history. Run from the repository root and use the key and Environment that match the inventory:

     **WSL/Linux:**

     ```sh
     set -o pipefail
     cat "$HOME/.ssh/cdo-admin-staging" \
       | python3 deployment/tools/encode_ssh_private_key.py \
       | gh secret set ANSIBLE_SSH_PRIVATE_KEY --repo Buzilion/CentralDevOps --env Staging
     ```

     **Native Windows PowerShell:**

     ```powershell
     cmd.exe /c 'type "%USERPROFILE%\.ssh\cdo-admin-staging" | py -3 deployment\tools\encode_ssh_private_key.py | gh secret set ANSIBLE_SSH_PRIVATE_KEY --repo Buzilion/CentralDevOps --env Staging'
     ```

     For Production, use the Production key filename and `--env Production`. Base64 is encoding, not encryption; treat the encoded value as private-key material. Do not display it, add it to a workflow input, or commit it.

   - `VPS_INITIAL_ACCESS_PASSWORD`: the provider-issued password for this specific VPS. Set it in the selected Environment only when preparing a fresh or reset host. With GitHub CLI, omit `--body` to enter the value at the prompt:

     ```sh
     gh secret set VPS_INITIAL_ACCESS_PASSWORD --repo Buzilion/CentralDevOps --env Staging
     ```

     Use `--env Production` for Production. Never put this password in inventory or a dispatch input. Remove it only after the workflow confirms a fresh `cdo-admin` key login on port 22.

5. **Validate and merge the reviewed configuration.** From the repository root, run the local checks:

   ```sh
   python3 deployment/tools/check-github-names.py
   python3 -m unittest discover -s deployment/tools/tests
   ```

   On Windows, use `py -3` in place of `python3`. Open a pull request and wait for `Lint` to pass; it also validates both inventories, Ansible syntax and lint, and workflow security. Dispatch from a branch that contains the reviewed inventory change.

6. **Dispatch the bootstrap.** In **Actions → Bootstrap VPS → Run workflow**, select a branch reference and provide:

   - `target_environment`: exactly `Staging` or `Production`.
   - `target_host`: the exact alias added to that Environment's `hosts.yml`.

   Staging accepts branch refs and still uses its configured Environment review gate. Production requires a `release/*` branch and reviewer approval. The workflow rejects non-branch refs, an unknown or cross-Environment host alias, an incorrect inventory path, or invalid host/key configuration before making an SSH connection.

7. **Wait for the proofs before closing access.** The workflow validates the target and SSH pins, then checks that the private key matches the reviewed public key before SSH. It uses the initial password for the port-22 bootstrap, proves a new admin-key login on port 22, and notifies you to remove `VPS_INITIAL_ACCESS_PASSWORD`. It then enables both SSH ports, proves a fresh login on 4671, finalizes SSH and the VPS firewall to port 4671 only, and proves another fresh login. **Only after that final 4671 proof succeeds**, remove provider-firewall TCP 22 and verify from outside the provider that 4671 is reachable and 22 is closed. Provider-firewall rules are not managed by Ansible. If a proof fails, stop and follow the runbook; do not remove the remaining access path or retry blindly.

### Lint

`Lint` runs automatically for every pull request and every push to `main`; it has no manual inputs. It checks GitHub Actions syntax and security, workflow naming and secret references, both Ansible inventories, playbook syntax and lint, and the `deployment/tools/tests` suite.

## Future workflows

No application deployment workflow is currently available. When one is added, document its trigger, required inputs, Environment variables and secrets, chronological run steps, verification, and rollback here.

## Repository layout

| Path | Purpose |
|---|---|
| `.github/workflows/` | Current `Lint` and `Bootstrap VPS` GitHub Actions workflows. |
| `inventories/{staging,production}/` | Environment-specific hosts, variables, and pinned SSH host keys. |
| `playbooks/` | Ansible bootstrap, SSH, access-proof, and Fail2ban operations. |
| `roles/` | Reusable host, user, firewall, SSH-hardening, and Fail2ban tasks. |
| `deployment/tools/` | Inventory and workflow validators, SSH-key encoder, phase runners, and tests. |
| `ansible.cfg`, `requirements*.txt`, `requirements.yml` | Ansible defaults and pinned controller dependencies and collections. |
| `docs/runbooks/` | Operator procedures, including the detailed VPS bootstrap runbook. |

## Conventions

- Use lowercase kebab-case for app slugs and descriptive directories; use `SCREAMING_SNAKE_CASE` with subsystem prefixes for variables and secrets.
- Use only the GitHub Environment names `Staging` and `Production`; keep variable and secret names the same in both Environments, with each Environment supplying its own value.
- Deploy by immutable image digest; mutable tags are not deployment inputs.

## Local checks

Run from the repository root:

```sh
python3 deployment/tools/check-github-names.py
python3 -m unittest discover -s deployment/tools/tests
```

On Windows, use `py -3` in place of `python3`.

## Platform assumptions

GitHub's [Environments REST documentation](https://docs.github.com/en/rest/deployments/environments) states that public repositories support Environments, deployment-branch policies, required reviewers, and wait timers on current plans (legacy plans excluded). Private or internal repositories need Pro, Team, or Enterprise for Environment and deployment-branch features, and Enterprise for required-reviewer or wait-timer protection rules.

**Repository-specific status (2026-11-01):** With `GH_TOKEN` unset, `gh repo view Buzilion/CentralDevOps --json nameWithOwner,visibility,viewerPermission` succeeded as `aldoawp` with `PUBLIC` visibility and `ADMIN` permission. The Buzilion organization plan is `Free`. The Environment list is exactly `["Production","Staging"]`; Production requires approval by `aldoawp`, disallows administrator bypass, and accepts only `release/*`. Staging requires the fixed reviewer gate, permits self-review and administrator bypass, and accepts runs from any branch. The current settings are documented in the [GitHub Environments runbook](docs/runbooks/github-environments.md).

Use the [GitHub Environments runbook](docs/runbooks/github-environments.md) to re-audit after any visibility or plan change. Environment protection settings and the active `main`/`release/*` ruleset (ID `26226141`) are verified; the canonical ruleset payload is maintained at `.github/rulesets/main.json`.
