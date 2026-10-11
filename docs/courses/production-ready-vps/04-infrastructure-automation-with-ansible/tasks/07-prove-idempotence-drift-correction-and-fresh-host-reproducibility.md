# Task 07 — Prove idempotence, drift correction, and fresh-host reproducibility

## Outcome

Demonstrate that the automation converges on the current VPS, corrects a harmless controlled drift, and can establish the same approved baseline on a fresh or disposable host.

## Prerequisites

- Read [Lessons 04 and 08](../lessons/04-idempotency-handlers-and-convergence.md) and [Safe rollouts, drift, validation, and recovery](../lessons/08-safe-rollouts-drift-validation-and-recovery.md).
- Complete Task 06 with no unresolved availability or access issue.
- Have an authorized disposable VPS/snapshot or another isolated test host matching the supported OS; do not test destructive drift on production.

## Procedure

1. Run the complete reviewed playbook against the intended VPS again without changing inputs. Inspect every task result and investigate repeated changes rather than setting `changed_when: false`.
2. On the disposable host, start from the documented prerequisite state. Apply the automation and independently verify every managed resource. Record packages, users, files, services, and other settings that are in scope.
3. Change one harmless, automation-owned setting on the disposable host to a known incorrect value. Do not alter SSH access, firewall reachability, Docker data, application data, or credentials.
4. Run the playbook and verify that it corrects only the intended drift. Run it once more; the final run should report no unexplained changes.
5. If snapshots or host rebuilds are available, rebuild the disposable target and apply the automation from the documented prerequisites. Confirm the result does not rely on unrecorded manual steps, a personal controller configuration, or a secret stored beside the code.
6. Compare the resulting state against the approved baseline matrix. Record any intentionally unmanaged provider settings and manual prerequisites explicitly.
7. Restore or remove the disposable environment through the provider's documented lifecycle, preserving any evidence needed and avoiding broad cleanup commands.

## Acceptance criteria

- [ ] A repeat run on the configured VPS has no unexplained changes.
- [ ] Harmless induced drift on a disposable host is corrected to the declared state.
- [ ] A subsequent run on that host is effectively a no-op.
- [ ] A fresh/disposable host reaches the baseline from documented prerequisites, or the exact untested limitation and remediation are recorded.
- [ ] No production data, SSH access, firewall protection, or credentials were used as drift-test material.
- [ ] Automation, dependency versions, inventory, prerequisites, and verification steps are sufficient for another authorized operator to reproduce the result.

## Deliverable

A private convergence and reproducibility record containing sanitized first-run, repeat-run, drift-correction, and fresh-host evidence. Any unreproduced baseline element is a production-readiness gap, not a completed checklist item.
