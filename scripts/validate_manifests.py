from __future__ import annotations

import json
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except Exception as exc:  # pragma: no cover
    raise SystemExit("Install jsonschema first: pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "packages" / "gennai_form_spec" / "schema" / "request-format.schema.json"
MANIFEST_DIR = ROOT / "manifests"


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    failures = 0
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            failures += 1
            print(f"[NG] {path.name}")
            for error in errors:
                loc = ".".join(str(p) for p in error.path) or "<root>"
                print(f"  - {loc}: {error.message}")
        else:
            print(f"[OK] {path.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
