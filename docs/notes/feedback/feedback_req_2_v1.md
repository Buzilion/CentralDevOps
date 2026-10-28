## Open items decision

1. Production deployments must be approval-gated. Initially, I will be the required approver; once the deployment team is assigned, it should become the required approver (or be added if we decide both approvals are required). Cross-repo dispatch is not needed at this moment. Please use a same-repo workflow and standard GitHub Actions authentication if that meets the design. Validate the OIDC audience/claims and reusable-workflow secret behavior against the chosen design before building deploy-app.yml.
2. Sumopod VPS has it's own private network, firewall setting, and console. The S3 storage is different product. The S3 included info like S3 endpoint, region, bucket name, access key id, and secret access key. Sumopod has no snapshot nor API.
3. The backup destination should be to a S3 bucket. The same bucket that is defined on point 2 later.
4. Each app will either do migration using ORM like Prisma, or directly on the database using a well-known GUI for PostgreSQL.
5. Yes for Production: require and verify build provenance attestations. Staging can remain optional.
6. I don't think I needed it yet. Deployment records could be seen on GitHub Action tab on each app repos.
7. Current production VPS has 2vCPU, 4GB RAM, and 60GB SSD. The staging VPS should have less powerfull specs, but still support multiple app deployment in the VPS. Maybe the spec could be 1vCPU, 2GB RAM, and 20GB SSD (estimation). I don't know each VPS will contain how many exact app, but make sure that each VPS could support multiple app deployment in a single VPS.
8. I use exabytes.co.id as the domain provider. The DNS provider is *.masterweb.com. The A/AAAA record TTL is 14400 seconds.
9. Start on the current free plan only if its quotas cover the expected usage; estimate or measure ingestion, keep an eye on quotas, and upgrade or reduce log volume if needed. Ensure host-down and backup-age alerts are covered.
10. I confirm decisions A–I with the following changes and clarifications:
    - **A — revise:** Use a same-repo workflow; cross-repo dispatch is not needed now. Use standard GitHub Actions authentication/OIDC where appropriate, but first validate the token audience and claims and how environment secrets behave with the selected reusable-workflow design. Do not build `deploy-app.yml` until that spike confirms the design.
    - **B — retain the security goal, validate the mechanism:** Keep sensitive runtime data encrypted and avoid passing plaintext through artifacts. Confirm during the same-repo workflow spike whether a single age-encrypted bundle is still needed; do not add a bundle transfer if the chosen workflow does not cross a trust boundary.
    - **C — confirm:** Production must be approval-gated through the Production GitHub Environment. I will be the required approver initially; once the deployment team is assigned, make it the approver, or add it alongside me if we decide both approvals are required.
    - **D — confirm:** Enforce Compose policy centrally on the rendered configuration.
    - **E — revise:** Defer GitHub Deployments status integration. GitHub Actions run history in each app repository is sufficient for now; retain off-host backups for recovery.
    - **F — confirm:** Keep Staging and Production on separate VPS instances.
    - **G — confirm with clarification:** Each placement group maps to exactly one host in v3, but each host must be able to run multiple apps. Use capacity limits; the exact app count per VPS is not decided yet.
    - **H — confirm:** Commit reviewed host-key pins in `inventories/<env>/known_hosts`, not as secrets.
    - **I — confirm:** Back up databases every 6 hours to the S3 bucket described above. Keep encryption-key custody and the backup tool as open design items.daw

---

Notes: please don't keep generating new questions if not really necessary.