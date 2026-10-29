# Checklist for 01_init-cicd_291026/07_routing-and-tls

Implementation is blocked until every task in `04_docker-and-deploy-runtime/checklist.md`, `05_host-verification/checklist.md`, and `06_registry-and-compose-policy/checklist.md` is complete. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is accepted.

- [ ] Task 1: nginx-certbot-roles - Idempotent proxy and certificate-renewal roles in the existing configure profiles
- [ ] Task 2: trusted-route-templates - HTTP-01 and HTTPS templates with platform-owned proxy/TLS policy
- [ ] Task 3: dns-and-route-preflight - Inventory-bound DNS validation and docker_edge route-plan checks
- [ ] Task 4: atomic-route-activation - Restricted route entrypoint, HTTP-01 issuance, safe updates and HSTS confirmation
- [ ] Task 5: renewal-and-verification - Validated renewal hook, certificate-expiry checks and alertable metric
- [ ] Task 6: disposable-acceptance-and-runbook - Staging-CA acceptance evidence and routing/TLS operations runbook
