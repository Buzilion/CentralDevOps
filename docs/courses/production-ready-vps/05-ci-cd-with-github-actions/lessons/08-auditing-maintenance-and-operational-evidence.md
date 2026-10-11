# 08 — Auditing, maintenance, and operational evidence

## Learning objectives

You can review a delivery workflow as privileged production code, maintain its actions and credentials, and retain enough sanitized evidence to understand or investigate each deployment.

## Review the whole execution path

Before enabling production deployment, review more than the workflow YAML:

- Trigger/ref rules, protected branches and tags, and environment deployment restrictions.
- Token permissions for every job; secret scope and who can approve/use it.
- Action dependencies pinned to full commit SHAs and their update process.
- Shell quoting, expression interpolation, user-controlled inputs, and remote argument validation.
- Runner type, network reachability, workspace cleanup, and untrusted-code exposure.
- Package visibility, publishing identity, production pull credential, and retention policy.
- Server account, SSH key restrictions, host-key verification, script ownership, and effective Docker/root privileges.
- Health-check target, timeout, rollback behavior, migration compatibility, and operator path on failure.

Keep the workflow readable and small. Reusable workflows and composite actions can reduce duplication but also create an additional trust boundary; pin and review them. Do not solve a simple single-host deployment by introducing a persistent runner or new orchestration platform without a concrete requirement and security plan.

## Maintain the pipeline

Define who reviews workflow changes and action updates. Monitor dependency and action advisories, update pinned SHAs deliberately, and test changes before production. Rotate and revoke credentials on a schedule and after suspected exposure or operator changes. Remove obsolete deploy keys, environment secrets, package grants, and runner registrations. Review production environment reviewers and eligible refs periodically.

Use workflow logs as diagnostic evidence, not a place to store secrets or raw private infrastructure data. Avoid dumping the entire environment, Docker config, or SSH configuration. Retention should meet operational and organizational needs without keeping unnecessary sensitive output. Record the exact workflow run, commit, image digest, target environment, approver, start/end time, health result, and rollback outcome in a deployment record accessible to authorized operators.

Prepare for common failures:

| Symptom | First evidence to inspect |
|---|---|
| Workflow never starts | Trigger filters, workflow file path/ref, event type, repository Actions policy |
| CI job is skipped | `needs`, path filters, conditions, required status-check naming |
| Registry push fails | Job token permissions, package linkage/visibility, image name and registry login |
| SSH fails | Runner network path, key format/permissions, account authorization, verified host key |
| Image pull fails on VPS | Registry identity, package read grant, image reference/digest, architecture |
| Container starts but release fails | Compose result, logs, readiness endpoint, dependency state, migration outcome |
| Rollback cannot pull | Digest retention and server-side access to prior release |

Do not "fix" a failed deployment by disabling host-key verification, making the package public, granting broad repository permissions, exposing a database port, or pasting a secret into a log. Stop the rollout and fix the cause with the least privilege needed.

## Practical checkpoint

Conduct a review using the checklist above and retain a sanitized deployment record and a short incident/rollback runbook. Ensure another authorized operator can identify the deployed commit/digest and safely stop or restore service without needing undocumented personal credentials. Complete [Task 07 — Audit and document the production delivery path](../tasks/07-audit-and-document-the-production-delivery-path.md).

## Knowledge check

1. Why is a full commit SHA pin stronger than a mutable action tag?
2. What evidence lets an operator connect an incident to a source change?
3. Which routine credential cleanup actions reduce the blast radius of old access?
4. Why should disabling host-key checking never be used as a deployment troubleshooting fix?

## References

- [GitHub Actions: Security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [GitHub Actions: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Docs: Reviewing your security log](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-security-log)
