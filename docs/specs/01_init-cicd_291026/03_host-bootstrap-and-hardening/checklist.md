# Checklist for 01_init-cicd_291026/03_host-bootstrap-and-hardening

> Implementation is blocked until every task in `01_foundation-and-access/checklist.md` is checked off.

- [x] Task 1: ansible-foundation - Pin Ansible dependencies and add the repository Ansible configuration
- [x] Task 2: environment-inventories - Add isolated inventories, host-key pin handling, and capacity facts
- [x] Task 3: bootstrap-baseline - Create the initial-access playbook and account, update, and firewall roles
- [ ] Task 4: key-gated-hardening - Prove independent admin-key login before applying SSH hardening; the first disposable attempt failed at fresh SSH, and four later runs stopped at private-key validation before SSH.
- [ ] Task 5: bootstrap-workflow - Add the protected, on-demand bootstrap workflow and credential lifecycle; implementation is present, but live credential cleanup is blocked on Task 4 and the Environment key's passphrase/encoding status.
- [ ] Task 6: disposable-vps-proof - Prove bootstrap, hardening, recovery, source policy, and brute-force controls on a disposable VPS
- [ ] Task 7: bootstrap-acceptance - Audit requirements and record evidence for spec 04
