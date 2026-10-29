# Checklist for 01_init-cicd_291026/04_docker-and-deploy-runtime

Implementation is blocked until every task in `03_host-bootstrap-and-hardening/checklist.md` is checked off and the disposable-host hardening proof is recorded.

- [ ] Task 1: configure-workflow - On-demand configure workflow, Environment isolation, dispatch-App rejection, and fail-closed input preflight
- [ ] Task 2: configure-profiles - Ansible configure entrypoint, exact profile matrix, dry run and validated host/group limits
- [ ] Task 3: docker-networks - Versioned Docker Engine/Compose role and idempotent `edge`/`db` networks
- [ ] Task 4: deploy-runtime - Restricted deploy account, root-owned fail-closed scripts, and scoped sudo
- [ ] Task 5: deploy-credentials - Environment-specific deploy keys and root-only read-only GHCR token
- [ ] Task 6: runtime-acceptance - Disposable-host acceptance, runbook, and evidence
