# Task 02 — Monitor VPS resources and establish a capacity baseline

## Outcome

Make the VPS's core resource and availability signals visible through a selected, access-controlled collection path, then record a representative baseline and safe operating margins.

## Prerequisites

- Complete [Task 01 — Define service signals, ownership, and measurable objectives](01-define-service-signals-ownership-and-measurable-objectives.md).
- Read [Lesson 02 — VPS health: CPU, memory, storage, network, and capacity](../lessons/02-vps-health-cpu-memory-storage-network-and-capacity.md).
- Have administrative access, a tested recovery method, and knowledge of provider limits.

## Procedure

1. Inventory the actual VPS CPU/core count, RAM/swap, filesystems and mounts, inode counts, network interfaces, provider limits, and services/containers. Record each measurement's source and unit.
2. Choose a provider dashboard/agent, lightweight host agent, or external collector that meets the contract's signals and failure-boundary requirements. Compare resource cost, data location, credentials, retention, and recovery path before installation.
3. If an agent/exporter is installed, apply least privilege and bind/restrict its endpoint to the collector or private network. Verify host and provider firewalls; never open a scrape or admin port publicly for convenience.
4. Configure collection and retention with bounded resource use. Ensure missing/stale samples remain visibly distinct from zero. Avoid collecting process arguments, sensitive filesystem paths, or broad host details unless needed.
5. Verify CPU/load, available memory and swap activity, disk bytes and inodes per relevant filesystem, uptime/restarts, and any available network or I/O pressure indicators. Compare at least one sample with a trusted local system command or provider view.
6. Observe through normal activity plus one representative scheduled operation such as a backup or deployment. Record sample window, typical and peak values, errors, known maintenance, and collection overhead. If there is no representative traffic, label the baseline provisional.
7. Estimate filesystem growth and time to exhaustion from measured changes. Define warning and critical actions with enough remaining headroom for investigation and recovery; do not use a threshold copied from an unrelated host.
8. Confirm the monitoring path remains useful if the agent is restarted or stops reporting. Document the independent provider console or external path available during a VPS/collector outage.

## Acceptance criteria

- [ ] CPU/load, memory pressure/availability, disk bytes and inodes, and host/service restart context are visible with units and recent timestamps.
- [ ] Each relevant filesystem and container limit is distinguished; stale samples are not represented as healthy zero.
- [ ] At least one metric is cross-checked against a trusted independent local/provider observation.
- [ ] Agent/exporter interfaces are not publicly reachable unless an explicitly reviewed and protected design requires it.
- [ ] Collection and retention are bounded, and monitoring overhead is acceptable for the actual VPS size.
- [ ] A representative baseline includes measurement window, expected workload, unusual activity, provisional gaps, and resource growth.
- [ ] Warning/critical limits have documented reasoning and a safe operator action.
- [ ] An operator can identify an independent access path if the VPS or its local collector becomes unavailable.

## Deliverable

A sanitized **VPS monitoring and capacity record** with the collection topology, protected interface exposure, observed baseline, filesystem/inode inventory, growth assumptions, thresholds/actions, and remaining capacity risks.
