import importlib.util
import base64
import struct
import tempfile
import sys
import unittest
from pathlib import Path
from unittest import mock
import json


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

BOOTSTRAP = sys.modules.get("bootstrap_inventory")
if BOOTSTRAP is None:
    BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
        "bootstrap_inventory", TOOLS / "bootstrap_inventory.py"
    )
    if BOOTSTRAP_SPEC is None or BOOTSTRAP_SPEC.loader is None:
        raise RuntimeError("could not load bootstrap inventory validation module")
    BOOTSTRAP = importlib.util.module_from_spec(BOOTSTRAP_SPEC)
    sys.modules[BOOTSTRAP_SPEC.name] = BOOTSTRAP
    BOOTSTRAP_SPEC.loader.exec_module(BOOTSTRAP)

import configure_inputs as VALIDATOR


def ed25519_public_key_fixture() -> str:
    key_blob = (
        struct.pack(">I", len(b"ssh-ed25519"))
        + b"ssh-ed25519"
        + struct.pack(">I", 32)
        + b"\x01" * 32
    )
    return f"ssh-ed25519 {base64.b64encode(key_blob).decode('ascii')} fixture"


def inventory_fixture() -> dict[str, object]:
    common_facts = {
        "bootstrap_admin_public_key": ed25519_public_key_fixture(),
        "docker_engine_package_version": "5:29.9.3-1~ubuntu.24.04~noble",
        "docker_containerd_package_version": "2.4.2-3~ubuntu.24.04~noble",
        "docker_buildx_package_version": "0.38.1-1~ubuntu.24.04~noble",
        "docker_compose_plugin_package_version": "2.40.3-1~ubuntu.24.04~noble",
        "docker_db_subnet_cidr": "10.251.0.0/24",
        "docker_default_address_pools": [
            {"base": "10.250.0.0/16", "size": 24}
        ],
        "deploy_runtime_public_key": ed25519_public_key_fixture(),
    }
    return {
        "_meta": {
            "hostvars": {
                "stg-aio-01": dict(common_facts),
                "stg-proxy-01": dict(common_facts),
            }
        },
        "all": {
            "children": ["app_nodes", "proxy_nodes"],
            "hosts": [],
        },
        "app_nodes": {
            "children": [],
            "hosts": ["stg-aio-01"],
        },
        "proxy_nodes": {
            "children": [],
            "hosts": ["stg-proxy-01"],
        },
    }


class ConfigureInputValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.configure_profile_config = VALIDATOR.load_configure_profile_config(
            VALIDATOR.ROOT
        )
        profile_path = self.root / VALIDATOR.PROFILE_FILE
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(
                {
                    "configure_profiles": {
                        profile: list(roles)
                        for profile, roles in self.configure_profile_config.profiles.items()
                    },
                    "configure_required_inventory_facts": list(
                        self.configure_profile_config.required_inventory_facts
                    ),
                }
            ),
            encoding="utf-8",
        )
        for roles in self.configure_profile_config.profiles.values():
            for role in roles:
                task_file = self.root / "roles" / role / "tasks" / "main.yml"
                task_file.parent.mkdir(parents=True, exist_ok=True)
                task_file.touch()

    def validate(
        self,
        *,
        environment: str = "Staging",
        profile: str = "app",
        limit: str = "",
        check_mode: str = "true",
        reference: str = "refs/heads/feature/configure",
        actor_id: str = "12345",
        inventory: dict[str, object] | None = None,
    ):
        return VALIDATOR.validate_request(
            root=self.root,
            target_environment=environment,
            profile=profile,
            limit=limit,
            check_mode=check_mode,
            reference=reference,
            actor_id=actor_id,
            inventory_document=inventory_fixture() if inventory is None else inventory,
        )

    def test_exact_choices_and_empty_limit_select_the_fixed_inventory(self) -> None:
        request = self.validate()

        self.assertEqual(request.target_environment, "Staging")
        self.assertEqual(request.profile, "app")
        self.assertEqual(
            request.inventory_path.as_posix(),
            "inventories/staging/hosts.yml",
        )
        self.assertEqual(request.target_hosts, ("stg-aio-01", "stg-proxy-01"))
        self.assertTrue(request.check_mode)

    def test_exact_host_and_group_limits_select_only_inventory_targets(self) -> None:
        host_request = self.validate(limit="stg-aio-01")
        group_request = self.validate(limit="app_nodes")

        self.assertEqual(host_request.target_hosts, ("stg-aio-01",))
        self.assertEqual(group_request.target_hosts, ("stg-aio-01",))

    def test_valid_production_release_dispatch_selects_production_inventory(self) -> None:
        staging_hostvars = inventory_fixture()["_meta"]["hostvars"]
        production_hostvars = dict(
            staging_hostvars["stg-aio-01"]
        )
        inventory = {
            "_meta": {"hostvars": {"prd-aio-01": production_hostvars}},
            "all": {"children": ["app_nodes"], "hosts": []},
            "app_nodes": {"children": [], "hosts": ["prd-aio-01"]},
        }

        request = self.validate(
            environment="Production",
            limit="prd-aio-01",
            reference="refs/heads/release/v1",
            inventory=inventory,
        )

        self.assertEqual(
            request.inventory_path.as_posix(),
            "inventories/production/hosts.yml",
        )

    def test_dispatch_app_identity_is_rejected_before_inventory_loading(self) -> None:
        with mock.patch.object(VALIDATOR, "load_inventory_document") as load:
            with self.assertRaisesRegex(
                VALIDATOR.ConfigureValidationError,
                "deployment App identity",
            ):
                VALIDATOR.validate_request(
                    target_environment="Staging",
                    profile="app",
                    limit="",
                    check_mode="true",
                    reference="refs/heads/feature/configure",
                    actor_id=str(BOOTSTRAP.DISPATCH_APP_ACTOR_ID),
                )

        load.assert_not_called()

    def test_production_requires_release_branch_before_inventory_loading(self) -> None:
        with mock.patch.object(VALIDATOR, "load_inventory_document") as load:
            with self.assertRaisesRegex(
                VALIDATOR.ConfigureValidationError,
                "release branches",
            ):
                VALIDATOR.validate_request(
                    target_environment="Production",
                    profile="app",
                    limit="",
                    check_mode="true",
                    reference="refs/heads/main",
                    actor_id="12345",
                )

        load.assert_not_called()

    def test_invalid_environment_profile_check_mode_and_actor_are_rejected(self) -> None:
        invalid_requests = (
            {"environment": "staging"},
            {"profile": "all"},
            {"check_mode": "yes"},
            {"actor_id": "not-an-id"},
        )
        for overrides in invalid_requests:
            with self.subTest(overrides=overrides):
                with self.assertRaises(VALIDATOR.ConfigureValidationError):
                    self.validate(**overrides)

    def test_production_release_prefix_requires_a_branch_name(self) -> None:
        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "release branches",
        ):
            self.validate(
                environment="Production",
                reference="refs/heads/release/",
            )

    def test_rejects_pattern_syntax_and_option_like_limits_before_loading(self) -> None:
        invalid_limits = (
            "*",
            "--limit=stg-aio-01",
            "stg-aio-01,stg-proxy-01",
            "all:!proxy_nodes",
            "stg-aio-01 ",
            "stg-aio-01\n",
            "stg/aio/01",
        )
        for limit in invalid_limits:
            with self.subTest(limit=limit):
                with mock.patch.object(VALIDATOR, "load_inventory_document") as load:
                    with self.assertRaises(VALIDATOR.ConfigureValidationError):
                        VALIDATOR.validate_request(
                            target_environment="Staging",
                            profile="app",
                            limit=limit,
                            check_mode="true",
                            reference="refs/heads/feature/configure",
                            actor_id="12345",
                        )
                load.assert_not_called()

    def test_rejects_unknown_cross_environment_and_empty_group_limits(self) -> None:
        for limit in ("stg-aio-02", "prd-aio-01", "missing_group"):
            with self.subTest(limit=limit):
                with self.assertRaises(VALIDATOR.ConfigureValidationError):
                    self.validate(limit=limit)

        inventory = inventory_fixture()
        inventory["empty_nodes"] = {"children": [], "hosts": []}
        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "group has no hosts",
        ):
            self.validate(limit="empty_nodes", inventory=inventory)

    def test_rejects_an_empty_target_inventory(self) -> None:
        inventory = inventory_fixture()
        inventory["_meta"] = {"hostvars": {}}

        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "no target hosts",
        ):
            self.validate(inventory=inventory)

    def test_exact_profile_role_matrix_and_deduplicated_all_in_one(self) -> None:
        config = VALIDATOR.load_configure_profile_config(VALIDATOR.ROOT)
        base = (
            "common",
            "users",
            "ssh_hardening",
            "firewall",
            "docker",
            "deploy_runtime",
            "monitoring_agent",
            "backup",
        )
        self.assertEqual(config.profiles["app"], base)
        self.assertEqual(config.profiles["proxy"], base + ("nginx", "certbot"))
        self.assertEqual(
            config.profiles["database"],
            (
                "common",
                "users",
                "ssh_hardening",
                "firewall",
                "docker",
                "deploy_runtime",
                "monitoring_agent",
                "postgresql",
                "backup",
            ),
        )
        self.assertEqual(
            config.profiles["monitoring"],
            base + ("collector",),
        )

        all_in_one = config.profiles["all-in-one"]
        expected = tuple(
            dict.fromkeys(
                config.profiles["app"]
                + config.profiles["proxy"]
                + config.profiles["database"]
            )
        )
        self.assertEqual(all_in_one, expected)
        self.assertEqual(len(all_in_one), len(set(all_in_one)))

    def test_missing_profile_roles_fail_before_inventory_loading(self) -> None:
        empty_root = self.root / "missing-roles"
        profile_path = empty_root / VALIDATOR.PROFILE_FILE
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(
                {
                    "configure_profiles": {
                        "app": ["common", "docker"],
                        "proxy": ["common", "docker"],
                        "database": ["common", "docker"],
                        "monitoring": ["common", "docker"],
                        "all-in-one": ["common", "docker"],
                    },
                    "configure_required_inventory_facts": list(
                        self.configure_profile_config.required_inventory_facts
                    ),
                }
            ),
            encoding="utf-8",
        )
        with mock.patch.object(VALIDATOR, "load_inventory_document") as load:
            with self.assertRaisesRegex(
                VALIDATOR.ConfigureValidationError,
                "missing required roles: common, docker",
            ):
                VALIDATOR.validate_request(
                    root=empty_root,
                    target_environment="Staging",
                    profile="app",
                    limit="",
                    check_mode="true",
                    reference="refs/heads/feature/configure",
                    actor_id="12345",
                )
        load.assert_not_called()

    def test_required_inventory_facts_fail_closed_on_missing_key_and_overlap(self) -> None:
        inventory = inventory_fixture()
        inventory["_meta"]["hostvars"]["stg-aio-01"].pop(
            "deploy_runtime_public_key"
        )
        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "deploy_runtime_public_key.*missing",
        ):
            self.validate(limit="stg-aio-01", inventory=inventory)

        inventory = inventory_fixture()
        inventory["_meta"]["hostvars"]["stg-aio-01"][
            "docker_db_subnet_cidr"
        ] = "10.250.0.0/24"
        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "overlaps a Docker address pool",
        ):
            self.validate(limit="stg-aio-01", inventory=inventory)

    def test_requires_exactly_one_deploy_public_key(self) -> None:
        inventory = inventory_fixture()
        key = inventory["_meta"]["hostvars"]["stg-aio-01"][
            "deploy_runtime_public_key"
        ]
        inventory["_meta"]["hostvars"]["stg-aio-01"][
            "deploy_runtime_public_key"
        ] = f"{key}\n{key}"

        with self.assertRaisesRegex(
            VALIDATOR.ConfigureValidationError,
            "exactly one public key",
        ):
            self.validate(limit="stg-aio-01", inventory=inventory)

    def test_inventory_validation_does_not_inherit_secret_values(self) -> None:
        source_environment = {
            "CONFIGURE_TARGET_ENVIRONMENT": "Staging",
            "ANSIBLE_SSH_PRIVATE_KEY": "admin-private-key",
            "DEPLOY_SSH_PRIVATE_KEY": "deploy-private-key",
            "GHCR_PULL_TOKEN": "ghcr-secret",
        }

        validation_environment = VALIDATOR.inventory_validation_environment(
            source_environment
        )

        self.assertNotIn("ANSIBLE_SSH_PRIVATE_KEY", validation_environment)
        self.assertNotIn("DEPLOY_SSH_PRIVATE_KEY", validation_environment)
        self.assertNotIn("GHCR_PULL_TOKEN", validation_environment)
        self.assertEqual(
            validation_environment["CONFIGURE_TARGET_ENVIRONMENT"],
            "Staging",
        )


if __name__ == "__main__":
    unittest.main()
