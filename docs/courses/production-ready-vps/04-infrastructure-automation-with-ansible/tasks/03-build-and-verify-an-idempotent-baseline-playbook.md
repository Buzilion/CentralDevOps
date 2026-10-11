# Task 03 — Build and verify an idempotent baseline playbook

## Outcome

Implement a small playbook that changes one reviewed, low-risk baseline item into an explicit desired state, then demonstrate that repeated runs converge.

## Prerequisites

- Read [Lessons 03 and 04](../lessons/03-playbooks-modules-facts-and-execution.md) and [Idempotency, handlers, and convergence](../lessons/04-idempotency-handlers-and-convergence.md).
- Complete Task 02 and confirm the intended target pattern.
- Have a disposable host available for first-run experimentation; otherwise choose a low-risk, approved setting that cannot interrupt access or application service.

## Procedure

1. Select one setting from the approved baseline matrix. It must have a clear state, verification method, and recovery action. Do not begin with SSH, firewall, storage, data deletion, or Docker networking.
2. Implement it with an appropriate `ansible.builtin` module and a fully qualified module name. Prefer a declarative state over a shell command. Define required inputs explicitly and fail clearly on unsupported operating systems.
3. Scope the play to the intended group, use a non-root SSH account, and enable `become` only if the resource requires it.
4. Inspect the playbook, inventory, and active Ansible config. Run syntax check, host listing, and check mode. Review all predicted changes and confirm no unintended hosts or secrets are exposed.
5. Apply to the disposable host or approved single VPS. Inspect the task result and verify the resource independently using the operating system's normal inspection tool.
6. Run the same playbook again with the same inputs. Investigate any repeated change result. Do not suppress change reporting to make the recap appear clean.
7. Record the exact automation revision, sanitized invocations, first-run and second-run recaps, verification command/result, and any check-mode limitations.

## Acceptance criteria

- [ ] The playbook manages a specific approved state using a suitable module.
- [ ] The host pattern resolves to only the intended test target.
- [ ] Syntax check passes and the proposed diff/result was reviewed before application.
- [ ] Independent inspection confirms the desired state after the first run.
- [ ] The second run reports no unexplained changes.
- [ ] No broad shell command, secret, plaintext password, or bypassed host-key check is introduced.
- [ ] Failure behavior and rollback/recovery are documented for the selected resource.

## Deliverable

A minimal, reviewed playbook and sanitized evidence of target selection, first convergence, independent verification, and a no-op second run. Treat this as a learning slice, not yet the complete VPS baseline.
