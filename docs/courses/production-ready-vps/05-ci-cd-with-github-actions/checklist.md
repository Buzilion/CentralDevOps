# CI/CD with GitHub Actions — Course Checklist

Complete this subject after **Linux Server Administration**, **Networking, DNS, and Firewall Security**, **Docker and Container Operations**, and **Infrastructure Automation with Ansible**. The application must already have an understood runtime contract, the VPS should have a reviewed baseline, and a known-good deployment/recovery method should exist. GitHub Actions delivers the application; Ansible owns host configuration. Never commit secrets, private keys, raw production data, or identifying VPS details.

## Lessons

- [ ] [01 — Workflow model, triggers, runners, and trust boundaries](lessons/01-workflow-model-triggers-runners-and-trust-boundaries.md)
- [ ] [02 — Application release contract and workflow design](lessons/02-application-release-contract-and-workflow-design.md)
- [ ] [03 — Testing, building, and artifact provenance](lessons/03-testing-building-and-artifact-provenance.md)
- [ ] [04 — Container registry and GHCR image delivery](lessons/04-container-registry-and-ghcr-image-delivery.md)
- [ ] [05 — Deployment credentials, environments, and approvals](lessons/05-deployment-credentials-environments-and-approvals.md)
- [ ] [06 — Safe SSH deployment and concurrency](lessons/06-safe-ssh-deployment-and-concurrency.md)
- [ ] [07 — Post-deployment verification and rollback](lessons/07-post-deployment-verification-and-rollback.md)
- [ ] [08 — Auditing, maintenance, and operational evidence](lessons/08-auditing-maintenance-and-operational-evidence.md)

## Hands-on tasks

- [ ] [Task 01 — Inspect the application and define the release contract](tasks/01-inspect-the-application-and-define-the-release-contract.md)
- [ ] [Task 02 — Add pull-request and branch verification](tasks/02-add-pull-request-and-branch-verification.md)
- [ ] [Task 03 — Publish a versioned image to GHCR](tasks/03-publish-a-versioned-image-to-ghcr.md)
- [ ] [Task 04 — Protect production deployment access](tasks/04-protect-production-deployment-access.md)
- [ ] [Task 05 — Deploy a selected image through a constrained SSH path](tasks/05-deploy-a-selected-image-through-a-constrained-ssh-path.md)
- [ ] [Task 06 — Verify a release and rehearse rollback](tasks/06-verify-a-release-and-rehearse-rollback.md)
- [ ] [Task 07 — Audit and document the production delivery path](tasks/07-audit-and-document-the-production-delivery-path.md)

## Subject completion gate

- [ ] The release contract is based on the actual application build, tests, runtime, health behavior, configuration, and migration requirements.
- [ ] Pull-request CI has no production secrets and fails for a deliberately failing required check.
- [ ] Release jobs use minimal per-job token permissions, reviewed full-SHA action pins, and protected source/ref rules.
- [ ] The tested image is published once, linked to source commit and workflow run, and deployable by immutable digest.
- [ ] GHCR publisher and VPS puller are separate principals; the VPS has only package-read access for private images.
- [ ] Production environment protection, reviewers, eligible refs, and secret scope are enabled and verified in repository settings.
- [ ] SSH uses a dedicated deploy identity and independently verified host key; no host-check bypass or unrestricted CI root shell exists.
- [ ] The VPS's effective Docker/OS privileges are understood, and the server-side deployment interface accepts only the intended release operation.
- [ ] Deployment is serialized, does not cancel an in-progress production change, and cannot accept arbitrary host/image/command inputs.
- [ ] Deployment success requires the expected digest and meaningful bounded readiness checks, not just a running container.
- [ ] Failure and rollback were rehearsed safely; the failed run remains failed, and database/persistent data recovery is addressed separately.
- [ ] Another authorized operator can trace, verify, halt, and recover a release using sanitized evidence and the documented runbook.
- [ ] Temporary credentials/access were removed or rotated; ongoing workflow, action, reviewer, and key maintenance has named owners.

## Exit criteria

Proceed to **Reverse Proxy, HTTPS, and Application Serving** only when an authorized release can be built, published, and deployed through the protected workflow, the running image is traceable to its source, and a safe recovery procedure has been proven. If required deployment protection is unavailable under the repository's plan, document the limitation and use an equivalent reviewed manual gate rather than implying that an unprotected environment is approved.
