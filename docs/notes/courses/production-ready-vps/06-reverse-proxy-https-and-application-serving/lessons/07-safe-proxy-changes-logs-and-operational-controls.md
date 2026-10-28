# 07 — Safe proxy changes, logs, and operational controls

## Learning objectives

You can make a reversible proxy change, distinguish configuration validation from live service verification, use logs without leaking secrets, and define practical controls for proxy and certificate operations.

## Configuration is production state

Keep the proxy configuration in a reviewed source of truth: version control, Ansible, or another deliberate configuration-management approach. Do not edit a generated file that automation will overwrite without recording the change in that source. Restrict write access to configuration and private key material. The service identity should read the files it needs but should not be able to modify its own executable configuration or gain broad administrative access.

A safe change has a bounded diff and a recovery copy:

1. Identify the file(s), active service, and current configuration.
2. Save the prior known-good version with owner/mode preserved.
3. Make one coherent change and review the diff for hostname, upstream, ports, and secret material.
4. Run the proxy's native configuration validation.
5. Reload rather than restart when supported; check service state and logs immediately.
6. Test the external hostname and representative routes.
7. If checks fail, restore the known-good configuration, validate it, reload, and repeat the tests.

Never use an unvalidated reload or overwrite the only known-good configuration. A syntactically valid configuration may still route traffic incorrectly, so live verification is mandatory.

## Understand reload and rollback semantics

A reload generally asks the proxy to adopt new configuration while preserving the service; exact behavior differs. A restart can interrupt active connections and may leave the service down if startup fails. Record which operation your proxy/package supports and test it outside a critical window.

Keep deployment and proxy configuration changes distinct when diagnosing a problem. If app releases and proxy routes are changed together, a failure has more candidate causes and rollback is harder. Change one layer at a time unless a release explicitly requires coordinated changes.

Rollback the configuration artifact that caused the failure; do not delete certificates or application data as part of a proxy rollback. If the new proxy points to an incompatible app release, application rollback may also be needed. Preserve the failed configuration and sanitized error evidence for diagnosis.

## Logs: useful, bounded, and safe

Access logs help associate a request path/status/timing with a user-visible failure. Error logs help identify TLS, config, and upstream-connect errors. Application logs may provide the business-level cause. Correlate with request IDs if configured, but do not treat a client-supplied ID as trusted identity.

Log retention and rotation matter: unbounded access logs can fill a small VPS disk. Check where logs are written, who can read them, how they rotate, and whether containers send to stdout/stderr or files. Do not log authorization headers, session cookies, tokens, passwords, sensitive query parameters, or request bodies by default. Scrub evidence before sharing it.

Use the proxy's status and logs rather than broadening permissions or disabling TLS verification as a first response. A 502 and a 504 imply different upstream connection/response issues; inspect their error log details alongside the app's health and listener state.

## Operational checks to record

- Which service/container owns ports 80 and 443?
- Where is the source-of-truth config, and who can change it?
- How is the config validated and reloaded?
- Where are logs, how are they rotated, and what is retained?
- How are certificate data and private keys protected?
- What executes renewal, how is success observed, and who responds to failure?
- Which external probes validate the hostname and certificate?
- How is a previous configuration restored without changing application data?

Monitoring and actionable alert delivery are covered in the later Monitoring subject. This course still requires a human-readable method to inspect current state and determine renewal status.

## Knowledge check

1. Why does a successful config parse not prove the live site works?
2. What makes a config rollback safer than “trying another edit” during an outage?
3. Name information that should not be present in routine proxy logs.
4. Why should proxy configuration and app release changes be separated when possible?

## Practical checkpoint

Record the actual validation, reload, status, log, and restore commands for the selected proxy. Rehearse them in [Task 07 — Document proxy operations, renewal, and recovery](../tasks/07-document-proxy-operations-renewal-and-recovery.md).

## References

- [NGINX: Controlling nginx](https://nginx.org/en/docs/control.html)
- [NGINX: Logging](https://nginx.org/en/docs/http/ngx_http_log_module.html)
- [Caddy: Command line](https://caddyserver.com/docs/command-line)
- [Caddy: Logging](https://caddyserver.com/docs/caddyfile/directives/log)
