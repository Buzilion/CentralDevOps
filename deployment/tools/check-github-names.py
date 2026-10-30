#!/usr/bin/env python3
"""Check GitHub workflow references and tracked files for policy violations."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable


REQUIRED_CATALOG_KEYS = {
    "prefixes",
    "reserved_prefixes",
    "generic_names",
    "names",
    "forbidden_in",
}
REFERENCE_KINDS = {"secrets": "secret", "vars": "variable"}

DOT_REFERENCE_RE = re.compile(
    r"\b(?P<context>secrets|vars)\s*\.\s*(?P<name>[A-Za-z0-9_]+)"
)
BRACKET_REFERENCE_RE = re.compile(
    r"""\b(?P<context>secrets|vars)\s*\[\s*(?P<quote>['"])(?P<name>[^'"]*)(?P=quote)\s*\]"""
)
BRACKET_ACCESS_RE = re.compile(r"\b(?P<context>secrets|vars)\s*\[[^\]]*\]")
DYNAMIC_REFERENCE_RES = (
    re.compile(r"\btoJSON\s*\(\s*(?:secrets|vars)\s*\)", re.IGNORECASE),
    re.compile(r"\bsecrets\s*:\s*inherit\b", re.IGNORECASE),
    re.compile(r"\bsecrets\s*\.\s*inherit\b", re.IGNORECASE),
)
PRIVATE_KEY_HEADER_RE = re.compile(br"-----BEGIN [A-Z ]*PRIVATE KEY-----")


class CheckerError(Exception):
    """Raised when the checker cannot safely complete its scan."""


class CatalogError(CheckerError):
    """Raised when the name catalog is missing or invalid."""


@dataclass(frozen=True)
class Catalog:
    prefixes: tuple[str, ...]
    reserved_prefixes: tuple[str, ...]
    generic_names: frozenset[str]
    names: dict[str, dict[str, str]]
    forbidden_in: dict[str, frozenset[str]]
    name_pattern: re.Pattern[str]


@dataclass(frozen=True)
class NameReference:
    context: str
    name: str
    start: int
    end: int


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule_id: str
    message: str = ""

    def format(self) -> str:
        location = f"{self.path}:{self.line} {self.rule_id}"
        return f"{location} {self.message}" if self.message else location


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _string_list(
    value: object, key: str, *, require_values: bool = True
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CatalogError(f"{key!r} must be a list of strings")
    if require_values and not value:
        raise CatalogError(f"{key!r} must not be empty")

    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item or item != item.strip():
            raise CatalogError(f"{key!r} must contain non-empty strings")
        if item in seen:
            raise CatalogError(f"{key!r} contains a duplicate value")
        seen.add(item)
        items.append(item)
    return tuple(items)


def _validate_catalog(data: object, path: Path) -> Catalog:
    if not isinstance(data, dict):
        raise CatalogError(f"{path}: catalog must be a JSON object")

    missing = sorted(REQUIRED_CATALOG_KEYS - data.keys())
    if missing:
        raise CatalogError(
            f"{path}: catalog is missing required keys: {', '.join(missing)}"
        )

    prefixes = _string_list(data["prefixes"], "prefixes")
    for prefix in prefixes:
        if not re.fullmatch(r"[A-Z]+", prefix):
            raise CatalogError(f"{path}: invalid name prefix {prefix!r}")

    reserved_prefixes = _string_list(data["reserved_prefixes"], "reserved_prefixes")
    for prefix in reserved_prefixes:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*_", prefix):
            raise CatalogError(f"{path}: invalid reserved prefix {prefix!r}")

    generic_names = _string_list(data["generic_names"], "generic_names")
    for name in generic_names:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            raise CatalogError(f"{path}: invalid generic name {name!r}")

    prefix_pattern = "|".join(
        re.escape(prefix) for prefix in sorted(prefixes, key=len, reverse=True)
    )
    name_pattern = re.compile(
        rf"(?:{prefix_pattern})_[A-Z0-9]+(?:_[A-Z0-9]+)*\Z"
    )

    raw_names = data["names"]
    if not isinstance(raw_names, dict) or not raw_names:
        raise CatalogError(f"{path}: 'names' must be a non-empty object")

    names: dict[str, dict[str, str]] = {}
    for name, metadata in raw_names.items():
        if not isinstance(name, str) or not name:
            raise CatalogError(f"{path}: catalog names must be non-empty strings")
        if any(name.startswith(prefix) for prefix in reserved_prefixes):
            raise CatalogError(f"{path}: catalog name {name!r} uses a reserved prefix")
        if name in generic_names or not name_pattern.fullmatch(name):
            raise CatalogError(f"{path}: catalog name {name!r} has an invalid pattern")
        if not isinstance(metadata, dict):
            raise CatalogError(f"{path}: metadata for {name!r} must be an object")

        missing_metadata = {"kind", "level", "introduced_by"} - metadata.keys()
        if missing_metadata:
            fields = ", ".join(sorted(missing_metadata))
            raise CatalogError(f"{path}: metadata for {name!r} is missing {fields}")

        kind = metadata["kind"]
        level = metadata["level"]
        introduced_by = metadata["introduced_by"]
        if not isinstance(kind, str) or kind not in {"secret", "variable"}:
            raise CatalogError(f"{path}: invalid kind for {name!r}")
        if not isinstance(level, str) or not level.strip():
            raise CatalogError(f"{path}: invalid level for {name!r}")
        if not isinstance(introduced_by, str) or not introduced_by.strip():
            raise CatalogError(f"{path}: invalid introduced_by for {name!r}")
        names[name] = {
            "kind": kind,
            "level": level,
            "introduced_by": introduced_by,
        }

    raw_forbidden = data["forbidden_in"]
    if not isinstance(raw_forbidden, dict):
        raise CatalogError(f"{path}: 'forbidden_in' must be an object")

    forbidden_in: dict[str, frozenset[str]] = {}
    for workflow, values in raw_forbidden.items():
        if not isinstance(workflow, str) or not workflow:
            raise CatalogError(f"{path}: forbidden workflow paths must be strings")
        workflow_path = PurePosixPath(workflow)
        if (
            workflow_path.is_absolute()
            or ".." in workflow_path.parts
            or not workflow.startswith(".github/")
        ):
            raise CatalogError(f"{path}: invalid forbidden workflow path {workflow!r}")

        forbidden_names = _string_list(
            values, f"forbidden_in[{workflow!r}]", require_values=False
        )
        unknown_names = sorted(set(forbidden_names) - names.keys())
        if unknown_names:
            raise CatalogError(
                f"{path}: forbidden names missing from catalog: "
                f"{', '.join(unknown_names)}"
            )
        forbidden_in[workflow] = frozenset(forbidden_names)

    return Catalog(
        prefixes=prefixes,
        reserved_prefixes=reserved_prefixes,
        generic_names=frozenset(generic_names),
        names=names,
        forbidden_in=forbidden_in,
        name_pattern=name_pattern,
    )


def load_catalog(path: Path) -> Catalog:
    try:
        with path.open("r", encoding="utf-8") as catalog_file:
            data = json.load(catalog_file, object_pairs_hook=_unique_json_object)
    except CatalogError as exc:
        raise CatalogError(f"{path}: {exc}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        detail = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
        raise CatalogError(f"cannot read catalog {path}: {detail}") from exc
    return _validate_catalog(data, path)


def _is_reserved(reference: NameReference, catalog: Catalog) -> bool:
    return any(
        reference.name.startswith(prefix) for prefix in catalog.reserved_prefixes
    )


def _is_generic(reference: NameReference, catalog: Catalog) -> bool:
    return reference.name in catalog.generic_names


def _has_bad_pattern(reference: NameReference, catalog: Catalog) -> bool:
    return catalog.name_pattern.fullmatch(reference.name) is None


def _is_uncataloged_or_wrong_kind(reference: NameReference, catalog: Catalog) -> bool:
    metadata = catalog.names.get(reference.name)
    return (
        metadata is None
        or metadata["kind"] != REFERENCE_KINDS[reference.context]
    )


NAME_RULES: tuple[
    tuple[str, str, Callable[[NameReference, Catalog], bool]], ...
] = (
    ("N02", "uses a reserved prefix", _is_reserved),
    ("N03", "is a generic name", _is_generic),
    ("N01", "does not match the required name pattern", _has_bad_pattern),
    ("N04", "is not cataloged with the referenced kind", _is_uncataloged_or_wrong_kind),
)


def _dynamic_spans(line: str) -> list[tuple[int, int]]:
    spans = [
        (match.start(), match.end())
        for pattern in DYNAMIC_REFERENCE_RES
        for match in pattern.finditer(line)
    ]

    static_brackets = {
        (match.start(), match.end()) for match in BRACKET_REFERENCE_RE.finditer(line)
    }
    spans.extend(
        (match.start(), match.end())
        for match in BRACKET_ACCESS_RE.finditer(line)
        if (match.start(), match.end()) not in static_brackets
    )

    merged: list[tuple[int, int]] = []
    for start, end in sorted(set(spans)):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _references(line: str) -> list[NameReference]:
    references = [
        NameReference(
            context=match.group("context"),
            name=match.group("name"),
            start=match.start(),
            end=match.end(),
        )
        for pattern in (DOT_REFERENCE_RE, BRACKET_REFERENCE_RE)
        for match in pattern.finditer(line)
    ]
    return sorted(references, key=lambda reference: (reference.start, reference.end))


def _overlaps(reference: NameReference, spans: list[tuple[int, int]]) -> bool:
    return any(
        start < reference.end and reference.start < end for start, end in spans
    )


def _check_reference(
    reference: NameReference,
    workflow: str,
    line_number: int,
    catalog: Catalog,
) -> list[Violation]:
    violations: list[Violation] = []

    if not (reference.context == "secrets" and reference.name == "GITHUB_TOKEN"):
        for rule_id, explanation, predicate in NAME_RULES:
            if predicate(reference, catalog):
                if rule_id == "N04":
                    expected_kind = REFERENCE_KINDS[reference.context]
                    message = (
                        f"{reference.context}.{reference.name} is not cataloged "
                        f"as a {expected_kind}"
                    )
                else:
                    message = f"{reference.name} {explanation}"
                violations.append(
                    Violation(workflow, line_number, rule_id, message)
                )
                break

    if reference.name in catalog.forbidden_in.get(workflow, frozenset()):
        violations.append(
            Violation(
                workflow,
                line_number,
                "F01",
                f"{reference.name} is forbidden in this workflow",
            )
        )
    return violations


def _read_text(path: Path) -> str | None:
    try:
        contents = path.read_bytes()
    except OSError as exc:
        raise CheckerError(f"cannot read {path}") from exc
    if b"\0" in contents:
        return None
    return contents.decode("utf-8-sig", errors="replace")


def _raise_walk_error(error: OSError) -> None:
    path = error.filename or "<unknown>"
    raise CheckerError(f"cannot scan directory {path}") from error


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, filenames in os.walk(
        root, onerror=_raise_walk_error, followlinks=False
    ):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory.lower() != ".git"
            and not (current_path / directory).is_symlink()
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if not path.is_symlink():
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def scan_workflows(root: Path, catalog: Catalog) -> list[Violation]:
    github_directory = root / ".github"
    try:
        mode = github_directory.lstat().st_mode
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise CheckerError(f"cannot inspect {github_directory}") from exc
    if not stat.S_ISDIR(mode):
        raise CheckerError(f"{github_directory} is not a directory")

    violations: list[Violation] = []
    workflow_paths = sorted(
        path
        for path in _walk_files(github_directory)
        if path.suffix.lower() in {".yml", ".yaml"}
    )
    for path in workflow_paths:
        text = _read_text(path)
        if text is None:
            continue
        relative_path = path.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            dynamic_spans = _dynamic_spans(line)
            for _start, _end in dynamic_spans:
                violations.append(
                    Violation(
                        relative_path,
                        line_number,
                        "N05",
                        "dynamic secret or variable access is not allowed",
                    )
                )

            for reference in _references(line):
                if _overlaps(reference, dynamic_spans):
                    continue
                violations.extend(
                    _check_reference(reference, relative_path, line_number, catalog)
                )
    return violations


def _fallback_files(root: Path) -> list[Path]:
    return _walk_files(root)


def _repository_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return _fallback_files(root)

    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").lower()
        if "not a git repository" in error:
            return _fallback_files(root)
        raise CheckerError("git ls-files failed; cannot determine tracked files")

    files: list[Path] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = Path(os.fsdecode(raw_path))
        if ".git" in relative_path.parts:
            continue
        path = root / relative_path
        if not path.is_symlink() and path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def scan_private_key_material(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in _repository_files(root):
        try:
            contents = path.read_bytes()
        except FileNotFoundError:
            continue
        except OSError as exc:
            relative_path = path.relative_to(root).as_posix()
            raise CheckerError(f"cannot read tracked file {relative_path}") from exc

        if b"\0" in contents:
            continue
        relative_path = path.relative_to(root).as_posix()
        for line_number, line in enumerate(contents.splitlines(), start=1):
            if PRIVATE_KEY_HEADER_RE.search(line):
                violations.append(Violation(relative_path, line_number, "K01"))
    return violations


def check_repository(root: Path, catalog: Catalog) -> list[Violation]:
    violations = scan_workflows(root, catalog)
    violations.extend(scan_private_key_material(root))
    return sorted(
        violations,
        key=lambda violation: (
            violation.path,
            violation.line,
            violation.rule_id,
            violation.message,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check workflow name references and tracked files for private keys."
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="repository root (defaults to the root containing this checker)",
    )
    arguments = parser.parse_args(argv)

    try:
        root = (arguments.root or Path(__file__).resolve().parents[2]).expanduser().resolve()
        if not root.is_dir():
            raise CheckerError(f"repository root is not a directory: {root}")
        catalog = load_catalog(root / "deployment" / "tools" / "github-names.json")
        violations = check_repository(root, catalog)
    except CheckerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for violation in violations:
        print(violation.format())
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
