#!/usr/bin/env python3
"""Run one guarded bootstrap phase without passing credentials in argv."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping

from bootstrap_inventory import (
    BootstrapValidationError,
    DISPATCH_APP_ACTOR_ID,
    ROOT,
    validate_dispatch,
    validate_inventory_path,
    validate_public_admin_key,
    validate_target,
)

ADMIN_KEY_VALIDATION_PHASE = "validate-admin-key"


PHASE_PLAYBOOKS = {
    "initial-access": Path("playbooks/bootstrap.yml"),
    "admin-key-proof": Path("playbooks/prove-admin-key.yml"),
    "ssh-hardening": Path("playbooks/harden-ssh.yml"),
    "post-hardening-proof": Path("playbooks/prove-admin-key.yml"),
}


class BootstrapPhaseError(ValueError):
    """Raised when a bootstrap phase cannot safely start."""


def inventory_validation_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        name: value
        for name, value in environment.items()
        if name not in {"VPS_INITIAL_ACCESS_PASSWORD", "ANSIBLE_SSH_PRIVATE_KEY"}
    }


def build_command(inventory_path: str, target: str, playbook: Path) -> list[str]:
    return [
        "ansible-playbook",
        "--inventory",
        inventory_path,
        "--limit",
        target,
        playbook.as_posix(),
    ]


@contextmanager
def private_key_file(
    private_key: str, directory: Path | None = None
) -> Iterator[Path]:
    if not isinstance(private_key, str) or not private_key:
        raise BootstrapPhaseError("admin SSH key secret is missing")
    if "\r" in private_key:
        raise BootstrapPhaseError("admin SSH key secret must use LF line endings")

    temporary_directory = directory or Path(tempfile.gettempdir())
    if not temporary_directory.is_dir():
        raise BootstrapPhaseError("runner temporary directory is unavailable")

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix="cdo-admin-key-",
        dir=temporary_directory,
        delete=False,
    )
    path = Path(handle.name)
    try:
        os.chmod(path, 0o600)
        with handle:
            handle.write(private_key)
            handle.flush()
            os.fsync(handle.fileno())
        yield path
    finally:
        if not handle.closed:
            handle.close()
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _public_key_identity(value: object) -> tuple[str, str]:
    if not isinstance(value, str):
        raise BootstrapPhaseError("admin public key is missing")
    parts = value.strip().split()
    if len(parts) < 2:
        raise BootstrapPhaseError("admin public key is malformed")
    return parts[0], parts[1]


def _keygen_failure_error(stderr: str, returncode: int) -> BootstrapPhaseError:
    diagnostic = " ".join(stderr.casefold().split())
    if "passphrase" in diagnostic:
        return BootstrapPhaseError(
            "admin SSH private key is passphrase-protected; "
            "the workflow requires an unencrypted key"
        )
    if "invalid format" in diagnostic:
        return BootstrapPhaseError(
            "admin SSH private key could not be parsed: ssh-keygen reported "
            "invalid format; check that the complete private-key file was supplied"
        )
    if "error in libcrypto" in diagnostic:
        return BootstrapPhaseError(
            "admin SSH private key could not be decoded by OpenSSH/libcrypto; "
            "check for a passphrase, unsupported encoding, or damaged key data"
        )
    return BootstrapPhaseError(
        "ssh-keygen could not parse the admin SSH private key "
        f"(exit code {returncode})"
    )


def validate_admin_private_key(
    private_key: str,
    expected_public_key: object,
    *,
    directory: Path | None = None,
    command_environment: Mapping[str, str] | None = None,
) -> None:
    try:
        validate_public_admin_key(expected_public_key)
    except BootstrapValidationError as exc:
        raise BootstrapPhaseError(
            "reviewed inventory admin public key is invalid"
        ) from exc

    expected_identity = _public_key_identity(expected_public_key)
    keygen_environment = inventory_validation_environment(
        os.environ if command_environment is None else command_environment
    )
    keygen_environment.pop("ANSIBLE_PRIVATE_KEY_FILE", None)

    with private_key_file(private_key, directory) as key_path:
        try:
            result = subprocess.run(
                ["ssh-keygen", "-y", "-P", "", "-f", str(key_path)],
                env=keygen_environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise BootstrapPhaseError(
                "ssh-keygen is required to validate the admin SSH key"
            ) from exc

    if result.returncode != 0:
        raise _keygen_failure_error(result.stderr, result.returncode)

    try:
        actual_identity = _public_key_identity(result.stdout)
    except BootstrapPhaseError as exc:
        raise BootstrapPhaseError(
            "ssh-keygen did not return a valid admin public key"
        ) from exc
    if actual_identity != expected_identity:
        raise BootstrapPhaseError(
            "admin SSH private key does not match the reviewed inventory public key"
        )


def _validate_phase_inputs(
    phase: str, environment: Mapping[str, str], root: Path
) -> tuple[Path, str, Mapping[str, object]]:
    if phase not in (*PHASE_PLAYBOOKS, ADMIN_KEY_VALIDATION_PHASE):
        raise BootstrapPhaseError("bootstrap phase is invalid")

    target_environment = environment.get("BOOTSTRAP_ENVIRONMENT")
    target_host = environment.get("BOOTSTRAP_TARGET_HOST")
    reference = environment.get("BOOTSTRAP_REF")
    actor_id = environment.get("BOOTSTRAP_ACTOR_ID")
    try:
        validate_dispatch(
            target_environment,
            reference,
            actor_id,
            expected_actor_id=DISPATCH_APP_ACTOR_ID,
        )
        inventory_path = validate_inventory_path(
            target_environment,
            environment.get("ANSIBLE_INVENTORY_PATH"),
            required=True,
        )
        host_variables = validate_target(
            root,
            target_environment,
            target_host,
            environment.get("ANSIBLE_INVENTORY_PATH"),
            require_inventory_path=True,
            command_environment=inventory_validation_environment(environment),
        )
    except BootstrapValidationError as exc:
        raise BootstrapPhaseError(str(exc)) from exc

    if not isinstance(target_host, str):
        raise BootstrapPhaseError("target host must be one exact inventory alias")
    return inventory_path, target_host, host_variables


def execute_phase(
    phase: str,
    *,
    root: Path = ROOT,
    environment: Mapping[str, str] | None = None,
) -> int:
    phase_environment = dict(os.environ if environment is None else environment)
    inventory_path, target_host, host_variables = _validate_phase_inputs(
        phase, phase_environment, root
    )

    if phase == ADMIN_KEY_VALIDATION_PHASE:
        private_key = phase_environment.pop("ANSIBLE_SSH_PRIVATE_KEY", None)
        if not private_key:
            raise BootstrapPhaseError("admin SSH key secret is missing")
        phase_environment.pop("VPS_INITIAL_ACCESS_PASSWORD", None)
        temporary_directory = Path(
            phase_environment.get("RUNNER_TEMP", tempfile.gettempdir())
        )
        validate_admin_private_key(
            private_key,
            host_variables.get("bootstrap_admin_public_key"),
            directory=temporary_directory,
            command_environment=inventory_validation_environment(phase_environment),
        )
        return 0

    command = build_command(
        inventory_path.as_posix(), target_host, PHASE_PLAYBOOKS[phase]
    )

    if phase == "initial-access":
        if not phase_environment.get("VPS_INITIAL_ACCESS_PASSWORD"):
            raise BootstrapPhaseError("initial-access password secret is missing")
        phase_environment.pop("ANSIBLE_SSH_PRIVATE_KEY", None)
        try:
            return subprocess.run(
                command,
                cwd=root,
                env=phase_environment,
                check=False,
            ).returncode
        except OSError as exc:
            raise BootstrapPhaseError("could not start the Ansible phase") from exc

    private_key = phase_environment.pop("ANSIBLE_SSH_PRIVATE_KEY", None)
    if not private_key:
        raise BootstrapPhaseError("admin SSH key secret is missing")
    phase_environment.pop("VPS_INITIAL_ACCESS_PASSWORD", None)
    temporary_directory = Path(
        phase_environment.get("RUNNER_TEMP", tempfile.gettempdir())
    )
    try:
        with private_key_file(private_key, temporary_directory) as key_path:
            phase_environment["ANSIBLE_PRIVATE_KEY_FILE"] = str(key_path)
            try:
                return subprocess.run(
                    command,
                    cwd=root,
                    env=phase_environment,
                    check=False,
                ).returncode
            except OSError as exc:
                raise BootstrapPhaseError(
                    "could not start the Ansible phase"
                ) from exc
    finally:
        phase_environment.pop("ANSIBLE_PRIVATE_KEY_FILE", None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one secret-scoped bootstrap phase."
    )
    parser.add_argument(
        "--phase",
        choices=(*PHASE_PLAYBOOKS, ADMIN_KEY_VALIDATION_PHASE),
        default=os.environ.get("BOOTSTRAP_PHASE"),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    arguments = parser.parse_args(argv)

    try:
        if not arguments.phase:
            raise BootstrapPhaseError("bootstrap phase is missing")
        return execute_phase(arguments.phase, root=arguments.root.resolve())
    except BootstrapPhaseError as exc:
        print(f"bootstrap phase failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
