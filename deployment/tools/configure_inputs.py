#!/usr/bin/env python3
"""Validate configure workflow inputs before selecting an Environment job."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from bootstrap_inventory import (
    BootstrapValidationError,
    ENVIRONMENTS,
    load_inventory_document,
    validate_dispatch,
    validate_public_admin_key,
)


ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = Path("deployment/tools/configure-profiles.json")
SUPPORTED_PROFILE_CHOICES = frozenset(
    {"app", "proxy", "database", "monitoring", "all-in-one"}
)
CONFIGURE_REQUIRED_INVENTORY_FACTS = (
    "bootstrap_admin_public_key",
    "docker_engine_package_version",
    "docker_containerd_package_version",
    "docker_buildx_package_version",
    "docker_compose_plugin_package_version",
    "docker_db_subnet_cidr",
    "docker_default_address_pools",
    "deploy_runtime_public_key",
)
LIMIT_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")
ROLE_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z")
VERSION_PATTERN = re.compile(r"[0-9][A-Za-z0-9.+:~_-]*\Z")
ENVIRONMENT_HOST_PREFIXES = frozenset({"stg-", "prd-"})
RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
SECRET_ENVIRONMENT_NAMES = frozenset(
    {
        "ANSIBLE_SSH_PRIVATE_KEY",
        "ANSIBLE_VAULT_PASSWORD",
        "BACKUP_RESTIC_PASSWORD",
        "BACKUP_S3_ACCESS_KEY_ID",
        "BACKUP_S3_SECRET_ACCESS_KEY",
        "DEPLOY_RUNTIME_AGE_PRIVATE_KEY",
        "DEPLOY_SSH_PRIVATE_KEY",
        "GHCR_PULL_TOKEN",
        "MONITORING_GRAFANA_CLOUD_TOKEN",
        "VPS_INITIAL_ACCESS_PASSWORD",
    }
)


class ConfigureValidationError(ValueError):
    """Raised when a configure request cannot be safely targeted."""


@dataclass(frozen=True)
class ConfigureProfileConfig:
    profiles: Mapping[str, tuple[str, ...]]
    required_inventory_facts: tuple[str, ...]


@dataclass(frozen=True)
class ConfigureRequest:
    target_environment: str
    profile: str
    inventory_path: Path
    limit: str
    check_mode: bool
    target_hosts: tuple[str, ...]
    inventory_document: Mapping[str, Any]


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigureValidationError(
                f"configure profile file contains duplicate key {key!r}"
            )
        result[key] = value
    return result


def load_configure_profile_config(root: Path) -> ConfigureProfileConfig:
    path = root / PROFILE_FILE
    try:
        with path.open("r", encoding="utf-8") as profile_file:
            data = json.load(profile_file, object_pairs_hook=_unique_json_object)
    except ConfigureValidationError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConfigureValidationError(
            f"cannot read configure profile file {path}"
        ) from exc

    expected_keys = {
        "configure_profiles",
        "configure_required_inventory_facts",
    }
    if not isinstance(data, dict) or set(data) != expected_keys:
        raise ConfigureValidationError(
            "configure profile file has an invalid structure"
        )

    raw_profiles = data["configure_profiles"]
    if (
        not isinstance(raw_profiles, dict)
        or set(raw_profiles) != SUPPORTED_PROFILE_CHOICES
    ):
        raise ConfigureValidationError(
            "configure profile file must define the exact supported profiles"
        )

    profiles: dict[str, tuple[str, ...]] = {}
    for profile, raw_roles in raw_profiles.items():
        if (
            not isinstance(raw_roles, list)
            or not raw_roles
            or not all(
                isinstance(role, str) and ROLE_NAME_PATTERN.fullmatch(role)
                for role in raw_roles
            )
            or len(raw_roles) != len(set(raw_roles))
        ):
            raise ConfigureValidationError(
                f"configure profile {profile!r} has an invalid role list"
            )
        profiles[profile] = tuple(raw_roles)

    raw_facts = data["configure_required_inventory_facts"]
    if not isinstance(raw_facts, list) or tuple(raw_facts) != (
        CONFIGURE_REQUIRED_INVENTORY_FACTS
    ):
        raise ConfigureValidationError(
            "configure profile file does not define the exact required inventory facts"
        )

    return ConfigureProfileConfig(
        profiles=profiles,
        required_inventory_facts=tuple(raw_facts),
    )


def inventory_validation_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        name: value
        for name, value in environment.items()
        if name not in SECRET_ENVIRONMENT_NAMES
    }


def _inventory_groups(
    inventory: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    metadata = inventory.get("_meta")
    hostvars = metadata.get("hostvars") if isinstance(metadata, Mapping) else None
    if not isinstance(hostvars, Mapping):
        raise ConfigureValidationError(
            "selected environment inventory has no host-variable map"
        )
    if not all(isinstance(host, str) and host for host in hostvars):
        raise ConfigureValidationError(
            "selected environment inventory contains an invalid host alias"
        )

    groups = {
        name: value
        for name, value in inventory.items()
        if name != "_meta" and isinstance(name, str) and isinstance(value, Mapping)
    }
    if "all" not in groups:
        raise ConfigureValidationError(
            "selected environment inventory has no all group"
        )
    if not hostvars:
        raise ConfigureValidationError(
            "selected environment inventory has no target hosts"
        )
    return groups, hostvars


def _hosts_for_group(
    group_name: str,
    groups: Mapping[str, Any],
    visiting: frozenset[str] = frozenset(),
) -> set[str]:
    if group_name in visiting:
        raise ConfigureValidationError(
            "selected environment inventory contains a group cycle"
        )
    group = groups.get(group_name)
    if not isinstance(group, Mapping):
        raise ConfigureValidationError(
            "selected environment inventory contains an invalid group"
        )

    hosts = group.get("hosts", [])
    children = group.get("children", [])
    if hosts is None:
        hosts = []
    if children is None:
        children = []
    if not isinstance(hosts, list) or not all(
        isinstance(host, str) and host for host in hosts
    ):
        raise ConfigureValidationError(
            "selected environment inventory contains invalid group hosts"
        )
    if not isinstance(children, list) or not all(
        isinstance(child, str) and child for child in children
    ):
        raise ConfigureValidationError(
            "selected environment inventory contains invalid group children"
        )

    result = set(hosts)
    for child in children:
        result.update(
            _hosts_for_group(child, groups, visiting | {group_name})
        )
    return result


def _selected_hosts(
    target_environment: str,
    limit: str,
    inventory: Mapping[str, Any],
) -> tuple[str, ...]:
    groups, hostvars = _inventory_groups(inventory)
    known_hosts = set(hostvars)
    if not limit:
        return tuple(sorted(known_hosts))

    expected_prefix = (
        "stg-" if target_environment == "Staging" else "prd-"
    )
    if any(limit.startswith(prefix) for prefix in ENVIRONMENT_HOST_PREFIXES):
        if not limit.startswith(expected_prefix):
            raise ConfigureValidationError(
                "limit host belongs to the other Environment"
            )

    if limit in known_hosts:
        return (limit,)
    if limit not in groups:
        raise ConfigureValidationError(
            "limit must exactly match a host alias or group in the selected inventory"
        )

    selected_hosts = _hosts_for_group(limit, groups)
    if not selected_hosts:
        raise ConfigureValidationError(
            "limit group has no hosts in the selected inventory"
        )
    unknown_hosts = selected_hosts - known_hosts
    if unknown_hosts:
        raise ConfigureValidationError(
            "selected inventory group references an unknown host"
        )
    return tuple(sorted(selected_hosts))


def _validate_profile_roles(
    root: Path,
    profile: str,
    profile_config: ConfigureProfileConfig,
) -> None:
    missing_roles = [
        role
        for role in profile_config.profiles[profile]
        if not (root / "roles" / role / "tasks" / "main.yml").is_file()
    ]
    if missing_roles:
        raise ConfigureValidationError(
            f"profile {profile!r} cannot run; missing required roles: "
            + ", ".join(missing_roles)
        )


def _private_ipv4_network(
    value: object, fact: str, host: str
) -> ipaddress.IPv4Network:
    try:
        network = ipaddress.ip_network(value, strict=True)
    except (TypeError, ValueError) as exc:
        raise ConfigureValidationError(
            f"inventory fact {fact!r} is not a valid CIDR for {host}"
        ) from exc
    if (
        not isinstance(network, ipaddress.IPv4Network)
        or not any(network.subnet_of(private) for private in RFC1918_NETWORKS)
        or network.prefixlen > 30
    ):
        raise ConfigureValidationError(
            f"inventory fact {fact!r} must be a private IPv4 subnet for {host}"
        )
    return network


def _validate_single_public_key(
    host: str,
    fact: str,
    value: object,
) -> None:
    if not isinstance(value, str) or len(value.strip().splitlines()) != 1:
        raise ConfigureValidationError(
            f"inventory fact {fact!r} must contain exactly one public key for {host}"
        )
    try:
        validate_public_admin_key(value)
    except BootstrapValidationError as exc:
        raise ConfigureValidationError(
            f"inventory fact {fact!r} is missing or malformed for {host}"
        ) from exc


def _validate_inventory_facts(
    host: str,
    host_variables: Mapping[str, Any],
    required_facts: tuple[str, ...],
) -> None:
    for fact in required_facts:
        value = host_variables.get(fact)
        if value is None or value == "":
            raise ConfigureValidationError(
                f"required inventory fact {fact!r} is missing for {host}"
            )

    for fact in required_facts:
        if fact.endswith("_package_version"):
            version = host_variables[fact]
            if (
                not isinstance(version, str)
                or VERSION_PATTERN.fullmatch(version) is None
            ):
                raise ConfigureValidationError(
                    f"inventory fact {fact!r} is not a pinned package version for {host}"
                )

    for fact in ("bootstrap_admin_public_key", "deploy_runtime_public_key"):
        _validate_single_public_key(
            host,
            fact,
            host_variables.get(fact),
        )

    db_subnet = _private_ipv4_network(
        host_variables["docker_db_subnet_cidr"],
        "docker_db_subnet_cidr",
        host,
    )
    address_pools = host_variables["docker_default_address_pools"]
    if not isinstance(address_pools, list) or not address_pools:
        raise ConfigureValidationError(
            f"inventory fact 'docker_default_address_pools' must be a non-empty list for {host}"
        )

    for pool in address_pools:
        if not isinstance(pool, Mapping):
            raise ConfigureValidationError(
                f"inventory fact 'docker_default_address_pools' is invalid for {host}"
            )
        base = _private_ipv4_network(
            pool.get("base"),
            "docker_default_address_pools.base",
            host,
        )
        size = pool.get("size")
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or size <= base.prefixlen
            or size > 30
        ):
            raise ConfigureValidationError(
                f"inventory fact 'docker_default_address_pools.size' is invalid for {host}"
            )
        if db_subnet.overlaps(base):
            raise ConfigureValidationError(
                f"docker_db_subnet_cidr overlaps a Docker address pool for {host}"
            )


def validate_request(
    *,
    root: Path = ROOT,
    target_environment: str | None,
    profile: str | None,
    limit: str | None,
    check_mode: str | None,
    reference: str | None,
    actor_id: str | None,
    inventory_document: Mapping[str, Any] | None = None,
    command_environment: Mapping[str, str] | None = None,
) -> ConfigureRequest:
    if (
        not isinstance(target_environment, str)
        or target_environment not in ENVIRONMENTS
    ):
        raise ConfigureValidationError(
            "target environment must be exactly Staging or Production"
        )
    try:
        validate_dispatch(target_environment, reference, actor_id)
    except BootstrapValidationError as exc:
        raise ConfigureValidationError(str(exc)) from exc

    profile_config = load_configure_profile_config(root)
    if not isinstance(profile, str) or profile not in profile_config.profiles:
        raise ConfigureValidationError(
            "profile must be exactly app, proxy, database, monitoring, or all-in-one"
        )
    _validate_profile_roles(root, profile, profile_config)
    if not isinstance(check_mode, str) or check_mode not in {"true", "false"}:
        raise ConfigureValidationError("check_mode must be true or false")
    if not isinstance(limit, str):
        raise ConfigureValidationError("limit must be one exact host or group name")
    if limit and LIMIT_PATTERN.fullmatch(limit) is None:
        raise ConfigureValidationError(
            "limit must be one exact host alias or group name without Ansible pattern syntax"
        )

    if inventory_document is None:
        try:
            inventory_document = load_inventory_document(
                root,
                target_environment,
                command_environment=inventory_validation_environment(
                    os.environ if command_environment is None else command_environment
                ),
            )
        except BootstrapValidationError as exc:
            raise ConfigureValidationError(str(exc)) from exc

    target_hosts = _selected_hosts(
        target_environment,
        limit,
        inventory_document,
    )
    _, hostvars = _inventory_groups(inventory_document)
    for host in target_hosts:
        host_variables = hostvars.get(host)
        if not isinstance(host_variables, Mapping):
            raise ConfigureValidationError(
                f"selected inventory has no variable map for {host}"
            )
        _validate_inventory_facts(
            host,
            host_variables,
            profile_config.required_inventory_facts,
        )

    return ConfigureRequest(
        target_environment=target_environment,
        profile=profile,
        inventory_path=ENVIRONMENTS[target_environment].inventory,
        limit=limit,
        check_mode=check_mode == "true",
        target_hosts=target_hosts,
        inventory_document=inventory_document,
    )


def write_github_output(path: Path, request: ConfigureRequest) -> None:
    values = {
        "target_environment": request.target_environment,
        "profile": request.profile,
        "inventory_path": request.inventory_path.as_posix(),
        "limit": request.limit,
        "check_mode": "true" if request.check_mode else "false",
    }
    with path.open("a", encoding="utf-8", newline="\n") as output_file:
        for name, value in values.items():
            output_file.write(f"{name}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one on-demand configure workflow request."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    environment = os.environ

    try:
        request = validate_request(
            root=arguments.root.resolve(),
            target_environment=environment.get("CONFIGURE_TARGET_ENVIRONMENT"),
            profile=environment.get("CONFIGURE_PROFILE"),
            limit=environment.get("CONFIGURE_LIMIT", ""),
            check_mode=environment.get("CONFIGURE_CHECK_MODE"),
            reference=environment.get("CONFIGURE_REF"),
            actor_id=environment.get("CONFIGURE_ACTOR_ID"),
        )
        output_path = environment.get("GITHUB_OUTPUT")
        if output_path:
            write_github_output(Path(output_path), request)
    except ConfigureValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print("Configure request preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
