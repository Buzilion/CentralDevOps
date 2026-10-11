# 06 — SSH, privilege escalation, and least privilege

## Learning objectives

You can configure Ansible's SSH connection without weakening host verification, explain `become`, and choose an automation account whose permissions and recovery implications are understood.

## SSH is the transport and host identity matters

Ansible typically authenticates to Linux hosts over SSH using a named account and a key held on the control node or accessed through a protected agent. Inventory can set `ansible_user`, `ansible_port`, and a private-key path, or the operator can provide connection options. Keep credentials out of source-controlled inventory. Ansible should verify the target's SSH host key just as a human SSH client should; disabling host-key checking invites a machine-in-the-middle connection to an unintended host.

Establish the VPS fingerprint through a trusted provider console or another independent channel, then populate the controller's `known_hosts` through a verified process. Do not blindly trust the first key observed on an untrusted network, and do not silence changed-key warnings without investigating whether the VPS was rebuilt or intercepted.

The SSH account should be non-root and have the narrowly intended login access. Use the recovery and access controls from the Linux and networking subjects. Do not put a private key in the repository, on the managed VPS, or in a command-line argument that can be captured in process listings or logs.

## Privilege escalation with `become`

SSH login identity and task execution identity are separate. `become: true` asks Ansible to elevate privileges, typically with `sudo`; `become_user` selects another execution account when needed. Apply escalation at the smallest useful scope—play, role, or task—and do not elevate tasks that need no privileged access.

The operator may need to provide a sudo password interactively (`--ask-become-pass`) or use a carefully reviewed automation policy. Non-interactive sudo can be convenient, but unrestricted passwordless sudo grants broad administrative authority to anyone who controls the SSH key or controller. Treat an automation account with root-equivalent sudo as highly privileged even though it cannot log in directly as root.

Starting with `become: true` does not require SSH as root. Prefer a non-root administrative login and explicit elevation. Verify both the login identity and the effective privileges on the intended target before a live play.

## Bootstrap and lockout risk

Ansible cannot use an SSH account that does not yet exist, a key that has not been installed, or network access blocked by the firewall. Bootstrap identity, host keys, and firewall reachability through the documented manual or provider process first. Do not create a circular dependency in which the playbook is the only way to restore the account or network access required to run that playbook.

Changes to SSH configuration, user keys, UFW, or provider rules can cut off the active control connection. For these changes:

1. Have provider console or an independently tested recovery route.
2. Keep the current SSH session open.
3. Validate generated configuration before reload.
4. Apply to one host with an explicit limit.
5. Open a new SSH session and verify `sudo` before closing the existing one.

Subject 2 contains the detailed SSH and firewall hardening procedure. Ansible should preserve those proven invariants; it should not change access policy merely to make a playbook pass.

## Knowledge check

1. Why are SSH authentication and `become` separate decisions?
2. What security impact does unrestricted passwordless sudo have?
3. Why is disabling SSH host-key checking not an acceptable workaround?
4. What independent recovery path should exist before automating SSH or firewall changes?

## Practical checkpoint

Complete [Task 02 — Create an inventory and prove SSH connectivity](../tasks/02-create-an-inventory-and-prove-ssh-connectivity.md), then review access before Task 06.
