# Task 02 — Prove DNS, firewall, and origin preconditions

## Outcome

Verify that domain resolution, the intended public web ports, and the private application upstream match the design before issuing a public certificate.

## Prerequisites

- Complete Task 01.
- Read [Lesson 02 — Domain, DNS, firewall, and listener preflight](../lessons/02-domain-dns-firewall-and-listener-preflight.md).
- Control the domain and have an independent client network. Confirm a provider console recovery path before firewall changes.

## Procedure

1. Record the intended hostname and expected A/AAAA answers using a sanitized alias in evidence. Confirm the authoritative DNS provider and compare its current records with the VPS provider's allocated addresses.
2. Publish only address families that are configured end to end. Query A and AAAA independently; test every published family from outside the VPS. Remove or correct a record that directs clients to an unready address.
3. Write an exposure matrix for SSH, HTTP, HTTPS, application, and database ports. For each, mark intended public reachability, owning firewall/listener, and test method.
4. Review provider firewall rules and host firewall status without changing SSH access blindly. Allow only 80/443 when the proxy is ready and the chosen serving/certificate design needs them. Preserve the established SSH policy.
5. Inspect host listeners and Docker published ports. Confirm the app listens on loopback/private network only and that no database or unrelated service has become public.
6. From the proxy's actual network namespace, query the application at its documented health/known route. Record status and response meaning; do not expose the upstream to make this test pass.
7. From a separate network, test intended public and expected-closed TCP ports for IPv4 and each published IPv6 endpoint. Investigate differences between provider, host, and Docker behavior.

## Acceptance criteria

- [ ] Authoritative and recursive DNS answers match the chosen endpoint or any cache difference is explained.
- [ ] Every published A/AAAA address is externally reachable only on intended ports.
- [ ] The provider and host firewall exposure matrices agree with the design.
- [ ] The application responds on the proxy-to-upstream path but is not directly reachable from the public internet.
- [ ] Database and other private service ports are externally unreachable.
- [ ] IPv4 and IPv6 results are separate; no untested AAAA record remains.
- [ ] Evidence includes test method and expected/observed outcomes, without credentials or identifying address details.

## Deliverable

A sanitized DNS snapshot, expected-exposure matrix, upstream health result, and external port-test report.
