"""Executable JSON Schema contracts for the 6-node orchestration pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_DIR = Path(__file__).resolve().parent
CONTRACT_EDGE_NAMES = (
    "receiver_to_planner",
    "planner_to_router",
    "router_to_executor",
    "executor_to_synthesizer",
    "synthesizer_to_verifier",
)
SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True)
class Contract:
    edge: str
    version: str
    path: Path
    schema: dict[str, Any]


def list_contracts() -> list[Contract]:
    contracts: list[Contract] = []
    for edge in CONTRACT_EDGE_NAMES:
        schema = load_contract_schema(edge)
        version = str(schema.get("x-contract-version", ""))
        contracts.append(Contract(edge=edge, version=version, path=_schema_path(edge), schema=schema))
    return contracts


def load_contract_schema(edge: str) -> dict[str, Any]:
    if edge not in CONTRACT_EDGE_NAMES:
        raise KeyError(f"Unknown pipeline contract edge: {edge}")
    return json.loads(_schema_path(edge).read_text())


def validate_edge_payload(edge: str, payload: dict[str, Any]) -> list[str]:
    schema = load_contract_schema(edge)
    return validate_payload(schema, payload)


def validate_payload(schema: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return _fallback_validate(schema, payload, "$")

    validator = Draft202012Validator(schema)
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    ]


def validate_contract_set() -> dict[str, Any]:
    contracts = list_contracts()
    errors: list[str] = []
    seen_ids: set[str] = set()
    versions: dict[str, str] = {}

    for contract in contracts:
        schema_id = str(contract.schema.get("$id", ""))
        if not schema_id:
            errors.append(f"{contract.edge}: missing $id")
        elif schema_id in seen_ids:
            errors.append(f"{contract.edge}: duplicate $id {schema_id}")
        seen_ids.add(schema_id)

        if not SEMVER_PATTERN.match(contract.version):
            errors.append(f"{contract.edge}: invalid SemVer version {contract.version!r}")
        versions[contract.edge] = contract.version

        required = contract.schema.get("required", [])
        if not required:
            errors.append(f"{contract.edge}: schema must declare required fields")

    return {
        "ok": not errors,
        "errors": errors,
        "contracts": [
            {
                "edge": contract.edge,
                "version": contract.version,
                "schema": str(contract.path.relative_to(CONTRACT_DIR.parents[2])),
            }
            for contract in contracts
        ],
        "versions": versions,
    }


def generate_contract_markdown() -> str:
    contracts = list_contracts()
    lines = [
        "# 6-Node Pipeline Contracts",
        "",
        "These JSON Schema contracts define the payload expected on each LangGraph edge.",
        "",
        "| Edge | Version | Required Fields | Schema |",
        "| --- | --- | --- | --- |",
    ]
    for contract in contracts:
        required = ", ".join(f"`{field}`" for field in contract.schema.get("required", []))
        lines.append(
            f"| `{contract.edge}` | `{contract.version}` | {required} | "
            f"`{contract.path.name}` |"
        )

    for contract in contracts:
        title = contract.schema.get("title", contract.edge)
        description = str(contract.schema.get("description", "")).strip()
        if description:
            lines.extend(["", f"## {title}", "", description, ""])
    return "\n".join(lines).rstrip() + "\n"


def current_versions() -> dict[str, str]:
    return {contract.edge: contract.version for contract in list_contracts()}


def detect_major_version_bumps(
    previous: dict[str, str],
    current: dict[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    current = current or current_versions()
    bumps: dict[str, dict[str, str]] = {}
    for edge, current_version in current.items():
        previous_version = previous.get(edge)
        if not previous_version:
            continue
        previous_major = _major(previous_version)
        current_major = _major(current_version)
        if current_major > previous_major:
            bumps[edge] = {"previous": previous_version, "current": current_version}
    return bumps


def _schema_path(edge: str) -> Path:
    return CONTRACT_DIR / f"{edge}.schema.json"


def _major(version: str) -> int:
    match = SEMVER_PATTERN.match(version)
    if not match:
        raise ValueError(f"Invalid SemVer version: {version}")
    return int(match.group(1))


def _fallback_validate(schema: dict[str, Any], value: Any, path: str) -> list[str]:
    errors: list[str] = []

    if "oneOf" in schema:
        branch_results = [_fallback_validate(branch, value, path) for branch in schema["oneOf"]]
        if not any(not branch_errors for branch_errors in branch_results):
            errors.append(f"{path}: does not match any oneOf branch")
        return errors

    if "anyOf" in schema:
        branch_results = [_fallback_validate(branch, value, path) for branch in schema["anyOf"]]
        if not any(not branch_errors for branch_errors in branch_results):
            errors.append(f"{path}: does not match any anyOf branch")
        return errors

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
        return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: missing required property")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                errors.extend(_fallback_validate(child_schema, value[key], f"{path}.{key}"))

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(_fallback_validate(schema["items"], item, f"{path}[{index}]"))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, str) and "minLength" in schema and len(value) < schema["minLength"]:
        errors.append(f"{path}: string is shorter than {schema['minLength']}")

    if isinstance(value, list) and "minItems" in schema and len(value) < schema["minItems"]:
        errors.append(f"{path}: array has fewer than {schema['minItems']} items")

    return errors


def _matches_type(value: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(value, item) for item in expected_type)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True
