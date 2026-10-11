# 05 — Roles, templates, and reusable configuration

## Learning objectives

You can organize a small automation project, explain what belongs in a role, render a template with explicit ownership and permissions, and keep role behavior testable and reviewable.

## From a playbook to roles

A playbook is a useful orchestration entry point. As related tasks grow, a **role** groups reusable defaults, variables, tasks, handlers, files, templates, and metadata:

```text
ansible/
  ansible.cfg
  inventory/
    production/hosts.yml
  playbooks/
    site.yml
  roles/
    base/
      defaults/main.yml
      tasks/main.yml
      handlers/main.yml
      templates/
```

The exact layout can vary, but conventional role structure makes ownership easier to find. A top-level playbook can sequence small roles:

```yaml
- name: Configure the reviewed VPS baseline
  hosts: production
  become: true
  roles:
    - base
```

Keep responsibilities cohesive: a base role might manage explicitly selected common settings, while SSH, firewall, and Docker behavior belong in separate roles when their lifecycle and risk justify it. Do not split every task into a role. Too many abstractions make a one-host configuration harder to understand.

Role defaults should be safe and overridable. A role should state its supported platforms and required variables, avoid silently inventing passwords or opening ports, and fail clearly when a required decision is absent. Avoid global mutable variables and hidden dependencies between roles. If a later role needs an earlier service, make the ordering and prerequisite explicit.

Collections provide namespaced modules and roles. Record external collections in a dependency manifest such as `requirements.yml`, pin reviewed versions, and install them into a predictable location. Do not install dependencies during every playbook run without a deliberate reason.

## Templates are managed artifacts

Jinja templates render host configuration from variables. A template should contain only the settings the role owns, with conditions and defaults that are easy to review. Use the `template` module to state destination, owner, group, and mode explicitly. Remember YAML's parsing of numbers: quote file modes, such as `"0640"`, to avoid unexpected numeric interpretation.

If the service offers a syntax-validation command, use the module's `validate` option with the temporary file placeholder. A validation command should check the rendered candidate before it replaces the destination. Verify the actual command and behavior for the target program; validating one file alone may not detect conflicts with included configuration elsewhere.

Avoid templating a whole vendor-owned configuration file when a supported drop-in exists. Replacing an entire file can discard distribution defaults or future package changes. Keep templates free of secret values unless there is a compelling, reviewed need; protected Ansible variables are preferable to embedding credentials.

## Files, ownership, and handlers

The `copy` and `template` modules can set explicit owner, group, and mode. For secret-bearing files, restrict access to the service account and root as required by the runtime. A file with correct content but overly broad permissions is still a security defect.

Use handlers for validation-backed reloads or restarts only after confirming the service operation and impact. The role should not restart unrelated services or conceal a failed validation. On a first run, use a disposable host or a non-critical file to prove the template and handler behavior before managing a production service.

## Knowledge check

1. What responsibilities belong in the playbook versus a role?
2. Why should templates set owner and mode explicitly?
3. How can whole-file templating conflict with package-managed defaults?
4. What does a `validate` command protect against, and what might it still miss?

## Practical checkpoint

Complete [Task 04 — Refactor configuration into roles and a validated template](../tasks/04-refactor-configuration-into-roles-and-a-validated-template.md).
