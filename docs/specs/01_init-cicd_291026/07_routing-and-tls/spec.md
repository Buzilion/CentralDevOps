# Spec 07: Routing and TLS

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 07 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation gated on completion of specs 04, 05 and 06 |
| Depends on | `04_docker-and-deploy-runtime`, `05_host-verification`, and `06_registry-and-compose-policy` (each checklist must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md` (`RTE`), `infrastructure-v1.md` (`INF`), `registry-and-policy-v1.md` (`REG`), `central-deployment-v1.md` (`DEP`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§2–7; `docs/design/naming-and-repository-conventions.md` §§3, 5, 7–8; v5 design §§6.2–6.4, 8.3–8.5, 9.1–9.2, 10.1–10.4, 12.1, 13.1, 15.1, 15.3, 16 steps 5–6 |

## What

Install and verify the shared Nginx proxy and Certbot renewal service; add the trusted HTTP and HTTPS templates, DNS precondition, and safe route activation behavior. The first release serves apps on the same host through the Docker `edge` network, issues per-domain HTTP-01 certificates, redirects HTTP to HTTPS, and keeps a bad route from changing the last known-good configuration.

This spec adds the route-management behavior behind the restricted `centraldevops-route` entrypoint created by spec 04. It does not implement the central deployment workflow, app-side smoke-test reporting, or split-host proxying.

## Context and sequencing

- Do not implement this spec until specs 04, 05 and 06 have complete checklists. Spec 04 supplies the proxy profile, Docker `edge` network and restricted route entrypoint; spec 05 supplies `verify-vps.yml`; spec 06 owns registry and manifest schemas and the `private_ip` schema value.
- Add role-level verification to the existing `verify-vps.yml` as each role is delivered (INF-18). Do not create a second verification workflow.
- The registry is the authority for allowed domains and placement. The app manifest may request a domain, service name, container port, health path and TLS preference only. The central deployment must validate the manifest against the registry before connecting to a host; the route script must not accept caller-supplied Nginx directives, template paths or configuration file paths.
- `routing.upstream_mode` accepts `docker_edge` and `private_ip` as registry data. This spec implements only `docker_edge`; reject `private_ip` before SSH or route changes until the separate-proxy capability is approved and delivered. Do not publish app ports for `docker_edge`.
- For `docker_edge`, the central deploy derives the reserved `EDGE_ALIAS` as `<app-slug>-<environment-path>` and supplies it to the routed Compose service. The route template uses the same alias; it is not an app-manifest field.
- Preserve `/usr/local/sbin/centraldevops-route`, its root ownership, non-deploy-writable permissions and sudo boundary from spec 04. Do not grant the deploy account Docker access or general shell privileges.
- Route activation is invoked only after the central deployment's app health check passes. Spec 11 owns the runner-side HTTPS smoke test, its run-summary result, and deployment locking/acceptance. This spec defines the route-script interface that spec 11 will call.
- DNS records remain manually managed at Masterweb. HTTP-01 requires public port 80; wildcard certificates, DNS-01 and CDN-fronted validation are not part of this release.

## Requirements

| ID | Statement | Source |
|---|---|---|
| RTE-01 | A registered app domain serves its healthy app over HTTPS; plain HTTP redirects to HTTPS. | §10.3 |
| RTE-02 | Routing mode is registry-owned. The initial all-in-one deployment uses `docker_edge` and its centrally derived edge alias; the registry schema also accepts `private_ip`, which this spec rejects at runtime until that capability is delivered. | §10.1 |
| RTE-03 | Before route activation, DNS A/AAAA results must match the proxy's public addresses from the selected inventory. A mismatch fails clearly before SSH or certificate issuance. | §10.2 |
| RTE-04 | After the app health check, validate the route plan against the registry allow-list, render trusted configuration, expose HTTP-01 for a new domain, validate and reload Nginx, obtain the certificate, then validate and reload the HTTPS route. | §10.3 |
| RTE-05 | Applying an unchanged route performs no route-file rewrite and no Nginx reload. | §10.3 |
| RTE-06 | A candidate configuration that fails `nginx -t` is rolled back on disk, is not reloaded, fails the operation, and does not affect other apps' routes. | §10.3 |
| RTE-08 | Certificates renew automatically; the renewal hook validates Nginx before reloading. Verification reports certificates with fewer than 21 days remaining as FAIL and provides an expiry signal for alerting. | §10.3 #7, §13.1 |
| RTE-09 | Routes use modern TLS, HTTP-to-HTTPS redirection, standard forwarded headers and bounded proxy timeouts. HSTS is enabled only for verified Production domains. | §10.3 #4 |
| RTE-10 | Certificate-issuance tests use the CA staging endpoint; no test issues a production certificate. | §10.3 #3 |

## Design

### Placement and configuration ownership

- Read `upstream_mode` only from the validated CentralDevOps registry. For `docker_edge`, route to `http://<edge_alias>:<container_port>` on the shared Docker `edge` network. Derive `edge_alias` as `<app-slug>-<environment-path>` (for example, `customer-builder-staging`); the app cannot choose it.
- Require the validated manifest's TLS preference to be `true`; reject a request to serve a registered public route without HTTPS.
- The `private_ip` registry value is schema-valid but not deployable in v1. The central preflight rejects it before opening SSH. Do not add a published-port exception or route to an arbitrary host supplied by an app.
- The central deployment checks the requested domain against that app/Environment's registry allow-list before connecting. The root-owned script separately validates the canonical hostname, app slug, Environment, port and mode; it accepts no raw Nginx snippets or caller-selected paths.
- Store one active route at `/opt/centraldevops/nginx/conf.d/<app>-<env>.conf`, where `<env>` is `staging` or `production`. Keep the shared ACME webroot at `/var/lib/letsencrypt`; only `/.well-known/acme-challenge/` is served from it.
- Store the proxy's independently verified public addresses in the proxy host's inventory as `proxy_public_ips`. The Ansible role installs them at `/etc/centraldevops/proxy-public-ips.json`, owned by root and not writable by the deploy account. Do not fall back to `ansible_host`, workflow input or app manifest values when this fact is absent.
- Configure Nginx listeners for the address families declared in `proxy_public_ips`. An AAAA answer is valid only when the proxy has a matching IPv6 address and its IPv6 HTTP/HTTPS listener and firewall path are configured.

### DNS precondition

- Run `deployment/tools/check-domain-dns.py` on the central runner before SSH for every route activation. Resolve the domain's terminal A/AAAA addresses and require the complete result set to equal `proxy_public_ips`. An empty result, unexpected address, missing expected address, invalid inventory value or resolver failure is a blocking error.
- Install the same DNS checker at `/usr/local/lib/centraldevops/check-domain-dns.py`; the host-side route command repeats the check immediately before a new Certbot request using `/etc/centraldevops/proxy-public-ips.json`. This closes the gap between runner preflight and issuance and prevents a direct route-script call from bypassing the precondition.
- A DNS failure must name the domain and explain the expected/observed mismatch without attempting Certbot. DNS is not changed automatically.

### Route activation and rollback

- The route command interface is:

  ```text
  centraldevops-route apply --app <slug> --environment <staging|production> \
    --domain <fqdn> --container-port <port> --upstream-mode docker_edge
  centraldevops-route confirm --app <slug> --environment <staging|production> \
    --domain <fqdn>
  ```

- `apply` is called only after the central health check and registry/manifest validation. It derives the route filename and edge alias itself. The command rejects malformed or unsupported inputs before touching Nginx or requesting a certificate.
- The central Compose-policy/deployment path must ensure the routed service advertises the same derived `EDGE_ALIAS` on the external `edge` network. `routing.tls: false`, an unlisted domain or a mismatch between the registry, manifest and route plan fails before SSH.
- For a new domain, render an HTTP-only challenge route, validate it with `nginx -t`, and reload Nginx. Request a webroot HTTP-01 certificate only after the DNS precondition passes. Then render the HTTPS route, validate it and reload. HTTP requests other than the ACME challenge redirect to HTTPS once the HTTPS route is active.
- For an existing route, render the HTTPS candidate directly when its certificate is valid; do not request a certificate on an unchanged deployment. When a domain changes, keep the current route serving until the new domain's HTTPS candidate validates and is ready to replace it.
- Render to a temporary file and atomically replace the active file. On `nginx -t` failure, restore the previous file (or remove a first-route candidate), do not reload the invalid configuration, and return a nonzero sanitized error. On reload failure, restore and validate the previous configuration, report the failure, and do not claim activation.
- If issuance for a new domain fails, retain only the validated HTTP-01 challenge route for retry; do not proxy app traffic over plain HTTP. If a prior route exists, it remains active.
- All route edits and reloads, including the Certbot deploy hook, use the same proxy-wide lock. Spec 11 owns the deployment-level locking contract and its concurrent-deployment acceptance test.
- If the rendered candidate is byte-for-byte unchanged, do not rewrite it or reload Nginx. Report an unchanged result.

### TLS policy, verification and renewal

- The HTTPS template permits TLS 1.2 and TLS 1.3 only. It redirects HTTP to HTTPS, forwards `Host`, `X-Real-IP`, `X-Forwarded-For` and `X-Forwarded-Proto`, and sets explicit bounded connect/read/send timeouts. App input cannot change these directives.
- A new or changed route starts without HSTS. After the runner-side HTTPS smoke test succeeds, spec 11 calls `confirm`. The route script records a root-owned confirmation for the current route fingerprint and enables HSTS only when the Environment is `production` and the confirmation still matches. A route/domain/TLS-policy change invalidates that confirmation; Staging never enables HSTS.
- Use a conservative `max-age=86400`; do not add `includeSubDomains` or `preload` in v1.
- Certbot renews through its systemd timer. Its deploy hook acquires the proxy lock, runs `nginx -t`, and reloads only when validation passes. If validation fails, it reports failure and does not reload.
- Extend the existing role-scoped verification to emit one certificate PASS/FAIL result per host, with sanitized per-domain days-remaining details. A certificate with fewer than 21 days remaining or already expired is FAIL. Publish `centraldevops_certificate_expiry_days{domain="..."}` in `/var/lib/centraldevops/metrics/certificate-expiry.prom` for the monitoring role; refresh it daily and after route/certificate changes. Spec 14 owns Grafana alert delivery. No configured certificate is not a failure when the registry expects no routes.

### Deployment integration and Q8 decision

- Spec 11 calls `apply` after the internal health check, runs the external HTTPS smoke test, and calls `confirm` only after that smoke test succeeds. A failed smoke test fails the deployment and is visible in the run summary.
- **Q8 decision:** a failed post-activation HTTPS smoke test reports failure but does not automatically roll back the app or route. DEP-12's automatic rollback remains limited to an app health-check failure, which occurs before route activation. Operators diagnose the external failure and may manually redeploy the previous digest. A new or changed Production route remains without HSTS until a successful smoke test is confirmed.

## Deliverables

```text
playbooks/configure.yml                         # add nginx/certbot to proxy and all-in-one profiles
playbooks/verify.yml                            # add Nginx and certificate checks
roles/nginx/
roles/nginx/tasks/verify.yml
roles/certbot/
roles/certbot/tasks/verify.yml
deployment/nginx-templates/http-only.conf.j2
deployment/nginx-templates/https.conf.j2
deployment/scripts/centraldevops-route
deployment/scripts/centraldevops-certbot-deploy-hook
deployment/scripts/centraldevops-compose-policy       # add the route-alias assertion
deployment/tools/check-domain-dns.py
deployment/tools/check-cert-expiry.py
deployment/tools/tests/
docs/runbooks/routing-and-tls.md
```

The roles also add the verified `proxy_public_ips` inventory fact to `/etc/centraldevops/proxy-public-ips.json`. Do not add sample host addresses or issue certificates while configuring a host.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Implement `docker_edge` only; accept `private_ip` in the registry schema but fail closed if selected for deployment. | Enable split-host routing now | The initial topology is all-in-one, and private publishing/firewall policy is a separate capability (RTE-13). | Yes |
| D2 | Use `proxy_public_ips` from the selected proxy host inventory for exact DNS comparison, both before SSH and immediately before issuance. | Infer the public IP from `ansible_host` or a workflow input | SSH and public addresses can differ; inventory is the reviewed source of host facts. | Yes |
| D3 | Derive the edge alias as `<app-slug>-<environment-path>` and keep Nginx directives platform-owned. | Accept an alias or Nginx fragment from the app | Keeps route identity deterministic and prevents app-controlled proxy configuration. | Yes |
| D4 | Enable HSTS only after a successful external HTTPS smoke test for the current Production route; never use `includeSubDomains` or `preload`. | Enable HSTS on first certificate issuance | Avoids caching HTTPS policy before the route has been externally verified and avoids a broad subdomain commitment. | Yes |
| D5 | A failed HTTPS smoke test fails and reports the deployment but does not automatically roll back the app or route. | Roll back app and route automatically | The design specifies automatic rollback for container health failures only; a smoke failure can be external/transient and has no agreed rollback contract. | Yes |
| D6 | Use the CA staging endpoint for all certificate-issuance tests; only a real, approved deployment may use the production endpoint. | Use production CA for acceptance tests | Avoids consuming production issuance and failed-validation limits. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Only a registry-allowed domain can reach route activation. | Negative test: an unlisted manifest domain fails before SSH and Certbot. |
| The initial route uses the derived edge alias and never publishes an app port. | Inspect the validated Compose config, registry mode and rendered Nginx upstream. |
| DNS mismatch cannot trigger certificate issuance. | Test wrong/missing A and AAAA answers; assert no SSH and no Certbot invocation. |
| A failed Nginx validation never reloads the candidate or changes other apps' active routes. | Inject an invalid candidate and inspect the restored file, reload count and a second app's response. |
| An unchanged route produces zero file rewrites and zero Nginx reloads. | Apply the same validated plan twice and compare file metadata and reload events. |
| Only verified Production routes contain HSTS. | Test unverified/changed routes and every Staging route without HSTS; confirm only a matching verified Production route has the header. |
| Renewal never reloads invalid Nginx configuration. | Force `nginx -t` to fail in the deploy-hook test and assert no reload. |
| Certificate expiry below 21 days is a verification failure and an alertable signal. | Use a synthetic near-expiry certificate; verify FAIL and the expected metrics sample. |
| Route and renewal mutations are serialized. | Assert all route/reload paths use the shared lock; spec 11 proves cross-deployment serialization. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Any dependency checklist is incomplete. | Do not implement or run this spec against a host; identify the incomplete prerequisite. |
| Proxy group does not resolve to exactly one host, or `proxy_public_ips` is absent/invalid. | Fail preflight before SSH; do not guess an address. |
| DNS resolution is empty, fails, or contains an address outside the inventory set. | Fail with a clear domain/address diagnostic before SSH and without requesting a certificate. |
| Domain is not in the app/Environment registry allow-list, a manifest field is invalid, or `upstream_mode` is `private_ip`. | Fail central preflight before SSH; do not create or modify a route. |
| Route script receives a malformed slug, Environment, hostname, port or mode. | Reject before file access, Nginx reload or Certbot invocation. |
| `nginx -t` rejects a candidate. | Restore the last known-good file, do not reload the candidate, fail with sanitized diagnostics. |
| Certbot issuance fails or is rate-limited. | Do not activate HTTPS or proxy app traffic over HTTP; retain only a validated challenge route for retry and surface the Certbot result. |
| Renewal validation fails. | Keep the current Nginx process/configuration, do not reload, fail the renewal hook and expose the failure for alerting. |
| HSTS confirmation fails validation or the route fingerprint changed. | Keep the valid HTTPS route without HSTS, do not set a verified marker, and fail the confirmation. |
| External HTTPS smoke test fails after activation. | Fail and report the run without automatic app/route rollback; do not confirm a new or changed route for HSTS. |

## Testing Strategy

- **Static/config tests:** run the repository workflow/name checks, `ansible-lint`, playbook syntax checks and role-level tests. Render both templates with safe fixtures and require `nginx -t` to pass.
- **DNS tests:** matching IPv4/IPv6, missing answers, stale A/AAAA records, unexpected extra addresses, invalid inventory values and resolver errors. Prove a failed preflight prevents SSH and Certbot.
- **Route-script tests:** malformed input, unlisted route plan, unsupported mode, first route, changed route, invalid Nginx candidate, reload failure, unchanged route and two-app isolation. Assert file rollback, reload counts and sanitized errors.
- **TLS/HSTS tests:** reject TLS 1.0/1.1; verify HTTP redirect and ACME challenge behavior; verify HSTS is absent by default and in Staging, present only after a matching Production confirmation, and absent again after a route change.
- **Certificate tests:** use only the CA staging endpoint for issuance and renewal dry runs. Test the deploy hook with passing and failing `nginx -t`; use synthetic certificates around the 21-day threshold for verification and metrics.
- **Disposable-host acceptance:** exercise a test domain on a disposable Ubuntu host, never a Production host or Production certificate. Record route behavior, idempotence, renewal, rollback and verification evidence in the task summary.
- **Runbook:** document DNS setup, preflight behavior, first issuance, renewal, verification, common failures and safe recovery. Keep secrets and private host credentials out of evidence.

## Out of Scope

- Completing prerequisites from specs 04, 05 and 06; this spec only consumes their contracts.
- The runner-side HTTPS smoke-test implementation and app/central run-summary reporting (RTE-07), and deployment-level lock acceptance (RTE-11); spec 11 owns these. This spec supplies the route `confirm` interface and shared mutation lock.
- Certificate-rate-limit recovery instructions in the disaster-recovery runbook (RTE-12; spec 13).
- Operating `private_ip` mode on a separate proxy host (RTE-13), CDN/proxy-fronted validation changes (RTE-14), DNS automation, DNS-01 and wildcard certificates.
- Automatic rollback after the external HTTPS smoke test; the decision for Q8 is recorded above.
- App source, app health-check implementation, deployment authorization, general registry/Compose policy and capacity checks (spec 06), database, backup or general alert routing. Task 3 adds only the route-specific derived-alias assertion needed for `docker_edge`.
