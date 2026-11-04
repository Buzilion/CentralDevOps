#!/usr/bin/env python3
"""Fail closed when the Docker db subnet overlaps a host or Docker network."""

from __future__ import annotations

import argparse
import ipaddress
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


DOCKER_DAEMON_CONFIG = Path("/etc/docker/daemon.json")
RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


class DockerSubnetValidationError(ValueError):
    """Raised when the Docker db subnet conflicts with existing networks."""


def _private_ipv4_network(value: object, label: str) -> ipaddress.IPv4Network:
    try:
        network = ipaddress.ip_network(value, strict=True)
    except (TypeError, ValueError) as exc:
        raise DockerSubnetValidationError(f"{label} is not a valid CIDR") from exc
    if (
        not isinstance(network, ipaddress.IPv4Network)
        or not any(network.subnet_of(private) for private in RFC1918_NETWORKS)
        or network.prefixlen > 30
    ):
        raise DockerSubnetValidationError(
            f"{label} must be a private IPv4 subnet with usable host addresses"
        )
    return network


def _pool_networks(value: object) -> tuple[ipaddress.IPv4Network, ...]:
    if not isinstance(value, list) or not value:
        raise DockerSubnetValidationError(
            "Docker default-address-pools must be a non-empty list"
        )

    networks: list[ipaddress.IPv4Network] = []
    for pool in value:
        if not isinstance(pool, Mapping):
            raise DockerSubnetValidationError(
                "Docker default-address-pools contains an invalid entry"
            )
        network = _private_ipv4_network(
            pool.get("base"),
            "Docker default-address-pools base",
        )
        size = pool.get("size")
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or size <= network.prefixlen
            or size > 30
        ):
            raise DockerSubnetValidationError(
                "Docker default-address-pools contains an invalid subnet size"
            )
        networks.append(network)
    return tuple(networks)


def _docker_network_subnets(
    docker_networks: object,
) -> tuple[
    tuple[tuple[str, ipaddress.IPv4Network], ...],
    bool,
    frozenset[str],
]:
    if not isinstance(docker_networks, list):
        raise DockerSubnetValidationError("Docker network inspection is invalid")

    subnets: list[tuple[str, ipaddress.IPv4Network]] = []
    seen_names: set[str] = set()
    bridge_devices: set[str] = set()
    db_network_exists = False
    for docker_network in docker_networks:
        if not isinstance(docker_network, Mapping):
            raise DockerSubnetValidationError("Docker network inspection is invalid")
        name = docker_network.get("Name")
        if not isinstance(name, str) or not name:
            raise DockerSubnetValidationError("Docker network has no name")
        if name in seen_names:
            raise DockerSubnetValidationError("Docker network names are duplicated")
        seen_names.add(name)
        if name == "db":
            db_network_exists = True

        if name in {"edge", "db"} and (
            docker_network.get("Driver") != "bridge"
            or docker_network.get("Scope") != "local"
            or docker_network.get("EnableIPv6", False) is True
        ):
            raise DockerSubnetValidationError(
                f"existing {name} network does not match the reviewed bridge policy"
            )

        if docker_network.get("Driver") == "bridge":
            options = docker_network.get("Options")
            options = options if isinstance(options, Mapping) else {}
            bridge_name = options.get("com.docker.network.bridge.name")
            network_id = docker_network.get("Id")
            if name == "bridge":
                bridge_devices.add("docker0")
            elif isinstance(bridge_name, str) and bridge_name:
                bridge_devices.add(bridge_name)
            elif isinstance(network_id, str) and len(network_id) >= 12:
                bridge_devices.add(f"br-{network_id[:12]}")

        ipam = docker_network.get("IPAM")
        config = ipam.get("Config", []) if isinstance(ipam, Mapping) else []
        if config is None:
            config = []
        if not isinstance(config, list):
            raise DockerSubnetValidationError(
                f"Docker IPAM configuration is invalid for network {name}"
            )
        for item in config:
            if not isinstance(item, Mapping):
                raise DockerSubnetValidationError(
                    f"Docker IPAM configuration is invalid for network {name}"
                )
            value = item.get("Subnet")
            if value is None:
                continue
            try:
                network = ipaddress.ip_network(value, strict=True)
            except (TypeError, ValueError) as exc:
                raise DockerSubnetValidationError(
                    f"Docker subnet is invalid for network {name}"
                ) from exc
            if isinstance(network, ipaddress.IPv4Network):
                subnets.append((name, network))
    return tuple(subnets), db_network_exists, frozenset(bridge_devices)


def validate_subnet_state(
    subnet: object,
    routes: object,
    docker_networks: object,
    default_address_pools: object,
) -> None:
    candidate = _private_ipv4_network(subnet, "docker_db_subnet_cidr")
    pools = _pool_networks(default_address_pools)
    networks, db_network_exists, bridge_devices = _docker_network_subnets(
        docker_networks
    )

    for pool in pools:
        if candidate.overlaps(pool):
            raise DockerSubnetValidationError(
                "docker_db_subnet_cidr overlaps a Docker address pool"
            )

    db_subnets = [network for name, network in networks if name == "db"]
    if db_network_exists and (
        len(db_subnets) != 1 or db_subnets[0] != candidate
    ):
        raise DockerSubnetValidationError(
            "existing db network does not match docker_db_subnet_cidr"
        )

    for name, network in networks:
        if name == "db" and network == candidate:
            continue
        if candidate.overlaps(network):
            raise DockerSubnetValidationError(
                "docker_db_subnet_cidr overlaps an existing Docker network"
            )

    if not isinstance(routes, list):
        raise DockerSubnetValidationError("host route inspection is invalid")
    for route in routes:
        if not isinstance(route, Mapping):
            raise DockerSubnetValidationError("host route inspection is invalid")
        destination = route.get("dst")
        if destination in (None, "", "default", "0.0.0.0/0"):
            continue
        if not isinstance(destination, str):
            raise DockerSubnetValidationError("host route destination is invalid")
        try:
            route_network = ipaddress.ip_network(destination, strict=False)
        except ValueError as exc:
            raise DockerSubnetValidationError(
                "host route destination is invalid"
            ) from exc
        if (
            not isinstance(route_network, ipaddress.IPv4Network)
            or route_network.prefixlen == 0
        ):
            continue
        if route.get("dev") in bridge_devices:
            continue
        if any(pool.overlaps(route_network) for pool in pools):
            raise DockerSubnetValidationError(
                "Docker address pool overlaps a host route"
            )
        if candidate.overlaps(route_network):
            raise DockerSubnetValidationError(
                "docker_db_subnet_cidr overlaps a host route"
            )


def _run_json_command(command: list[str], description: str) -> Any:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise DockerSubnetValidationError(
            f"could not inspect {description}"
        ) from exc
    if result.returncode != 0:
        raise DockerSubnetValidationError(f"could not inspect {description}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise DockerSubnetValidationError(
            f"{description} returned invalid JSON"
        ) from exc


def read_host_network_state() -> tuple[list[Any], list[Any], Any]:
    routes = _run_json_command(
        ["/usr/sbin/ip", "-j", "route", "show", "table", "all"],
        "host routes",
    )
    try:
        network_result = subprocess.run(
            [
                "/usr/bin/docker",
                "--host",
                "unix:///run/docker.sock",
                "network",
                "ls",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise DockerSubnetValidationError(
            "could not enumerate Docker networks"
        ) from exc
    if network_result.returncode != 0:
        raise DockerSubnetValidationError("could not enumerate Docker networks")

    network_ids = [
        network_id
        for network_id in network_result.stdout.splitlines()
        if network_id
    ]
    networks = (
        _run_json_command(
            [
                "/usr/bin/docker",
                "--host",
                "unix:///run/docker.sock",
                "network",
                "inspect",
                *network_ids,
            ],
            "Docker networks",
        )
        if network_ids
        else []
    )
    try:
        daemon_configuration = json.loads(
            DOCKER_DAEMON_CONFIG.read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise DockerSubnetValidationError(
            "could not read Docker daemon configuration"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DockerSubnetValidationError(
            "Docker daemon configuration is invalid"
        ) from exc
    if not isinstance(daemon_configuration, dict):
        raise DockerSubnetValidationError(
            "Docker daemon configuration is invalid"
        )
    return (
        routes,
        networks,
        daemon_configuration.get("default-address-pools"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the db Docker subnet before network creation."
    )
    parser.add_argument("--subnet", required=True)
    arguments = parser.parse_args(argv)

    try:
        routes, networks, address_pools = read_host_network_state()
        validate_subnet_state(
            arguments.subnet,
            routes,
            networks,
            address_pools,
        )
    except DockerSubnetValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print("Docker db subnet does not overlap host routes or Docker networks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
