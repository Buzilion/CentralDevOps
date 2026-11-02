import base64
import subprocess
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
ENCODER_PATH = TOOLS / "encode_ssh_private_key.py"


class EncodeSSHPrivateKeyTests(unittest.TestCase):
    def test_encodes_exact_input_with_prefix_and_without_wrapping(self) -> None:
        private_key = (
            b"-----BEGIN OPENSSH PRIVATE KEY-----\r\n"
            + b"A" * 200
            + b"\r\n-----END OPENSSH PRIVATE KEY-----\r\n"
        )

        result = subprocess.run(
            [sys.executable, str(ENCODER_PATH)],
            input=private_key,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout,
            b"base64:" + base64.b64encode(private_key),
        )
        self.assertEqual(result.stderr, b"")

    def test_empty_input_fails_without_writing_to_stdout(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ENCODER_PATH)],
            input=b"",
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"empty", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
