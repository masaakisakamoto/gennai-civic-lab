from __future__ import annotations

from typing import Any
Field = dict[str, Any]

def text(title: str, desc: str = "", *, required: bool = False, min_length: int | None = None, max_length: int | None = None, default_value: str | None = None) -> Field:
    f: Field = {"type": "text", "title": title}
    if desc: f["desc"] = desc
    if required: f["required"] = True
    if min_length is not None: f["min_length"] = min_length
    if max_length is not None: f["max_length"] = max_length
    if default_value is not None: f["default_value"] = default_value
    return f

def textarea(title: str, desc: str = "", *, required: bool = False, min_length: int | None = None, max_length: int | None = None, default_value: str | None = None) -> Field:
    f = text(title, desc, required=required, min_length=min_length, max_length=max_length, default_value=default_value)
    f["type"] = "textarea"
    return f

def number(title: str, desc: str = "", *, required: bool = False, min: int | float | None = None, max: int | float | None = None, default_value: int | float | None = None) -> Field:
    f: Field = {"type": "number", "title": title}
    if desc: f["desc"] = desc
    if required: f["required"] = True
    if min is not None: f["min"] = min
    if max is not None: f["max"] = max
    if default_value is not None: f["default_value"] = default_value
    return f

def file(title: str, desc: str = "", *, required: bool = False, accept: str | None = None, multiple: bool = False, max_size: str | None = None, max_file_count: int | None = None) -> Field:
    f: Field = {"type": "file", "title": title}
    if desc: f["desc"] = desc
    if required: f["required"] = True
    if accept: f["accept"] = accept
    if multiple: f["multiple"] = True
    if max_size: f["max_size"] = max_size
    if max_file_count is not None: f["max_file_count"] = max_file_count
    return f

def _items(values: list[tuple[str, str | int | float]]) -> list[dict[str, str | int | float]]:
    return [{"title": title, "value": value} for title, value in values]

def select(title: str, items: list[tuple[str, str | int | float]], desc: str = "", *, required: bool = False, default_value: str | int | float | None = None) -> Field:
    f: Field = {"type": "select", "title": title, "items": _items(items)}
    if desc: f["desc"] = desc
    if required: f["required"] = True
    if default_value is not None: f["default_value"] = default_value
    return f

def checkbox(title: str, items: list[tuple[str, str | int | float]], desc: str = "", *, required: bool = False, default_value: str | int | float | None = None) -> Field:
    f = select(title, items, desc, required=required, default_value=default_value)
    f["type"] = "checkbox"
    return f

def radio(title: str, items: list[tuple[str, str | int | float]], desc: str = "", *, required: bool = False, default_value: str | int | float | None = None) -> Field:
    f = select(title, items, desc, required=required, default_value=default_value)
    f["type"] = "radio"
    return f

def hidden(default_value: str | int | float) -> Field:
    return {"type": "hidden", "default_value": default_value}

def manifest(**fields: Field) -> dict[str, Field]:
    validate_manifest(fields)
    return fields

def validate_manifest(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise ValueError("manifest must be a dict")
    allowed_types = {"text", "number", "textarea", "file", "select", "checkbox", "radio", "hidden"}
    for key, field in spec.items():
        if not isinstance(key, str) or not key:
            raise ValueError("manifest keys must be non-empty strings")
        if not isinstance(field, dict):
            raise ValueError(f"field {key!r} must be a dict")
        t = field.get("type")
        if t not in allowed_types:
            raise ValueError(f"field {key!r} has unsupported type {t!r}")
        if t != "hidden" and not field.get("title"):
            raise ValueError(f"field {key!r} must have title")
        if t in {"select", "checkbox", "radio"} and not isinstance(field.get("items"), list):
            raise ValueError(f"field {key!r} must have items")
