import importlib.util
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

SPEC = importlib.util.spec_from_file_location(
    "validate_docker_subnet", TOOLS / "validate_docker_subnet.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load Docker subnet validation module")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


DEFAULT_POOLS = [{"base": "10.250.0.0/16", "size": 24}]
EXISTING_NETWORKS = [
    {
        "Name": "bridge",
        "Id": "b" * 64,
        "Driver": "bridge",
        "Scope": "local",
        "IPAM": {"Config": [{"Subnet": "172.17.0.0/16"}]},
    },
    {
        "Name": "edge",
        "Id": "e" * 64,
        "Driver": "bridge",
        "Scope": "local",
        "IPAM": {"Config": [{"Subnet": "10.250.0.0/24"}]},
    },
]


class DockerSubnetValidationTests(unittest.TestCase):
    def validate(
        self,
        subnet: str = "10.251.0.0/24",
        routes=None,
        networks=None,
        pools=None,
    ) -> None:
        VALIDATOR.validate_subnet_state(
            subnet,
            [{"dst": "default"}] if routes is None else routes,
            EXISTING_NETWORKS if networks is None else networks,
            DEFAULT_POOLS if pools is None else pools,
        )

    def test_non_overlapping_subnet_and_existing_matching_db_are_idempotent(self) -> None:
        networks = EXISTING_NETWORKS + [
            {
                "Name": "db",
                "Id": "d" * 64,
                "Driver": "bridge",
                "Scope": "local",
                "IPAM": {"Config": [{"Subnet": "10.251.0.0/24"}]},
            }
        ]
        routes = [
            {"dst": "default"},
            {"dst": "192.168.10.0/24"},
            {"dst": "10.251.0.0/24", "dev": "br-dddddddddddd"},
            {"dst": "10.251.0.8/32", "dev": "br-dddddddddddd"},
        ]

        self.validate(routes=routes, networks=networks)

    def test_detects_host_route_even_when_matching_db_network_exists(self) -> None:
        networks = EXISTING_NETWORKS + [
            {
                "Name": "db",
                "Id": "d" * 64,
                "Driver": "bridge",
                "Scope": "local",
                "IPAM": {"Config": [{"Subnet": "10.251.0.0/24"}]},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "docker_db_subnet_cidr overlaps a host route",
        ):
            self.validate(
                routes=[{"dst": "10.251.0.0/24", "dev": "eth0"}],
                networks=networks,
            )

    def test_rejects_malformed_non_private_and_oversized_subnets(self) -> None:
        for subnet in (
            "10.251.0.1/24",
            "203.0.113.0/24",
            "10.251.0.0/31",
            "10.251.0.0/24;echo bad",
        ):
            with self.subTest(subnet=subnet):
                with self.assertRaises(
                    VALIDATOR.DockerSubnetValidationError
                ):
                    self.validate(subnet=subnet)

    def test_rejects_overlap_with_docker_pool(self) -> None:
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "Docker address pool",
        ):
            self.validate(subnet="10.250.1.0/24")

    def test_rejects_overlap_with_host_route(self) -> None:
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "host route",
        ):
            self.validate(routes=[{"dst": "10.251.0.0/25"}])

    def test_rejects_default_pool_overlap_with_host_route(self) -> None:
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "Docker address pool overlaps a host route",
        ):
            self.validate(
                routes=[{"dst": "10.250.0.0/24"}],
                networks=[],
            )

    def test_rejects_overlap_with_an_existing_docker_network(self) -> None:
        networks = EXISTING_NETWORKS + [
            {
                "Name": "apps",
                "Id": "a" * 64,
                "Driver": "bridge",
                "Scope": "local",
                "IPAM": {"Config": [{"Subnet": "10.251.0.0/25"}]},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "existing Docker network",
        ):
            self.validate(networks=networks)

    def test_rejects_an_existing_db_network_with_a_different_subnet(self) -> None:
        networks = EXISTING_NETWORKS + [
            {
                "Name": "db",
                "Id": "d" * 64,
                "Driver": "bridge",
                "Scope": "local",
                "IPAM": {"Config": [{"Subnet": "10.252.0.0/24"}]},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "existing db network does not match",
        ):
            self.validate(networks=networks)

    def test_rejects_an_existing_db_network_without_a_fixed_ipv4_subnet(self) -> None:
        networks = EXISTING_NETWORKS + [
            {
                "Name": "db",
                "Id": "d" * 64,
                "Driver": "bridge",
                "Scope": "local",
                "IPAM": {"Config": []},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "existing db network does not match",
        ):
            self.validate(networks=networks)

    def test_rejects_misconfigured_shared_network_driver(self) -> None:
        networks = [
            {
                "Name": "edge",
                "Driver": "host",
                "Scope": "local",
                "IPAM": {"Config": []},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "existing edge network",
        ):
            self.validate(networks=networks)

    def test_rejects_shared_network_with_ipv6_enabled(self) -> None:
        networks = [
            {
                "Name": "edge",
                "Driver": "bridge",
                "Scope": "local",
                "EnableIPv6": True,
                "IPAM": {"Config": [{"Subnet": "10.250.0.0/24"}]},
            }
        ]
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "reviewed bridge policy",
        ):
            self.validate(networks=networks)

    def test_rejects_invalid_routes_and_address_pools(self) -> None:
        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "host route destination",
        ):
            self.validate(routes=[{"dst": "not-a-network"}])

        with self.assertRaisesRegex(
            VALIDATOR.DockerSubnetValidationError,
            "address-pools",
        ):
            self.validate(pools=[])


if __name__ == "__main__":
    unittest.main()
