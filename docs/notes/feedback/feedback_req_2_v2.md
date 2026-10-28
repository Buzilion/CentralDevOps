## Open items decision

| # | Item | Status |
|---|---|---|
| 1 | **Same-repo workflow spike:** validate OIDC audience and claims (`repository`, `job_workflow_ref`, `environment`) for a reusable-workflow call; validate Environment-secret behavior (which repo's Environment/secrets a called workflow sees; where `DEPLOY_SSH_PRIVATE_KEY` can safely live); confirm whether a single age-encrypted bundle is still needed. The deployment model depends on it | **Open. Required before building `deploy-app.yml`** |
| 3 | Backup tool and encryption-key custody (destination resolved: Sumopod S3) | **Open** |
| 11 | GitHub paid plan for private repos (Environments depend on it). Environment secrets/variables were tested and work; document the plan/visibility assumption in the README so a downgrade is noticed | Assumption |

---
Answers:

1. Store separate DEPLOY_SSH_PRIVATE_KEY values as GitHub Environment secrets in CentralDevOps’s Staging and Production environments—never commit key files—and run the privileged deployment workflow in CentralDevOps, selecting the matching environment only after validating the request. That means using a CentralDevOps-context trigger (for example, authenticated cross-repository dispatch), not relying on the app’s workflow_call to access CentralDevOps secrets. Keep Production approval protection and ensure the selected environment and VPS target cannot disagree.
3. Use Restic for off-host backups to the Sumopod S3-compatible bucket. Continue PostgreSQL logical exports every six hours (pg_dump per database and pg_dumpall --globals-only), and back up those exports plus persistent application data with Restic. Use Restic’s client-side repository encryption with a unique, randomly generated, high-entropy repository password for each environment. Keep the recovery copy in the organization’s password manager, accessible to at least two authorized operators; provide it to automation as BACKUP_RESTIC_PASSWORD and install it on the host as a root-readable secret. Keep this recovery copy separate from the S3 credentials and outside the VPS, repository, and bucket. Use least-privilege S3 credentials; enable provider-side encryption/versioning if supported as additional protection, not as a substitute for client-side encryption. Verify the Sumopod endpoint with a test backup and isolated Staging restore before Production, then perform regular restore drills.
11. Once more, I've confirmed with my current Free plan, I CAN make github environment secrets/variable on my org repos. So, it shouldn't be a problem at all.