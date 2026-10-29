# Task 3: Per-host capacity control

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md` |
| Depends on | Task 2; spec 03 capacity facts and inventory layout are complete |
| Needs | Reviewed inventory facts and local fixtures; no VPS access |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Fail registry validation when the total registered app memory limit on any placement host exceeds its reviewed inventory budget.

## Relevant files or references

- Extend `deployment/tools/validate-registry.py`
- `inventories/<environment>/host_vars/<host-alias>.yml`
- Spec 03 capacity policy and its `physical_memory_mib`, `platform_reserve_mib` and `capacity_budget_mib` facts
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (`REG-07`)

## Proposed approach

1. For each registry entry, resolve `placement.app_group` and associate its memory ceiling with the single app host.
2. Normalize every supported `limits.memory` value to an exact byte count; avoid floating-point arithmetic and document the accepted units.
3. Sum app memory limits per `(Environment, host alias)` and compare against `capacity_budget_mib * 1024 * 1024`.
4. Fail if a used host lacks physical memory, reserve or capacity facts, or if its budget exceeds physical memory minus reserve.
5. Keep budget values in inventory. Do not hard-code the spec 03 planning values or infer a budget from nominal VPS size.
6. Add fixtures for several apps sharing one host, apps on separate hosts, and a host with an invalid reserve/budget relationship.

## Acceptance criteria

- The exact budget passes; exceeding it by one byte fails.
- App limits from multiple registry entries on one host are summed before comparison.
- Separate host totals are not combined.
- Missing budget facts, an invalid memory value and a budget greater than physical memory minus reserve all fail closed.
- The check remains a memory-capacity check; it does not invent a host CPU budget.

## Source reference

REG-07, INF-20, PRD Q7; P-07; spec 03 capacity decision.

## Verify

- Run the focused capacity tests using fixture inventories resolved by `ansible-inventory`.
- Confirm totals in diagnostics are reported in MiB and point to the host and registry entries without exposing secrets.

## Out of scope

Compose service-level resource enforcement, changing inventory budgets or measuring a live VPS.
