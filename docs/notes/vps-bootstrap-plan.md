# VPS Bootstrap Workflow Implementation Plan

> **Superseded planning note:** This plan predates the current workflow and inventory structure. Development now runs locally on developer workstations; VPS bootstrap and deployment target staging and production only. Treat the development-target steps below as historical and use [bootstrap-vps-v3.md](../requirements/01/bootstrap-vps-v3.md) and [requirement_01_feedback_v2.md](../feedback/requirement_01_feedback_v2.md) for current environment decisions.

## Problem and proposed approach

This plan captures an earlier proposal for a GitHub Actions-to-Ansible VPS bootstrap. Its original first target was a development VPS; that decision is superseded. Development runs locally, while VPS bootstrap and deployment target staging and production.

## Confirmed requirements and planning assumptions

- Runner: GitHub-hosted Ubuntu runner.
- Initial target: one approved staging or production inventory host, reported as Ubuntu 24.04.
- Authentication: a dedicated SSH private key stored as a GitHub Actions secret.
- Trigger: manual `workflow_dispatch`.
- Bootstrap scope: propose a minimal, idempotent baseline; agree on exact packages/tasks before implementation.
- Keep host-key verification enabled. Do not put private keys in the repository or disable SSH host verification.
- Do not make firewall, SSH daemon, user/account, or OS-upgrade changes in the initial baseline. Do not execute any mutating test until the user explicitly authorizes the VPS run.

## Repository state recorded when this plan was drafted

- `.github/workflows/bootstrap-vps.yml`: empty.
- `ansible/ansible.cfg`: empty.
- `ansible/playbooks/bootstrap.yml`: empty.
- The inventory plan included a development VPS; current inventories target staging and production only.
- `README.md`: project description only; no setup or test instructions.
- The Customer Builder Engine inventory currently has a local worktree change; preserve it and verify its target mapping.

## Plan and step-by-step test gates

1. **Agree on the safe baseline and target**
   - Verify that the selected staging or production inventory entry is the intended, authorized Ubuntu 24.04 VPS and that a recoverable snapshot/backup is available.
   - Set the initial baseline to low-risk, idempotent package prerequisites only (for example, apt cache refresh and an explicitly reviewed small package list). Exclude OS upgrades, firewall and SSH changes, account changes, application deployment, and rebooting.
   - Decide the GitHub environment/reviewer gate for the mutating run. Keep execution manual, scoped to the selected staging or production target, and default to a non-mutating/check path where feasible.

2. **Implement Ansible configuration and playbook**
   - Fill `ansible/ansible.cfg` with repository-relative inventory/roles paths and useful, safe defaults; avoid disabling host-key checking or hiding errors.
   - Implement `ansible/playbooks/bootstrap.yml` with an explicit target group, privilege escalation, supported Ubuntu target assumptions, and the agreed minimal idempotent tasks.
   - Keep host-specific values in inventory or variables rather than embedding credentials or environment-specific assumptions in the playbook.

3. **Implement the manual GitHub Actions workflow**
   - Fill `.github/workflows/bootstrap-vps.yml` with `workflow_dispatch`, least-privilege workflow permissions, a GitHub-hosted Ubuntu runner, and explicit working-directory/path handling.
   - Install a controlled Ansible version, load the dedicated SSH key from a GitHub secret without logging it, and provide independently verified SSH host keys. Keep strict host-key checking enabled.
   - Target only a selected staging or production inventory group. Separate connectivity/preflight from applying changes; require an explicit input and/or protected GitHub environment approval for mutation.
   - Do not automatically add broad inbound SSH access to accommodate GitHub-hosted runner networking. If the VPS only permits fixed source IPs, stop and reassess the runner/network design.

4. **Test workflow and Ansible offline (no VPS connection)**
   - Parse/lint the workflow and YAML files; run Ansible configuration and inventory parsing/listing.
   - Run `ansible-playbook --syntax-check` against the selected staging or production inventory and inspect the resolved target list.
   - Review workflow permissions, secret handling, host-key handling, playbook arguments, environment gates, and default non-mutating behavior.
   - Fix any validation failures before proceeding.

5. **Test the GitHub Actions runner itself**
   - Push the reviewed workflow to a test branch or approved branch and manually dispatch a preflight-only run.
   - Confirm GitHub schedules it on the intended GitHub-hosted Ubuntu runner; verify checkout, Ansible installation/version, working directory, and inventory/playbook paths.
   - Confirm secrets are present without printing their values and that failure paths fail visibly rather than appearing successful.

6. **Test VPS SSH access from that runner (non-mutating)**
   - Configure the dedicated private key as a GitHub Actions secret and verified host-key material through an appropriately protected secret/variable.
   - From the GitHub-hosted runner, test SSH authentication and Ansible `ping` against only the selected staging or production host. Verify the expected host identity and `ubuntu` account, then run check mode where supported.
   - If connection fails, diagnose key/authorized-key, host-key, sudo, or firewall/network causes. Do not weaken host verification or expose SSH broadly; if runner IP restrictions block access, reassess before changing network controls.

7. **Run the guarded end-to-end VPS test**
   - Confirm backup/snapshot, exact planned changes, recovery access, and explicit user authorization. Use the protected environment/reviewer gate if configured.
   - Dispatch the workflow manually in non-mutating/check mode first and review the complete diff/change plan.
   - Only after approval, dispatch the mutating run against the selected staging or production target. Verify task results and VPS access/services after completion.
   - Run the same playbook again and verify idempotency (no unexpected changes). Record the tested workflow/ref and result before considering staging/production scope.

## Important considerations

- GitHub-hosted runner outbound IP addresses are not a stable single address. Confirm the VPS's SSH ingress policy before the connectivity test; never solve this by opening SSH indiscriminately.
- Confirm the inventory target is correct before each real run. Preserve the current Customer Builder Engine inventory worktree change while verifying its target aliases.
- Ansible check mode is not a perfect simulation for every module; inspect its output and retain a separate explicit approval before applying changes.
- Development VPS rollout is out of scope. Any staging or production rollout must follow the current bootstrap requirements and approval gates.
