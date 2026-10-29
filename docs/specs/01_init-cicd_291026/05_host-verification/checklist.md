# Checklist for 01_init-cicd_291026/05_host-verification

Implementation is blocked until every task in `04_docker-and-deploy-runtime/checklist.md` is checked off and its disposable-host evidence is recorded. The spec-02 dispatch App identity and spec-01 workflow lint/name checker are also required before enabling the workflow. At each task close, add its sanitized summary under `summaries/`.

- [ ] Task 1: verification-workflow - Manual workflow, Environment selection, actor/ref rejection, and exact target preflight
- [ ] Task 2: read-only-check-framework - Ansible verifier, per-host result contract, and fail-closed aggregation
- [ ] Task 3: base-host-checks - Admin access, expected users, SSH policy, firewall, updates, and disk/inode measurements
- [ ] Task 4: docker-network-checks - Docker/Compose, `edge`/`db`, daemon exposure, and published-port checks
- [ ] Task 5: deploy-runtime-checks - Deploy account, script integrity/ownership, sudoers, and token-file permissions
- [ ] Task 6: verification-runbook - Safe operational runbook and future role-check extension contract
- [ ] Task 7: disposable-host-acceptance - Prove read-only behavior, failures, report completeness, and handoff evidence
