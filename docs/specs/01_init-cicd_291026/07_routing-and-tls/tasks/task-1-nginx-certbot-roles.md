# Task 1: Nginx and Certbot roles

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Complete checklists for specs 04, 05 and 06 |
| Needs | Reviewed `proxy_public_ips` inventory facts; no Production certificate or workload |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Install the shared Nginx and Certbot host foundations through the existing Ansible configure operation, without creating an app route or issuing a certificate during configuration.

## Relevant files or references

- Update `playbooks/configure.yml`
- Create `roles/nginx/` and `roles/certbot/`
- Update the applicable proxy host inventory variables without adding sample addresses
- Spec sections: Placement and configuration ownership, TLS policy, Error Behavior
- INF-06, INF-18; RTE-08

## Proposed approach

1. Confirm the spec 04 configure profile and spec 05 verification contracts are complete before changing role mappings.
2. Add `nginx` and `certbot` to the existing `proxy` profile and deduplicated `all-in-one` profile; do not add them to unrelated profiles.
3. Configure Nginx with the platform-owned include directory `/opt/centraldevops/nginx/conf.d`, the shared webroot `/var/lib/letsencrypt`, and the root-owned `/etc/centraldevops/proxy-public-ips.json` generated from the proxy host's `proxy_public_ips`.
4. Require the inventory address list to be valid IPv4/IPv6 literals. Fail configuration if the proxy host lacks the fact; do not substitute `ansible_host` or invent a value.
5. Configure listeners for each public address family in `proxy_public_ips`; an IPv6 DNS answer is not accepted unless the host has an IPv6 listener and firewall path for ports 80/443.
6. Install Certbot and enable its systemd renewal timer. Keep ACME server selection in reviewed Ansible/host configuration, never in the app manifest or route command.
7. Make both roles idempotent and safe in Ansible check mode. Do not create app-specific server blocks or run `certbot certonly` from a role task.

## Acceptance criteria

- Configure profile mapping includes each role exactly where required; missing roles still fail preflight before SSH.
- Nginx owns the expected directories and includes only generated platform route files.
- The root-owned proxy-address configuration matches inventory and is readable by the route script; the deploy account cannot modify it.
- Nginx listeners and the verified firewall path match the configured IPv4/IPv6 address families.
- Certbot renewal timer is enabled, and role convergence issues no certificate and does not add an app route.
- A second unchanged role run reports zero changes.

## Source reference

INF-03, INF-06, INF-18; RTE-02, RTE-08; v5 §§6.2, 6.3, 10.2–10.3, 16 steps 5–6.

## Verify

- Run `ansible-lint` and `ansible-playbook --syntax-check` for the configure and verify playbooks.
- Run role tests with check mode and repeat an unchanged converge on a disposable test host.
- Inspect the resulting Nginx include paths, proxy-address file ownership, and Certbot timer state.

## Out of scope

Creating routes, contacting a certificate authority, changing firewall policy, or using a Staging/Production service host.
