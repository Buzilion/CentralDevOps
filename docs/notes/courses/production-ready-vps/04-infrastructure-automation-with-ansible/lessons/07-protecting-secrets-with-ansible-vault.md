# 07 — Protecting secrets with Ansible Vault

## Learning objectives

You can distinguish encrypted-at-rest secret storage from runtime secret handling, encrypt a file or value with Ansible Vault, protect the vault password, and avoid common disclosure paths in diffs, logs, and evidence.

## What Vault does—and does not do

Ansible Vault encrypts data files or individual variables so that secret values need not be stored as plaintext in version control. It does not protect a secret after decryption, secure a compromised control node, rotate an exposed credential, or replace a deliberate access and backup policy. Anyone who has both the ciphertext and the vault password can decrypt it.

Before adding a secret, ask whether the server actually needs it during configuration. Prefer not to store application runtime secrets in host-provisioning variables if the app deployment process has a better secret store. Keep Ansible host configuration separate from application delivery and runtime secret distribution unless there is an explicitly designed interface.

## Encrypt and use secrets

An encrypted vars file can be created with:

```sh
ansible-vault create inventory/production/group_vars/production/vault.yml
```

Existing plaintext data can be encrypted locally with `ansible-vault encrypt`; individual values can use `ansible-vault encrypt_string`. Inspect metadata with `ansible-vault view` only in a trusted terminal, and edit encrypted content with `ansible-vault edit`. Never paste decrypted output into a terminal recording, ticket, shared chat, or evidence artifact.

At execution time, provide the password interactively with `--ask-vault-pass` or use a vault ID and an approved password source. If a password file is used, keep it outside the repository with restrictive permissions and ensure it is not backed up or logged in an unprotected location. Do not pass the password as a literal command-line argument. A vault ID labels which key should decrypt data; it does not make the key available securely by itself.

An encrypted file is safe to commit only if the repository's access and the key's storage are independently controlled. Keep the vault password out of the repository, build logs, shell history, and the same storage location as the ciphertext. Document authorized access, recovery, rotation, and re-encryption (`ansible-vault rekey`) without recording the key itself.

## Runtime disclosure controls

Vault encryption at rest does not prevent tasks or plugins from displaying decrypted values. Avoid debug output for secrets. Use `no_log: true` on tasks whose arguments or results contain sensitive values, understanding that this also reduces troubleshooting detail. Do not use `--diff` on secret-bearing templates or files unless you know the diff is safely suppressed; diff output may disclose rendered values. Redact task output and logs before retaining or sharing them.

Use separate, least-privilege credentials for different environments. Never reuse a production secret in a lab or test. If a secret is accidentally committed or emitted in logs, treat it as exposed: revoke or rotate it first, then remove it from future history and investigate exposure. Deleting the visible file alone does not invalidate a leaked credential.

## Knowledge check

1. What two things are required to decrypt a Vault file?
2. Why does encrypting a file not protect its contents from task output?
3. Why should a Vault password not be stored next to the encrypted data?
4. What is the correct response if a production secret has been committed?

## Practical checkpoint

Complete [Task 05 — Encrypt and safely use Ansible secrets](../tasks/05-encrypt-and-safely-use-ansible-secrets.md).
