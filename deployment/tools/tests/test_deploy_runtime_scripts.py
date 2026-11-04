import shutil
import subprocess
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "deployment" / "scripts"
DEPLOY_RUNTIME_TASKS = ROOT / "roles" / "deploy_runtime" / "tasks" / "main.yml"


@unittest.skipUnless(shutil.which("sh"), "POSIX shell is required for entrypoint tests")
class DeployRuntimeScriptTests(unittest.TestCase):
    def test_entrypoints_fail_closed_without_echoing_arguments(self) -> None:
        argument = "synthetic-sensitive-argument"
        for script_name in ("centraldevops-deploy", "centraldevops-route"):
            script = SCRIPTS / script_name
            with self.subTest(script=script_name):
                result = subprocess.run(
                    ["sh", str(script), argument],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("not enabled yet", result.stderr)
                self.assertNotIn(argument, result.stderr)

    def test_ghcr_token_install_is_redacted_and_diff_disabled(self) -> None:
        tasks = yaml.safe_load(
            DEPLOY_RUNTIME_TASKS.read_text(encoding="utf-8")
        )
        token_task = next(
            task
            for task in tasks
            if task.get("name")
            == "Install the GHCR pull token without logging or diffing its value"
        )

        self.assertTrue(token_task["no_log"])
        self.assertFalse(token_task["ansible.builtin.copy"]["diff"])


if __name__ == "__main__":
    unittest.main()
