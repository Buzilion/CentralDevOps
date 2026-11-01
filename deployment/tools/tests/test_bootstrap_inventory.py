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

import yaml


TOOLS = Path(__file__).resolve().parents[1]
INVENTORY_MODULE_PATH = TOOLS / "bootstrap_inventory.py"
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_inventory", INVENTORY_MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load bootstrap inventory validation module")
BOOTSTRAP_INVENTORY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BOOTSTRAP_INVENTORY
SPEC.loader.exec_module(BOOTSTRAP_INVENTORY)


@unittest.skipUnless(shutil.which("ssh-keygen"), "OpenSSH is required for pin tests")
class BootstrapInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_parent = os.environ.get("CENTRALDEVOPS_TEST_TMPDIR")
        self.temporary_directory = tempfile.TemporaryDirectory(dir=temporary_parent)
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.write_fixture()
        self.hostvars = self.fixture_hostvars()

    def write_fixture(self) -> None:
        inventory_root = self.root / "inventories"
        staging = inventory_root / "staging"
        (staging / "group_vars").mkdir(parents=True)
        (staging / "host_vars").mkdir()
        self.key_directory = self.root / "generated-keys"
        self.key_directory.mkdir()
        self.addCleanup(shutil.rmtree, self.key_directory, ignore_errors=True)

        self.admin_private_key = self.key_directory / "admin"
        self.host_private_key = self.key_directory / "host"
        for key_path in (self.admin_private_key, self.host_private_key):
            subprocess.run(
                [
                    "ssh-keygen",
                    "-q",
                    "-t",
                    "ed25519",
                    "-N",
                    "",
                    "-f",
                    str(key_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        admin_public_key = self.admin_private_key.with_suffix(".pub").read_text(
            encoding="utf-8"
        ).strip()
        host_public_key = self.host_private_key.with_suffix(".pub").read_text(
            encoding="utf-8"
        ).strip()
        host_key_parts = host_public_key.split()
        (staging / "known_hosts").write_text(
            f"fixture.invalid {host_key_parts[0]} {host_key_parts[1]}\n",
            encoding="utf-8",
        )
        (staging / "hosts.yml").write_text(
            "all:\n"
            "  children:\n"
            "    app_nodes:\n"
            "      hosts:\n"
            "        stg-disposable-01: {}\n"
            "    proxy_nodes:\n"
            "      hosts: {}\n"
            "    database_nodes:\n"
            "      hosts: {}\n",
            encoding="utf-8",
        )
        (staging / "group_vars" / "all.yml").write_text(
            "bootstrap_admin_user: cdo-admin\n"
            "bootstrap_admin_public_key: "
            + json.dumps(admin_public_key)
            + "\n"
            "bootstrap_capacity_reference:\n"
            "  physical_memory_mib: 2048\n"
            "  platform_reserve_mib: 1024\n"
            "  capacity_budget_mib: 1024\n",
            encoding="utf-8",
        )
        (staging / "host_vars" / "stg-disposable-01.yml").write_text(
            "ansible_host: fixture.invalid\n"
            "provider_username: fixture-user\n"
            "physical_memory_mib: 2048\n"
            "platform_reserve_mib: 1024\n"
            "capacity_budget_mib: 1024\n"
            "bootstrap_disposable: true\n"
            "ssh_source_policy_exception: "
            "GitHub-hosted runner egress is not stable; revisit when the runner has a fixed CIDR.\n",
            encoding="utf-8",
        )
        (self.root / "ansible.cfg").write_text(
            "[defaults]\nhost_key_checking = True\n",
            encoding="utf-8",
        )

    def fixture_hostvars(self):
        group_vars = yaml.safe_load(
            (self.root / "inventories" / "staging" / "group_vars" / "all.yml").read_text(
                encoding="utf-8"
            )
        )
        host_vars = yaml.safe_load(
            (
                self.root
                / "inventories"
                / "staging"
                / "host_vars"
                / "stg-disposable-01.yml"
            ).read_text(encoding="utf-8")
        )
        return {"stg-disposable-01": {**group_vars, **host_vars}}

    def validate(self, target: str = "stg-disposable-01", hostvars=None) -> None:
        BOOTSTRAP_INVENTORY.validate_inventory_target(
            "Staging",
            target,
            self.hostvars if hostvars is None else hostvars,
            self.root / "inventories" / "staging" / "known_hosts",
        )

    def test_inventory_loader_uses_the_fixed_inventory_and_parses_json(self) -> None:
        inventory_output = json.dumps({"_meta": {"hostvars": self.hostvars}})
        with mock.patch.object(
            BOOTSTRAP_INVENTORY.subprocess,
            "run",
            return_value=SimpleNamespace(
                returncode=0, stdout=inventory_output, stderr=""
            ),
        ) as run:
            loaded = BOOTSTRAP_INVENTORY.load_inventory(self.root, "Staging")

        self.assertEqual(loaded, self.hostvars)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "ansible-inventory")
        self.assertEqual(
            Path(command[2]),
            self.root / "inventories" / "staging" / "hosts.yml",
        )

    @unittest.skipIf(
        os.name == "nt"
        or os.environ.get("RUN_ANSIBLE_INVENTORY_INTEGRATION") != "1"
        or shutil.which("ansible-inventory") is None,
        "Ansible controller CLI integration runs on supported Unix runners",
    )
    def test_ansible_inventory_parses_the_temporary_fixture(self) -> None:
        loaded = BOOTSTRAP_INVENTORY.load_inventory(self.root, "Staging")

        self.assertEqual(loaded, self.hostvars)

    def test_known_staging_host_with_pin_and_valid_capacity_passes(self) -> None:
        self.validate()

    def test_flagged_disposable_target_passes_disposable_only_validation(
        self,
    ) -> None:
        validated = BOOTSTRAP_INVENTORY.validate_inventory_target(
            "Staging",
            "stg-disposable-01",
            self.hostvars,
            self.root / "inventories" / "staging" / "known_hosts",
            require_disposable=True,
        )

        self.assertEqual(validated, self.hostvars["stg-disposable-01"])

    def test_disposable_output_requires_the_exact_purpose_and_flag(self) -> None:
        host = self.hostvars["stg-disposable-01"]
        self.assertTrue(
            BOOTSTRAP_INVENTORY.is_disposable_target("stg-disposable-01", host)
        )
        self.assertFalse(
            BOOTSTRAP_INVENTORY.is_disposable_target("stg-test-disposable-01", host)
        )
        self.assertFalse(
            BOOTSTRAP_INVENTORY.is_disposable_target(
                "stg-disposable-01", {**host, "bootstrap_disposable": False}
            )
        )

    def test_rejects_unknown_cross_environment_and_pattern_targets(self) -> None:
        invalid_targets = (
            "stg-disposable-02",
            "prd-disposable-01",
            "stg-*",
            "app_nodes",
            "stg-disposable-01,stg-disposable-02",
            "stg-disposable-1",
            "stg-disposable-00",
        )
        for target in invalid_targets:
            with self.subTest(target=target):
                with self.assertRaises(
                    BOOTSTRAP_INVENTORY.BootstrapValidationError
                ):
                    self.validate(target)

    def test_rejects_missing_or_mismatched_host_key_pin(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError, "no committed host-key pin"
        ):
            hostvars = {
                **self.hostvars,
                "stg-disposable-01": {
                    **self.hostvars["stg-disposable-01"],
                    "ansible_host": "other.invalid",
                },
            }
            self.validate(hostvars=hostvars)

    def test_service_host_is_blocked_until_disposable_proof_is_recorded(self) -> None:
        service_host = {
            **self.hostvars["stg-disposable-01"],
            "bootstrap_disposable": False,
        }
        hostvars = {"stg-aio-01": service_host}

        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "blocked until the disposable VPS proof",
        ):
            self.validate("stg-aio-01", hostvars=hostvars)

        BOOTSTRAP_INVENTORY.validate_inventory_target(
            "Staging",
            "stg-aio-01",
            hostvars,
            self.root / "inventories" / "staging" / "known_hosts",
            disposable_proof_commit="a" * 40,
        )

    def test_production_disposable_host_passes_before_proof(self) -> None:
        production_host = {
            **self.hostvars["stg-disposable-01"],
            "bootstrap_capacity_reference": {
                "physical_memory_mib": 4096,
                "platform_reserve_mib": 1536,
                "capacity_budget_mib": 2560,
            },
        }
        hostvars = {"prd-disposable-01": production_host}

        validated = BOOTSTRAP_INVENTORY.validate_inventory_target(
            "Production",
            "prd-disposable-01",
            hostvars,
            self.root / "inventories" / "staging" / "known_hosts",
        )

        self.assertEqual(validated, production_host)

    def test_production_service_alias_is_blocked_even_if_flagged_disposable(self) -> None:
        service_host = {
            **self.hostvars["stg-disposable-01"],
            "bootstrap_disposable": True,
            "bootstrap_capacity_reference": {
                "physical_memory_mib": 4096,
                "platform_reserve_mib": 1536,
                "capacity_budget_mib": 2560,
            },
        }
        hostvars = {"prd-aio-01": service_host}

        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "blocked until the disposable VPS proof",
        ):
            BOOTSTRAP_INVENTORY.validate_inventory_target(
                "Production",
                "prd-aio-01",
                hostvars,
                self.root / "inventories" / "staging" / "known_hosts",
            )

    def test_disposable_only_operation_rejects_service_alias_after_proof(self) -> None:
        service_host = {
            **self.hostvars["stg-disposable-01"],
            "bootstrap_disposable": False,
        }
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "explicitly flagged disposable host",
        ):
            BOOTSTRAP_INVENTORY.validate_inventory_target(
                "Staging",
                "stg-aio-01",
                {"stg-aio-01": service_host},
                self.root / "inventories" / "staging" / "known_hosts",
                disposable_proof_commit="a" * 40,
                require_disposable=True,
            )

    def test_disposable_only_operation_requires_disposable_flag_after_proof(
        self,
    ) -> None:
        hostvars = {
            "stg-disposable-01": {
                **self.hostvars["stg-disposable-01"],
                "bootstrap_disposable": False,
            }
        }
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "explicitly flagged disposable host",
        ):
            BOOTSTRAP_INVENTORY.validate_inventory_target(
                "Staging",
                "stg-disposable-01",
                hostvars,
                self.root / "inventories" / "staging" / "known_hosts",
                disposable_proof_commit="a" * 40,
                require_disposable=True,
            )

    def test_invalid_disposable_proof_reference_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "full Git commit SHA",
        ):
            BOOTSTRAP_INVENTORY.validate_inventory_target(
                "Staging",
                "stg-disposable-01",
                self.hostvars,
                self.root / "inventories" / "staging" / "known_hosts",
                disposable_proof_commit="not-a-commit",
            )

        known_hosts = self.root / "inventories" / "staging" / "known_hosts"
        known_hosts.write_text("# no verified fixture key\n", encoding="utf-8")
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError, "no committed host-key pin"
        ):
            self.validate()

    def test_rejects_capacity_above_physical_ram_after_reserve(self) -> None:
        hostvars = {
            **self.hostvars,
            "stg-disposable-01": {
                **self.hostvars["stg-disposable-01"],
                "capacity_budget_mib": 1025,
            },
        }
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "exceeds physical memory",
        ):
            self.validate(hostvars=hostvars)

    def test_rejects_capacity_above_the_environment_reference_ceiling(self) -> None:
        hostvars = {
            **self.hostvars,
            "stg-disposable-01": {
                **self.hostvars["stg-disposable-01"],
                "physical_memory_mib": 4096,
                "capacity_budget_mib": 1025,
            },
        }
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "reference ceiling",
        ):
            self.validate(hostvars=hostvars)

    def test_rejects_missing_source_policy_exception(self) -> None:
        hostvars = {
            **self.hostvars,
            "stg-disposable-01": {
                key: value
                for key, value in self.hostvars["stg-disposable-01"].items()
                if key != "ssh_source_policy_exception"
            },
        }
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "documented exception",
        ):
            self.validate(hostvars=hostvars)

    def test_rejects_passwords_and_private_keys_in_inventory_variables(self) -> None:
        for variable_name in ("provider_password", "ansible_ssh_private_key_file"):
            with self.subTest(variable_name=variable_name):
                hostvars = {
                    **self.hostvars,
                    "stg-disposable-01": {
                        **self.hostvars["stg-disposable-01"],
                        variable_name: "fixture-value",
                    },
                }
                with self.assertRaisesRegex(
                    BOOTSTRAP_INVENTORY.BootstrapValidationError,
                    "must not contain",
                ):
                    self.validate(hostvars=hostvars)


class BootstrapDispatchTests(unittest.TestCase):
    def test_proven_dispatch_app_actor_id_is_rejected_by_default(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "deployment App identity",
        ):
            BOOTSTRAP_INVENTORY.validate_dispatch(
                "Staging",
                "refs/heads/feature/bootstrap",
                str(BOOTSTRAP_INVENTORY.DISPATCH_APP_ACTOR_ID),
            )

        BOOTSTRAP_INVENTORY.validate_dispatch(
            "Staging",
            "refs/heads/feature/bootstrap",
            "12345",
        )

    def test_dispatch_app_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "deployment App identity",
        ):
            BOOTSTRAP_INVENTORY.validate_dispatch(
                "Staging",
                "refs/heads/feature/bootstrap",
                "12345",
                expected_actor_id=12345,
            )

    def test_unknown_dispatch_app_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "identity is not proven",
        ):
            BOOTSTRAP_INVENTORY.validate_dispatch(
                "Staging",
                "refs/heads/feature/bootstrap",
                "12345",
                expected_actor_id=None,
            )

    def test_production_requires_release_branch(self) -> None:
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "release branches",
        ):
            BOOTSTRAP_INVENTORY.validate_dispatch(
                "Production",
                "refs/heads/main",
                "12345",
                expected_actor_id=67890,
            )

    def test_inventory_path_is_fixed_by_environment(self) -> None:
        self.assertEqual(
            BOOTSTRAP_INVENTORY.validate_inventory_path(
                "Staging", "inventories/staging/hosts.yml", required=True
            ).as_posix(),
            "inventories/staging/hosts.yml",
        )
        with self.assertRaisesRegex(
            BOOTSTRAP_INVENTORY.BootstrapValidationError,
            "fixed mapping",
        ):
            BOOTSTRAP_INVENTORY.validate_inventory_path(
                "Staging", "inventories/production/hosts.yml", required=True
            )

    def test_target_preflight_writes_only_the_validated_disposable_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"
            environment = {
                "BOOTSTRAP_ENVIRONMENT": "Staging",
                "BOOTSTRAP_TARGET_HOST": "stg-disposable-01",
                "ANSIBLE_INVENTORY_PATH": "inventories/staging/hosts.yml",
                "GITHUB_OUTPUT": str(output_path),
            }
            host = {"bootstrap_disposable": True}

            with mock.patch.dict(os.environ, environment, clear=True):
                with mock.patch.object(
                    BOOTSTRAP_INVENTORY,
                    "validate_target",
                    return_value=host,
                ):
                    result = BOOTSTRAP_INVENTORY.main(["--stage", "target"])

            self.assertEqual(result, 0)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "target_disposable=true\n",
            )


if __name__ == "__main__":
    unittest.main()
