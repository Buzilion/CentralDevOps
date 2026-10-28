# 07 — Patching, dependency updates, and access reviews

## Learning objectives

You can plan OS and application updates according to risk, maintain an auditable dependency and credential lifecycle, coordinate reboots, and review access without locking out the service owner.

## Treat maintenance as a planned operational change

Production maintenance includes OS packages, kernel and runtime updates, container base images, application libraries, database engines, reverse proxy software, CI/CD actions, and credentials. Each update has a source, version, urgency, compatibility risk, validation path, and owner. A vulnerability's severity alone does not determine response: consider exploitability, exposure, available mitigations, data sensitivity, and provider guidance. Act promptly on actively exploited vulnerabilities.

Keep a concise inventory of supported components and where their versions are defined. Pin deployable artifacts for reproducibility, but do not interpret pinning as “never update.” Schedule regular review, test the update, and deliberately advance to a supported version. Subscribe to vendor/security advisories for components that do not update through the ordinary OS package manager.

## Define an update workflow

For a routine update:

1. Identify affected package/image/dependency, current version, target, security reason, and any required compatibility change.
2. Check release notes and known migration or reboot requirements.
3. Confirm backups and a usable recovery path when state or schema may change.
4. Test in a representative environment where feasible; run the application's actual build and tests.
5. Select a maintenance window if users may be affected and communicate expected impact.
6. Apply a bounded change; record package/artifact identifiers and results.
7. Verify service health, user-facing behavior, logs, alerts, and background work.
8. Record unresolved risk and next review date.

Automated security updates can reduce exposure but may restart services or install a change without application-level validation. Decide which packages can update automatically, how reboot-required status is detected, who reviews failures, and how a reboot is scheduled. Do not disable security updates indefinitely because one update once caused an interruption.

## Handle credentials and access as operational state

Review VPS accounts, SSH keys, sudo access, deployment credentials, GitHub Actions secrets, registry tokens, monitoring accounts, backup credentials, and provider-console access. For each, record its owner, scope, expiry/rotation process, and revocation method—not the secret itself. Remove departed or unused access promptly. Use least privilege and separate deploy, administration, and backup identities where practical.

Before rotating a credential, identify every consumer and stage the replacement so a partial rollout does not lock out the service or destroy the only recovery path. Verify new access, then revoke old credentials. Preserve at least one tested administrative/recovery route before tightening SSH or provider access. Store recovery codes and credentials only in the approved protected system.

## Keep supply-chain changes reviewable

Review dependency updates, Docker base images, workflow actions, and automation roles/modules. Use trusted sources and fixed versions or commit references consistent with the repository's policy. Limit workflow permissions and production deployment credentials. Do not run unreviewed scripts as root merely because they simplify an update. Capture what artifact was built and deployed so an incident can be tied to a source revision.

## Practical checkpoint

Complete [Task 07 — Complete a patching, dependency, and access review](../tasks/07-complete-patching-and-access-review.md).

## Knowledge check

1. Why is pinning an image not a security-update strategy by itself?
2. What should be confirmed before rotating a deployment credential?
3. How should unattended OS updates and required reboots be governed?
4. Which component versions should be included in the maintenance inventory?

## References

- [Ubuntu Server Guide — Security](https://documentation.ubuntu.com/server/how-to/security/)
- [GitHub Docs — Secure use reference](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [Docker Docs — Image digests](https://docs.docker.com/dhi/core-concepts/digests/)
