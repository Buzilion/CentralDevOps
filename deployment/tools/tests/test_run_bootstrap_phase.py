import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
