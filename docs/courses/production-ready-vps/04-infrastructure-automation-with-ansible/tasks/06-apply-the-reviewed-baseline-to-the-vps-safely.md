# Task 06 — Apply the reviewed baseline to the VPS safely

## Outcome

Run the reviewed Ansible baseline against the intended VPS in a controlled change, verify critical services and access afterward, and retain sanitized change evidence.

## Prerequisites

- Read [Lesson 08 — Safe rollouts, drift, validation, and recovery](../lessons/08-safe-rollouts-drift-validation-and-recovery.md).
- Complete Tasks 01–05, with a manually verified baseline, explicit inventory, reviewed roles, and protected secrets.
- Have provider console/recovery access, an open administrative session, a second tested SSH path, and a change window if needed.

## Procedure

1. Review the full change set and verify it manages only items in the approved baseline matrix. Confirm repository revision, Ansible version, collections, active config, inventory, and vault identity.
2. Verify the target and task scope with inventory graph, `--list-hosts`, and `--list-tasks`. Run syntax check. Run check mode and diff where supported; inspect output locally and check for secret disclosure.
3. Plan the order of risky operations. Exclude any untested SSH, firewall, disk, Docker networking, or reboot change. Test those separately on a disposable host first and define the recovery action.
4. Apply to only the approved VPS alias using `--limit`. Keep the current SSH session open. Watch for `failed`, `unreachable`, unexpected `changed`, or skipped tasks that are required for correctness.
5. Independently verify SSH with a new connection, expected firewall policy, critical service state, Docker daemon and existing Compose workload, and any other baseline settings covered by this run. Use the normal OS/service tools; a green Ansible recap is not enough.
6. If any check fails, stop and use the documented recovery path; do not repeatedly rerun a partially failed playbook without understanding its current state.
7. Record sanitized revision, command options, target alias/group, recap, independent checks, deviations, and follow-up items. Keep raw addresses, usernames, service logs, and secret-bearing output private.

## Acceptance criteria

- [ ] The actual target is previewed and limited to the intended VPS.
- [ ] Syntax and change review are complete, and unsupported check-mode behavior is accounted for.
- [ ] No access- or availability-critical change was applied without a proven test and recovery method.
- [ ] A fresh SSH login and required `sudo` access work after the run.
- [ ] Existing required services and Docker workloads remain healthy.
- [ ] Unexpected failures or changes are resolved or clearly block completion; they are not hidden.
- [ ] Sanitized evidence is sufficient for another authorized operator to understand what revision ran and what was verified.

## Deliverable

A private, sanitized Ansible change record containing the automation revision, exact non-secret invocation, target alias, recap, independent verification results, and any remaining exceptions.
