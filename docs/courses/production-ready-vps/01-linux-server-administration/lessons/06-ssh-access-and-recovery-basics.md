# 06 — SSH access and recovery basics

## Learning objectives

You can describe the client/server roles in SSH, verify an access path without exposing private credentials, troubleshoot common connection failures, and preserve a recovery route before future hardening.

## SSH in this course

SSH provides an encrypted remote shell and file-transfer protocols. The client runs on your workstation; the server runs on the VPS. Authentication commonly uses a key pair: the private key stays under your control on the client, while the matching public key is authorized for an account on the server.

This lesson covers access verification and diagnosis. It does **not** prescribe final SSH daemon hardening, port exposure, brute-force controls, or firewall policy; those belong to the next roadmap subject and must be coordinated with provider networking and recovery options.

## Confirm the client-side context

On your workstation, check the exact target, account, key selection, and SSH configuration before connecting. A minimal connection is typically:

```sh
ssh USER@HOST
```

If a specific key is required:

```sh
ssh -i PATH_TO_PRIVATE_KEY USER@HOST
```

Use a private key only from your trusted local machine. Do not paste it into chat, a ticket, a server shell, or a repository. The private key is not the `.pub` file. Protect the local private key using the operating system's recommended credential storage and file permissions.

After login, verify the server and identity:

```sh
hostname
whoami
id
```

Confirm the hostname and account are the VPS you intend to administer, especially if you manage several environments.

## Host-key trust

On first connection, SSH presents a server host-key fingerprint. Verify it through a trusted independent source, such as the provider console or a known administrative record, before accepting it. The host key identifies the server endpoint; it is different from your user authentication key.

A changed host-key warning can indicate a legitimate rebuild or address reassignment, but it can also indicate interception or that you connected to the wrong host. Do not reflexively delete the old known-host entry or bypass the warning. Verify the new fingerprint through a trusted path, then update the local record deliberately.

## Diagnose from the outside inward

For a connection failure, separate common layers:

1. **Name/address:** does the hostname resolve to the intended VPS address?
2. **Network path:** is the VPS online and is the intended SSH port reachable according to provider and host firewall policy?
3. **Server daemon:** is SSH installed, running, and listening on the expected address/port?
4. **Host identity:** does the presented fingerprint match the trusted record?
5. **User authentication:** is the intended account valid and is the correct key offered?
6. **Authorization/session:** is that account permitted to log in and obtain a shell?

From the client, a bounded diagnostic can show connection details:

```sh
ssh -vvv -o ConnectTimeout=8 USER@HOST
```

Verbose output can reveal usernames, hostnames, addresses, key paths, and other operational metadata. Redact it before sharing. It must never include the contents of a private key; never enable or request private-key debug dumps.

After reaching the provider console or another authorized shell, inspect server-side state:

```sh
sudo systemctl status ssh --no-pager
sudo journalctl -u ssh --since '30 minutes ago' --no-pager
sudo ss -lntp
```

Some releases or configurations may use a different unit name or log destination. Confirm actual service names and logging configuration rather than assuming every host is identical. Do not restart or edit SSH settings over the only live SSH session.

## Recovery before hardening

Before changing access policy, know how to reach the provider's serial/VNC/web console, rescue environment, or support process, and ensure your account has the required provider permissions. Keep an existing session open while validating a replacement login in a second session. Confirm the replacement account and key can obtain the needed privilege. Only after independent verification should old access be removed.

If SSH stops working, stop making repeated blind configuration changes. Use the recovery console, inspect recent changes and service logs, validate configuration syntax using the appropriate tool, then restore a known-good configuration and verify a new connection. Maintain a record of the recovery procedure without storing credentials in it.

## Knowledge check

1. What is the difference between the SSH host key and your user key pair?
2. Why is a host-key change warning not safe to dismiss automatically?
3. Which troubleshooting layer is implicated by “connection refused” versus “permission denied”?
4. Why keep a working session open while validating a second login?
5. What is a safe response if the only SSH access is lost?

## Practical checkpoint

Complete [Task 05 — Prove SSH access and document recovery](../tasks/05-prove-ssh-access-and-document-recovery.md).
