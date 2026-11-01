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
    validate_target,
)


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


def _validate_phase_inputs(
    phase: str, environment: Mapping[str, str], root: Path
) -> tuple[Path, str, str]:
    if phase not in PHASE_PLAYBOOKS:
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
        validate_target(
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
    return inventory_path, target_host, str(PHASE_PLAYBOOKS[phase])


def execute_phase(
    phase: str,
    *,
    root: Path = ROOT,
    environment: Mapping[str, str] | None = None,
) -> int:
    phase_environment = dict(os.environ if environment is None else environment)
    inventory_path, target_host, playbook = _validate_phase_inputs(
        phase, phase_environment, root
    )
    command = build_command(inventory_path.as_posix(), target_host, Path(playbook))

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
        choices=tuple(PHASE_PLAYBOOKS),
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
