import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[1]


def test_all_manifests_match_schema():
    schema = json.loads(
        (ROOT / "packages/gennai_form_spec/schema/request-format.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = jsonschema.Draft202012Validator(schema)
    for path in sorted((ROOT / "manifests").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = list(validator.iter_errors(data))
        assert errors == [], f"{path.name}: {[e.message for e in errors]}"
