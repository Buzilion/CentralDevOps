# 04 — Idempotency, handlers, and convergence

## Learning objectives

You can distinguish idempotency from mere repeatability, use handlers for change-triggered service actions, recognize resources that need validation or special sequencing, and interpret Ansible's changed/ok/failed results.

## Idempotency is a property of the desired operation

An idempotent operation can be applied more than once while leaving the system in the same intended state. For example, “ensure package X is installed” should not install it again on every run. Ansible modules often express this naturally through state parameters such as `present`, `absent`, `started`, and `enabled`.

The goal is **convergence**: if actual state differs from the declared state, a run makes the intended correction; if it already matches, another run has no unexplained changes. This makes safe repeat runs possible and gives a way to detect accidental manual drift.

Ansible cannot make arbitrary commands idempotent automatically. For example, a task that appends a line on every run, creates a new user each time, or downloads an unpinned “latest” artifact may change the host repeatedly. Prefer dedicated modules (`lineinfile`, `blockinfile`, `user`, `get_url`, and others) with explicit state and validation. For a one-time command, define a reliable guard and explain why it is safe. Avoid blanket `changed_when: false`; it can create a green-looking run that hides ongoing changes.

## Changed state and handlers

Ansible modules report whether they changed a resource. A task can notify a **handler** only when it reports a change. Handlers usually run at the end of a play and are deduplicated, so multiple edits can trigger one service reload:

```yaml
tasks:
  - name: Install reviewed service configuration
    ansible.builtin.template:
      src: service.conf.j2
      dest: /etc/example/service.conf
      owner: root
      group: root
      mode: "0644"
      validate: "/usr/sbin/exampled --check-config %s"
    notify: Reload example service

handlers:
  - name: Reload example service
    ansible.builtin.service:
      name: example
      state: reloaded
```

This is a pattern, not a command to install or manage a service on the VPS. Use the service's actual validation command and reload semantics. Confirm that the daemon supports reload; a service that requires restart needs a deliberate downtime/recovery plan. A handler runs after tasks complete, so validation should occur before replacing a live config whenever the module supports a `validate` argument. If a change needs immediate application before later tasks, `meta: flush_handlers` is available, but use it only when the ordering requirement is understood.

Service reloads and restarts are side effects. Make sure handlers target exactly the intended service, avoid notifying them on irrelevant changes, and validate their behavior on a disposable target or during a controlled window.

## Interpreting the recap

Typical result categories include:

- `ok`: the task ran and reported no change.
- `changed`: the module reports that it changed the target.
- `failed`: a task did not complete as required.
- `unreachable`: Ansible could not establish or maintain the connection.
- `skipped`: a condition or tag excluded the task.

A nonzero `changed` count is not automatically a defect: the first convergence is expected to modify an unconfigured host. An unexplained change on a second equivalent run is a signal to investigate. An `ok` result is not necessarily proof of correctness if custom conditions falsely suppress change reporting or a module is unable to observe the desired state.

## Knowledge check

1. What evidence demonstrates convergence rather than a successful one-time run?
2. What causes a handler to run, and why is it better than restarting after every task?
3. Why should a configuration file be validated before reload?
4. How can an incorrect `changed_when` make automation less trustworthy?

## Practical checkpoint

Complete [Task 03 — Build and verify an idempotent baseline playbook](../tasks/03-build-and-verify-an-idempotent-baseline-playbook.md), then use the repeated-run evidence in Task 07.
