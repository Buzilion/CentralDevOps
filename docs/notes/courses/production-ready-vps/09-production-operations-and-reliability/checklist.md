# Production Operations and Reliability — Course Checklist

Complete this subject after the first eight subjects: **Linux Server Administration**, **Networking, DNS, and Firewall Security**, **Docker and Container Operations**, **Infrastructure Automation with Ansible**, **CI/CD with GitHub Actions**, **Reverse Proxy, HTTPS, and Application Serving**, **Data Persistence, Backup, and Recovery**, and **Monitoring, Logging, and Alerting**. Use the actual application runtime, release contract, recovery procedures, and monitoring signals established earlier. Do not assume a particular language, database, process manager, cloud provider, or deployment topology.

The objective is not to promise zero downtime or eliminate every failure. It is to make routine changes controlled, failures diagnosable, recovery deliberate, and operational ownership clear. A single VPS remains a single point of failure; a restart policy, backup, or second application process does not make it highly available by itself.

## Lessons

- [ ] [01 — Production operating model, ownership, and service expectations](lessons/01-production-operating-model-and-service-ownership.md)
- [ ] [02 — Health checks, restart behavior, and process supervision](lessons/02-health-checks-restart-behavior-and-process-supervision.md)
- [ ] [03 — Failure diagnosis and dependency resilience](lessons/03-failure-diagnosis-and-dependency-resilience.md)
- [ ] [04 — Safe deployments, downtime, and rollback](lessons/04-safe-deployments-downtime-and-rollback.md)
- [ ] [05 — Capacity, resource pressure, and dependency limits](lessons/05-capacity-resource-pressure-and-dependency-limits.md)
- [ ] [06 — Incident response, decision-making, and operational runbooks](lessons/06-incident-response-and-operational-runbooks.md)
- [ ] [07 — Patching, dependency updates, and access reviews](lessons/07-maintenance-patching-dependency-updates-and-access-reviews.md)
- [ ] [08 — Reliability exercises and continuous improvement](lessons/08-reliability-exercises-and-continuous-improvement.md)

## Hands-on tasks

- [ ] [Task 01 — Define the operating contract and maintenance cadence](tasks/01-define-operating-contract-and-maintenance-cadence.md)
- [ ] [Task 02 — Validate health checks and restart recovery](tasks/02-validate-health-and-restart-recovery.md)
- [ ] [Task 03 — Build a failure diagnosis matrix](tasks/03-build-failure-diagnosis-matrix.md)
- [ ] [Task 04 — Rehearse deployment, downtime, and rollback](tasks/04-rehearse-deployment-downtime-and-rollback.md)
- [ ] [Task 05 — Budget capacity and test resource alerts safely](tasks/05-budget-capacity-and-test-resource-alerts.md)
- [ ] [Task 06 — Practice incident response and update runbooks](tasks/06-practice-incident-response-and-update-runbooks.md)
- [ ] [Task 07 — Complete a patching, dependency, and access review](tasks/07-complete-patching-and-access-review.md)
- [ ] [Task 08 — Run a production operations readiness review](tasks/08-run-production-readiness-review.md)

## Subject completion gate

- [ ] The service has a named owner and backup contact, a concise operating contract, defined maintenance windows, and explicit limits to the availability promise.
- [ ] Liveness, readiness, and startup checks have distinct purposes; their failure behavior, timeouts, dependencies, and privacy properties have been verified.
- [ ] Restart behavior has been tested for a process crash and a host reboot; operators understand that restart policies do not repair an unhealthy application or its data.
- [ ] The operator can use recent deploy/change records, host and application signals, logs, and external checks to investigate representative failure symptoms without guessing or destroying evidence.
- [ ] The deployment procedure pins an identifiable release, defines preflight and post-deploy checks, states expected downtime, has stop conditions, and has a tested rollback or forward-fix decision.
- [ ] Capacity assumptions include CPU, memory, disk space, inodes, logs, temporary files, backups, image storage, and monitoring overhead, with warning thresholds and safe responses.
- [ ] Incident roles, severity examples, communications, decision authority, escalation, evidence handling, recovery verification, and follow-up ownership are documented.
- [ ] OS security updates, application dependency updates, reboot coordination, vulnerability response, secrets, and access reviews have named owners and a recurring cadence.
- [ ] At least one bounded failure or deployment exercise has been performed in a suitable non-production or explicitly approved low-risk scope; timestamps and sanitized evidence are recorded.
- [ ] Operational documents are stored outside the VPS, reviewed by someone other than their author where practical, and identify known gaps rather than implying guarantees.

## Exit criteria

An operator other than the person who configured the VPS can identify the active release, determine whether users are affected, find the relevant evidence, follow a safe mitigation, and prove recovery. A routine release and a maintenance update have controlled procedures and a rollback or recovery decision. Capacity exhaustion, missing dependencies, restart loops, and unavailable monitoring are treated as distinct conditions. Proceed only when operational readiness is demonstrated with evidence; a successful deployment or a green dashboard alone is not the completion criterion.
