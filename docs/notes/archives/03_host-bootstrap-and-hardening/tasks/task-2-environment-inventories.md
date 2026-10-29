# Task 2: Environment inventories and host-key pins

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 1 |

## Goal

Create the separate Staging and Production inventory structure and a safe, repeatable process for adding a real host and its independently verified SSH key pin.

## Relevant files or references

- Create `inventories/staging/` and `inventories/production/` with `hosts.yml`, `known_hosts`, `group_vars/all.yml`, and host-vars directories
- `docs/design/naming-and-repository-conventions.md` §§3.1–3.2, 7–8
- `docs/design/variables-and-secrets.md` §§1.2, 3.2, 9
- Spec sections: Inventory and trust, Capacity policy (PRD Q7)

## Proposed approach

1. Create per-Environment inventory roots and role groups without fabricating host entries or key material.
2. Add only public admin-key configuration to reviewed group variables. Keep provider usernames, host addresses, ports, physical RAM, memory budget and SSH policy in the relevant host-vars file.
3. Encode the D4 initial budget and reserve values in the inventory contract. Each added host must declare physical memory, `platform_reserve_mib`, and `capacity_budget_mib`; assert budget does not exceed physical memory minus reserve.
4. Implement a runbook procedure to obtain a host public key/fingerprint from Sumopod's console, independently compare it, and add it to the correct environment's `known_hosts`. Never trust a workflow-time `ssh-keyscan`.
5. Add exact host-alias validation for `<env>-<purpose>-<number>` and exact membership validation against the chosen inventory. Bootstrap accepts exactly one host, never groups or patterns.
6. Document how the selected GitHub Environment maps to its fixed inventory path. Inventory aliases and host data must not be accepted as arbitrary workflow-supplied connection details.

## Acceptance criteria

- Staging and Production data are physically separate and have no cross-environment host references.
- No actual IP, username, placeholder address, or unverified host key is committed before a real host exists.
- Host aliases and required memory facts follow the spec.
- Unknown, wildcard, group, and other-Environment-only targets fail validation before SSH.
- Effective SSH configuration requires the selected committed host-key file and rejects a mismatched pin.

## Verify

```bash
ansible-inventory -i inventories/staging/hosts.yml --list
ansible-inventory -i inventories/production/hosts.yml --list
```

Add focused tests for target selection and budget validation using temporary fixture inventories, including cross-environment and invalid-pattern cases.

## Out of scope

VPS provisioning, password values, workflows, and SSH hardening.
