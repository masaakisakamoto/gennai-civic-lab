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
    "meeting_summary": "apps.meeting_summary.app",
    "citizen_faq_rag": "apps.citizen_faq_rag.app",
    "sports_promotion_advisor": "apps.sports_promotion_advisor.app",
    "policy_briefing": "apps.policy_briefing.app",
    "ordinance_checklist": "apps.ordinance_checklist.app",
}


@dataclass(frozen=True)
class EvalResult:
    ok: bool
    message: str


def load_handle(app_name: str):
    if app_name not in APP_MODULES:
        raise KeyError(f"unknown app: {app_name}")
    module = importlib.import_module(APP_MODULES[app_name])
    return module.handle


def run_case(app_name: str, case: dict[str, Any]) -> EvalResult:
    handle = load_handle(app_name)
    result = handle(case["input"])
    out = result.get("outputs", "")

    missing = [s for s in case.get("expect_contains", []) if s not in out]
    forbidden = [s for s in case.get("expect_not_contains", []) if s in out]
    regex_missing = [p for p in case.get("expect_regex", []) if not re.search(p, out, re.MULTILINE)]

    errors: list[str] = []
    if missing:
        errors.append(f"missing={missing}")
    if forbidden:
        errors.append(f"forbidden={forbidden}")
    if regex_missing:
        errors.append(f"regex_missing={regex_missing}")
    if errors:
        return EvalResult(False, f"{case['name']}: " + "; ".join(errors))
    return EvalResult(True, f"{case['name']}: ok")


def run_file(file: Path) -> int:
    data = yaml.safe_load(file.read_text(encoding="utf-8"))
    failures = 0
    for case in data.get("cases", []):
        result = run_case(data["app"], case)
        print(("✅ " if result.ok else "❌ ") + result.message)
        failures += 0 if result.ok else 1
    return failures


def main(argv: list[str]) -> int:
    if yaml is None:
        print("pyyaml is required: pip install pyyaml", file=sys.stderr)
        return 2
    if not argv:
        print("usage: runner.py evals/*.yaml", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "packages" / "gennai_app_kit" / "src"))

    failures = sum(run_file(Path(file)) for file in argv)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
