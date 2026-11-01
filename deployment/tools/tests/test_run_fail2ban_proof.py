import base64
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_fail2ban_proof as FAIL2BAN_PROOF
from run_bootstrap_phase import BootstrapPhaseError


class Fail2banProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.environment = {
            "BOOTSTRAP_ENVIRONMENT": "Staging",
            "BOOTSTRAP_TARGET_HOST": "stg-disposable-01",
            "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
            "BOOTSTRAP_ACTOR_ID": "12345",
            "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
            "ANSIBLE_SSH_PRIVATE_KEY": "base64:"
            + base64.b64encode(b"synthetic-admin-private-key").decode("ascii"),
            "VPS_INITIAL_ACCESS_PASSWORD": "synthetic-initial-password",
            "BOOTSTRAP_DEPLOY_TEST_PUBLIC_KEY": "must-not-be-inherited",
            "BOOTSTRAP_DEPLOY_TEST_PRIVATE_KEY_FILE": "must-not-be-inherited",
            "RUNNER_TEMP": str(self.root),
        }

    def test_validation_requires_disposable_host_before_ssh(self) -> None:
        with mock.patch.object(FAIL2BAN_PROOF, "validate_target") as validate_target:
            inventory_path, target = FAIL2BAN_PROOF._validate_inputs(
                self.root, self.environment
            )

        self.assertEqual(inventory_path.as_posix(), "inventories/staging/hosts.yml")
        self.assertEqual(target, "stg-disposable-01")
        self.assertTrue(validate_target.call_args.kwargs["require_disposable"])
        command_environment = validate_target.call_args.kwargs["command_environment"]
        self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", command_environment)
        self.assertNotIn("VPS_INITIAL_ACCESS_PASSWORD", command_environment)
        self.assertNotIn("BOOTSTRAP_DEPLOY_TEST_PUBLIC_KEY", command_environment)

    def test_observation_probes_both_paths_until_window_ends(self) -> None:
        now = [0.0]
        events = []

        def clock() -> float:
            return now[0]

        def sleep(seconds: float) -> None:
            now[0] += seconds

        FAIL2BAN_PROOF.observe_access_paths(
            lambda: events.append("admin"),
            lambda: events.append("deploy"),
            window_seconds=120,
            interval_seconds=60,
            monotonic=clock,
            sleep=sleep,
        )

        self.assertEqual(events, ["admin", "deploy"] * 3)

    def test_access_path_failure_rolls_back_and_removes_temporary_key(self) -> None:
        events = []

        def observe(prove_admin, prove_deploy) -> None:
            prove_admin()
            raise BootstrapPhaseError("deploy access failed")

        with self.assertRaisesRegex(
            BootstrapPhaseError, "deploy access failed"
        ):
            FAIL2BAN_PROOF._run_proof_sequence(
                prove_admin=lambda: events.append("admin"),
                manage_deploy_key=lambda state: events.append(f"key-{state}"),
                prove_deploy=lambda: events.append("deploy"),
                enable_fail2ban=lambda: events.append("enable"),
                disable_fail2ban=lambda: events.append("disable"),
                observe=observe,
            )

        self.assertEqual(
            events,
            [
                "admin",
                "key-present",
                "deploy",
                "enable",
                "admin",
                "disable",
                "key-absent",
            ],
        )

    def test_success_uses_fresh_paths_and_removes_temporary_key(self) -> None:
        calls = []
        key_files_during_calls = []

        def command_runner(command, **kwargs):
            calls.append((command, kwargs))
            key_files_during_calls.append(
                Path(kwargs["env"]["ANSIBLE_PRIVATE_KEY_FILE"]).is_file()
            )
            return SimpleNamespace(returncode=0)

        with mock.patch.object(
            FAIL2BAN_PROOF,
            "_validate_inputs",
            return_value=(
                Path("inventories/staging/hosts.yml"),
                "stg-disposable-01",
            ),
        ):
            result = FAIL2BAN_PROOF.execute_fail2ban_proof(
                root=self.root,
                environment=self.environment,
                observation_window_seconds=0,
                command_runner=command_runner,
            )

        self.assertEqual(result, 0)
        playbooks = [Path(command[-1]).name for command, _ in calls]
        self.assertEqual(
            playbooks,
            [
                "prove-admin-key.yml",
                "manage-deploy-test-key.yml",
                "prove-deploy-key.yml",
                "enable-fail2ban-test.yml",
                "prove-admin-key.yml",
                "prove-deploy-key.yml",
                "manage-deploy-test-key.yml",
            ],
        )
        for command, kwargs in calls:
            self.assertNotIn("synthetic-admin-private-key", command)
            self.assertNotIn("synthetic-initial-password", command)
            self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", kwargs["env"])
            self.assertNotIn("VPS_INITIAL_ACCESS_PASSWORD", kwargs["env"])
            self.assertNotIn(
                "BOOTSTRAP_DEPLOY_TEST_PRIVATE_KEY_FILE", kwargs["env"]
            )
        self.assertTrue(all(key_files_during_calls))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_post_enable_failure_attempts_rollback_before_key_removal(self) -> None:
        calls = []
        deploy_proofs = 0

        def command_runner(command, **kwargs):
            nonlocal deploy_proofs
            playbook = Path(command[-1]).name
            calls.append(playbook)
            if playbook == "prove-deploy-key.yml":
                deploy_proofs += 1
                if deploy_proofs == 2:
                    return SimpleNamespace(returncode=1)
            return SimpleNamespace(returncode=0)

        with mock.patch.object(
            FAIL2BAN_PROOF,
            "_validate_inputs",
            return_value=(
                Path("inventories/staging/hosts.yml"),
                "stg-disposable-01",
            ),
        ):
            with self.assertRaisesRegex(BootstrapPhaseError, "cdo-deploy access"):
                FAIL2BAN_PROOF.execute_fail2ban_proof(
                    root=self.root,
                    environment=self.environment,
                    observation_window_seconds=0,
                    command_runner=command_runner,
                )

        self.assertEqual(
            calls[-3:],
            [
                "prove-deploy-key.yml",
                "disable-fail2ban-test.yml",
                "manage-deploy-test-key.yml",
            ],
        )
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
