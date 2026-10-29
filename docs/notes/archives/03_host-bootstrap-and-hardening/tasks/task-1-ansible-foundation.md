# Task 1: Ansible foundation

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Spec 01 fully checked off; first task in this spec |

## Goal

Introduce a reproducible Ansible controller configuration and pinned dependencies for the bootstrap work, without connecting to a VPS.

## Relevant files or references

- Create root `ansible.cfg` and `requirements.yml`
- `docs/design/naming-and-repository-conventions.md` §7
- Spec sections: Deliverables, Inventory and trust, Testing strategy

## Proposed approach

1. Confirm all tasks in spec 01's checklist are complete. If not, stop before changing files.
2. Confirm Sumopod offers Ubuntu Server 24.04 LTS. Choose a supported Ansible Core version and exact collection versions from their official release sources. Record the selected versions and supported Python/runner versions in the spec or task summary; do not use floating `latest` dependencies.
3. Configure Ansible to use repository-local roles/collections, disable host-key auto-acceptance, and use strict SSH host-key checking. Ensure the selected Environment's `known_hosts` is passed to the SSH client.
4. Add only collections required by bootstrap (for example `ansible.posix` and `community.general`) with exact version pins. Verify module support for the selected controller and target Ubuntu version before locking versions.
5. Document the install/check commands in the bootstrap runbook as the workflow equivalent; do not add provider credentials or real host facts.

## Acceptance criteria

- Ansible and each collection have exact version pins from official sources.
- Ubuntu Server 24.04 LTS is confirmed available from the provider and recorded as the target host release.
- Effective Ansible configuration enforces strict host-key checking and does not accept unknown keys.
- No password or private key appears in the new files.
- The pinned dependencies install in a clean Ubuntu runner and syntax checks can execute.

## Verify

```bash
ansible --version
ansible-galaxy collection list
ansible-config dump --only-changed
```

## Out of scope

Inventory content, playbooks, roles, SSH access, and workflow creation.
