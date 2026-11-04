import contextlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

SPEC = importlib.util.spec_from_file_location(
    "run_configure", TOOLS / "run_configure.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load configure runner module")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def configure_request(
    *,
    limit: str = "app_nodes",
    check_mode: bool = True,
):
    return RUNNER.ConfigureRequest(
        target_environment="Staging",
        profile="app",
        inventory_path=Path("inventories/staging/hosts.yml"),
        limit=limit,
        check_mode=check_mode,
        target_hosts=("stg-aio-01",),
        inventory_document={"_meta": {"hostvars": {}}},
    )


class ConfigureRunnerTests(unittest.TestCase):
    def test_build_command_has_fixed_playbook_and_only_prevalidated_limit(self) -> None:
        command = RUNNER.build_command(configure_request())

        self.assertEqual(
            command,
            [
                "ansible-playbook",
                "--inventory",
                "inventories/staging/hosts.yml",
                "--limit",
                "app_nodes",
                "--check",
                "--diff",
                "playbooks/configure.yml",
            ],
        )

    def test_normal_convergence_omits_check_mode_flags_and_empty_limit(self) -> None:
        command = RUNNER.build_command(
            configure_request(limit="", check_mode=False)
        )

        self.assertEqual(
            command,
            [
                "ansible-playbook",
                "--inventory",
                "inventories/staging/hosts.yml",
                "playbooks/configure.yml",
            ],
        )

    def test_secrets_are_not_passed_in_args_or_to_inventory_validation(self) -> None:
        environment = {
            "ANSIBLE_CONFIG": "ansible.cfg",
            "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
            "ANSIBLE_SSH_PRIVATE_KEY": "base64:synthetic-admin-key",
            "DEPLOY_SSH_PRIVATE_KEY": "synthetic-deploy-key",
            "GHCR_PULL_TOKEN": "synthetic-ghcr-token",
            "ANSIBLE_PRIVATE_KEY_FILE": "untrusted-key-path",
            "CONFIGURE_TARGET_ENVIRONMENT": "Staging",
            "CONFIGURE_PROFILE": "app",
            "CONFIGURE_LIMIT": "app_nodes",
            "CONFIGURE_CHECK_MODE": "true",
            "CONFIGURE_REF": "refs/heads/feature/configure",
            "CONFIGURE_ACTOR_ID": "12345",
            "RUNNER_TEMP": "runner-temp",
        }
        request = configure_request()

        @contextlib.contextmanager
        def fake_private_key_file(private_key, directory):
            self.assertEqual(private_key, "base64:synthetic-admin-key")
            self.assertEqual(directory, Path("runner-temp"))
            yield Path("runner-temp") / "private-key"

        with (
            mock.patch.object(RUNNER, "validate_request", return_value=request) as validate,
            mock.patch.object(
                RUNNER,
                "validate_inventory_path",
                return_value=request.inventory_path,
            ),
            mock.patch.object(RUNNER, "_validate_admin_key") as validate_key,
            mock.patch.object(
                RUNNER,
                "private_key_file",
                side_effect=fake_private_key_file,
            ),
            mock.patch.object(
                RUNNER.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0),
            ) as run,
        ):
            result = RUNNER.execute_configure(
                root=Path("repo-root"),
                environment=environment,
            )

        self.assertEqual(result, 0)
        command = run.call_args.args[0]
        child_environment = run.call_args.kwargs["env"]
        self.assertNotIn("synthetic-admin-key", command)
        self.assertNotIn("synthetic-deploy-key", command)
        self.assertNotIn("synthetic-ghcr-token", command)
        self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", child_environment)
        self.assertNotIn("DEPLOY_SSH_PRIVATE_KEY", child_environment)
        self.assertEqual(
            child_environment["GHCR_PULL_TOKEN"],
            "synthetic-ghcr-token",
        )
        self.assertEqual(
            child_environment["ANSIBLE_PRIVATE_KEY_FILE"],
            str(Path("runner-temp") / "private-key"),
        )
        self.assertEqual(
            validate.call_args.kwargs["command_environment"].get(
                "GHCR_PULL_TOKEN"
            ),
            None,
        )
        validate_key.assert_called_once()

    def test_missing_pull_token_stops_before_admin_key_or_ansible(self) -> None:
        environment = {
            "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
            "ANSIBLE_SSH_PRIVATE_KEY": "base64:synthetic-admin-key",
            "CONFIGURE_TARGET_ENVIRONMENT": "Staging",
            "CONFIGURE_PROFILE": "app",
            "CONFIGURE_LIMIT": "",
            "CONFIGURE_CHECK_MODE": "true",
            "CONFIGURE_REF": "refs/heads/feature/configure",
            "CONFIGURE_ACTOR_ID": "12345",
        }
        with (
            mock.patch.object(
                RUNNER,
                "validate_request",
                return_value=configure_request(limit=""),
            ),
            mock.patch.object(
                RUNNER,
                "validate_inventory_path",
                return_value=Path("inventories/staging/hosts.yml"),
            ),
            mock.patch.object(RUNNER, "_validate_admin_key") as validate_key,
            mock.patch.object(RUNNER.subprocess, "run") as run,
        ):
            with self.assertRaisesRegex(
                RUNNER.ConfigureRunnerError,
                "GHCR pull token secret is missing",
            ):
                RUNNER.execute_configure(environment=environment)

        validate_key.assert_not_called()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
