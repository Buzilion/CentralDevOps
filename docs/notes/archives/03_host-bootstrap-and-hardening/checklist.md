# Checklist for 01_init-cicd_291026/03_host-bootstrap-and-hardening

> Implementation is blocked until every task in `01_foundation-and-access/checklist.md` is checked off.

- [ ] Task 1: ansible-foundation - Pin Ansible dependencies and add the repository Ansible configuration
- [ ] Task 2: environment-inventories - Add isolated inventories, host-key pin handling, and capacity facts
- [ ] Task 3: bootstrap-baseline - Create the initial-access playbook and account, update, and firewall roles
- [ ] Task 4: key-gated-hardening - Prove independent admin-key login before applying SSH hardening
- [ ] Task 5: bootstrap-workflow - Add the protected, on-demand bootstrap workflow and credential lifecycle
- [ ] Task 6: disposable-vps-proof - Prove bootstrap, hardening, recovery, source policy, and brute-force controls on a disposable VPS
- [ ] Task 7: bootstrap-acceptance - Audit requirements and record evidence for spec 04
