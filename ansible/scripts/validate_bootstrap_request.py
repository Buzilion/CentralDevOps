#!/usr/bin/env python3
"""Validate the single-host bootstrap dispatch against the approved inventory."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DIRECTORY = Path("ansible") / "inventory"
INVENTORY_SUFFIXES = {".yml", ".yaml"}
SUPPORTED_ENVIRONMENTS = {"staging", "production"}
HOST_ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
HOST_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]*[$]?$")
SERVICE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DATABASE_IDENTIFIER_PATTERN = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.?$"
)
S3_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
S3_ENDPOINT_PATTERN = re.compile(r"^https://[A-Za-z0-9._~:/?=&%+-]+$")
S3_REGION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
BACKUP_INTERVAL_PATTERN = re.compile(r"^[A-Za-z0-9*.,/: _-]+$")
SENSITIVE_INVENTORY_KEY = re.compile(
    r"(?:password|private[_-]?key|secret|token|credential|api[_-]?key)",
    re.IGNORECASE,
)
POSTGRESQL_REQUIRED_INVENTORY_VARIABLES = (
    "bootstrap_postgresql_network_name",
    "bootstrap_postgresql_bucket",
    "bootstrap_postgresql_s3_endpoint",
    "bootstrap_postgresql_s3_region",
    "bootstrap_postgresql_backup_interval",
    "bootstrap_postgresql_backup_max_age_seconds",
)
SERVICE_INPUTS = {
    "docker": "BOOTSTRAP_SERVICE_DOCKER",
    "nginx": "BOOTSTRAP_SERVICE_NGINX",
    "postgresql": "BOOTSTRAP_SERVICE_POSTGRESQL",
    "alloy": "BOOTSTRAP_SERVICE_ALLOY",
}


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def available_inventory_paths() -> list[str]:
    inventory_directory = REPOSITORY_ROOT / INVENTORY_DIRECTORY
    if not inventory_directory.is_dir():
        return []
    return sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in inventory_directory.iterdir()
        if path.suffix.lower() in INVENTORY_SUFFIXES
        and not path.is_symlink()
        and path.is_file()
    )


def valid_absolute_inventory_path(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value == value.strip()
        and bool(re.fullmatch(r"/[A-Za-z0-9._/-]+", value))
        and ".." not in value.split("/")
    )


def validate_postgresql_inventory_configuration(
    variables: dict[str, Any], errors: list[str]
) -> None:
    missing = [
        name
        for name in POSTGRESQL_REQUIRED_INVENTORY_VARIABLES
        if name != "bootstrap_postgresql_backup_max_age_seconds"
        and (
            not isinstance(variables.get(name), str)
            or not variables[name].strip()
        )
    ]
    if missing:
        add_error(
            errors,
            "PostgreSQL requires inventory configuration for: "
            + ", ".join(missing)
            + ".",
        )

    for name in (
        "bootstrap_postgresql_network_name",
        "bootstrap_postgresql_container_name",
        "bootstrap_postgresql_compose_project_name",
        "bootstrap_postgresql_volume_name",
        "bootstrap_postgresql_backup_id",
    ):
        value = variables.get(name)
        if value is not None and (
            not isinstance(value, str)
            or not SERVICE_IDENTIFIER_PATTERN.fullmatch(value)
        ):
            add_error(errors, f"{name} must be a safe service identifier.")

    for name in (
        "bootstrap_postgresql_database_name",
        "bootstrap_postgresql_database_user",
    ):
        value = variables.get(name)
        if value is not None and (
            not isinstance(value, str)
            or not DATABASE_IDENTIFIER_PATTERN.fullmatch(value)
        ):
            add_error(errors, f"{name} must be a safe PostgreSQL identifier.")

    for name in (
        "bootstrap_postgresql_directory",
        "bootstrap_postgresql_config_directory",
        "bootstrap_postgresql_state_directory",
        "bootstrap_postgresql_compose_file",
    ):
        value = variables.get(name)
        if value is not None and not valid_absolute_inventory_path(value):
            add_error(errors, f"{name} must be a safe absolute Linux path.")

    bucket = variables.get("bootstrap_postgresql_bucket")
    if bucket is not None and (
        not isinstance(bucket, str) or not S3_BUCKET_PATTERN.fullmatch(bucket)
    ):
        add_error(errors, "bootstrap_postgresql_bucket must be a valid S3 bucket name.")

    endpoint = variables.get("bootstrap_postgresql_s3_endpoint")
    if endpoint is not None and (
        not isinstance(endpoint, str) or not S3_ENDPOINT_PATTERN.fullmatch(endpoint)
    ):
        add_error(errors, "bootstrap_postgresql_s3_endpoint must be an HTTPS endpoint.")

    region = variables.get("bootstrap_postgresql_s3_region")
    if region is not None and (
        not isinstance(region, str) or not S3_REGION_PATTERN.fullmatch(region)
    ):
        add_error(errors, "bootstrap_postgresql_s3_region contains unsupported characters.")

    interval = variables.get("bootstrap_postgresql_backup_interval")
    if interval is not None and (
        not isinstance(interval, str)
        or interval != interval.strip()
        or not BACKUP_INTERVAL_PATTERN.fullmatch(interval)
    ):
        add_error(errors, "bootstrap_postgresql_backup_interval contains unsupported characters.")

    max_age = variables.get("bootstrap_postgresql_backup_max_age_seconds")
    if type(max_age) is not int or max_age <= 0:
        add_error(
            errors,
            "bootstrap_postgresql_backup_max_age_seconds must be a positive integer.",
        )

    backup_namespace = variables.get("bootstrap_postgresql_backup_namespace")
    if backup_namespace is not None and backup_namespace != "" and (
        not isinstance(backup_namespace, str)
        or not HOST_ID_PATTERN.fullmatch(backup_namespace)
    ):
        add_error(
            errors,
            "bootstrap_postgresql_backup_namespace must be a lowercase application slug or empty.",
        )


def parse_boolean(name: str, errors: list[str]) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if value not in {"true", "false"}:
        add_error(errors, f"{name} must be true or false.")
        return False
    return value == "true"


def load_inventory(relative_path: str, errors: list[str]) -> dict[str, Any]:
    command = [
        "ansible-inventory",
        "--inventory",
        relative_path,
        "--list",
    ]
    result = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        add_error(
            errors,
            f"Could not load inventory {relative_path}: "
            + (detail[-1] if detail else "ansible-inventory failed."),
        )
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        add_error(errors, f"Inventory {relative_path} did not produce valid JSON: {error}.")
        return {}


def inventory_hosts(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return data.get("_meta", {}).get("hostvars", {})


def group_hosts(data: dict[str, Any], group_name: str) -> set[str]:
    hosts = data.get(group_name, {}).get("hosts", {})
    if isinstance(hosts, dict):
        return set(hosts)
    if isinstance(hosts, list):
        return set(hosts)
    return set()


def host_environments(data: dict[str, Any], host: str) -> set[str]:
    return {
        environment
        for environment in SUPPORTED_ENVIRONMENTS
        if host in group_hosts(data, environment)
    }


def bootstrap_environment_for(
    variables: dict[str, Any], environments: set[str]
) -> str | None:
    configured_environment = variables.get("bootstrap_environment")
    if configured_environment is not None:
        if (
            isinstance(configured_environment, str)
            and configured_environment in SUPPORTED_ENVIRONMENTS
        ):
            return configured_environment
        return None
    if len(environments) == 1:
        return next(iter(environments))
    return None


def sensitive_inventory_keys(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_text = str(key)
            if SENSITIVE_INVENTORY_KEY.search(key_text):
                found.append(key_text)
            found.extend(sensitive_inventory_keys(nested_value))
    elif isinstance(value, list):
        for nested_value in value:
            found.extend(sensitive_inventory_keys(nested_value))
    return found


def canonical_address(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return value.rstrip(".").lower()


def valid_connection_address(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return bool(HOSTNAME_PATTERN.fullmatch(value))
    return "%" not in value


def resolve_address(value: str) -> set[str]:
    try:
        return {str(ipaddress.ip_address(value))}
    except ValueError:
        return {
            item[4][0]
            for item in socket.getaddrinfo(value, None, type=socket.SOCK_STREAM)
        }


def write_outputs(outputs: dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        for name, value in outputs.items():
            print(f"{name}={value}")
        return
    with open(output_path, "a", encoding="utf-8", newline="\n") as output_file:
        for name, value in outputs.items():
            output_file.write(f"{name}={value}\n")


def main() -> int:
    errors: list[str] = []
    inventory_path = os.environ.get("BOOTSTRAP_INVENTORY", "").strip()
    inventory_paths = available_inventory_paths()
    inventory_stems = [Path(path).stem for path in inventory_paths]
    if len(inventory_stems) != len(set(inventory_stems)):
        add_error(errors, "Inventory filenames must have unique application stems.")
    target_host = os.environ.get("BOOTSTRAP_TARGET_HOST", "").strip()
    execution_mode = os.environ.get("BOOTSTRAP_EXECUTION_MODE", "").strip().lower()

    if inventory_path not in inventory_paths:
        add_error(
            errors,
            "Select an existing inventory YAML file under ansible/inventory.",
        )
    if execution_mode not in {"validate", "apply"}:
        add_error(errors, "Execution mode must be validate or apply.")
    if not HOST_ALIAS_PATTERN.fullmatch(target_host):
        add_error(errors, "Target host must be one exact inventory alias.")
    else:
        try:
            ipaddress.ip_address(target_host)
        except ValueError:
            pass
        else:
            add_error(errors, "IP addresses are not accepted as target host aliases.")

    requested_services = [
        service
        for service, variable in SERVICE_INPUTS.items()
        if parse_boolean(variable, errors)
    ]
    effective_services = list(requested_services)
    if any(service in requested_services for service in ("nginx", "postgresql")):
        if "docker" not in effective_services:
            effective_services.append("docker")
    effective_services.sort()
    requested_services.sort()

    default_branch = os.environ.get("DEFAULT_BRANCH", "").strip()
    git_ref = os.environ.get("GITHUB_REF", "").strip()
    if execution_mode == "apply" and (
        not default_branch or git_ref != f"refs/heads/{default_branch}"
    ):
        add_error(
            errors,
            "Apply is permitted only from the repository's default branch; "
            "use validate on other refs.",
        )

    inventories: dict[str, dict[str, Any]] = {}
    if inventory_path in inventory_paths:
        for approved_path in inventory_paths:
            inventories[approved_path] = load_inventory(approved_path, errors)

    selected_inventory = inventories.get(inventory_path, {})
    selected_hosts = inventory_hosts(selected_inventory)
    if target_host not in selected_hosts:
        add_error(errors, "Target host is not an alias in the selected inventory.")

    selected_hostvars = selected_hosts.get(target_host, {})
    application = Path(inventory_path).stem if inventory_path in inventory_paths else ""
    if application and not HOST_ID_PATTERN.fullmatch(application):
        add_error(
            errors,
            "Inventory filename must be a lowercase application slug using letters, "
            "numbers, and hyphens.",
        )
        application = ""

    if "postgresql" in requested_services:
        validate_postgresql_inventory_configuration(selected_hostvars, errors)

    selected_environment_groups = host_environments(selected_inventory, target_host)
    if len(selected_environment_groups) != 1:
        add_error(
            errors,
            "Target must belong to exactly one of the staging or production groups.",
        )
        application_environment = ""
    else:
        application_environment = next(iter(selected_environment_groups))

    explicit_environment = selected_hostvars.get("bootstrap_environment")
    if explicit_environment is not None:
        if (
            not isinstance(explicit_environment, str)
            or explicit_environment not in SUPPORTED_ENVIRONMENTS
        ):
            add_error(errors, "bootstrap_environment must be staging or production.")

    bootstrap_environment = bootstrap_environment_for(
        selected_hostvars, selected_environment_groups
    )
    if bootstrap_environment is None:
        bootstrap_environment = ""
    if (
        application_environment == "production"
        and bootstrap_environment != "production"
    ):
        add_error(
            errors,
            "Production aliases must use bootstrap_environment: production.",
        )

    for approved_path, data in inventories.items():
        for host_name, variables in inventory_hosts(data).items():
            forbidden = sorted(set(sensitive_inventory_keys(variables)))
            if forbidden:
                add_error(
                    errors,
                    f"Inventory contains credential-like fields for {host_name} "
                    f"in {approved_path}: "
                    + ", ".join(forbidden),
                )

    bootstrap_host_id = selected_hostvars.get("bootstrap_host_id")
    if not isinstance(bootstrap_host_id, str) or not HOST_ID_PATTERN.fullmatch(
        bootstrap_host_id
    ):
        add_error(
            errors,
            "Selected host must define a verified bootstrap_host_id using lowercase "
            "letters, numbers, and hyphens.",
        )
        bootstrap_host_id = ""

    bootstrap_user = selected_hostvars.get("bootstrap_user")
    if not isinstance(bootstrap_user, str) or not USERNAME_PATTERN.fullmatch(
        bootstrap_user
    ):
        add_error(
            errors,
            "Selected host must define the provider-created bootstrap_user in inventory.",
        )
        bootstrap_user = ""
    elif bootstrap_user == "deploy":
        add_error(errors, "bootstrap_user must be distinct from the managed deploy account.")

    ansible_host = selected_hostvars.get("ansible_host")
    if not valid_connection_address(ansible_host):
        add_error(
            errors,
            "Selected host must define ansible_host as an IP address or valid DNS name.",
        )
        ansible_host = ""

    selected_address = canonical_address(ansible_host)
    shared_host_collision = False
    same_address_records: list[tuple[str, str, dict[str, Any], set[str]]] = []
    selected_identity_records: list[tuple[str, str, dict[str, Any], set[str]]] = []
    selected_alias_records: list[str] = []

    for approved_path, data in inventories.items():
        for host_name, variables in inventory_hosts(data).items():
            address = canonical_address(variables.get("ansible_host"))
            environments = host_environments(data, host_name)
            record = (approved_path, host_name, variables, environments)
            if host_name == target_host:
                selected_alias_records.append(approved_path)
            if selected_address and address == selected_address:
                same_address_records.append(record)
            if bootstrap_host_id and variables.get("bootstrap_host_id") == bootstrap_host_id:
                selected_identity_records.append(record)

    if len(selected_alias_records) > 1:
        add_error(
            errors,
            f"Host alias {target_host} occurs in multiple approved inventories; "
            "select an unambiguous alias.",
        )

    if len(same_address_records) > 1:
        collision_aliases = sorted({record[1] for record in same_address_records})
        collision_id_values = [
            record[2].get("bootstrap_host_id") for record in same_address_records
        ]
        collision_ids = {
            value for value in collision_id_values if isinstance(value, str)
        }
        missing_identity = any(
            not isinstance(record[2].get("bootstrap_host_id"), str)
            or not HOST_ID_PATTERN.fullmatch(record[2].get("bootstrap_host_id", ""))
            for record in same_address_records
        )
        collision_bootstrap_environments: set[str] = set()
        missing_bootstrap_environment = False
        for record in same_address_records:
            record_environment = bootstrap_environment_for(record[2], record[3])
            if record_environment is None:
                missing_bootstrap_environment = True
            else:
                collision_bootstrap_environments.add(record_environment)
        if (
            missing_identity
            or len(collision_ids) != 1
            or missing_bootstrap_environment
            or len(collision_bootstrap_environments) != 1
        ):
            collision_id_summary = ", ".join(sorted(collision_ids)) or "missing or invalid"
            add_error(
                errors,
                "Unresolved ansible_host collision for "
                f"{selected_address} across aliases {', '.join(collision_aliases)}; "
                f"bootstrap_host_id values: {collision_id_summary}. Aliases must share "
                "one verified physical-host ID and one effective bootstrap_environment; "
                "set bootstrap_environment for cross-environment aliases.",
            )
        else:
            shared_host_collision = True

    if len(selected_identity_records) > 1:
        identity_addresses = {
            canonical_address(record[2].get("ansible_host"))
            for record in selected_identity_records
        }
        identity_bootstrap_environments: set[str] = set()
        missing_identity_bootstrap_environment = False
        identity_application_environments = {
            environment
            for record in selected_identity_records
            for environment in record[3]
        }
        for record in selected_identity_records:
            record_environment = bootstrap_environment_for(record[2], record[3])
            if record_environment is None:
                missing_identity_bootstrap_environment = True
            else:
                identity_bootstrap_environments.add(record_environment)

        if (
            len(identity_addresses) != 1
            or missing_identity_bootstrap_environment
            or len(identity_bootstrap_environments) != 1
        ):
            add_error(
                errors,
                f"bootstrap_host_id {bootstrap_host_id} maps to multiple addresses "
                "or bootstrap environments; cross-environment aliases must use one "
                "effective bootstrap_environment.",
            )
        elif (
            "production" in identity_application_environments
            and bootstrap_environment != "production"
        ):
            if application_environment != "production":
                add_error(
                    errors,
                    f"bootstrap_host_id {bootstrap_host_id} includes production aliases "
                    "and must use bootstrap_environment: production.",
                )
        else:
            shared_host_collision = True

    route: dict[str, Any] = {}
    route_fqdn = ""
    if "nginx" in requested_services and application_environment:
        routes_path = REPOSITORY_ROOT / "ansible" / "vars" / "bootstrap-routes.yml"
        try:
            with routes_path.open(encoding="utf-8") as route_file:
                route_data = yaml.safe_load(route_file) or {}
            route = route_data["bootstrap_routes"][application][application_environment]
            route_fqdn = str(route["fqdn"])
        except (OSError, KeyError, TypeError, yaml.YAMLError) as error:
            add_error(errors, f"Could not load the approved Nginx route mapping: {error}.")

        if route_fqdn and ansible_host:
            try:
                resolved_route = resolve_address(route_fqdn)
                resolved_target = resolve_address(str(ansible_host))
                inventory_ipv6 = selected_hostvars.get("bootstrap_ipv6_address")
                if inventory_ipv6:
                    resolved_target |= resolve_address(str(inventory_ipv6))
                if not resolved_route:
                    add_error(errors, f"Route FQDN {route_fqdn} has no DNS records.")
                elif not resolved_route.issubset(resolved_target):
                    add_error(
                        errors,
                        f"Route DNS for {route_fqdn} does not resolve only to the "
                        "selected VPS address; verify both A and AAAA records.",
                    )
            except OSError:
                add_error(
                    errors,
                    f"Could not resolve route FQDN {route_fqdn}; verify its A and AAAA records.",
                )

    normalized_host_id = bootstrap_host_id.upper().replace("-", "_")
    normalized_application = application.upper().replace("-", "_")
    deploy_public_key_variable = (
        "STG_SSH_PUBLIC_KEY"
        if bootstrap_environment == "staging"
        else f"{normalized_host_id}_SSH_PUBLIC_KEY"
    )
    deploy_private_key_secret = (
        "VPS_SSH_PRIVATE_KEY"
        if bootstrap_environment == "staging"
        else f"{normalized_host_id}_SSH_PRIVATE_KEY"
    )
    bootstrap_known_hosts_variable = (
        f"BOOTSTRAP_{normalized_host_id}_SSH_KNOWN_HOSTS"
        if bootstrap_environment == "staging"
        else "BUZ_PROD_KNOWN_HOSTS"
    )
    outputs = {
        "bootstrap_inventory": inventory_path,
        "bootstrap_target_host": target_host,
        "bootstrap_mode": execution_mode,
        "bootstrap_user": bootstrap_user,
        "ansible_host": str(ansible_host),
        "bootstrap_host_id": bootstrap_host_id,
        "bootstrap_host_id_normalized": normalized_host_id,
        "bootstrap_application_environment": application_environment,
        "bootstrap_environment": bootstrap_environment,
        "github_environment": (
            "Staging" if bootstrap_environment == "staging" else "Production"
        ),
        "bootstrap_application": application,
        "bootstrap_postgresql_requested": str(
            "postgresql" in requested_services
        ).lower(),
        "bootstrap_postgresql_db_password_secret": (
            f"{normalized_application}_DB_PASSWORD"
        ),
        "bootstrap_postgresql_s3_access_key_id_variable": (
            f"{normalized_application}_POSTGRESQL_S3_ACCESS_KEY_ID"
        ),
        "bootstrap_postgresql_s3_secret_access_key_secret": (
            f"{normalized_application}_POSTGRESQL_S3_SECRET_ACCESS_KEY"
        ),
        "bootstrap_postgresql_s3_restore_access_key_id_variable": (
            f"{normalized_application}_POSTGRESQL_S3_RESTORE_ACCESS_KEY_ID"
        ),
        "bootstrap_postgresql_s3_restore_secret_access_key_secret": (
            f"{normalized_application}_POSTGRESQL_S3_RESTORE_SECRET_ACCESS_KEY"
        ),
        "bootstrap_postgresql_backup_policy_variable": (
            f"{normalized_application}_POSTGRESQL_BACKUP_POLICY_VERIFIED"
        ),
        "bootstrap_requested_services": ",".join(requested_services),
        "bootstrap_effective_services": ",".join(effective_services),
        "bootstrap_requested_services_json": json.dumps(
            requested_services, separators=(",", ":")
        ),
        "bootstrap_effective_services_json": json.dumps(
            effective_services, separators=(",", ":")
        ),
        "bootstrap_route_fqdn": route_fqdn,
        "bootstrap_shared_host_collision": str(shared_host_collision).lower(),
        "bootstrap_password_secret": (
            f"{normalized_host_id}_PASSWORD"
        ),
        "bootstrap_known_hosts_variable": bootstrap_known_hosts_variable,
        "deploy_public_key_variable": deploy_public_key_variable,
        "deploy_private_key_secret": deploy_private_key_secret,
    }

    if errors:
        for message in errors:
            print(f"::error::{message}")
        return 1

    write_outputs(outputs)
    print(
        "Validated one target: "
        f"{inventory_path}:{target_host} ({application_environment} app environment, "
        f"{bootstrap_environment} bootstrap environment, "
        f"host ID {bootstrap_host_id}); requested services "
        f"{','.join(requested_services) or 'none'}, effective services "
        f"{','.join(effective_services) or 'none'}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
