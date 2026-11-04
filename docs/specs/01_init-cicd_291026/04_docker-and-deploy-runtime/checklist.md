# Checklist for 01_init-cicd_291026/04_docker-and-deploy-runtime

Every task in `03_host-bootstrap-and-hardening/checklist.md` is checked off, and the repository owner has attested that the post-reset disposable-host hardening proof is complete in `docs/runbooks/bootstrap-vps.md`. This unblocks local spec 04 implementation only; spec 04's own disposable-host runtime acceptance is still required, and non-disposable service-host bootstrap remains blocked by the reviewed `DISPOSABLE_VPS_PROOF_COMMIT` gate. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: configure-workflow - On-demand configure workflow, Environment isolation, dispatch-App rejection, and fail-closed input preflight
- [ ] Task 2: configure-profiles - Ansible configure entrypoint, exact profile matrix, dry run and validated host/group limits
- [ ] Task 3: docker-networks - Versioned Docker Engine/Compose role and idempotent `edge`/`db` networks
- [ ] Task 4: deploy-runtime - Restricted deploy account, root-owned fail-closed scripts, and scoped sudo
- [ ] Task 5: deploy-credentials - Environment-specific deploy keys and root-only read-only GHCR token
- [ ] Task 6: runtime-acceptance - Disposable-host acceptance, runbook, and evidence
