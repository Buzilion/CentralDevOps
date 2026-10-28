# 08 — Safe rollouts, drift, validation, and recovery

## Learning objectives

You can preflight an Ansible change, limit its blast radius, interpret check-mode limitations, distinguish drift correction from rollback, and define a recovery process before applying risky changes.

## Review scope before state

Treat playbooks as privileged change. Before execution:

1. Review the diff and dependencies, including templates, handlers, variables, and collections.
2. Confirm the active Ansible config, inventory, vault identity, and SSH identity.
3. Preview matched hosts with `--list-hosts` and tasks with `--list-tasks`.
4. Run `--syntax-check`; inspect a check-mode result when relevant.
5. Review every file diff and task predicted to change, including whether secrets could appear.
6. Limit the first production application to the intended host and use a planned change window for disruptive work.

An illustrative preflight uses the project's actual paths:

```sh
ansible-playbook -i inventory/production/hosts.yml playbooks/site.yml --syntax-check
ansible-playbook -i inventory/production/hosts.yml playbooks/site.yml --list-hosts
ansible-playbook -i inventory/production/hosts.yml playbooks/site.yml --check --diff --limit app_vps
```

Do not copy a command until its target pattern and inventory are confirmed. `--limit` is a safety aid, not a guarantee: a broad pattern or incorrect inventory can still target an unintended system.

Check mode is module-dependent; it may not model task dependencies or every side effect. A change that can alter SSH, firewall, users, disks, Docker networking, or boot behavior requires stronger evidence than a clean check-mode run. Test on a disposable host first where practical and maintain out-of-band recovery.

## Rollout and change control

Apply changes in small, separable units. Prefer a one-host canary for a single VPS. For multiple hosts, `serial` can limit batches, but set it deliberately and understand handler timing. Avoid making unrelated changes in the same play; if the run fails, you should be able to identify which change caused the failure.

After applying, inspect the recap, service state, expected configuration, listeners, and application behavior relevant to the change. For an SSH change, open a new session. For a firewall change, test from the required source. For Docker, verify the daemon and existing application stack. Keep the previous session or recovery console until checks pass.

## Drift is not rollback

A later Ansible run can converge manually altered state back to its declared value, but it is not a transaction and does not reverse every consequence. A package removal, database migration, data deletion, certificate issuance, or user lockout may not be safely undone by rerunning a playbook. Design destructive changes separately, back up affected state, and obtain review before execution.

To test drift safely, change a harmless, automation-owned setting on a disposable host, run Ansible to restore the declared value, and then run again to confirm no further changes. Never induce drift by deleting production data, opening public ports, or breaking SSH.

## Evidence and recovery

Record the code revision, Ansible and collection versions, inventory alias/group, command options, sanitized recap, service verification, and any exceptions. Do not store raw inventories, full facts, private IPs/hostnames, credentials, vault passwords, or unredacted logs in public documentation.

Before a high-impact run, identify the recovery owner, console path, last known-good config, data backup needs, and the steps to restore service. A backup only helps if its relevant state can be restored. Keep the last working automation revision available; do not rely on an improvised “rollback playbook” that has never been tested.

## Knowledge check

1. Why is `--check --diff` helpful but insufficient for a risky production change?
2. How does limiting a play differ from proving that the selected inventory is correct?
3. Why is desired-state convergence not the same as rollback?
4. What evidence would demonstrate a safe change and a successful recovery path?

## Practical checkpoint

Complete [Task 06 — Apply the reviewed baseline to the VPS safely](../tasks/06-apply-the-reviewed-baseline-to-the-vps-safely.md) and [Task 07 — Prove idempotence, drift correction, and fresh-host reproducibility](../tasks/07-prove-idempotence-drift-correction-and-fresh-host-reproducibility.md).
