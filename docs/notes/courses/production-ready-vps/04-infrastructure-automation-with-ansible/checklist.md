# Infrastructure Automation with Ansible — Course Checklist

Complete this subject after **Linux Server Administration**, **Networking, DNS, and Firewall Security**, and **Docker and Container Operations**. The intended server state must already be understood and tested manually before it is automated. Ansible should encode a reviewed baseline, not conceal unknown changes. Keep recovery access available whenever a play can affect SSH, firewall rules, users, storage, or the container runtime. Never commit credentials, vault passwords, private keys, or identifying VPS details.

## Lessons

- [ ] [01 — Ansible architecture: control nodes and managed hosts](lessons/01-ansible-architecture-control-nodes-and-managed-hosts.md)
- [ ] [02 — Inventory, host groups, and variable design](lessons/02-inventory-host-groups-and-variable-design.md)
- [ ] [03 — Playbooks, modules, facts, and execution](lessons/03-playbooks-modules-facts-and-execution.md)
- [ ] [04 — Idempotency, handlers, and convergence](lessons/04-idempotency-handlers-and-convergence.md)
- [ ] [05 — Roles, templates, and reusable configuration](lessons/05-roles-templates-and-reusable-configuration.md)
- [ ] [06 — SSH, privilege escalation, and least privilege](lessons/06-ssh-privilege-escalation-and-least-privilege.md)
- [ ] [07 — Protecting secrets with Ansible Vault](lessons/07-protecting-secrets-with-ansible-vault.md)
- [ ] [08 — Safe rollouts, drift, validation, and recovery](lessons/08-safe-rollouts-drift-validation-and-recovery.md)

## Hands-on tasks

- [ ] [Task 01 — Document the manual baseline and prepare the control node](tasks/01-document-the-manual-baseline-and-prepare-the-control-node.md)
- [ ] [Task 02 — Create an inventory and prove SSH connectivity](tasks/02-create-an-inventory-and-prove-ssh-connectivity.md)
- [ ] [Task 03 — Build and verify an idempotent baseline playbook](tasks/03-build-and-verify-an-idempotent-baseline-playbook.md)
- [ ] [Task 04 — Refactor configuration into roles and a validated template](tasks/04-refactor-configuration-into-roles-and-a-validated-template.md)
- [ ] [Task 05 — Encrypt and safely use Ansible secrets](tasks/05-encrypt-and-safely-use-ansible-secrets.md)
- [ ] [Task 06 — Apply the reviewed baseline to the VPS safely](tasks/06-apply-the-reviewed-baseline-to-the-vps-safely.md)
- [ ] [Task 07 — Prove idempotence, drift correction, and fresh-host reproducibility](tasks/07-prove-idempotence-drift-correction-and-fresh-host-reproducibility.md)

## Subject completion gate

- [ ] I can explain which work happens on the control node and which changes happen on each managed host.
- [ ] Inventory and variables identify intended hosts and desired state without storing plaintext credentials or relying on hidden global configuration.
- [ ] The playbook uses supported Ansible modules and fully qualified collection names where appropriate; shell commands are limited to cases that need them.
- [ ] A second run reports no unintended changes, and any remaining `changed` result has a documented reason.
- [ ] Reusable configuration is organized into roles with clear defaults, tasks, handlers, templates, and ownership.
- [ ] Privilege escalation is explicit, SSH host identity is verified, and the automation account's access is understood.
- [ ] Sensitive variables are encrypted at rest or retrieved from an approved secret manager; vault passwords and private keys are kept outside the repository.
- [ ] Syntax, target selection, check/diff output, and a limited live run are reviewed before broad execution.
- [ ] A change that can disrupt SSH, firewall, storage, or Docker has an independently tested recovery path and a controlled rollout plan.
- [ ] A deliberate harmless drift test converges back to the declared state; no destructive cleanup is used as a substitute for state management.
- [ ] A fresh or disposable host can reach the same documented baseline using the checked-in automation and its documented prerequisites.
- [ ] All seven task deliverables are stored as sanitized operations evidence; no secret values or raw identifying logs are included.

## Exit criteria

Continue to **CI/CD with GitHub Actions** only when the playbook has configured the intended VPS safely, a second run is effectively a no-op, and the baseline can be reproduced on a disposable host or the limitation is explicitly recorded. Keep application build and release delivery in the CI/CD subject: Ansible owns host configuration, not the application's release pipeline. If a manual setting or recovery procedure is unknown, investigate and document it before automating it.
