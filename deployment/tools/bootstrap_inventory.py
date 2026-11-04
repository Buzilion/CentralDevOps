#!/usr/bin/env python3
"""Fail-closed input, inventory, capacity, and SSH host-key validation."""

from __future__ import annotations

import argparse
import base64
import binascii
import ipaddress
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class EnvironmentConfig:
    inventory: Path
    known_hosts: Path
    host_code: str


ENVIRONMENTS = {
    "Staging": EnvironmentConfig(
        inventory=Path("inventories/staging/hosts.yml"),
        known_hosts=Path("inventories/staging/known_hosts"),
        host_code="stg",
    ),
    "Production": EnvironmentConfig(
        inventory=Path("inventories/production/hosts.yml"),
        known_hosts=Path("inventories/production/known_hosts"),
        host_code="prd",
    ),
}

HOST_ALIAS_RE = re.compile(
    r"(?P<environment>stg|prd)-(?P<purpose>[a-z0-9]+(?:-[a-z0-9]+)*)-(?P<number>[0-9]{2})\Z"
)
USERNAME_RE = re.compile(r"[a-z_][a-z0-9_-]*\$?\Z")
HOSTNAME_RE = re.compile(
    r"(?=.{1,253}\Z)"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\Z"
)
FORBIDDEN_INVENTORY_SECRET_RE = re.compile(
    r"password|private[_-]?key|secret|(?:ssh|become)[_-]pass(?:word)?",
    re.IGNORECASE,
)

# Resolved from the completed spec-02 proof run's trusted actor metadata.
DISPATCH_APP_ACTOR_ID = 350767931
INITIAL_BOOTSTRAP_SSH_PORT = 22
MANAGED_SSH_PORT = 4671

# Set only after the disposable-host proof is recorded in the bootstrap runbook.
DISPOSABLE_VPS_PROOF_COMMIT: str | None = None


class BootstrapValidationError(ValueError):
    """Raised when bootstrap inputs or inventory facts are unsafe."""


def _environment_config(environment: str | None) -> EnvironmentConfig:
    if not isinstance(environment, str) or environment not in ENVIRONMENTS:
        raise BootstrapValidationError(
            "target environment must be exactly Staging or Production"
        )
    return ENVIRONMENTS[environment]


def validate_dispatch(
    environment: str | None,
    ref: str | None,
    actor_id: str | None,
    expected_actor_id: int | None = DISPATCH_APP_ACTOR_ID,
) -> None:
    _environment_config(environment)

    if not isinstance(ref, str) or not ref.startswith("refs/heads/"):
        raise BootstrapValidationError("dispatch ref must identify a branch")
    if environment == "Production" and not ref.startswith("refs/heads/release/"):
        raise BootstrapValidationError(
            "Production dispatches are allowed only from release branches"
        )
    if environment == "Production" and ref == "refs/heads/release/":
        raise BootstrapValidationError(
            "Production dispatches are allowed only from release branches"
        )

    if (
        isinstance(expected_actor_id, bool)
        or not isinstance(expected_actor_id, int)
        or expected_actor_id <= 0
    ):
        raise BootstrapValidationError(
            "dispatch App identity is not proven; bootstrap is disabled"
        )
    if not isinstance(actor_id, str) or not re.fullmatch(r"[0-9]+", actor_id):
        raise BootstrapValidationError("dispatch actor ID is invalid")
    try:
        numeric_actor_id = int(actor_id)
    except ValueError as exc:
        raise BootstrapValidationError("dispatch actor ID is invalid") from exc
    if numeric_actor_id == expected_actor_id:
        raise BootstrapValidationError(
            "dispatch from the deployment App identity is not allowed"
        )


def validate_target_alias(environment: str, target: str | None) -> str:
    config = _environment_config(environment)
    if not isinstance(target, str):
        raise BootstrapValidationError("target host must be one exact inventory alias")

    match = HOST_ALIAS_RE.fullmatch(target)
    if match is None or int(match.group("number")) == 0:
        raise BootstrapValidationError("target host alias has an invalid format")
    if match.group("environment") != config.host_code:
        raise BootstrapValidationError(
            "target host alias does not belong to the selected environment"
        )
    return target


def is_disposable_target(target: str, host: Mapping[str, Any]) -> bool:
    alias = HOST_ALIAS_RE.fullmatch(target)
    return (
        alias is not None
        and alias.group("purpose") == "disposable"
        and host.get("bootstrap_disposable") is True
    )


def validate_inventory_path(
    environment: str | None,
    provided_path: str | None,
    *,
    required: bool = False,
) -> Path:
    config = _environment_config(environment)
    expected = config.inventory.as_posix()
    if provided_path is None or provided_path == "":
        if required:
            raise BootstrapValidationError(
                "selected environment inventory path is not configured"
            )
        return config.inventory
    if provided_path != expected:
        raise BootstrapValidationError(
            "selected environment inventory path does not match the fixed mapping"
        )
    return config.inventory


def validate_public_admin_key(value: object) -> None:
    if not isinstance(value, str):
        raise BootstrapValidationError("the reviewed admin public key is missing")

    parts = value.strip().split()
    if len(parts) < 2 or parts[0] != "ssh-ed25519":
        raise BootstrapValidationError(
            "the reviewed admin key must be an Ed25519 public key"
        )
    try:
        key_blob = base64.b64decode(parts[1], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise BootstrapValidationError(
            "the reviewed admin public key is malformed"
        ) from exc

    key_type = b"ssh-ed25519"
    if len(key_blob) < 4:
        raise BootstrapValidationError("the reviewed admin public key is malformed")
    key_type_length = int.from_bytes(key_blob[:4], "big")
    key_type_start = 4
    key_data_length_start = key_type_start + key_type_length
    if (
        key_blob[key_type_start:key_data_length_start] != key_type
        or len(key_blob) < key_data_length_start + 4
    ):
        raise BootstrapValidationError("the reviewed admin public key is malformed")
    key_length = int.from_bytes(
        key_blob[key_data_length_start : key_data_length_start + 4], "big"
    )
    key_start = key_data_length_start + 4
    if key_length != 32 or len(key_blob) != key_start + key_length:
        raise BootstrapValidationError("the reviewed admin public key is malformed")


def _positive_integer(values: Mapping[str, Any], name: str, description: str) -> int:
    value = values.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BootstrapValidationError(f"{description} is missing or invalid")
    return value


def _valid_host_address(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return HOSTNAME_RE.fullmatch(value) is not None


def host_key_endpoint(host: str, port: int) -> str:
    if port == 22:
        return host
    return f"[{host}]:{port}"


def _require_host_key_pin(
    known_hosts_path: Path,
    endpoint: str,
    *,
    ssh_keygen: str = "ssh-keygen",
    command_environment: Mapping[str, str] | None = None,
) -> frozenset[tuple[str, str]]:
    if not known_hosts_path.is_file():
        raise BootstrapValidationError("selected environment host-key file is missing")
    keygen_environment = dict(
        os.environ if command_environment is None else command_environment
    )
    try:
        result = subprocess.run(
            [ssh_keygen, "-F", endpoint, "-f", str(known_hosts_path)],
            env=keygen_environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BootstrapValidationError(
            "could not inspect the selected environment host-key file"
        ) from exc

    if result.returncode == 1:
        raise BootstrapValidationError(
            "selected target has no committed host-key pin"
        )
    if result.returncode != 0:
        raise BootstrapValidationError(
            "could not inspect the selected environment host-key file"
        )
    key_material = set()
    for line in result.stdout.splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        parts = line.split()
        key_index = 2 if parts and parts[0].startswith("@") else 1
        if len(parts) > key_index + 1:
            key_material.add((parts[key_index], parts[key_index + 1]))
    if not key_material:
        raise BootstrapValidationError(
            "selected target host-key pin has no readable key material"
        )
    return frozenset(key_material)


def validate_inventory_target(
    environment: str,
    target: str,
    hostvars: Mapping[str, Any],
    known_hosts_path: Path,
    *,
    ssh_keygen: str = "ssh-keygen",
    command_environment: Mapping[str, str] | None = None,
    disposable_proof_commit: str | None = DISPOSABLE_VPS_PROOF_COMMIT,
    require_disposable: bool = False,
    require_initial_ssh_port: bool = True,
) -> Mapping[str, Any]:
    target = validate_target_alias(environment, target)
    if not isinstance(hostvars, Mapping) or not hostvars:
        raise BootstrapValidationError("selected environment inventory has no hosts")

    for alias in hostvars:
        validate_target_alias(environment, alias)

    host = hostvars.get(target)
    if not isinstance(host, Mapping):
        raise BootstrapValidationError(
            "target host is not an exact member of the selected inventory"
        )
    alias = HOST_ALIAS_RE.fullmatch(target)
    if require_disposable and not is_disposable_target(target, host):
        raise BootstrapValidationError(
            "this operation requires an explicitly flagged disposable host"
        )
    if disposable_proof_commit is None:
        if (
            alias is None
            or alias.group("purpose") != "disposable"
            or host.get("bootstrap_disposable") is not True
        ):
            raise BootstrapValidationError(
                "service-host bootstrap is blocked until the disposable VPS proof is recorded"
            )
    elif re.fullmatch(r"[0-9a-f]{40}", disposable_proof_commit) is None:
        raise BootstrapValidationError(
            "disposable VPS proof commit must be a full Git commit SHA"
        )

    if any(
        isinstance(name, str) and FORBIDDEN_INVENTORY_SECRET_RE.search(name)
        for name in host
    ):
        raise BootstrapValidationError(
            "inventory must not contain passwords, private keys, or secrets"
        )

    address = host.get("ansible_host")
    if not _valid_host_address(address):
        raise BootstrapValidationError("target host address is missing or invalid")

    provider_username = host.get("provider_username")
    if (
        not isinstance(provider_username, str)
        or USERNAME_RE.fullmatch(provider_username) is None
    ):
        raise BootstrapValidationError(
            "target provider username is missing or invalid"
        )

    port = host.get("ansible_port")
    if isinstance(port, bool) or not isinstance(port, int) or port != MANAGED_SSH_PORT:
        raise BootstrapValidationError(
            f"target SSH port must be {MANAGED_SSH_PORT}"
        )
    initial_port = host.get("bootstrap_initial_ssh_port")
    if require_initial_ssh_port and (
        isinstance(initial_port, bool)
        or not isinstance(initial_port, int)
        or initial_port != INITIAL_BOOTSTRAP_SSH_PORT
    ):
        raise BootstrapValidationError(
            f"initial bootstrap SSH port must be {INITIAL_BOOTSTRAP_SSH_PORT}"
        )
    if initial_port is not None and (
        isinstance(initial_port, bool)
        or not isinstance(initial_port, int)
        or initial_port != INITIAL_BOOTSTRAP_SSH_PORT
    ):
        raise BootstrapValidationError(
            f"initial bootstrap SSH port must be {INITIAL_BOOTSTRAP_SSH_PORT}"
        )
    managed_port = host.get("bootstrap_managed_ssh_port")
    if (
        isinstance(managed_port, bool)
        or not isinstance(managed_port, int)
        or managed_port != MANAGED_SSH_PORT
    ):
        raise BootstrapValidationError(
            f"managed SSH port must be {MANAGED_SSH_PORT}"
        )

    validate_public_admin_key(host.get("bootstrap_admin_public_key"))

    physical_memory = _positive_integer(
        host, "physical_memory_mib", "physical memory fact"
    )
    platform_reserve = _positive_integer(
        host, "platform_reserve_mib", "platform memory reserve"
    )
    capacity_budget = _positive_integer(
        host, "capacity_budget_mib", "application memory budget"
    )
    capacity_reference = host.get("bootstrap_capacity_reference")
    if not isinstance(capacity_reference, Mapping):
        raise BootstrapValidationError("environment capacity reference is missing")
    _positive_integer(
        capacity_reference,
        "physical_memory_mib",
        "reference physical memory",
    )
    _positive_integer(
        capacity_reference,
        "platform_reserve_mib",
        "reference platform reserve",
    )
    budget_ceiling = _positive_integer(
        capacity_reference,
        "capacity_budget_mib",
        "reference application memory budget",
    )
    if capacity_budget > physical_memory - platform_reserve:
        raise BootstrapValidationError(
            "application memory budget exceeds physical memory after platform reserve"
        )
    if capacity_budget > budget_ceiling:
        raise BootstrapValidationError(
            "application memory budget exceeds the environment reference ceiling"
        )

    source_cidrs = host.get("ssh_source_cidrs")
    if source_cidrs is not None:
        if not isinstance(source_cidrs, list):
            raise BootstrapValidationError("SSH source CIDRs must be a list")
        for cidr in source_cidrs:
            if not isinstance(cidr, str):
                raise BootstrapValidationError("SSH source CIDR is invalid")
            try:
                ipaddress.ip_network(cidr, strict=True)
            except ValueError as exc:
                raise BootstrapValidationError("SSH source CIDR is invalid") from exc
    if not source_cidrs:
        exception = host.get("ssh_source_policy_exception")
        if not isinstance(exception, str) or not exception.strip():
            raise BootstrapValidationError(
                "target needs a stable SSH source CIDR or a documented exception"
            )

    endpoint_ports = [port]
    if require_initial_ssh_port:
        endpoint_ports.insert(0, initial_port)
    endpoint_pins = [
        _require_host_key_pin(
            known_hosts_path,
            host_key_endpoint(address, endpoint_port),
            ssh_keygen=ssh_keygen,
            command_environment=command_environment,
        )
        for endpoint_port in endpoint_ports
    ]
    if len(endpoint_pins) == 2 and endpoint_pins[0] != endpoint_pins[1]:
        raise BootstrapValidationError(
            "initial and final SSH host-key pins do not match"
        )
    return host


def load_inventory_document(
    root: Path,
    environment: str,
    *,
    command_environment: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    config = _environment_config(environment)
    inventory_path = root / config.inventory
    if not inventory_path.is_file():
        raise BootstrapValidationError("selected environment inventory is missing")

    command = [
        "ansible-inventory",
        "--inventory",
        str(inventory_path),
        "--list",
    ]
    inventory_environment = dict(
        os.environ if command_environment is None else command_environment
    )
    inventory_environment["ANSIBLE_CONFIG"] = str((root / "ansible.cfg").resolve())
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=inventory_environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BootstrapValidationError(
            "ansible-inventory is required to validate the selected inventory"
        ) from exc
    if result.returncode != 0:
        raise BootstrapValidationError(
            "selected environment inventory could not be parsed"
        )
    try:
        inventory = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BootstrapValidationError(
            "selected environment inventory returned invalid JSON"
        ) from exc
    if not isinstance(inventory, dict):
        raise BootstrapValidationError(
            "selected environment inventory returned an invalid structure"
        )
    return inventory


def load_inventory(
    root: Path,
    environment: str,
    *,
    command_environment: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    inventory = load_inventory_document(
        root,
        environment,
        command_environment=command_environment,
    )

    metadata = inventory.get("_meta")
    hostvars = metadata.get("hostvars") if isinstance(metadata, dict) else None
    if not isinstance(hostvars, dict):
        raise BootstrapValidationError(
            "selected environment inventory has no host-variable map"
        )
    return hostvars


def validate_target(
    root: Path,
    environment: str | None,
    target: str | None,
    provided_inventory_path: str | None = None,
    *,
    require_inventory_path: bool = False,
    command_environment: Mapping[str, str] | None = None,
    require_disposable: bool = False,
    require_initial_ssh_port: bool = True,
) -> Mapping[str, Any]:
    if not isinstance(environment, str) or not isinstance(target, str):
        raise BootstrapValidationError(
            "target environment and host are required"
        )
    validate_inventory_path(
        environment,
        provided_inventory_path,
        required=require_inventory_path,
    )
    config = _environment_config(environment)
    hostvars = load_inventory(
        root,
        environment,
        command_environment=command_environment,
    )
    return validate_inventory_target(
        environment,
        target,
        hostvars,
        root / config.known_hosts,
        command_environment=command_environment,
        require_disposable=require_disposable,
        require_initial_ssh_port=require_initial_ssh_port,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a single-host bootstrap dispatch and inventory target."
    )
    parser.add_argument(
        "--stage",
        choices=("dispatch", "target", "all"),
        default="all",
        help="validate dispatch identity/ref, target inventory, or both",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--require-environment-inventory",
        action="store_true",
        help="require the selected GitHub Environment inventory variable",
    )
    arguments = parser.parse_args(argv)

    environment = os.environ.get("BOOTSTRAP_ENVIRONMENT")
    target = os.environ.get("BOOTSTRAP_TARGET_HOST")
    try:
        if arguments.stage in {"dispatch", "all"}:
            validate_dispatch(
                environment,
                os.environ.get("BOOTSTRAP_REF"),
                os.environ.get("BOOTSTRAP_ACTOR_ID"),
            )
        if arguments.stage in {"target", "all"}:
            target_facts = validate_target(
                arguments.root.resolve(),
                environment,
                target,
                os.environ.get("ANSIBLE_INVENTORY_PATH"),
                require_inventory_path=arguments.require_environment_inventory,
            )
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                disposable = is_disposable_target(target, target_facts)
                try:
                    with Path(github_output).open(
                        "a", encoding="utf-8", newline="\n"
                    ) as output:
                        output.write(
                            f"target_disposable={str(disposable).lower()}\n"
                        )
                except OSError as exc:
                    raise BootstrapValidationError(
                        "could not write the validated target output"
                    ) from exc
    except BootstrapValidationError as exc:
        print(f"bootstrap preflight failed: {exc}", file=sys.stderr)
        return 1

    print("Bootstrap preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
