# 03 — Playbooks, modules, facts, and execution

## Learning objectives

You can read the play/task structure, prefer declarative modules over ad hoc shell commands, use gathered facts deliberately, and run a playbook in a controlled sequence from syntax check through execution.

## A playbook describes work and target scope

A playbook is YAML containing one or more plays. A play selects inventory hosts and may set connection behavior, fact gathering, variables, and privilege escalation. Its tasks invoke modules to move resources toward a declared state:

```yaml
---
- name: Apply reviewed baseline
  hosts: production
  become: true
  gather_facts: true
  tasks:
    - name: Ensure a reviewed baseline package is installed
      ansible.builtin.package:
        name: "{{ base_required_packages }}"
        state: present
```

This illustrates structure only. `base_required_packages` must be defined, reviewed for the target distribution, and appropriate to the host before this example can be run. A playbook is not safe merely because its YAML parses.

Prefer fully qualified collection names, such as `ansible.builtin.package`, over short ambiguous module names. Modules understand resources and desired states: packages can be `present`, a service can be `started` and `enabled`, a file can have a specific owner and mode. These operations communicate intent and are generally easier to make repeatable than shell snippets.

Use `ansible.builtin.command` for a command that genuinely has no suitable module; it does not interpret shell operators or pipes. Use `ansible.builtin.shell` only when shell behavior is required and inputs are controlled. A command that reports success may still make a different change each time. Where supported, use `creates` or `removes` with `command`/`shell` tasks, and define `changed_when`/`failed_when` to match the command's real behavior. These controls affect execution or reporting; they do not make an operation safe or reversible. For example, `changed_when: false` on a mutating command hides its changed status, so repeated work can look like a no-op; it does not, by itself, change whether a nonzero exit fails the task.

## Facts and conditionals

Facts are information gathered from a managed host, such as distribution, release, interfaces, memory, or CPU data. They can select a platform-specific task or validate assumptions. Facts are observations at run time, not desired state. For example, check the target distribution before running Ubuntu-specific package or service configuration; stop explicitly if a playbook is not designed for that platform.

Gather only the facts needed for the work. Be cautious about logging or publishing full fact output: it can reveal addresses, hostnames, mount points, and other operational details. A condition based on facts should be understandable and tested on each supported OS release.

## A disciplined command sequence

From the project root, use the same explicit inventory and playbook path throughout:

```sh
ansible --version
ansible-inventory -i inventory/production/hosts.yml --graph
ansible production --list-hosts -i inventory/production/hosts.yml
ansible-playbook -i inventory/production/hosts.yml playbooks/site.yml --syntax-check
ansible-playbook -i inventory/production/hosts.yml playbooks/site.yml --check --diff
```

These commands answer different questions:

- `--version` shows the executable, Python environment, and config-file path.
- Inventory inspection displays defined targets.
- `--list-hosts` previews the hosts matched by a pattern.
- `--syntax-check` checks basic playbook parsing and structure; it does not connect or validate every runtime behavior.
- `--check` asks supported modules to predict changes without applying them.
- `--diff` displays proposed file changes for modules that support it.

Check mode is not a transaction or a complete simulation. Some modules do not support it fully; dependent tasks may not behave as they would during a real run. Diff output can expose secret values. Review both limitations before using these options.

After preflight, a live invocation should use the narrowest valid host limit and an understood privilege policy. Read the final recap and task output; resolve failed or unexpectedly changed results rather than repeating the command blindly.

## Knowledge check

1. Why is a package module usually preferable to a shell command that invokes a package manager?
2. What do syntax check, check mode, and diff each tell you?
3. Why are facts not equivalent to declared desired state?
4. When can `changed_when: false` hide a real problem?

## Practical checkpoint

Complete [Task 03 — Build and verify an idempotent baseline playbook](../tasks/03-build-and-verify-an-idempotent-baseline-playbook.md).
