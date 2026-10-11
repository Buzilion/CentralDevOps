# 06 — Persistent data, volumes, and safe storage handling

## Learning objectives

You can distinguish a container's disposable writable layer from persistent storage, choose between a named volume and a bind mount, and explain why persistent storage does not by itself provide backup or recovery.

## What survives replacement?

An image is immutable in normal operation. A running container adds a writable layer on top of it. That layer is tied to the container instance: removing the container removes the layer. Any data that must outlive container replacement must be deliberately stored elsewhere.

Docker offers two common storage forms:

| Storage type | Managed by | Typical use | Important consideration |
|---|---|---|---|
| Named volume | Docker Engine | Application/database state | Data is outside the container layer, but still resides on the VPS unless separately backed up. |
| Bind mount | Administrator chooses a host path | Configuration or deliberate host-managed data | Host path, ownership, permissions, and accidental over-mounting must be managed explicitly. |

Temporary storage such as a `tmpfs` mount is useful only for data that should not persist. Do not mount broad host paths such as `/`, `/etc`, or the Docker socket into an application container.

## Named volumes

A named volume has an explicit name and mount point in the container. It is suitable when Docker-managed persistent storage is desired and host-level file layout need not be directly manipulated. Inspect the volume and its mounts rather than guessing where Docker stores it; storage-driver details may vary.

```sh
docker volume ls
docker volume inspect VOLUME_NAME
docker inspect CONTAINER
```

Removing a container does not normally remove its named volume. Compose's `down` also normally preserves named volumes, but flags such as `--volumes`/`-v` can remove project volumes. Confirm what is named, external, anonymous, or bind-mounted before any teardown.

## Bind mounts and permissions

A bind mount exposes a host path inside a container. It can be useful for a read-only configuration file or intentionally host-managed content. It can also expose more of the host than intended. Prefer narrow paths, read-only mounts when possible, and a specific container user.

File ownership is represented by numeric UID/GID on Linux. A username inside a container does not necessarily match a host username. If an application cannot write its mount, identify the exact UID/GID and path, then adjust only the necessary directory. Do not solve the problem with `chmod -R 777`, broad ownership changes, or by mounting a writable host system directory.

## Persistence is not backup

A volume protects data from container replacement; it does not protect it from host disk failure, deletion, ransomware, incorrect migration, filesystem corruption, or loss of the VPS. A production backup must be independent of the live volume and have a tested restore procedure. Databases often need a database-aware backup method or a consistency strategy; blindly copying a live data directory may produce an unusable backup.

Before a later backup subject is complete, record the exact stateful paths, database engines, consistency requirements, and retention/recovery goals. Do not claim a backup exists because a Docker volume exists, and do not use a volume as the only copy.

## Safe persistence experiment

Use a clearly named disposable volume and non-sensitive sample data to test the lifecycle:

1. Create the volume and write a unique test marker using a short-lived container.
2. Remove that container.
3. Start another container mounting the same volume and read the marker.
4. Record the observed result and remove only the disposable test volume after confirming it contains no needed data.

This proves that the test volume outlives a container. It does not prove your application writes its state to that mount or that a backup can be restored.

## Storage capacity and observability

Images, writable layers, volumes, build cache, logs, and host package data all consume disk. Check available filesystem space and Docker usage before and after a deployment:

```sh
df -h
df -i
docker system df
docker volume ls
```

Inode exhaustion can occur even when a filesystem appears to have free bytes. Do not prune to fix an unexplained disk issue before identifying which project, image, or volume uses the space. A prune operation can remove rollback images or persistent data depending on flags.

## Knowledge check

1. Why does data written only into a container's writable layer disappear on recreation?
2. How does a named volume differ operationally from a bind mount?
3. Why is a persistent Docker volume not a backup?
4. What is a safer response than recursively making a mounted directory world-writable?

## Practical checkpoint

Complete [Task 05 — Prove data persistence and private service connectivity](../tasks/05-prove-data-persistence-and-private-service-connectivity.md).
