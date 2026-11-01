import base64
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS = Path(__file__).resolve().parents[1]
PHASE_MODULE_PATH = TOOLS / "run_bootstrap_phase.py"
SPEC = importlib.util.spec_from_file_location("run_bootstrap_phase", PHASE_MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load bootstrap phase runner module")
RUN_BOOTSTRAP_PHASE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN_BOOTSTRAP_PHASE
SPEC.loader.exec_module(RUN_BOOTSTRAP_PHASE)


class BootstrapPhaseTests(unittest.TestCase):
    def test_inventory_validation_does_not_inherit_bootstrap_secrets(self) -> None:
        environment = {
            "BOOTSTRAP_ENVIRONMENT": "Staging",
            "VPS_INITIAL_ACCESS_PASSWORD": "initial-secret",
            "ANSIBLE_SSH_PRIVATE_KEY": "admin-key",
        }

        validation_environment = (
            RUN_BOOTSTRAP_PHASE.inventory_validation_environment(environment)
        )

        self.assertNotIn("VPS_INITIAL_ACCESS_PASSWORD", validation_environment)
        self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", validation_environment)
        self.assertEqual(validation_environment["BOOTSTRAP_ENVIRONMENT"], "Staging")

    def test_secret_values_are_not_added_to_ansible_arguments(self) -> None:
        private_key = "synthetic-private-key"
        password = "synthetic-password"
        command = RUN_BOOTSTRAP_PHASE.build_command(
            "inventories/staging/hosts.yml",
            "stg-aio-01",
            Path("playbooks/bootstrap.yml"),
        )

        self.assertNotIn(private_key, command)
        self.assertNotIn(password, command)
        self.assertEqual(
            command,
            [
                "ansible-playbook",
                "--inventory",
                "inventories/staging/hosts.yml",
                "--limit",
                "stg-aio-01",
                "playbooks/bootstrap.yml",
            ],
        )

    def test_admin_key_file_is_private_and_removed_after_success(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with RUN_BOOTSTRAP_PHASE.private_key_file(
                "synthetic-private-key", Path(directory)
            ) as key_path:
                self.assertTrue(key_path.is_file())
                if os.name != "nt":
                    self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)
            self.assertFalse(key_path.exists())

    def test_admin_key_file_is_removed_after_failure(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                with RUN_BOOTSTRAP_PHASE.private_key_file(
                    "synthetic-private-key", Path(directory)
                ) as key_path:
                    self.assertTrue(key_path.is_file())
                    raise RuntimeError("test failure")
            self.assertFalse(key_path.exists())


class AdminKeyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        self.fixture_directory = tempfile.TemporaryDirectory(dir=temporary_parent)
        self.addCleanup(self.fixture_directory.cleanup)
        self.fixture_root = Path(self.fixture_directory.name)
        self.runner_temp = self.fixture_root / "runner-temp"
        self.runner_temp.mkdir()
        self.admin_private_key = "synthetic-admin-private-key"
        self.admin_public_key = self._public_key(1)
        self.other_public_key = self._public_key(2)

    @staticmethod
    def _public_key(seed: int) -> str:
        key_blob = (
            b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"
            + bytes([seed]) * 32
        )
        encoded_key = base64.b64encode(key_blob).decode("ascii")
        return f"ssh-ed25519 {encoded_key} fixture-key"

    def test_validation_phase_checks_pair_without_inheriting_secrets(self) -> None:
        environment = dict(os.environ)
        environment.update(
            {
                "ANSIBLE_SSH_PRIVATE_KEY": self.admin_private_key,
                "ANSIBLE_PRIVATE_KEY_FILE": "unexpected-key-path",
                "BOOTSTRAP_PHASE": RUN_BOOTSTRAP_PHASE.ADMIN_KEY_VALIDATION_PHASE,
                "RUNNER_TEMP": str(self.runner_temp),
                "VPS_INITIAL_ACCESS_PASSWORD": "initial-secret",
            }
        )
        host_variables = {"bootstrap_admin_public_key": self.admin_public_key}

        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE,
            "_validate_phase_inputs",
            return_value=(
                Path("inventories/staging/hosts.yml"),
                "stg-disposable-01",
                host_variables,
            ),
        ):
            with mock.patch.object(
                RUN_BOOTSTRAP_PHASE.subprocess,
                "run",
                return_value=SimpleNamespace(
                    returncode=0, stdout=self.admin_public_key, stderr=""
                ),
            ) as run:
                result = RUN_BOOTSTRAP_PHASE.execute_phase(
                    RUN_BOOTSTRAP_PHASE.ADMIN_KEY_VALIDATION_PHASE,
                    environment=environment,
                )

        self.assertEqual(result, 0)
        command = run.call_args.args[0]
        child_environment = run.call_args.kwargs["env"]
        self.assertEqual(command[0], "ssh-keygen")
        self.assertNotIn(self.admin_private_key, command)
        self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", child_environment)
        self.assertNotIn("VPS_INITIAL_ACCESS_PASSWORD", child_environment)
        self.assertNotIn("ANSIBLE_PRIVATE_KEY_FILE", child_environment)
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    def test_mismatched_private_key_is_rejected_and_removed(self) -> None:
        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE.subprocess,
            "run",
            return_value=SimpleNamespace(
                returncode=0, stdout=self.other_public_key, stderr=""
            ),
        ):
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "does not match the reviewed inventory public key",
            ):
                RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                    self.admin_private_key,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )

        self.assertEqual(list(self.runner_temp.iterdir()), [])

    def test_keygen_failure_reports_unusable_private_key(self) -> None:
        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=1, stdout="", stderr=""),
        ):
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "passphrase-protected",
            ):
                RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                    self.admin_private_key,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    @unittest.skipIf(
        os.name == "nt" or not shutil.which("ssh-keygen"),
        "OpenSSH key permissions are supported in the Ubuntu runner",
    )
    def test_real_passphrase_protected_key_is_rejected_on_the_ubuntu_runner(
        self,
    ) -> None:
        private_key_path = self.fixture_root / "generated-protected-key"
        subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "fixture-passphrase",
                "-f",
                str(private_key_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        private_key = private_key_path.read_text(encoding="utf-8")
        public_key = private_key_path.with_suffix(".pub").read_text(encoding="utf-8")
        with self.assertRaisesRegex(
            RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
            "passphrase-protected",
        ):
            RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                private_key,
                public_key,
                directory=self.runner_temp,
            )
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    @unittest.skipIf(
        os.name == "nt" or not shutil.which("ssh-keygen"),
        "OpenSSH key permissions are supported in the Ubuntu runner",
    )
    def test_real_generated_key_pair_matches_on_the_ubuntu_runner(self) -> None:
        private_key_path = self.fixture_root / "generated-admin-key"
        subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(private_key_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        private_key = private_key_path.read_text(encoding="utf-8")
        public_key = private_key_path.with_suffix(".pub").read_text(encoding="utf-8")
        RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
            private_key,
            public_key,
            directory=self.runner_temp,
        )
        self.assertEqual(list(self.runner_temp.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
