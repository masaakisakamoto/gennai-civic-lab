from __future__ import annotations

import importlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

APP_MODULES = {
    "easy_japanese_rewriter": "apps.easy_japanese_rewriter.app",
    "citizen_faq_rag": "apps.citizen_faq_rag.app",
}


@dataclass(frozen=True)
class RedTeamResult:
    ok: bool
    message: str
    risk: str


def load_handle(app_name: str):
    if app_name not in APP_MODULES:
        raise KeyError(f"unknown red-team app: {app_name}")
    return importlib.import_module(APP_MODULES[app_name]).handle


def _expectation_to_text(value: Any) -> str:
    if isinstance(value, dict) and len(value) == 1:
        key, item = next(iter(value.items()))
        return f"{key}: {item}"
    return str(value)


def _expectations(case: dict[str, Any], key: str) -> list[str]:
    return [_expectation_to_text(value) for value in case.get(key, [])]


def run_case(case: dict[str, Any]) -> RedTeamResult:
    app_name = case["app"]
    risk = str(case.get("risk", "unspecified"))
    handle = load_handle(app_name)
    result = handle(case["input"])
    out = result.get("outputs", "")

    missing = [s for s in _expectations(case, "expect_contains") if s not in out]
    forbidden = [s for s in _expectations(case, "expect_not_contains") if s in out]
    regex_missing = [p for p in _expectations(case, "expect_regex") if not re.search(p, out, re.MULTILINE)]

    errors: list[str] = []
    if missing:
        errors.append(f"missing={missing}")
    if forbidden:
        errors.append(f"forbidden={forbidden}")
    if regex_missing:
        errors.append(f"regex_missing={regex_missing}")

    name = str(case.get("name", app_name))
    if errors:
        return RedTeamResult(False, f"{name}: " + "; ".join(errors), risk)
    return RedTeamResult(True, f"{name}: ok", risk)


def run_file(path: Path) -> int:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    failures = 0
    for case in data.get("cases", []):
        result = run_case(case)
        prefix = "✅" if result.ok else "❌"
        print(f"{prefix} [{result.risk}] {result.message}")
        failures += 0 if result.ok else 1
    return failures


def main(argv: list[str] | None = None) -> int:
    if yaml is None:
        print("pyyaml is required: pip install pyyaml", file=sys.stderr)
        return 2
    argv = argv or ["evals/red_team.yaml"]

    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    for package_src in sorted((repo_root / "packages").glob("*/src")):
        sys.path.insert(0, str(package_src))

    failures = sum(run_file(Path(file)) for file in argv)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
