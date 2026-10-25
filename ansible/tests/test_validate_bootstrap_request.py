import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPOSITORY_ROOT / "ansible" / "scripts" / "validate_bootstrap_request.py"
SPEC = importlib.util.spec_from_file_location("validate_bootstrap_request", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def make_inventory(hosts, staging=(), production=()):
    return {
        "_meta": {"hostvars": hosts},
        "staging": {"hosts": {host: {} for host in staging}},
        "production": {"hosts": {host: {} for host in production}},
    }


class ValidateBootstrapRequestTests(unittest.TestCase):
    def setUp(self):
        self.selected_path = "ansible/inventory/customer-builder-engine.yml"
        self.other_path = "ansible/inventory/outbound-marketing.yml"
        self.selected_inventory = make_inventory(
            {
                "cbe-staging-1": {
                    "ansible_host": "192.0.2.10",
                    "bootstrap_user": "provider",
                    "bootstrap_host_id": "buz-stg-1",
                }
            },
            staging=("cbe-staging-1",),
        )
        self.other_inventory = make_inventory({})

    def run_validator(self, *, extra_env=None, inventories=None):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "github-output"
            environment = {
                "BOOTSTRAP_INVENTORY": self.selected_path,
                "BOOTSTRAP_TARGET_HOST": "cbe-staging-1",
                "BOOTSTRAP_EXECUTION_MODE": "validate",
                "BOOTSTRAP_SERVICE_DOCKER": "false",
                "BOOTSTRAP_SERVICE_NGINX": "false",
                "BOOTSTRAP_SERVICE_POSTGRESQL": "false",
                "BOOTSTRAP_SERVICE_ALLOY": "false",
                "DEFAULT_BRANCH": "main",
                "GITHUB_REF": "refs/heads/main",
                "GITHUB_OUTPUT": str(output_path),
            }
            environment.update(extra_env or {})
            inventory_data = inventories or {
                self.selected_path: self.selected_inventory,
                self.other_path: self.other_inventory,
            }

            def fake_run(command, **kwargs):
                data = inventory_data[command[2]]
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(data),
                    stderr="",
                )

            stdout = io.StringIO()
            with (
                patch.dict(os.environ, environment, clear=True),
                patch.object(VALIDATOR.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(stdout),
            ):
                result = VALIDATOR.main()

            outputs = (
                output_path.read_text(encoding="utf-8")
                if output_path.exists()
                else ""
            )
            return result, stdout.getvalue(), outputs

    def test_valid_single_host_emits_stable_environment_and_identity(self):
        result, stdout, outputs = self.run_validator()

        self.assertEqual(result, 0)
        self.assertIn("Validated one target", stdout)
        self.assertIn("bootstrap_host_id=buz-stg-1", outputs)
        self.assertIn("github_environment=Staging", outputs)
        self.assertIn("bootstrap_effective_services_json=[]", outputs)
        self.assertIn(
            "bootstrap_known_hosts_variable=BOOTSTRAP_BUZ_STG_1_SSH_KNOWN_HOSTS",
            outputs,
        )
        self.assertIn("deploy_public_key_variable=STG_SSH_PUBLIC_KEY", outputs)
        self.assertIn("deploy_private_key_secret=VPS_SSH_PRIVATE_KEY", outputs)
        self.assertIn(
            "bootstrap_password_secret=BUZ_STG_1_PASSWORD",
            outputs,
        )

    def test_production_password_secret_name_matches_host_id(self):
        production_host = "buz-prod-cbe-1"
        production_inventory = make_inventory(
            {
                production_host: {
                    "ansible_host": "192.0.2.11",
                    "bootstrap_user": "ubuntu",
                    "bootstrap_host_id": "buz-prod-1",
                }
            },
            production=(production_host,),
        )

        result, stdout, outputs = self.run_validator(
            extra_env={"BOOTSTRAP_TARGET_HOST": production_host},
            inventories={
                self.selected_path: production_inventory,
                self.other_path: self.other_inventory,
            },
        )

        self.assertEqual(result, 0, stdout)
        self.assertIn("bootstrap_password_secret=BUZ_PROD_1_PASSWORD", outputs)
        self.assertIn("bootstrap_known_hosts_variable=BUZ_PROD_KNOWN_HOSTS", outputs)
        self.assertIn("deploy_public_key_variable=BUZ_PROD_1_SSH_PUBLIC_KEY", outputs)
        self.assertIn("deploy_private_key_secret=BUZ_PROD_1_SSH_PRIVATE_KEY", outputs)

    def test_nginx_adds_docker_and_validates_the_route_dns(self):
        with patch.object(
            VALIDATOR.socket,
            "getaddrinfo",
            return_value=[(2, 1, 6, "", ("192.0.2.10", 443))],
        ):
            result, stdout, outputs = self.run_validator(
                extra_env={"BOOTSTRAP_SERVICE_NGINX": "true"}
            )

        self.assertEqual(result, 0, stdout)
        self.assertIn('"docker","nginx"', outputs)
        self.assertIn("bootstrap_route_fqdn=cbe-staging.buzilion.id", outputs)

    def test_same_address_across_environments_is_rejected(self):
        selected_inventory = make_inventory(
            {
                "cbe-staging-1": {
                    "ansible_host": "192.0.2.10",
                    "bootstrap_user": "provider",
                    "bootstrap_host_id": "buz-shared-1",
                }
            },
            staging=("cbe-staging-1",),
        )
        other_inventory = make_inventory(
            {
                "om-production-1": {
                    "ansible_host": "192.0.2.10",
                    "bootstrap_user": "provider",
                    "bootstrap_host_id": "buz-shared-1",
                }
            },
            production=("om-production-1",),
        )

        result, stdout, _ = self.run_validator(
            inventories={
                self.selected_path: selected_inventory,
                self.other_path: other_inventory,
            }
        )

        self.assertEqual(result, 1)
        self.assertIn("Unresolved ansible_host collision", stdout)

    def test_nested_inventory_credentials_are_rejected(self):
        selected_inventory = make_inventory(
            {
                "cbe-staging-1": {
                    "ansible_host": "192.0.2.10",
                    "bootstrap_user": "provider",
                    "bootstrap_host_id": "buz-stg-1",
                    "service_credentials": {"api_token": "not printed"},
                }
            },
            staging=("cbe-staging-1",),
        )

        result, stdout, _ = self.run_validator(
            inventories={
                self.selected_path: selected_inventory,
                self.other_path: self.other_inventory,
            }
        )

        self.assertEqual(result, 1)
        self.assertIn("credential-like fields", stdout)
        self.assertNotIn("not printed", stdout)


if __name__ == "__main__":
    unittest.main()
