# Task 05 — Prove SSH access and document recovery

## Outcome

Verify which client, host, account, and authentication method provide access to the VPS, then create a credential-free recovery runbook that does not depend solely on the current SSH session.

## Prerequisites

- Read [Lesson 06 — SSH access and recovery basics](../lessons/06-ssh-access-and-recovery-basics.md).
- Authorized access from a trusted client.
- Access to the provider control panel, console, or documented recovery process.

## Procedure

1. On the client, identify the intended host, account, key selection, and any SSH config alias before connecting. Do not display or copy private-key contents.
2. Connect using the approved command, then verify the server identity and account:

   ```sh
   hostname
   whoami
   id
   ```

3. If the host fingerprint is new or changed, verify it through a trusted provider/administrative channel before accepting it. Do not bypass a warning merely to restore convenience.
4. If you need diagnostic detail, use a bounded connection timeout:

   ```sh
   ssh -vvv -o ConnectTimeout=8 USER@HOST
   ```

   Keep diagnostic output private and redact addresses, usernames, key paths, and hostnames before sharing. Do not run commands that reveal private-key contents.

5. In the provider console, identify where console/recovery access is launched, which provider role is required, and what recovery options are available. Record navigation and support links without storing passwords, recovery codes, or API tokens.
6. Write a private runbook containing:
   - A sanitized server identifier and the approved login account.
   - How to reach the provider console/rescue path and who has permission.
   - How to verify the host fingerprint from a trusted source.
   - The sequence to inspect SSH service status and recent SSH logs from the console.
   - Who to contact and what minimal sanitized evidence to provide.
   - A warning not to remove a known-good login until a second session is verified.
7. Optionally, if permitted and safe, test the provider console's read-only login path. Do not stop/restart SSH or edit its configuration for this task.

## Acceptance criteria

- [ ] The intended host and account were confirmed after login.
- [ ] Host-key trust was verified or the unresolved verification requirement is documented.
- [ ] The client-side private key was never copied to the VPS, repository, or evidence.
- [ ] A recovery path independent of the current SSH session is named and its access prerequisites are known.
- [ ] The runbook contains no credentials, private keys, tokens, or recovery codes.
- [ ] No SSH daemon or firewall policy was changed.

## Deliverable

A private, credential-free SSH access and recovery runbook, plus a sanitized verification note. Store secrets in an approved secret manager, not in the runbook.
