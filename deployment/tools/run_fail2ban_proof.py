#!/usr/bin/env python3
"""Prove fail2ban preserves fresh admin and deploy access on one disposable VPS."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Mapping

from bootstrap_inventory import (
    BootstrapValidationError,
    DISPATCH_APP_ACTOR_ID,
    ROOT,
    validate_dispatch,
    validate_inventory_path,
    validate_public_admin_key,
    validate_target,
)
from run_bootstrap_phase import (
    BootstrapPhaseError,
    build_command,
    inventory_validation_environment,
    private_key_file,
)


FAIL2BAN_TEST_WINDOW_SECONDS = 120
FAIL2BAN_TEST_INTERVAL_SECONDS = 60

PLAYBOOKS = {
    "admin-proof": Path("playbooks/prove-admin-key.yml"),
    "deploy-key": Path("playbooks/manage-deploy-test-key.yml"),
    "deploy-proof": Path("playbooks/prove-deploy-key.yml"),
    "enable-fail2ban": Path("playbooks/enable-fail2ban-test.yml"),
    "disable-fail2ban": Path("playbooks/disable-fail2ban-test.yml"),
}


def _validation_environment(environment: Mapping[str, str]) -> dict[str, str]:
    result = inventory_validation_environment(environment)
    for name in (
        "BOOTSTRAP_DEPLOY_TEST_KEY_STATE",
        "BOOTSTRAP_DEPLOY_TEST_PRIVATE_KEY_FILE",
        "BOOTSTRAP_DEPLOY_TEST_PUBLIC_KEY",
    ):
        result.pop(name, None)
    return result


def _validate_inputs(
    root: Path, environment: Mapping[str, str]
) -> tuple[Path, str]:
    target_environment = environment.get("BOOTSTRAP_ENVIRONMENT")
    target_host = environment.get("BOOTSTRAP_TARGET_HOST")
    try:
        validate_dispatch(
            target_environment,
            environment.get("BOOTSTRAP_REF"),
            environment.get("BOOTSTRAP_ACTOR_ID"),
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
            command_environment=_validation_environment(environment),
            require_disposable=True,
            require_initial_ssh_port=False,
        )
    except BootstrapValidationError as exc:
        raise BootstrapPhaseError(str(exc)) from exc

    if not isinstance(target_host, str):
        raise BootstrapPhaseError("target host must be one exact inventory alias")
    return inventory_path, target_host


def _generate_deploy_test_key(
    directory: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[Path, str]:
    private_key_path = directory / "cdo-deploy-fail2ban-test"
    keygen = runner or subprocess.run
    try:
        result = keygen(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                "cdo-deploy-fail2ban-test",
                "-f",
                str(private_key_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BootstrapPhaseError(
            "could not generate the temporary deploy test key"
        ) from exc
    if result.returncode != 0:
        raise BootstrapPhaseError(
            "could not generate the temporary deploy test key"
        )

    try:
        public_key = private_key_path.with_suffix(".pub").read_text(
            encoding="utf-8"
        ).strip()
        os.chmod(private_key_path, 0o600)
        validate_public_admin_key(public_key)
    except (OSError, BootstrapValidationError) as exc:
        raise BootstrapPhaseError(
            "the temporary deploy test key is invalid"
        ) from exc
    if os.name != "nt" and private_key_path.stat().st_mode & 0o077:
        raise BootstrapPhaseError(
            "the temporary deploy test key permissions are too broad"
        )
    return private_key_path, public_key


def _run_playbook(
    phase_name: str,
    playbook: Path,
    inventory_path: Path,
    target_host: str,
    private_key_path: Path,
    root: Path,
    base_environment: Mapping[str, str],
    *,
    extra_environment: Mapping[str, str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> None:
    phase_environment = _validation_environment(base_environment)
    phase_environment["ANSIBLE_CONFIG"] = str((root / "ansible.cfg").resolve())
    phase_environment["ANSIBLE_PRIVATE_KEY_FILE"] = str(private_key_path)
    if extra_environment:
        phase_environment.update(extra_environment)

    command = build_command(inventory_path.as_posix(), target_host, playbook)
    run = runner or subprocess.run
    try:
        result = run(
            command,
            cwd=root,
            env=phase_environment,
            check=False,
        )
    except OSError as exc:
        raise BootstrapPhaseError(f"could not start the {phase_name} phase") from exc
    if result.returncode != 0:
        raise BootstrapPhaseError(f"the {phase_name} phase failed")


def observe_access_paths(
    prove_admin: Callable[[], None],
    prove_deploy: Callable[[], None],
    *,
    window_seconds: int = FAIL2BAN_TEST_WINDOW_SECONDS,
    interval_seconds: int = FAIL2BAN_TEST_INTERVAL_SECONDS,
    monotonic: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> None:
    if window_seconds < 0 or interval_seconds <= 0:
        raise BootstrapPhaseError("fail2ban observation window is invalid")

    clock = monotonic or time.monotonic
    pause = sleep or time.sleep
    deadline = clock() + window_seconds
    max_probe_count = (
        window_seconds + interval_seconds - 1
    ) // interval_seconds + 1
    for _ in range(max_probe_count):
        prove_admin()
        prove_deploy()
        remaining = deadline - clock()
        if remaining <= 0:
            return
        pause(min(interval_seconds, remaining))
    raise BootstrapPhaseError(
        "fail2ban observation window did not complete before the probe limit"
    )


def _run_proof_sequence(
    *,
    prove_admin: Callable[[], None],
    manage_deploy_key: Callable[[str], None],
    prove_deploy: Callable[[], None],
    enable_fail2ban: Callable[[], None],
    disable_fail2ban: Callable[[], None],
    observe: Callable[[Callable[[], None], Callable[[], None]], None],
) -> None:
    deploy_key_may_be_installed = False
    fail2ban_may_be_enabled = False
    primary_error: BootstrapPhaseError | None = None
    rollback_error: BootstrapPhaseError | None = None
    cleanup_error: BootstrapPhaseError | None = None

    try:
        prove_admin()
        deploy_key_may_be_installed = True
        manage_deploy_key("present")
        prove_deploy()
        fail2ban_may_be_enabled = True
        enable_fail2ban()
        observe(prove_admin, prove_deploy)
    except BootstrapPhaseError as exc:
        primary_error = exc
    except KeyboardInterrupt:
        primary_error = BootstrapPhaseError(
            "fail2ban access-path observation was interrupted"
        )
    finally:
        if primary_error is not None and fail2ban_may_be_enabled:
            try:
                disable_fail2ban()
            except BootstrapPhaseError as exc:
                rollback_error = exc
        if deploy_key_may_be_installed:
            try:
                manage_deploy_key("absent")
            except BootstrapPhaseError as exc:
                cleanup_error = exc

    errors = []
    if primary_error is not None:
        errors.append(str(primary_error))
    if rollback_error is not None:
        errors.append(
            "fail2ban rollback failed; use the Sumopod console to stop and disable it"
        )
    if cleanup_error is not None:
        errors.append(
            "temporary cdo-deploy key removal failed; remove it through the "
            "Sumopod console"
        )
    if errors:
        cause = primary_error or rollback_error or cleanup_error
        raise BootstrapPhaseError("; ".join(errors)) from cause


def execute_fail2ban_proof(
    *,
    root: Path = ROOT,
    environment: Mapping[str, str] | None = None,
    observation_window_seconds: int = FAIL2BAN_TEST_WINDOW_SECONDS,
    probe_interval_seconds: int = FAIL2BAN_TEST_INTERVAL_SECONDS,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    keygen_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    monotonic: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> int:
    base_environment = dict(os.environ if environment is None else environment)
    inventory_path, target_host = _validate_inputs(root, base_environment)
    admin_private_key = base_environment.get("ANSIBLE_SSH_PRIVATE_KEY")
    if not admin_private_key:
        raise BootstrapPhaseError("admin SSH key secret is missing")

    temporary_parent = Path(
        base_environment.get("RUNNER_TEMP", tempfile.gettempdir())
    )
    if not temporary_parent.is_dir():
        raise BootstrapPhaseError("runner temporary directory is unavailable")

    try:
        with tempfile.TemporaryDirectory(
            prefix="cdo-fail2ban-proof-", dir=temporary_parent
        ) as directory:
            key_directory = Path(directory)
            deploy_private_key, deploy_public_key = _generate_deploy_test_key(
                key_directory, runner=keygen_runner
            )
            with private_key_file(admin_private_key, key_directory) as admin_key_path:

                def run_admin(phase_name: str, playbook_name: str) -> None:
                    _run_playbook(
                        phase_name,
                        PLAYBOOKS[playbook_name],
                        inventory_path,
                        target_host,
                        admin_key_path,
                        root,
                        base_environment,
                        runner=command_runner,
                    )

                def prove_admin() -> None:
                    run_admin("cdo-admin access proof", "admin-proof")

                def prove_deploy() -> None:
                    _run_playbook(
                        "cdo-deploy access proof",
                        PLAYBOOKS["deploy-proof"],
                        inventory_path,
                        target_host,
                        deploy_private_key,
                        root,
                        base_environment,
                        runner=command_runner,
                    )

                def enable_fail2ban() -> None:
                    run_admin("fail2ban enablement", "enable-fail2ban")

                def disable_fail2ban() -> None:
                    run_admin("fail2ban rollback", "disable-fail2ban")

                def observe(
                    admin_probe: Callable[[], None],
                    deploy_probe: Callable[[], None],
                ) -> None:
                    print(
                        "Fail2ban is active; probing fresh admin and deploy "
                        f"SSH sessions every {probe_interval_seconds} seconds "
                        f"for {observation_window_seconds} seconds.",
                        flush=True,
                    )
                    observe_access_paths(
                        admin_probe,
                        deploy_probe,
                        window_seconds=observation_window_seconds,
                        interval_seconds=probe_interval_seconds,
                        monotonic=monotonic,
                        sleep=sleep,
                    )

                def manage_deploy_test_key(state: str) -> None:
                    _run_playbook(
                        f"temporary cdo-deploy key {state}",
                        PLAYBOOKS["deploy-key"],
                        inventory_path,
                        target_host,
                        admin_key_path,
                        root,
                        base_environment,
                        extra_environment={
                            "BOOTSTRAP_DEPLOY_TEST_PUBLIC_KEY": deploy_public_key,
                            "BOOTSTRAP_DEPLOY_TEST_KEY_STATE": state,
                        },
                        runner=command_runner,
                    )

                _run_proof_sequence(
                    prove_admin=prove_admin,
                    manage_deploy_key=manage_deploy_test_key,
                    prove_deploy=prove_deploy,
                    enable_fail2ban=enable_fail2ban,
                    disable_fail2ban=disable_fail2ban,
                    observe=observe,
                )
    except OSError as exc:
        raise BootstrapPhaseError(
            "temporary fail2ban proof files could not be managed"
        ) from exc

    print("Disposable fail2ban access-path proof succeeded.")
    return 0


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        return execute_fail2ban_proof()
    except BootstrapPhaseError as exc:
        print(f"fail2ban proof failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
