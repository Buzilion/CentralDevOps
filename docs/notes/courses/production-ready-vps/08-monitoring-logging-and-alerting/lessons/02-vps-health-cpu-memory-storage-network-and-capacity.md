# 02 — VPS health: CPU, memory, storage, network, and capacity

## Learning objectives

You can choose a small, useful set of host signals; understand their units and interpretation; establish a representative baseline; and detect sustained resource exhaustion before it becomes an outage.

## Observe saturation, not just a single number

Host metrics help explain service behavior and provide early warning of resource limits. At minimum, observe CPU utilization or load, memory pressure, filesystem free space and inodes, network reachability or interface errors where available, uptime/reboots, and the status of important services. Include a timestamp, hostname or stable host identity, and units. Collect at a cadence appropriate to the failure modes; excessively frequent polling can add load and storage without making the system more actionable.

### CPU and load

CPU utilization describes time spent running work versus idle; load average estimates runnable and uninterruptible tasks over time. They are related but not interchangeable. A load value around the number of available cores can mean the CPU is busy, but I/O waits can also increase load. Check sustained trends and correlate them with request latency, deploys, backups, and process-level evidence. A short CPU spike may be expected and may not affect users; a sustained rise paired with latency or queueing is more actionable.

### Memory and swap

Linux uses otherwise-unused memory for filesystem cache and can reclaim some cache when applications need memory. A simplistic “used memory” percentage can therefore create false alarms. Prefer available memory, swap activity, memory pressure if your collector exposes it, and process/container limits or out-of-memory events. Sustained swap-in/swap-out, rising pressure, repeated OOM kills, or a service restart can indicate a real shortage. Swap can absorb some bursts but is not a substitute for adequate RAM and may cause severe latency under pressure.

When containers are used, distinguish host memory from container limits and actual container usage. A host with free memory can still have an application constrained by its configured limit; a container can also consume enough memory to endanger the whole host if no limits exist.

### Filesystems, disk, and inodes

Watch free bytes and inode availability for each filesystem that matters: root, application state, database storage, backups, and log locations may live on different mounts. A filesystem can reject writes with free bytes remaining if it runs out of inodes. Include growth rate and projected time to exhaustion, not just a static percentage. The same percentage has different urgency on a 10 GB partition and a 2 TB volume.

Identify what consumes disk before it is full: database growth, container images/layers, writable container logs, journal files, temporary files, and backup staging are common sources. Monitoring cannot replace bounded log rotation, backup retention, and a safe cleanup procedure. Do not auto-delete unknown files to silence a disk alert.

### Network and system availability

Useful basic context includes host reachability, public endpoint result, interface error/drop counters if available, and whether required local services are running. A server's load or “uptime” does not prove the network path, DNS, TLS, proxy, or app works. A reboot resets uptime; it may be expected maintenance or a sign of a crash. Preserve reboot and service restart evidence and compare with deployment/change records.

## Establish capacity headroom

Collect a baseline across representative use, including scheduled backups and deployment work. Review minimum and maximum values as well as trends; averages can conceal brief but user-impacting saturation. Record known maintenance windows and avoid broad labels that hide real incidents. If the application has no production traffic yet, mark the baseline as provisional and use safe load testing only within the VPS provider's limits.

Choose thresholds using both a safety floor and time-to-exhaustion. For example, a disk warning may begin when free capacity approaches a reserved operating margin or when the projected growth reaches exhaustion before the next planned intervention. A critical condition can use a smaller free-space margin, but should still leave room for diagnosis, package operations, and graceful shutdown. Set values from actual filesystem size and growth, not a copied percentage. Revisit after major changes.

Capacity has dependencies: the VPS provider may throttle CPU or storage I/O; a snapshot can temporarily consume space; filesystem expansion may require downtime; and the monitoring database itself can grow. Record the measured or provider-documented limits and the action available when each boundary is reached.

## Collect host metrics with Alloy

The course's default collector is Grafana Alloy installed on the VPS as a package-managed systemd service. Alloy's `prometheus.exporter.unix` component collects Linux host metrics, `prometheus.scrape` gathers them inside Alloy, and `prometheus.remote_write` sends them to the Grafana Cloud Metrics endpoint. This avoids running a separate node-exporter listener or a metrics database on the same VPS. The exact configuration and credential handling are shown in [Lesson 05](05-metrics-collection-dashboards-and-safe-instrumentation.md).

Use the Grafana Cloud stack's own metrics endpoint and instance ID, and a write-only access-policy token. The VPS needs outbound HTTPS access to the Cloud endpoint; it does not need an inbound scrape port for this built-in exporter. If application metrics are available, add a separate scrape target bound to loopback or a private interface and forward it to the same remote-write receiver. Keep labels stable and bounded; do not attach user or request identifiers.

Run Alloy with the package's dedicated service account and grant only the host access needed by the selected collectors. Verify the process's actual listeners and keep Alloy's HTTP/UI interface private. Check the host's local values against Grafana Cloud, confirm the samples are fresh, and define how Cloud alert rules respond when Alloy stops reporting. Never expose a metrics endpoint that reveals process names, filesystem layouts, host labels, or configuration to the public Internet. Avoid mounting the Docker daemon socket into a monitoring container unless its powerful access is understood and tightly constrained.

Verify that host identity survives restarts and that dashboards distinguish current from stale samples. If a service stops reporting, the missing signal needs explicit treatment; it must not be plotted as zero utilization.

## Practical checkpoint

Use [Task 02 — Monitor VPS resources and establish a capacity baseline](../tasks/02-monitor-vps-resources-and-establish-a-capacity-baseline.md) to install Alloy, verify host metrics in Grafana Cloud, and capture the first baseline. Record values and infrastructure details only in an appropriately protected operational record.

## Knowledge check

1. Why can high Linux “used memory” be normal, and which signals make memory pressure clearer?
2. How can an inode alert indicate imminent write failure when free disk bytes remain?
3. Why should disk risk account for capacity and growth instead of only a percentage?
4. Which collection port or endpoint should never be opened to the public merely for convenience?

## References

- [Grafana Alloy — `prometheus.exporter.unix`](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.exporter.unix/)
- [Grafana Alloy — Install on Linux](https://grafana.com/docs/alloy/latest/set-up/install/linux/)
- [Grafana Cloud — Monitor a Linux server](https://grafana.com/docs/learning-journeys/linux-server-integration/)
- [Linux kernel documentation — Pressure Stall Information](https://docs.kernel.org/accounting/psi.html)
- [Docker documentation — Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
