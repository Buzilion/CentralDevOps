# 02 — Health checks, restart behavior, and process supervision

## Learning objectives

You can distinguish startup, liveness, and readiness checks; choose safe check behavior; explain container and host restart semantics; and verify the actual recovery path after a crash or reboot.

## Define what each health signal proves

Health checks are small tests with a specific consumer and decision. Avoid a single ambiguous `/health` endpoint used to mean “process exists,” “database works,” and “all business functions are available.”

- **Startup** answers whether the application has completed initialization. It can allow a slow but valid startup without declaring the process dead too early.
- **Liveness** answers whether the process is making progress and should remain running. A failed liveness check may trigger a restart, so it should generally avoid depending on a remote database or third-party API. Otherwise a shared dependency outage can cause every application instance to restart repeatedly.
- **Readiness** answers whether this instance can safely accept the relevant traffic. It can include dependencies necessary for the operation, but it should return a bounded result and avoid revealing internal details publicly.
- **External availability** checks whether a user can reach the intended public path, including DNS, TLS, proxy routing, and expected application behavior. It complements, rather than replaces, local process checks.

Choose the smallest useful response: healthy/unhealthy, a safe status code, and perhaps a non-sensitive component identifier. Do not expose stack traces, SQL errors, environment variables, internal hostnames, dependency credentials, or diagnostic dumps through a public health URL. Protect deeper diagnostic endpoints behind an appropriate access boundary.

## Make checks bounded and non-disruptive

A check should have a timeout, a known cadence, and a cost that remains safe under repeated execution. A health handler that runs a full report, scans a large table, or triggers side effects can add load during the very incident it is meant to diagnose. Define whether a dependency is required for all service use or only a subset of operations. A dependency failure should produce an honest readiness result without causing an uncontrolled restart cascade.

Health thresholds must account for startup and normal work. A slow initialization check should not repeatedly kill the process before it can become ready. A transient network error may warrant a short retry or a degraded state, not an immediate restart. Record the check's last result and age; missing or stale check data is not equivalent to healthy.

## Understand supervision and restart policies

The application process may be supervised by Docker, systemd, or another explicit process manager. Learn which layer owns the process and what it does after:

1. The application exits with an error.
2. The application stops responding but remains alive.
3. A dependency becomes unavailable.
4. The Docker daemon or VPS reboots.
5. The container is intentionally stopped for maintenance.

A container restart policy generally reacts to process exit; it does not guarantee that an `unhealthy` container will be restarted, and behavior varies by runtime configuration. A health status is useful only if the surrounding system or an operator acts on it. Restart loops can amplify a dependency outage, obscure the first failure, and consume resources. Set appropriate backoff or restart limits where supported, alert on repeated restarts, and preserve logs across the restart.

Do not confuse “starts on boot” with “starts in the correct order and becomes usable.” Configure and test dependencies, mounted files, secrets, network availability, and service readiness. Avoid brittle fixed sleep delays as a substitute for checking a dependency condition.

## Shutdown is part of health

On deployment or host shutdown, the process should receive its expected termination signal, stop accepting new work, finish or safely abort in-flight work within a bounded grace period, close connections, flush essential state, and exit. The runtime's stop timeout should exceed the application's realistic shutdown time but remain bounded. If forced termination is necessary, make the consequences and data-safety behavior explicit. Stateless web processes and background jobs may require different drain and retry behavior.

## Verify the actual recovery path

In a safe environment, observe the process identifier/restart count, health result, logs, and service response when exercising a controlled exit. Separately verify reboot behavior with a maintenance plan and a recovery route. A “healthy” result is not sufficient unless a real request succeeds. Verify that persistent data remains intact and that a dependency outage does not cause destructive retries or a restart storm.

## Practical checkpoint

Complete [Task 02 — Validate health checks and restart recovery](../tasks/02-validate-health-and-restart-recovery.md).

## Knowledge check

1. Why can a database-dependent liveness probe make an outage worse?
2. Does an unhealthy Docker health status necessarily restart a container?
3. What must be verified after the host reboots?
4. Which signals prove readiness at the public user boundary?

## References

- [Docker Docs — Healthchecks](https://docs.docker.com/reference/dockerfile/#healthcheck)
- [Docker Docs — Start containers automatically](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [systemd.service manual](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
