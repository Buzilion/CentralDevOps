# 02 — Inventory, host groups, and variable design

## Learning objectives

You can build a small, explicit inventory; group hosts by purpose; separate reusable defaults from environment-specific values; and identify where Ansible variables come from and which sources take precedence.

## Inventory is both targeting and connection data

Inventory describes the machines Ansible can address and organizes them into groups. It can be static YAML or INI, generated dynamically, or supplied by a plugin. For a first VPS, a static inventory is easier to audit. Use a stable alias rather than repeating a raw address in every command:

```yaml
all:
  children:
    production:
      hosts:
        app_vps:
          ansible_host: 203.0.113.20
          ansible_user: automation
          ansible_ssh_private_key_file: ~/.ssh/vps_automation
```

The address above is a documentation-only example. Replace it locally with the actual connection target; do not publish identifying server details if the repository is public. Keep private key material outside the project tree. Do not set `ansible_ssh_common_args` to disable host-key checking. Verify the VPS host-key fingerprint through a trusted provider console or other independent channel before accepting it.

Common patterns include groups for environment (`production`, `staging`), function (`web`, `database`), or platform. Keep grouping meaningful. If a group contains one server, it is still useful when it makes intent obvious, but avoid a complicated hierarchy for a single VPS.

Useful inspection commands include:

```sh
ansible-inventory -i inventory/production/hosts.yml --graph
ansible-inventory -i inventory/production/hosts.yml --list
ansible production --list-hosts -i inventory/production/hosts.yml
```

Inventory output can disclose addresses, usernames, and configuration. Inspect it locally and redact it before sharing.

## Variables and precedence

Variables parameterize desired state. Put broadly useful, non-sensitive defaults in role defaults; environment-specific choices in `group_vars`; exceptional host-specific values in `host_vars`; and task inputs close to the tasks that need them. Keep variable names descriptive and namespaced by role where collisions are possible, such as `base_timezone` or `docker_daemon_options`.

Ansible has many variable sources and a defined precedence order. Some inputs—especially extra variables passed with `-e`—can override values that an operator expected to be authoritative. This flexibility can also make behavior difficult to reason about. Prefer a small number of explicit sources and document intentional overrides. Before a change, inspect effective values using a safe debug or inventory command that does not print secrets.

A useful separation is:

- **Role defaults:** conservative, overridable values that make the role usable.
- **Group variables:** environment-wide choices such as a selected timezone or package list.
- **Host variables:** rare, documented exceptions.
- **Vault-encrypted variables:** secret values, never ordinary plaintext vars.
- **Command-line overrides:** deliberate short-lived overrides, recorded in the run evidence.

Do not place secrets in `ansible.cfg`, inventory, ordinary `group_vars`/`host_vars`, shell history, or `-e password=...`. Variables are not secret just because their name includes `secret`.

## Keep configuration local and understandable

A project directory often contains a project-local `ansible.cfg`, an inventory, playbooks, roles, and `group_vars`. Ansible searches for configuration according to its rules and may ignore a config in a world-writable current directory for security. Verify the active configuration with `ansible --version`; do not assume the file you edited is in use. Avoid changing shared machine-wide configuration to make a project work.

Use one inventory per environment or a clearly documented inventory source. Explicitly pass `-i` in learning and production commands until the project invocation is unambiguous. Never let a production playbook silently default to a broad or stale inventory.

## Knowledge check

1. What is the difference between an inventory host alias and its `ansible_host` address?
2. Why should production host selection be previewed before execution?
3. What makes a role default different from a group variable?
4. Why can a `-e` override make an otherwise reviewed run unsafe?

## Practical checkpoint

Complete [Task 02 — Create an inventory and prove SSH connectivity](../tasks/02-create-an-inventory-and-prove-ssh-connectivity.md).
