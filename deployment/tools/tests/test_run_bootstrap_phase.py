import base64
import importlib.util
import json
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


def encoded_private_key_secret(private_key: str | bytes) -> str:
    key_bytes = (
        private_key.encode("utf-8") if isinstance(private_key, str) else private_key
    )
    return "base64:" + base64.b64encode(key_bytes).decode("ascii")


class BootstrapPhaseTests(unittest.TestCase):
    def test_initial_phases_require_both_host_key_pins(self) -> None:
        environment = {
            "BOOTSTRAP_ENVIRONMENT": "Staging",
            "BOOTSTRAP_TARGET_HOST": "stg-aio-01",
            "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
            "BOOTSTRAP_ACTOR_ID": "12345",
            "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
        }
        phases = (
            ("validate-admin-key", True),
            ("initial-access", True),
            ("admin-key-proof", True),
            ("ssh-hardening", True),
            ("post-hardening-proof", False),
            ("finalize-ssh-port", False),
            ("post-port-finalization-proof", False),
            ("fail2ban-enable", False),
            ("post-fail2ban-proof", False),
            ("fail2ban-rollback", False),
        )

        for phase, require_initial_pin in phases:
            with self.subTest(phase=phase):
                with mock.patch.object(
                    RUN_BOOTSTRAP_PHASE,
                    "validate_dispatch",
                ):
                    with mock.patch.object(
                        RUN_BOOTSTRAP_PHASE,
                        "validate_inventory_path",
                        return_value=Path("inventories/staging/hosts.yml"),
                    ):
                        with mock.patch.object(
                            RUN_BOOTSTRAP_PHASE,
                            "validate_target",
                            return_value={},
                        ) as validate_target:
                            RUN_BOOTSTRAP_PHASE._validate_phase_inputs(
                                phase, environment, Path(".")
                            )

                self.assertEqual(
                    validate_target.call_args.kwargs[
                        "require_initial_ssh_port"
                    ],
                    require_initial_pin,
                )

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

    def test_initial_bootstrap_phases_connect_on_port_22(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            root = Path(directory)
            runner_temp = root / "runner-temp"
            runner_temp.mkdir()
            host_variables = {"bootstrap_initial_ssh_port": 22}

            for phase in (
                "initial-access",
                "admin-key-proof",
                "ssh-hardening",
            ):
                with self.subTest(phase=phase):
                    environment = {
                        "BOOTSTRAP_ENVIRONMENT": "Staging",
                        "BOOTSTRAP_TARGET_HOST": "stg-disposable-01",
                        "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
                        "BOOTSTRAP_ACTOR_ID": "12345",
                        "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
                        "RUNNER_TEMP": str(runner_temp),
                    }
                    if phase == "initial-access":
                        environment["VPS_INITIAL_ACCESS_PASSWORD"] = (
                            "synthetic-initial-password"
                        )
                    else:
                        environment["ANSIBLE_SSH_PRIVATE_KEY"] = (
                            encoded_private_key_secret("synthetic-private-key")
                        )

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
                            return_value=SimpleNamespace(returncode=0),
                        ) as run:
                            result = RUN_BOOTSTRAP_PHASE.execute_phase(
                                phase,
                                root=root,
                                environment=environment,
                            )

                    self.assertEqual(result, 0)
                    command = run.call_args.args[0]
                    extra_vars_index = command.index("--extra-vars")
                    self.assertEqual(
                        json.loads(command[extra_vars_index + 1]),
                        {"ansible_port": 22},
                    )

            self.assertEqual(list(runner_temp.iterdir()), [])

    def test_final_port_phases_use_the_inventory_port(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            root = Path(directory)
            runner_temp = root / "runner-temp"
            runner_temp.mkdir()

            for phase, playbook in (
                ("post-hardening-proof", "prove-admin-key.yml"),
                ("finalize-ssh-port", "finalize-ssh-port.yml"),
                ("post-port-finalization-proof", "prove-admin-key.yml"),
            ):
                with self.subTest(phase=phase):
                    environment = {
                        "BOOTSTRAP_ENVIRONMENT": "Staging",
                        "BOOTSTRAP_TARGET_HOST": "stg-disposable-01",
                        "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
                        "BOOTSTRAP_ACTOR_ID": "12345",
                        "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
                        "ANSIBLE_SSH_PRIVATE_KEY": encoded_private_key_secret(
                            "synthetic-private-key"
                        ),
                        "RUNNER_TEMP": str(runner_temp),
                    }
                    with mock.patch.object(
                        RUN_BOOTSTRAP_PHASE,
                        "_validate_phase_inputs",
                        return_value=(
                            Path("inventories/staging/hosts.yml"),
                            "stg-disposable-01",
                            {},
                        ),
                    ):
                        with mock.patch.object(
                            RUN_BOOTSTRAP_PHASE.subprocess,
                            "run",
                            return_value=SimpleNamespace(returncode=0),
                        ) as run:
                            result = RUN_BOOTSTRAP_PHASE.execute_phase(
                                phase,
                                root=root,
                                environment=environment,
                            )

                    self.assertEqual(result, 0)
                    command = run.call_args.args[0]
                    self.assertNotIn("--extra-vars", command)
                    self.assertEqual(command[-1], f"playbooks/{playbook}")

            self.assertEqual(list(runner_temp.iterdir()), [])

    def test_fail2ban_service_phase_uses_base64_key_file_and_cleans_up(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            root = Path(directory)
            runner_temp = root / "runner-temp"
            runner_temp.mkdir()
            private_key_secret = encoded_private_key_secret(
                b"synthetic-admin-key-line-one\r\n"
                b"synthetic-admin-key-line-two\r\n"
            )
            environment = {
                "BOOTSTRAP_ENVIRONMENT": "Staging",
                "BOOTSTRAP_TARGET_HOST": "stg-aio-01",
                "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
                "BOOTSTRAP_ACTOR_ID": "12345",
                "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
                "ANSIBLE_SSH_PRIVATE_KEY": private_key_secret,
                "VPS_INITIAL_ACCESS_PASSWORD": "initial-secret",
                "RUNNER_TEMP": str(runner_temp),
            }

            with mock.patch.object(
                RUN_BOOTSTRAP_PHASE,
                "_validate_phase_inputs",
                return_value=(
                    Path("inventories/staging/hosts.yml"),
                    "stg-aio-01",
                    {},
                ),
            ):
                with mock.patch.object(
                    RUN_BOOTSTRAP_PHASE.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0),
                ) as run:
                    result = RUN_BOOTSTRAP_PHASE.execute_phase(
                        "fail2ban-enable",
                        root=root,
                        environment=environment,
                    )

            self.assertEqual(result, 0)
            command = run.call_args.args[0]
            child_environment = run.call_args.kwargs["env"]
            self.assertEqual(command[-1], "playbooks/enable-fail2ban.yml")
            self.assertNotIn(private_key_secret, command)
            self.assertNotIn(private_key_secret, child_environment.values())
            self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", child_environment)
            self.assertNotIn("VPS_INITIAL_ACCESS_PASSWORD", child_environment)
            self.assertEqual(list(runner_temp.iterdir()), [])

    def test_fail2ban_rollback_phase_uses_managed_host_playbook(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            root = Path(directory)
            runner_temp = root / "runner-temp"
            runner_temp.mkdir()
            environment = {
                "BOOTSTRAP_ENVIRONMENT": "Staging",
                "BOOTSTRAP_TARGET_HOST": "stg-aio-01",
                "BOOTSTRAP_REF": "refs/heads/feature/host-bootstrap",
                "BOOTSTRAP_ACTOR_ID": "12345",
                "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
                "ANSIBLE_SSH_PRIVATE_KEY": encoded_private_key_secret(
                    "synthetic-private-key"
                ),
                "RUNNER_TEMP": str(runner_temp),
            }

            with mock.patch.object(
                RUN_BOOTSTRAP_PHASE,
                "_validate_phase_inputs",
                return_value=(
                    Path("inventories/staging/hosts.yml"),
                    "stg-aio-01",
                    {},
                ),
            ):
                with mock.patch.object(
                    RUN_BOOTSTRAP_PHASE.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0),
                ) as run:
                    result = RUN_BOOTSTRAP_PHASE.execute_phase(
                        "fail2ban-rollback",
                        root=root,
                        environment=environment,
                    )

            self.assertEqual(result, 0)
            command = run.call_args.args[0]
            child_environment = run.call_args.kwargs["env"]
            self.assertEqual(command[-1], "playbooks/disable-fail2ban.yml")
            self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", child_environment)
            self.assertEqual(list(runner_temp.iterdir()), [])

    def test_admin_key_file_is_private_and_removed_after_success(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with RUN_BOOTSTRAP_PHASE.private_key_file(
                encoded_private_key_secret("synthetic-private-key"), Path(directory)
            ) as key_path:
                self.assertTrue(key_path.is_file())
                if os.name != "nt":
                    self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)
            self.assertFalse(key_path.exists())

    def test_base64_crlf_admin_key_is_normalized_before_writing(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with RUN_BOOTSTRAP_PHASE.private_key_file(
                encoded_private_key_secret("first line\r\nsecond line\r\n"),
                Path(directory),
            ) as key_path:
                self.assertEqual(key_path.read_bytes(), b"first line\nsecond line\n")
            self.assertFalse(key_path.exists())

    def test_private_key_secret_requires_base64_prefix(self) -> None:
        with self.assertRaisesRegex(
            RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
            "Base64-encoded with the base64: prefix",
        ):
            RUN_BOOTSTRAP_PHASE.private_key_bytes(
                "-----BEGIN OPENSSH PRIVATE KEY-----\nsynthetic\n"
            )

        with self.assertRaisesRegex(
            RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
            "Base64-encoded with the base64: prefix",
        ):
            RUN_BOOTSTRAP_PHASE.private_key_bytes(
                base64.b64encode(b"synthetic key").decode("ascii")
            )

    def test_base64_admin_key_rejects_bare_carriage_returns(self) -> None:
        secret = encoded_private_key_secret(b"first line\rsecond line")
        with self.assertRaisesRegex(
            RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
            "bare carriage returns",
        ):
            RUN_BOOTSTRAP_PHASE.private_key_bytes(secret)

    def test_base64_admin_key_is_written_as_exact_bytes(self) -> None:
        private_key = b"synthetic admin key bytes\n"
        secret = "base64:" + base64.b64encode(private_key).decode("ascii")
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")

        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with RUN_BOOTSTRAP_PHASE.private_key_file(
                secret, Path(directory)
            ) as key_path:
                self.assertEqual(key_path.read_bytes(), private_key)
            self.assertFalse(key_path.exists())

    def test_invalid_base64_admin_key_is_rejected_without_a_file(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "invalid base64 payload",
            ):
                with RUN_BOOTSTRAP_PHASE.private_key_file(
                    "base64:not-valid-base64", Path(directory)
                ):
                    self.fail("invalid base64 should not create a key file")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_admin_key_file_is_removed_after_failure(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        with tempfile.TemporaryDirectory(dir=temporary_parent) as directory:
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                with RUN_BOOTSTRAP_PHASE.private_key_file(
                    encoded_private_key_secret("synthetic-private-key"),
                    Path(directory),
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
        self.admin_private_key_secret = encoded_private_key_secret(
            "synthetic-admin-private-key"
        )
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
                "ANSIBLE_SSH_PRIVATE_KEY": self.admin_private_key_secret,
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
        self.assertNotIn(self.admin_private_key_secret, command)
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
                    self.admin_private_key_secret,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )

        self.assertEqual(list(self.runner_temp.iterdir()), [])

    def test_invalid_key_format_reports_safe_specific_diagnostic(self) -> None:
        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE.subprocess,
            "run",
            return_value=SimpleNamespace(
                returncode=255,
                stdout="",
                stderr='Load key "/tmp/private-key": invalid format',
            ),
        ):
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "ssh-keygen reported invalid format",
            ) as error:
                RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                    self.admin_private_key_secret,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )
        self.assertNotIn("/tmp/private-key", str(error.exception))
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    def test_libcrypto_failure_reports_safe_diagnostic(self) -> None:
        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE.subprocess,
            "run",
            return_value=SimpleNamespace(
                returncode=1,
                stdout="",
                stderr='Load key "/tmp/private-key": error in libcrypto',
            ),
        ):
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "could not be decoded by OpenSSH/libcrypto",
            ) as error:
                RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                    self.admin_private_key_secret,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )
        self.assertNotIn("/tmp/private-key", str(error.exception))
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    def test_passphrase_failure_is_reported_without_revealing_stderr(self) -> None:
        with mock.patch.object(
            RUN_BOOTSTRAP_PHASE.subprocess,
            "run",
            return_value=SimpleNamespace(
                returncode=1,
                stdout="",
                stderr="incorrect passphrase supplied",
            ),
        ):
            with self.assertRaisesRegex(
                RUN_BOOTSTRAP_PHASE.BootstrapPhaseError,
                "requires an unencrypted key",
            ) as error:
                RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
                    self.admin_private_key_secret,
                    self.admin_public_key,
                    directory=self.runner_temp,
                )

        self.assertNotIn("incorrect passphrase supplied", str(error.exception))
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
                encoded_private_key_secret(private_key),
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
            encoded_private_key_secret(private_key),
            public_key,
            directory=self.runner_temp,
        )
        self.assertEqual(list(self.runner_temp.iterdir()), [])

    @unittest.skipIf(
        os.name == "nt" or not shutil.which("ssh-keygen"),
        "OpenSSH key permissions are supported in the Ubuntu runner",
    )
    def test_real_crlf_private_key_matches_after_normalization(self) -> None:
        private_key_path = self.fixture_root / "generated-crlf-admin-key"
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
        private_key = private_key_path.read_text(encoding="utf-8").replace(
            "\n", "\r\n"
        )
        public_key = private_key_path.with_suffix(".pub").read_text(
            encoding="utf-8"
        )
        RUN_BOOTSTRAP_PHASE.validate_admin_private_key(
            encoded_private_key_secret(private_key),
            public_key,
            directory=self.runner_temp,
        )
        self.assertEqual(list(self.runner_temp.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
