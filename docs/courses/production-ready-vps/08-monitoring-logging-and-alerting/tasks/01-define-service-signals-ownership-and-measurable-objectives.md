# Task 01 — Define service signals, ownership, and measurable objectives

## Outcome

Produce a concise monitoring contract for the actual deployed application: critical user behavior, service indicators and objectives, signal sources, owners, alertable risks, dependencies, and known blind spots. This contract is the basis for every later dashboard and alert; it must not be a list of guessed thresholds.

## Prerequisites

- Complete the application runtime and serving contract in the earlier course subjects.
- Read [Lesson 01 — Observability signals, service objectives, and monitoring boundaries](../lessons/01-observability-signals-service-objectives-and-monitoring-boundaries.md).
- Have the application owner's input on acceptable user impact and response expectations.

## Procedure

1. Inspect the real deployment: public hostname and address families, reverse proxy, application service/container, health route if present, database or other essential dependencies, scheduled jobs, backup signal, and deployment process. Mark unavailable facts as **unknown** rather than assuming.
2. Draw or describe the user request path from external client through DNS, firewall, TLS/proxy, application, and essential dependency. Add a separate line for collection, alert evaluation, notification destination, and responder.
3. List the critical user journeys or service promises. Separate core functionality from optional features and administrative functions. Do not place credentials or customer data in the inventory.
4. For each critical behavior, define one or more candidate SLIs. Specify the measurement point, numerator/denominator or precise check, excluded cases, collection source, time window, unit, and what missing data means.
5. Agree on an initial SLO or explicit baseline period for availability and, if meaningful, latency. Record the owner, target window, measurement assumptions, and date reviewed. An unapproved target must remain a proposal, not be presented as a commitment.
6. Inventory host, application, dependency, backup, certificate, and monitoring-path signals. Record source, freshness, expected collection interval, retention, signal owner, access boundary, and blind spot for each.
7. Rank failure conditions by user impact and urgency. Identify which require immediate notification, which belong on a dashboard, and which can be reviewed periodically. Note a first safe action and response owner for each candidate alert.
8. Record constraints: VPS size, provider monitoring options, public routes, available notification channels, budget, privacy restrictions, telemetry retention, and who can access the evidence.
9. Review the draft with the application/service owner. Resolve ambiguity or document an owner and due date for each unresolved design decision.

## Acceptance criteria

- [ ] The contract describes the actual, inspected request and dependency path; assumptions and unknowns are labelled.
- [ ] At least one user-facing availability SLI and a meaningful latency or failure indicator are specified, or the reason a candidate does not apply is recorded.
- [ ] Every indicator has a source, measurement definition, unit/window, signal owner, freshness expectation, and interpretation of missing data.
- [ ] Any SLO is approved, measurable, and tied to an explicit time window; unapproved proposals are clearly marked.
- [ ] The design includes both independent external detection and internal/host diagnosis, with their different blind spots.
- [ ] Candidate alert conditions are tied to user impact or a defined operational action rather than arbitrary copied thresholds.
- [ ] Privacy, access, retention, monitoring costs, and the single-VPS failure boundary are recorded.
- [ ] The service owner has reviewed the contract, with review date and remaining decisions identified.

## Deliverable

A dated, sanitized **monitoring contract** containing a request-path diagram or narrative, a signal inventory, proposed/approved SLI/SLO definitions, alert ownership, known blind spots, and design decisions. Store it in the approved operational documentation location; do not include private addresses, credentials, real user identifiers, or sensitive payloads.
