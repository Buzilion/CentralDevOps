import unittest
from pathlib import Path

from jinja2 import Environment, StrictUndefined


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOCKET_TEMPLATE = (
    REPOSITORY_ROOT
    / "roles"
    / "ssh_hardening"
    / "templates"
    / "centraldevops-ssh.socket.conf.j2"
)


class SSHSocketPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        template_source = SOCKET_TEMPLATE.read_text(encoding="utf-8")
        cls.template = Environment(undefined=StrictUndefined).from_string(
            template_source
        )

    def render_policy(self, ports: list[int]) -> list[str]:
        return [
            line
            for line in self.template.render(ssh_listen_ports=ports).splitlines()
            if line.strip()
        ]

    def test_transition_policy_resets_default_and_keeps_both_ports(self) -> None:
        self.assertEqual(
            self.render_policy([22, 4671]),
            [
                "[Socket]",
                "ListenStream=",
                "BindIPv6Only=ipv6-only",
                "ListenStream=0.0.0.0:22",
                "ListenStream=[::]:22",
                "ListenStream=0.0.0.0:4671",
                "ListenStream=[::]:4671",
            ],
        )

    def test_final_policy_resets_default_and_keeps_only_managed_port(self) -> None:
        self.assertEqual(
            self.render_policy([4671]),
            [
                "[Socket]",
                "ListenStream=",
                "BindIPv6Only=ipv6-only",
                "ListenStream=0.0.0.0:4671",
                "ListenStream=[::]:4671",
            ],
        )
