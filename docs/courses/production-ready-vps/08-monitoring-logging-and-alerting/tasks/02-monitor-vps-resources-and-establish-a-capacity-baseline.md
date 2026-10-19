# Task 02 — Monitor VPS resources and establish a capacity baseline

## Outcome

Make the VPS's core resource and availability signals visible through a selected, access-controlled collection path, then record a representative baseline and safe operating margins.

## Prerequisites

- Complete [Task 01 — Define service signals, ownership, and measurable objectives](01-define-service-signals-ownership-and-measurable-objectives.md).
- Read [Lesson 02 — VPS health: CPU, memory, storage, network, and capacity](../lessons/02-vps-health-cpu-memory-storage-network-and-capacity.md).
- Read the Alloy configuration example in [Lesson 05 — Metrics collection, dashboards, and safe instrumentation](../lessons/05-metrics-collection-dashboards-and-safe-instrumentation.md).
- Have administrative access, a tested recovery method, and knowledge of provider limits.
- Have access to the Grafana Cloud stack that will receive the host metrics.

## Procedure

1. Inventory the actual VPS CPU/core count, RAM/swap, filesystems and mounts, inode counts, network interfaces, provider limits, and services/containers. Record each measurement's source and unit.
2. In Grafana Cloud, confirm the target stack has the required metrics service and that its endpoint, instance ID, retention, ingestion limits, and plan are understood. Create a stack-scoped access-policy token with only `metrics:write`; do not use an admin or read token for Alloy.
3. Install Grafana Alloy from Grafana's signed package repository as a systemd service on the VPS, enable it at boot, and use the package's documented config and data paths. The Grafana Cloud Linux Server integration can guide setup and supply prebuilt dashboards/alerts when available; if you use it, review its generated configuration and do not duplicate the same host scrape.
4. Configure `prometheus.exporter.unix` -> `prometheus.scrape` -> `prometheus.remote_write` as shown in Lesson 05. Use the exact Cloud metrics endpoint and instance ID, and store the write token in a protected file loaded as an Alloy secret. Do not put a real token in `config.alloy`, Git, command history, or evidence.
5. Reload Alloy and verify its systemd status and logs. In Grafana Cloud Explore, confirm fresh `up` and host-metric samples for the expected instance. Compare CPU/load, available memory and swap activity, disk bytes and inodes per relevant filesystem, uptime/restarts, and available network or I/O pressure indicators with trusted local commands.
6. Keep Alloy's local UI private and do not open an inbound scrape or admin port. Confirm the VPS can reach the Cloud endpoint over outbound HTTPS, and document the agent's resource use, local state directory, and behavior during a Cloud/network interruption.
7. Observe through normal activity plus one representative scheduled operation such as a backup or deployment. Record sample window, typical and peak values, errors, known maintenance, and collection overhead. If there is no representative traffic, label the baseline provisional.
8. Estimate filesystem growth and time to exhaustion from measured changes. Define warning and critical actions with enough remaining headroom for investigation and recovery; do not use a threshold copied from an unrelated host.
9. Confirm the monitoring path remains useful if Alloy is restarted or stops reporting. Verify missing samples are shown as missing rather than zero, document the no-data alert to be exercised in Task 06, and record the independent external/provider path available during a VPS or collector outage.

## Acceptance criteria

- [ ] CPU/load, memory pressure/availability, disk bytes and inodes, and host/service restart context are visible with units and recent timestamps.
- [ ] Alloy runs as a systemd service, has a valid configuration, and sends fresh host samples to Grafana Cloud Metrics using a metrics-write-only token stored outside the config and repository.
- [ ] Each relevant filesystem and container limit is distinguished; stale samples are not represented as healthy zero.
- [ ] At least one metric is cross-checked against a trusted independent local/provider observation.
- [ ] Alloy's UI and all scrape/exporter interfaces are not publicly reachable; the required outbound HTTPS path to Grafana Cloud is allowed.
- [ ] Collection and retention are bounded, and monitoring overhead is acceptable for the actual VPS size.
- [ ] A representative baseline includes measurement window, expected workload, unusual activity, provisional gaps, and resource growth.
- [ ] Warning/critical limits have documented reasoning and a safe operator action.
- [ ] An operator can identify an independent access path if the VPS or its local collector becomes unavailable.

## Deliverable

A sanitized **VPS monitoring and capacity record** with the Alloy version/configuration path, Grafana Cloud metrics destination (without credentials), protected interface exposure, observed baseline, filesystem/inode inventory, growth assumptions, thresholds/actions, and remaining capacity risks.
