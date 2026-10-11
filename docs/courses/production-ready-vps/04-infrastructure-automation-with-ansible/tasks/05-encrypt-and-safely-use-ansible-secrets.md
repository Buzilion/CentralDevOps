# Task 05 — Encrypt and safely use Ansible secrets

## Outcome

Demonstrate that a required secret can be stored encrypted, made available only to an authorized run, and kept out of task output and evidence.

## Prerequisites

- Read [Lesson 07 — Protecting secrets with Ansible Vault](../lessons/07-protecting-secrets-with-ansible-vault.md).
- Have an approved secret-storage approach and a trusted control node.
- Use a disposable, non-production test value; do not use an application or VPS production credential for this exercise.

## Procedure

1. First verify that a secret is genuinely needed by host configuration. If not, document that no production Ansible secret is required and keep the practice exercise isolated.
2. Create a temporary test vault file with a unique, non-sensitive test value using `ansible-vault create` or `ansible-vault encrypt_string`. Keep the vault password outside the project tree and source control.
3. Reference the vaulted variable from a narrowly scoped test task. Do not print it with `debug`; use `no_log: true` where a task's arguments or results could reveal it.
4. Run the test using an interactive vault prompt or the project's approved protected password source. Inspect output and diffs for disclosure. Do not enable `--diff` for secret-bearing rendered files.
5. Verify the vault file in the repository is ciphertext and that the test works only when the authorized vault key is supplied. Do not decrypt it to a plaintext file inside the repository.
6. Remove the temporary test secret and its test task when no longer needed, without deleting or altering unrelated vault data. If a legitimate secret remains, document owner, access, backup, and rotation procedure—not its value.
7. Review Git status and ignored files to ensure the password source, private key, decrypted scratch file, and plaintext test values are not being committed.

## Acceptance criteria

- [ ] Only a disposable test value was used, or the no-production-secret rationale is recorded.
- [ ] Secret data is encrypted at rest and the vault password is stored separately with controlled access.
- [ ] The task does not print the secret, and output/diff review found no disclosure.
- [ ] The encrypted data can be decrypted only through the authorized workflow.
- [ ] No vault password, private key, decrypted temporary file, or plaintext secret is present in version control.
- [ ] The procedure covers rotation/rekeying and response to accidental exposure.

## Deliverable

A sanitized Vault workflow record and either an encrypted, actually required variable file or evidence from a disposable exercise that has been cleaned up. Never include the vault password or any secret value in the deliverable.
