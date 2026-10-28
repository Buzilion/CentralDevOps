# Module PRD: Routing and TLS (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `RTE` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

How an app's registered domain reaches its container over HTTPS: DNS precondition, proxy route activation, certificate issuance and renewal, and the placement contract that lets the proxy move to a separate host later.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| RTE-01 | Every deployed app is reachable at its registered domain over HTTPS through the shared proxy. Plain HTTP requests are redirected to HTTPS. | A request over HTTP is redirected to HTTPS. A request over HTTPS to the app's health path succeeds. | §10.3 |
| RTE-02 | The routing mode is data in the registry: `docker_edge` (proxy and app on the same host, over the Docker `edge` network) and `private_ip` (proxy on another host; the app is published only on its private IP and the firewall admits only the proxy host). `docker_edge` is implemented for the initial all-in-one hosts. | The all-in-one Staging app is served in `docker_edge` mode. The registry schema accepts `private_ip`. | §10.1 |
| RTE-03 | DNS A/AAAA records for each domain are created manually at the DNS provider (Masterweb) before the domain's first deployment. Before the first deployment of a domain, the deployment checks that it resolves to the proxy's public IP and fails with a clear message otherwise, without attempting certificate issuance. | A deployment with a domain not yet pointing at the proxy fails with an explanatory message and makes no certificate request. | §10.2 |
| RTE-04 | Route activation runs inside the central deployment after the health check. For a new domain: validate the domain against the allow-list, render the route from the trusted template, start with an HTTP-only route that serves the HTTP-01 challenge, validate and reload the proxy, obtain the certificate, render the HTTPS route and validate and reload again. | A new domain ends with a valid certificate and an HTTPS route. | §10.3 |
| RTE-05 | Route activation is idempotent. An unchanged route causes no file rewrite and no proxy reload. | Redeploying the same app with an unchanged manifest produces no proxy reload event. | §10.3 |
| RTE-06 | A route that fails proxy configuration validation restores the last known-good file, does not reload the proxy and fails the deployment. A bad route never affects other apps. | An injected invalid route fails the deployment while other apps keep being served. | §10.3 #5 |
| RTE-07 | After activation, an HTTPS smoke test runs from the runner. Its result is shown in the run summary and fails the run when unsuccessful. | A smoke-test failure is visible as a failed run with a clear message. | §8.3 #9, §10.3 #6 |
| RTE-08 | Certificates renew automatically. Each renewal validates the proxy configuration before reloading. Certificates expiring within 21 days are flagged by verification and raise an alert. | A renewal dry run succeeds. A certificate with fewer than 21 days left is reported FAIL by verification. | §10.3 #7, §13.1 |
| RTE-09 | The HTTPS route uses modern TLS, the HTTP to HTTPS redirect, forwarded headers and timeouts, and enables HSTS only after the domain is verified. | A TLS scan finds no legacy protocol. HSTS is present on verified production domains only. | §10.3 #4 |
| RTE-10 | Tests of certificate issuance use the certificate authority's staging endpoint. | No test run issues a production certificate. | §10.3 #3 |
| RTE-11 | Proxy configuration changes are serialised across apps so two deployments never edit or reload the proxy simultaneously. | See DEP-09. | §8.4 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| RTE-12 | The disaster recovery runbook accounts for certificate-authority rate limits when reissuing certificates for many domains after a rebuild. | The runbook states how many domains can be reissued and the fallback. | §13.3 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| RTE-13 | `private_ip` mode is implemented and exercised with a separate proxy host that has its own restricted deploy identity. | An app on host A is served by a proxy on host B, and backend ports are not public. | §10.1, §10.4 |
| RTE-14 | The certificate validation method is revisited if a CDN or proxy service is placed in front of the domains. | A written decision exists before the CDN is enabled. | §10.3 |
