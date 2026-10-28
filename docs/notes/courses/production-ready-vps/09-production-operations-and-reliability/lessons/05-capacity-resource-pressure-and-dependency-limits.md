# 05 — Capacity, resource pressure, and dependency limits

## Learning objectives

You can identify the resource limits that threaten service, estimate headroom from observed usage, recognize disk and memory failure modes, and choose actions that relieve pressure without damaging application data.

## Capacity is more than CPU

On a VPS, the application, database, container runtime, reverse proxy, backup job, and monitoring agent compete for finite resources. A capacity model should include:

- **CPU:** sustained saturation, throttling, and contention during image builds or backups.
- **Memory:** application working sets, database cache, kernel use, and container limits; abrupt out-of-memory termination can look like an unexplained crash.
- **Disk blocks and inodes:** database files, uploads, backups, logs, temporary files, Docker images/layers, and package caches. Free bytes do not help when inodes are exhausted.
- **I/O:** storage latency and queueing can make an otherwise available database appear hung.
- **Network and connections:** bandwidth, connection count, file descriptors, proxy limits, DNS resolution, and provider quotas.
- **Dependency capacity:** database connections, queue depth, API rate limits, registry availability, and backup destination quotas.

Use observed peak and growth rates rather than only average utilization. Include maintenance workloads and simultaneous activity: a backup, container image pull, log rotation, and database migration may compete at the same time. Estimate how much capacity is needed to complete a safe operation, not merely to serve steady-state traffic.

## Establish actionable thresholds

Track the metric, unit, collection interval, observation window, normal range, warning point, critical point, and expected action. Thresholds should allow time to respond before service impact. For growing disk use, estimate time-to-full from recent growth; a percentage threshold without growth context can be too late on a small disk or noisy on a large one. Monitor both disk bytes and inode availability, and include backup destinations where you control them.

Memory pressure needs context: inspect available memory, swap activity, OOM events, process/container limits, and restarts. CPU alerts should distinguish a short burst from sustained saturation that harms request latency. A metric that cannot lead to an owner and a safe action is likely noise.

## Plan safe relief actions

Relief options depend on the source and must preserve state:

- Reduce or pause non-critical work and retry later.
- Stop an unnecessary build or constrain concurrency.
- Correct excessive log generation and verify log rotation/retention.
- Remove only known disposable artifacts using documented retention rules.
- Expand storage or memory through the provider when feasible.
- Scale or optimize the workload based on evidence.

Do not run blanket Docker pruning commands or delete files from database, upload, or backup directories to recover space. Deleting a volume or the only backup can turn resource pressure into permanent data loss. Confirm what consumes space, ownership, retention, and recovery implications before cleanup.

## Bound workloads and maintenance jobs

Apply realistic CPU and memory budgets to optional or noisy workloads where supported. A hard memory limit set below the application's real working set may induce repeated OOM restarts. Bound backup duration, log volume, retry loops, queue size, and concurrent jobs. Stagger backups and deployments if they create a predictable resource spike. Monitor whether the monitoring system itself consumes a meaningful share of the VPS.

## Know when to scale or simplify

Repeatedly operating near a resource boundary is a reliability problem, not merely a dashboard issue. Identify the limiting resource and its growth driver. Options include tuning, removing unnecessary services, upgrading the VPS, moving a managed dependency off-host, or splitting work across hosts. Each choice has cost, complexity, and new failure modes. Kubernetes is not a substitute for understanding capacity on a single server.

## Practical checkpoint

Complete [Task 05 — Budget capacity and test resource alerts safely](../tasks/05-budget-capacity-and-test-resource-alerts.md).

## Knowledge check

1. Why must a disk monitor track inodes as well as free bytes?
2. What makes a cleanup command unsafe during a disk incident?
3. How can a backup job cause a production latency incident?
4. Which measurements help estimate time-to-full?

## References

- [Docker Docs — Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Google SRE Book — Managing Critical State](https://sre.google/sre-book/managing-critical-state/)
- [Ubuntu Server Guide — Storage](https://documentation.ubuntu.com/server/how-to/storage/)
