import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


CHECKER = Path(__file__).resolve().parents[1] / "check-github-names.py"
CATALOG = CHECKER.with_name("github-names.json")
CHECKER_SPEC = importlib.util.spec_from_file_location("check_github_names", CHECKER)
if CHECKER_SPEC is None or CHECKER_SPEC.loader is None:
    raise RuntimeError("could not load checker module for focused unit tests")
CHECKER_MODULE = importlib.util.module_from_spec(CHECKER_SPEC)
sys.modules[CHECKER_SPEC.name] = CHECKER_MODULE
CHECKER_SPEC.loader.exec_module(CHECKER_MODULE)


class CheckGithubNamesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.write_catalog()

    def write_catalog(self) -> Path:
        path = self.root / "deployment" / "tools" / "github-names.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.catalog, indent=2), encoding="utf-8")
        return path

    def write_workflow(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def initialize_git(self) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "init", "--quiet"],
            check=True,
            capture_output=True,
            text=True,
        )

    def git_add(self, *relative_paths: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", *relative_paths],
            check=True,
            capture_output=True,
            text=True,
        )

    def private_key_header(self) -> str:
        return (
            "-" * 5
            + "BEGIN "
            + "RSA "
            + "PRIVATE "
            + "KEY"
            + "-" * 5
        )

    def assert_violation(
        self,
        result: subprocess.CompletedProcess[str],
        relative_path: str,
        line: int,
        rule_id: str,
    ) -> None:
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f"{relative_path}:{line} {rule_id}", result.stdout)

    def test_repository_without_workflows_passes(self) -> None:
        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_clean_repository_and_static_references_pass(self) -> None:
        self.write_workflow(
            ".github/workflows/valid.yml",
            "\n".join(
                [
                    "name: valid",
                    "on: workflow_dispatch",
                    "env:",
                    "  CONFIG: ${{ vars.ANSIBLE_CONFIG_PATH }}",
                    "  BACKUP_BUCKET: ${{ vars['BACKUP_S3_BUCKET'] }}",
                    "  ADMIN_KEY: ${{ secrets['ANSIBLE_SSH_PRIVATE_KEY'] }}",
                    '  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}',
                ]
            ),
        )
        self.write_workflow(
            ".github/workflows/nested/valid.yaml",
            "name: nested valid\n"
            "env:\n"
            "  BUCKET: ${{ vars.BACKUP_S3_BUCKET }}\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")

    def test_reserved_and_generic_names_report_expected_rules_and_lines(self) -> None:
        self.write_workflow(
            ".github/workflows/names.yml",
            "\n".join(
                [
                    "name: bad names",
                    "env:",
                    "  STAGING: ${{ secrets.STAGING_X }}",
                    "  GITHUB: ${{ vars.GITHUB_X }}",
                    "  GENERIC: ${{ secrets.TOKEN }}",
                ]
            ),
        )

        result = self.run_checker()

        self.assert_violation(result, ".github/workflows/names.yml", 3, "N02")
        self.assertIn(".github/workflows/names.yml:4 N02", result.stdout)
        self.assertIn(".github/workflows/names.yml:5 N03", result.stdout)

    def test_bad_pattern_and_uncataloged_name_report_expected_rules_and_lines(
        self,
    ) -> None:
        self.write_workflow(
            ".github/workflows/names.yml",
            "\n".join(
                [
                    "name: bad names",
                    "env:",
                    "  WRONG: ${{ secrets.WRONG_PREFIX_NAME }}",
                    "  UNKNOWN: ${{ vars.DEPLOY_NOT_IN_CATALOG }}",
                ]
            ),
        )

        result = self.run_checker()

        self.assert_violation(result, ".github/workflows/names.yml", 3, "N01")
        self.assertIn(".github/workflows/names.yml:4 N04", result.stdout)

    def test_variable_used_as_secret_reports_wrong_kind(self) -> None:
        self.write_workflow(
            ".github/workflows/wrong-kind.yml",
            "name: wrong kind\n"
            "env:\n"
            "  VALUE: ${{ secrets.ANSIBLE_CONFIG_PATH }}\n",
        )

        result = self.run_checker()

        self.assert_violation(result, ".github/workflows/wrong-kind.yml", 3, "N04")

    def test_dynamic_access_and_inherit_forms_report_n05(self) -> None:
        self.write_workflow(
            ".github/workflows/dynamic.yml",
            "\n".join(
                [
                    "name: dynamic access",
                    "env:",
                    "  FIRST: ${{ secrets[env.NAME] }}",
                    "  SECOND: ${{ toJSON(secrets) }}",
                    "  THIRD: secrets: inherit",
                    "  FOURTH: ${{ secrets.inherit }}",
                ]
            ),
        )

        result = self.run_checker()

        self.assert_violation(result, ".github/workflows/dynamic.yml", 3, "N05")
        for line in (4, 5, 6):
            self.assertIn(f".github/workflows/dynamic.yml:{line} N05", result.stdout)
        self.assertNotIn(".github/workflows/dynamic.yml:6 N01", result.stdout)

    def test_forbidden_name_in_deploy_workflow_reports_f01(self) -> None:
        self.write_workflow(
            ".github/workflows/deploy-app.yml",
            "name: deploy\n"
            "env:\n"
            "  ADMIN_KEY: ${{ secrets.ANSIBLE_SSH_PRIVATE_KEY }}\n",
        )

        result = self.run_checker()

        self.assert_violation(result, ".github/workflows/deploy-app.yml", 3, "F01")

    def test_malformed_catalog_exits_two(self) -> None:
        catalog_path = self.write_catalog()
        catalog_path.write_text("{invalid json", encoding="utf-8")

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("catalog", result.stderr.lower())
        self.assertNotIn("Traceback", result.stderr)

    def test_incomplete_catalog_exits_two(self) -> None:
        del self.catalog["forbidden_in"]
        self.write_catalog()

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("forbidden_in", result.stderr)

    def test_catalog_contains_central_names_but_not_app_repository_names(self) -> None:
        names = self.catalog["names"]
        expected_names = {
            "ANSIBLE_CONFIG_PATH",
            "ANSIBLE_REQUIREMENTS_PATH",
            "ANSIBLE_PLAYBOOKS_PATH",
            "DEPLOY_REGISTRY_DIR",
            "ANSIBLE_INVENTORY_PATH",
            "DEPLOY_HEALTHCHECK_TIMEOUT",
            "MONITORING_ENDPOINT",
            "BACKUP_RETENTION_DAYS",
            "BACKUP_S3_ENDPOINT",
            "BACKUP_S3_REGION",
            "BACKUP_S3_BUCKET",
            "ANSIBLE_SSH_PRIVATE_KEY",
            "VPS_INITIAL_ACCESS_PASSWORD",
            "DEPLOY_SSH_PRIVATE_KEY",
            "DEPLOY_RUNTIME_AGE_PRIVATE_KEY",
            "GHCR_PULL_TOKEN",
            "BACKUP_RESTIC_PASSWORD",
            "BACKUP_S3_ACCESS_KEY_ID",
            "BACKUP_S3_SECRET_ACCESS_KEY",
            "MONITORING_GRAFANA_CLOUD_TOKEN",
            "ANSIBLE_VAULT_PASSWORD",
        }

        self.assertEqual(set(names), expected_names)
        self.assertNotIn("DEPLOY_DISPATCH_APP_ID", names)
        self.assertNotIn("APP_AUTH_SECRET", names)
        for metadata in names.values():
            self.assertEqual(
                set(metadata), {"kind", "level", "introduced_by"}
            )

    def test_private_key_scan_reports_location_without_matched_content(self) -> None:
        self.initialize_git()
        relative_path = "notes/tracked-text.txt"
        header = self.private_key_header()
        payload = "NEVER_PRINT_THIS_PRIVATE_KEY_PAYLOAD"
        path = self.root / relative_path
        path.parent.mkdir(parents=True)
        path.write_text(f"preamble\n{header}\n{payload}\n", encoding="utf-8")
        self.git_add(relative_path)

        result = self.run_checker()

        self.assert_violation(result, relative_path, 2, "K01")
        self.assertNotIn(header, result.stdout + result.stderr)
        self.assertNotIn(payload, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), f"{relative_path}:2 K01")

    def test_private_key_scan_falls_back_to_directory_walk_outside_git(self) -> None:
        relative_path = "notes/untracked-text.txt"
        header = self.private_key_header()
        path = self.root / relative_path
        path.parent.mkdir(parents=True)
        path.write_text(f"preamble\n{header}\n", encoding="utf-8")

        result = self.run_checker()

        self.assert_violation(result, relative_path, 2, "K01")
        self.assertNotIn(header, result.stdout + result.stderr)

    def test_directory_walk_errors_fail_closed(self) -> None:
        def fail_walk(_root: Path, **options: object) -> None:
            onerror = options["onerror"]
            error = PermissionError(
                13, "permission denied", str(self.root / "unreadable")
            )
            onerror(error)

        with mock.patch.object(CHECKER_MODULE.os, "walk", side_effect=fail_walk):
            with self.assertRaisesRegex(
                CHECKER_MODULE.CheckerError, "cannot scan directory"
            ):
                CHECKER_MODULE._fallback_files(self.root)

    def test_private_key_scan_ignores_untracked_and_binary_files_in_git(self) -> None:
        self.initialize_git()
        header = self.private_key_header().encode("ascii")
        untracked_path = self.root / "notes" / "untracked.txt"
        binary_path = self.root / "assets" / "binary.bin"
        untracked_path.parent.mkdir(parents=True)
        binary_path.parent.mkdir(parents=True)
        untracked_path.write_bytes(header + b"\n")
        binary_path.write_bytes(header + b"\0" + b"binary")
        self.git_add("assets/binary.bin")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        self.git_add("notes/untracked.txt")
        result = self.run_checker()
        self.assert_violation(result, "notes/untracked.txt", 1, "K01")
        self.assertNotIn(header.decode("ascii"), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
