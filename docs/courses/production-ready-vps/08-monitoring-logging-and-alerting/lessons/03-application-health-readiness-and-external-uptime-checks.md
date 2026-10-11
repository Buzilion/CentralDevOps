# 03 — Application health, readiness, and external uptime checks

## Learning objectives

You can define health checks that answer distinct questions, configure local and external probes without exposing internal details, and validate the user-facing request path through DNS, TLS, proxy, and application.

## Define what “healthy” means

Health endpoints are machine-readable contracts. Before adding one, inspect the application's existing behavior and deployment health check. Use the narrowest checks that support an operational decision:

- **Liveness** answers whether the process is alive and making progress. It should not normally fail just because a temporary database or external API is unavailable; an orchestrator that restarts a live process on every dependency timeout can amplify an outage.
- **Readiness** answers whether this instance should receive traffic now. It can include required dependencies when their absence means the app cannot serve its core contract. A not-ready response should not necessarily cause an automatic restart.
- **Startup** (where the runtime supports it) allows legitimate initialization or migrations time before liveness evaluation begins.
- **Synthetic/user-facing check** exercises a carefully selected path from outside the VPS, such as loading a public page or a dedicated low-impact endpoint through the intended domain and HTTPS.

Some applications expose only a single health endpoint or rely on a platform check. Do not invent routes without changing and testing the application contract. Document exactly what a `200`, non-`200`, timeout, or dependency-degraded response means. Keep checks fast, deterministic, low-cost, and side-effect-free.

## Keep health output safe and stable

Return only the status and minimum detail needed by the probe. Public health responses should not reveal database hostnames, version strings, stack traces, secrets, user information, or a detailed dependency inventory. If operators need dependency diagnostics, use a separate access-controlled mechanism or logs. Authentication policy must be compatible with the probe while preventing health routes from becoming an information disclosure path.

Set timeouts and retry behavior deliberately. A probe that waits too long can consume resources during an outage; a probe that fails after one transient packet loss can generate noise. Use a small, bounded timeout and a defined number/interval of retries, then measure end-to-end detection delay. Ensure the probe's polling load does not become material.

For Docker health checks, a health status does not automatically restart a container in all configurations. Confirm how the selected runtime, Compose setup, reverse proxy, or external deployment process consumes the status. Treat health checks as observations unless a documented controller takes action. Avoid commands that are missing from a minimal image; probe the actual listener and expected behavior with an available, reliable method.

## Trace the actual user path

An external probe should start outside the VPS and exercise the published hostname, not only `localhost` or the container network. A practical path includes:

```text
External probe
  -> DNS answer (A and, if published, AAAA)
  -> provider/host firewall
  -> public listener and TLS certificate
  -> reverse proxy route
  -> private application upstream
  -> expected safe response
```

Check certificate hostname and expiry, redirect behavior, expected status or stable response content, and latency. Test every public address family you advertise; a broken IPv6 route can affect some users while IPv4 checks pass. Avoid checks that depend on dynamic homepage content or expose real account credentials. If sign-in or a transactional flow must be monitored, use a dedicated synthetic identity, least privilege, safe cleanup, and no real side effects.

An endpoint returning `200` is not a complete availability SLI if it responds before critical state is usable. Conversely, probing a database directly from the public Internet is unnecessary and unsafe. Choose one shallow, reliable liveness/readiness signal for fast diagnosis and a separate user-facing synthetic check for the external service contract.

## Separate local diagnosis from independent detection

A local health check can help a process manager or deployment verify startup, but it cannot tell you that users can resolve the domain or reach the VPS. An external probe can detect those failures, but cannot identify the responsible internal component. Use both when possible and correlate timestamps.

External services can themselves fail. Confirm probe locations, status pages, maintenance behavior, and alert deduplication. Consider using more than one location or provider for high-value services, but do not interpret several correlated checks from one network as independent evidence. A probe that checks a URL through an internal tunnel may not represent the actual public path.

## Practical checkpoint

Complete [Task 03 — Verify application health locally and from outside the VPS](../tasks/03-verify-application-health-locally-and-externally.md). Record probe identity and safe results, not secrets, response bodies containing user data, or private endpoint addresses.

## Knowledge check

1. Why should a liveness check usually avoid failing solely because a downstream dependency is unavailable?
2. What operational decision is readiness intended to support?
3. Which layers can be proven by probing only `localhost`, and which cannot?
4. What additional risk comes with synthetic checks that sign in or perform transactions?

## References

- [Kubernetes documentation — Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [Prometheus documentation — Monitoring Docker container metrics](https://prometheus.io/docs/guides/cadvisor/)
- [OWASP Cheat Sheet Series — REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
