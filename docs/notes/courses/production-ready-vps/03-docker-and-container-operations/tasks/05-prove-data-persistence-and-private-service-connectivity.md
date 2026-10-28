# Task 05 — Prove data persistence and private service connectivity

## Outcome

Demonstrate that a deliberately selected Docker volume survives container replacement, and verify required service-to-service communication without exposing an internal port on the VPS.

## Prerequisites

- Read [Lesson 05 — Docker networking and Compose](../lessons/05-docker-networking-and-compose-service-operations.md) and [Lesson 06 — Persistent data and volumes](../lessons/06-persistent-data-volumes-and-safe-storage-handling.md).
- Completed Task 04, with a known Compose project and explicit data paths.
- Have a safe disposable test volume or non-production application dataset. Do not experiment on production data.

## Procedure

1. From Task 01 and the application's documentation, list every stateful path and determine whether the app actually needs a database or another persistent service. Do not infer that all container writes should persist.
2. For each required stateful path, record whether it uses a named volume, bind mount, external managed service, or is intentionally ephemeral. Inspect the effective Compose configuration and `docker inspect` mount details.
3. Create a disposable test volume and write a unique, non-sensitive marker to it from a temporary container. The following example uses a uniquely named volume and the official BusyBox image; run it in the same shell so `$TEST_VOLUME` remains set:

   ```sh
   TEST_VOLUME="course-persistence-test-$(date +%s)-$$"
   docker volume create "$TEST_VOLUME"
   docker run --rm --network none --mount "type=volume,source=$TEST_VOLUME,target=/data" busybox:1.37.0 sh -c 'printf "%s\n" "persistence-check" > /data/marker'
   docker run --rm --network none --mount "type=volume,source=$TEST_VOLUME,target=/data,readonly" busybox:1.37.0 cat /data/marker
   docker volume inspect "$TEST_VOLUME"
   ```

   The marker should be printed after the first temporary container is removed.
4. After confirming the volume name and marker, remove only this disposable volume with `docker volume rm "$TEST_VOLUME"`. Do not use volume-prune or broad `down -v` commands.
5. For every application dependency, inspect the Compose network membership and confirm the client uses the service name plus the container port. Confirm the database/backend does not have a host-published port.
6. Test service connectivity from the application container or an approved diagnostic container attached to the same private network. Use a test appropriate to the service; do not print credentials or rely only on `expose`.
7. Inspect `docker compose ps`, `docker network inspect`, `docker volume inspect`, `docker port`, and host listeners. Compare the result with the Subject 2 exposure matrix.
8. Record the backup requirement separately: volume persistence is not proof of an independent backup or tested restore. Do not claim recovery readiness until the later backup subject's restore exercise succeeds.

## Acceptance criteria

- [ ] Test marker remains available from the same named volume after its original container is removed.
- [ ] The disposable test volume is removed only after its identity and lack of needed data are confirmed.
- [ ] Application stateful paths and mount ownership/permissions are documented.
- [ ] Required containers can connect over the intended private network/service names.
- [ ] No application or database port is unintentionally published on the host.
- [ ] `docker port` and `ss` observations agree with the written exposure matrix.
- [ ] No production data was used for the persistence experiment.
- [ ] Volume persistence is explicitly distinguished from backup and restore.

## Deliverable

A sanitized storage/network evidence record listing stateful paths, volume or bind-mount choices, service network membership, test result, published-port inventory, and separate backup/restore requirements. Do not include secret connection strings or database contents.
