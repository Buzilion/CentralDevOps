#!/usr/bin/env python3
"""Run one preflighted configure request without exposing SSH key material."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping

from bootstrap_inventory import (
    BootstrapValidationError,
    validate_inventory_path,
)
from configure_inputs import (
    ConfigureRequest,
    ConfigureValidationError,
    ROOT,
    SECRET_ENVIRONMENT_NAMES,
    inventory_validation_environment,
    validate_request,
)
from run_bootstrap_phase import (
    BootstrapPhaseError,
    private_key_file,
    validate_admin_private_key,
)


class ConfigureRunnerError(ValueError):
    """Raised when a configure operation cannot safely start."""


def build_command(request: ConfigureRequest) -> list[str]:
    command = [
        "ansible-playbook",
        "--inventory",
        request.inventory_path.as_posix(),
    ]
    if request.limit:
        command.extend(["--limit", request.limit])
    if request.check_mode:
        command.extend(["--check", "--diff"])
    command.append("playbooks/configure.yml")
    return command


def _validate_admin_key(
    request: ConfigureRequest,
    private_key: str,
    temporary_directory: Path,
    command_environment: Mapping[str, str],
) -> None:
    metadata = request.inventory_document.get("_meta")
    hostvars = metadata.get("hostvars") if isinstance(metadata, Mapping) else None
    if not isinstance(hostvars, Mapping):
        raise ConfigureRunnerError(
            "selected environment inventory has no host-variable map"
        )

    for host in request.target_hosts:
        host_variables = hostvars.get(host)
        if not isinstance(host_variables, Mapping):
            raise ConfigureRunnerError(
                f"selected environment inventory has no variable map for {host}"
            )
        try:
            validate_admin_private_key(
                private_key,
                host_variables.get("bootstrap_admin_public_key"),
                directory=temporary_directory,
                command_environment=command_environment,
            )
        except BootstrapPhaseError as exc:
            raise ConfigureRunnerError(str(exc)) from exc


def execute_configure(
    *,
    root: Path = ROOT,
    environment: Mapping[str, str] | None = None,
) -> int:
    configure_environment = dict(os.environ if environment is None else environment)
    validation_environment = inventory_validation_environment(configure_environment)
    try:
        request = validate_request(
            root=root,
            target_environment=configure_environment.get(
                "CONFIGURE_TARGET_ENVIRONMENT"
            ),
            profile=configure_environment.get("CONFIGURE_PROFILE"),
            limit=configure_environment.get("CONFIGURE_LIMIT", ""),
            check_mode=configure_environment.get("CONFIGURE_CHECK_MODE"),
            reference=configure_environment.get("CONFIGURE_REF"),
            actor_id=configure_environment.get("CONFIGURE_ACTOR_ID"),
            command_environment=validation_environment,
        )
        inventory_path = validate_inventory_path(
            request.target_environment,
            configure_environment.get("ANSIBLE_INVENTORY_PATH"),
            required=True,
        )
    except (BootstrapValidationError, ConfigureValidationError) as exc:
        raise ConfigureRunnerError(str(exc)) from exc

    if inventory_path != request.inventory_path:
        raise ConfigureRunnerError(
            "selected environment inventory does not match the preflight mapping"
        )

    private_key = configure_environment.pop("ANSIBLE_SSH_PRIVATE_KEY", None)
    if not private_key:
        raise ConfigureRunnerError("admin SSH key secret is missing")
    if not configure_environment.get("GHCR_PULL_TOKEN"):
        raise ConfigureRunnerError("GHCR pull token secret is missing")

    temporary_directory = Path(
        configure_environment.get("RUNNER_TEMP", tempfile.gettempdir())
    )
    _validate_admin_key(
        request,
        private_key,
        temporary_directory,
        validation_environment,
    )

    for name in SECRET_ENVIRONMENT_NAMES - {"GHCR_PULL_TOKEN"}:
        configure_environment.pop(name, None)
    configure_environment.pop("ANSIBLE_PRIVATE_KEY_FILE", None)

    command = build_command(request)
    try:
        with private_key_file(private_key, temporary_directory) as key_path:
            child_environment = dict(configure_environment)
            child_environment["ANSIBLE_PRIVATE_KEY_FILE"] = str(key_path)
            try:
                return subprocess.run(
                    command,
                    cwd=root,
                    env=child_environment,
                    check=False,
                ).returncode
            except OSError as exc:
                raise ConfigureRunnerError(
                    "could not start the Ansible configure operation"
                ) from exc
    except BootstrapPhaseError as exc:
        raise ConfigureRunnerError(str(exc)) from exc


def main() -> int:
    try:
        return execute_configure()
    except ConfigureRunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
