# Checklist for 01_init-cicd_291026/03_host-bootstrap-and-hardening

> Implementation is blocked until every task in `01_foundation-and-access/checklist.md` is checked off.

- [x] Task 1: ansible-foundation - Pin Ansible dependencies and add the repository Ansible configuration
- [x] Task 2: environment-inventories - Add isolated inventories, host-key pin handling, and capacity facts
- [x] Task 3: bootstrap-baseline - Create the initial-access playbook and account, update, and firewall roles
- [ ] Task 4: key-gated-hardening - Prove admin-key access on 22, harden with temporary listeners on 22 and 4671, prove 4671, then finalize sshd/UFW to 4671 only.
- [ ] Task 5: bootstrap-workflow - Require a `base64:`-prefixed private-key secret, orchestrate the staged 22-to-4671 cutover and provider-firewall closure notice, and add post-proof Fail2ban activation/rollback.
- [ ] Task 6: disposable-vps-proof - Reverify the reset host key, prove bootstrap from port 22 through final port 4671, close provider port 22, and verify Fail2ban's 1d/1h/2-retry policy plus access-path recovery.
- [ ] Task 7: bootstrap-acceptance - Audit updated requirements and record evidence for spec 04.
