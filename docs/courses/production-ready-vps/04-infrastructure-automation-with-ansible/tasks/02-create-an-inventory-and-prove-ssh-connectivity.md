# Task 02 — Create an inventory and prove SSH connectivity

## Outcome

Create an explicit project-local inventory for the intended VPS and prove Ansible can connect as the expected non-root user without disabling SSH host-key verification.

## Prerequisites

- Read [Lessons 02 and 06](../lessons/02-inventory-host-groups-and-variable-design.md) and [SSH, privilege escalation, and least privilege](../lessons/06-ssh-privilege-escalation-and-least-privilege.md).
- Complete Task 01 and have an approved SSH key, account, and recovery path from Subject 2.

## Procedure

1. Create a project-local Ansible configuration and inventory directory. Configure only deliberate project defaults; verify the active file path with `ansible --version`.
2. Add one host alias and one purpose-specific group. Store the connection address and non-secret SSH user in a local or access-controlled inventory. Do not store private-key contents, passwords, or a production vault password there.
3. Add the verified VPS host key to the controller's `known_hosts` using a trusted fingerprint. Do not set `host_key_checking = False` or use SSH options that bypass verification.
4. Inspect inventory structure and target selection:

   ```sh
   ansible-inventory -i inventory/production/hosts.yml --graph
   ansible production --list-hosts -i inventory/production/hosts.yml
   ```

5. Run the Ansible ping module against the single intended alias using the selected SSH account and key:

   ```sh
   ansible app_vps -i inventory/production/hosts.yml -m ansible.builtin.ping
   ```

   Confirm it returns `pong`, which demonstrates Ansible module connectivity over SSH. Run a fact-gathering command only if authorized, and inspect only the minimum required facts.
6. Confirm the login account is non-root. Separately verify whether it can use the approved `sudo` policy; do not add broad privileges merely to make a connectivity test succeed.
7. Record sanitized commands and outcomes. Keep raw inventory, IPs, hostnames, usernames, verbose SSH traces, and fact dumps private.

## Acceptance criteria

- [ ] Inventory graph contains only the expected host and group.
- [ ] `--list-hosts` matches the intended VPS before any playbook is applied.
- [ ] SSH authentication succeeds with host-key verification enabled.
- [ ] The connection uses the expected non-root account and no private-key material is in the repository.
- [ ] The Ansible ping result is correctly understood as module connectivity, not an ICMP or application health test.
- [ ] Inventory and config do not silently select a different environment.

## Deliverable

A project-local, credential-free inventory structure plus sanitized connection evidence. Keep actual endpoint details in an appropriately protected local inventory if the repository should not disclose them.
