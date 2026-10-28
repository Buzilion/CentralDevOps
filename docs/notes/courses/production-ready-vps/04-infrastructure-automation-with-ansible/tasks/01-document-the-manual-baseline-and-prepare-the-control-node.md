# Task 01 — Document the manual baseline and prepare the control node

## Outcome

Create a reviewed, sanitized description of the VPS state Ansible is allowed to manage, and prepare a supported, version-recorded control environment without changing the VPS.

## Prerequisites

- Read [Lesson 01 — Ansible architecture](../lessons/01-ansible-architecture-control-nodes-and-managed-hosts.md).
- Complete the Linux, networking, and Docker subjects, including their recovery and runtime records.
- Have authorized access to the VPS and application operations records.

## Procedure

1. Choose a supported Linux/Unix control environment. On Windows, use a maintained Linux environment such as WSL2 rather than assuming native Windows is an Ansible control node.
2. Establish an isolated Python environment for Ansible. Install Ansible Core and any explicitly required collections using documented, repeatable versions. Do not install packages globally without understanding the effect on other projects.
3. Record `ansible --version`, Python version, OS, active config path, and installed collection versions in a private operations record.
4. Write a baseline matrix with each intended setting, current observed state, desired state, evidence/source of the decision, owner, risk, and verification method. Include only state already understood: for example, the administrative account, approved SSH policy, firewall allowlist, required system packages, Docker installation/service behavior, and any required host configuration.
5. Mark unknown or disputed settings as unresolved. Do not automate a value just because it is common in tutorials. Note which settings are owned by the VPS provider or a separate application deployment process.
6. Identify recovery paths for SSH, firewall, package, and Docker changes; verify access to provider console before including high-risk work.
7. Define evidence sanitization: record host aliases rather than public/private IPs, redact usernames if shared, and never capture keys, passwords, tokens, or production configuration values.

## Acceptance criteria

- [ ] The control environment is supported and uses an isolated, recorded Ansible installation.
- [ ] The active config-file path and collection dependencies are known.
- [ ] Every proposed automated setting has a source, desired value, verification step, and risk classification.
- [ ] Unknown settings and out-of-scope application-release responsibilities are explicitly identified.
- [ ] No VPS configuration was modified as part of this discovery task.
- [ ] Recovery access is verified or a blocking prerequisite is recorded.

## Deliverable

A private, sanitized baseline matrix and control-node record. Keep secrets and identifying VPS details outside the repository. Use this matrix as the approval boundary for later roles and playbooks.
