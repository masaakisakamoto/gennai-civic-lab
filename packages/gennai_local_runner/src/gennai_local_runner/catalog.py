from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PORTS = {
    "easy_japanese_rewriter": 8000,
    "citizen_faq_rag": 8001,
    "meeting_summary": 8002,
    "sports_promotion_advisor": 8003,
    "policy_briefing": 8004,
    "ordinance_checklist": 8005,
}


@dataclass(frozen=True)
class AppCatalogItem:
    app_id: str
    title: str
    manifest_path: str
    endpoint: str
    request_format: dict[str, Any]


def repo_root_from(start: Path | None = None) -> Path:
    """Find the repository root without depending on the current working directory."""

    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "manifests").is_dir() and (candidate / "apps").is_dir():
            return candidate
    raise FileNotFoundError("could not find repository root containing manifests/ and apps/")


def app_id_from_manifest(path: Path) -> str:
    name = path.name
    return name.removesuffix(".gennai.json")


def humanize_app_id(app_id: str) -> str:
    return re.sub(r"\s+", " ", app_id.replace("_", " ")).strip().title()


def default_endpoint(app_id: str, *, host: str = "127.0.0.1") -> str:
    port = DEFAULT_PORTS.get(app_id, 8999)
    return f"http://{host}:{port}/"


def build_default_inputs(request_format: dict[str, Any]) -> dict[str, Any]:
    """Create a demo payload from a manifest.

    This is intentionally conservative: text fields get safe examples, file inputs are skipped,
    and hidden/default values are preserved. The goal is a useful local smoke payload, not
    production form validation.
    """

    inputs: dict[str, Any] = {}
    for key, field in request_format.items():
        if not isinstance(field, dict):
            continue
        field_type = field.get("type")
        if "default_value" in field:
            inputs[key] = field["default_value"]
            continue
        if field_type in {"select", "radio", "checkbox"}:
            items = field.get("items") or []
            if items and isinstance(items, list):
                first = items[0]
                value = first.get("value") if isinstance(first, dict) else first
                inputs[key] = value
            else:
                inputs[key] = ""
        elif field_type == "number":
            inputs[key] = field.get("min", 1)
        elif field_type == "textarea":
            if key == "question":
                inputs[key] = "子ども医療費助成の申請に必要なものを教えてください"
            elif key == "text":
                inputs[key] = "本制度の利用に際しては、所定の申請書類を提出してください。"
            else:
                inputs[key] = ""
        elif field_type == "text":
            inputs[key] = ""
        elif field_type == "hidden":
            inputs[key] = field.get("default_value", "")
        elif field_type == "file":
            # Gennai file inputs are represented in inputs.files. The browser runner keeps
            # file upload out of scope for v0.4 and encourages text/Markdown pasting first.
            continue
    return inputs


def load_catalog(repo_root: Path | None = None) -> list[AppCatalogItem]:
    root = repo_root or repo_root_from()
    manifest_dir = root / "manifests"
    items: list[AppCatalogItem] = []
    for path in sorted(manifest_dir.glob("*.gennai.json")):
        app_id = app_id_from_manifest(path)
        request_format = json.loads(path.read_text(encoding="utf-8"))
        items.append(
            AppCatalogItem(
                app_id=app_id,
                title=humanize_app_id(app_id),
                manifest_path=str(path.relative_to(root)),
                endpoint=default_endpoint(app_id),
                request_format=request_format,
            )
        )
    return items
