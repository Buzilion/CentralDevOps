# Task 07 — Document proxy operations, renewal, and recovery

## Outcome

Leave an operator-ready runbook to inspect, validate, reload, troubleshoot, and recover the proxy and certificate path without guessing or exposing secrets.

## Prerequisites

- Complete Tasks 01–06.
- Read [Lesson 07 — Safe proxy changes, logs, and operational controls](../lessons/07-safe-proxy-changes-logs-and-operational-controls.md).

## Procedure

1. Document the selected proxy and version, service/container name, config source-of-truth location, public hostnames, upstream route, and intentionally open ports. Use aliases for sensitive infrastructure identifiers.
2. Record exact commands for current status, config validation, safe reload, recent logs, listener inspection, and restoration of the prior known-good configuration. Verify each command against the installed version instead of copying generic commands.
3. Document where access/error logs are collected and rotated, their retention, access permissions, and how to avoid or redact authorization headers, cookies, tokens, query secrets, and personal data.
4. Record the certificate manager, challenge type, certificate locations (not key contents), renewal scheduler, last successful test, and how to inspect failures. Document safe manual recovery/escalation if renewal fails.
5. Add the troubleshooting decision path for DNS, TCP/firewall, TLS, redirects, 404, 502, and 504. Include the working health route and expected responses.
6. Rehearse a config syntax failure in a disposable/staging copy or safe validation workflow; verify the live service remains on the previous valid configuration. Rehearse restoration of the known-good file without deleting certificate or application data.
7. Assign an owner and review interval for proxy software updates, hostname/certificate inventory, DNS/firewall drift, log retention, and renewal monitoring. Monitoring/alert delivery will be completed in the later monitoring subject.
8. Have another authorized operator follow the runbook to locate status/logs and explain the recovery sequence. Correct ambiguous steps.

## Acceptance criteria

- [ ] A second operator can identify the serving process, route, and public/private boundaries.
- [ ] Validation, reload, status, logs, and rollback steps are exact and tested for the installed proxy.
- [ ] Certificate renewal ownership, scheduler, test result, failure inspection, and recovery are explicit.
- [ ] Runbook and logs contain no secrets or unnecessary personal/infrastructure data.
- [ ] A failed candidate config is rejected without replacing the active known-good state.
- [ ] Update, renewal, exposure, and log-retention reviews have an owner and cadence.

## Deliverable

A reviewed reverse-proxy operations runbook and final production-serving evidence bundle.
