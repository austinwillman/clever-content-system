#!/usr/bin/env python3
"""Minimal JSON Schema subset validator built on the Python standard library.

Supports the keywords used by this repository's contracts: type, const, enum,
required, properties, additionalProperties, items, minItems, maxItems,
minLength, maxLength, pattern, minimum, and local "$ref" into "$defs".

It is deliberately small. It is not a general-purpose JSON Schema engine and it
fails loudly when it meets a keyword it does not implement.
"""

from __future__ import annotations

import re
from typing import Any

SUPPORTED_KEYWORDS = frozenset(
    (
        "$schema",
        "$id",
        "$defs",
        "$ref",
        "title",
        "description",
        "type",
        "const",
        "enum",
        "required",
        "properties",
        "additionalProperties",
        "items",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
    )
)

_TYPES: dict[str, Any] = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "boolean": bool,
}


class UnsupportedSchema(Exception):
    """Raised when the schema uses a keyword this validator does not implement."""


def _resolve(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if ref is None:
        return schema
    if not ref.startswith("#/$defs/"):
        raise UnsupportedSchema(f"unsupported $ref target: {ref}")
    name = ref[len("#/$defs/") :]
    target = root.get("$defs", {}).get(name)
    if target is None:
        raise UnsupportedSchema(f"missing $defs entry: {name}")
    merged = {key: value for key, value in schema.items() if key != "$ref"}
    resolved = dict(target)
    resolved.update(merged)
    return resolved


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    python_type = _TYPES.get(expected)
    if python_type is None:
        raise UnsupportedSchema(f"unsupported type: {expected}")
    if python_type is str and isinstance(value, bool):
        return False
    return isinstance(value, python_type)


def validate(instance: Any, schema: dict[str, Any], root: dict[str, Any] | None = None,
             path: str = "$") -> list[str]:
    """Return a list of human-readable validation errors. Empty means valid."""

    root = schema if root is None else root
    schema = _resolve(schema, root)

    unsupported = set(schema) - SUPPORTED_KEYWORDS
    if unsupported:
        raise UnsupportedSchema(f"unsupported keywords at {path}: {sorted(unsupported)}")

    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None and not _type_matches(instance, expected_type):
        return [f"{path}: expected {expected_type}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than {schema['maxLength']}")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{path}: does not match {pattern}")

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: unexpected property '{key}'")
        for key, subschema in properties.items():
            if key in instance:
                errors.extend(
                    validate(instance[key], subschema, root, f"{path}.{key}")
                )

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for position, item in enumerate(instance):
                errors.extend(
                    validate(item, item_schema, root, f"{path}[{position}]")
                )

    return errors
