# Task 05 — Budget capacity and test resource alerts safely

## Outcome

Create a capacity budget for the actual VPS workload and show that actionable resource alerts can be verified without exhausting production resources.

## Prerequisites

- Complete Tasks 01–04 and review [Lesson 05 — Capacity, resource pressure, and dependency limits](../lessons/05-capacity-resource-pressure-and-dependency-limits.md).
- Have monitoring and notification paths from Subject 08, and know the VPS/provider quotas and available safe test environment.

## Procedure

1. Inventory resource consumers: application, database, proxy, Docker/runtime, monitoring, logs, uploads, backups, temporary files, image layers, and scheduled jobs.
2. Capture representative baseline and peak measurements for CPU, memory/swap, disk bytes and growth, inodes, I/O latency if available, network/connections, and dependency limits. Label unusual maintenance or backup windows.
3. Estimate time-to-full for growing data and the headroom required for a deployment, migration, backup, restore, and log rotation. Include image pulls/builds and temporary storage.
4. Set warning and critical thresholds with observation windows, owner, expected lead time, and a safe response. For each alert, state what action is explicitly unsafe (such as deleting volumes or the only backup).
5. Check container/process resource limits and scheduled workload concurrency. Validate that limits allow normal peak use and do not induce restart loops.
6. Test alert behavior through a provider test function, synthetic rule, or staging/test metric. If a reversible production threshold test is approved, keep it far from actual exhaustion and define a stop condition. Never deliberately fill production disk or consume all memory/CPU.
7. Confirm delivery, acknowledgment, deduplication/recovery, and that stale/missing telemetry is not represented as healthy zero.
8. Review VPS resource cost and impact of monitoring; propose a capacity change or simplification if routine peak leaves inadequate headroom.

## Acceptance criteria

- [ ] All material consumers and resource dimensions are inventoried.
- [ ] Baseline, peak, growth rate, maintenance load, and meaningful headroom are documented with dates and units.
- [ ] Disk bytes and inode usage, as well as backup/log/image storage, have explicit limits and ownership.
- [ ] Thresholds lead to safe, named actions with enough response time; alert delivery is tested.
- [ ] Resource constraints and job concurrency are validated against observed workload.
- [ ] No production resource was intentionally exhausted; test artifacts are removed.
- [ ] Capacity shortfalls and monitoring overhead have an owner and decision date.

## Deliverable

A dated **VPS capacity budget and alert verification record** with measurements, assumptions, thresholds, alert evidence, and scaling/remediation decisions.
