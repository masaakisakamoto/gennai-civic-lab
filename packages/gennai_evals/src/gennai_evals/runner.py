from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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


@dataclass(frozen=True)
class EvalCaseRecord:
    file: str
    app: str
    name: str
    ok: bool
    message: str


@dataclass(frozen=True)
class EvalRunReport:
    schema_version: str
    generated_at: str
    total: int
    passed: int
    failed: int
    cases: list[EvalCaseRecord] = field(default_factory=list)


def load_handle(app_name: str):
    if app_name not in APP_MODULES:
        raise KeyError(f"unknown app: {app_name}")
    module = importlib.import_module(APP_MODULES[app_name])
    return module.handle


def _expectation_to_text(value: Any) -> str:
    if isinstance(value, dict) and len(value) == 1:
        key, item = next(iter(value.items()))
        return f"{key}: {item}"
    return str(value)


def _expectations(case: dict[str, Any], key: str) -> list[str]:
    return [_expectation_to_text(value) for value in case.get(key, [])]


def run_case(app_name: str, case: dict[str, Any]) -> EvalResult:
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
    if errors:
        return EvalResult(False, f"{case['name']}: " + "; ".join(errors))
    return EvalResult(True, f"{case['name']}: ok")


def run_file_records(file: Path) -> list[EvalCaseRecord]:
    data = yaml.safe_load(file.read_text(encoding="utf-8"))
    app_name = data["app"]
    records: list[EvalCaseRecord] = []
    for case in data.get("cases", []):
        result = run_case(app_name, case)
        records.append(
            EvalCaseRecord(
                file=str(file),
                app=app_name,
                name=str(case["name"]),
                ok=result.ok,
                message=result.message,
            )
        )
    return records


def run_file(file: Path) -> int:
    failures = 0
    for record in run_file_records(file):
        print(("✅ " if record.ok else "❌ ") + record.message)
        failures += 0 if record.ok else 1
    return failures


def build_report(records: list[EvalCaseRecord]) -> EvalRunReport:
    passed = sum(1 for record in records if record.ok)
    failed = len(records) - passed
    return EvalRunReport(
        schema_version="gennai.eval_report.v1",
        generated_at=datetime.now(timezone.utc).isoformat(),
        total=len(records),
        passed=passed,
        failed=failed,
        cases=records,
    )


def write_json_report(path: Path, report: EvalRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_report(path: Path, report: EvalRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gennai Eval Report",
        "",
        f"- generated_at: `{report.generated_at}`",
        f"- total: **{report.total}**",
        f"- passed: **{report.passed}**",
        f"- failed: **{report.failed}**",
        "",
        "## Cases",
        "",
        "| status | app | case | file |",
        "|---|---|---|---|",
    ]
    for record in report.cases:
        status = "✅ pass" if record.ok else "❌ fail"
        lines.append(f"| {status} | `{record.app}` | {record.name} | `{record.file}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run YAML eval cases for Gennai-compatible apps")
    parser.add_argument("files", nargs="+", help="eval YAML files")
    parser.add_argument("--json-report", help="write a machine-readable JSON report")
    parser.add_argument("--markdown-report", help="write a Markdown summary report")
    return parser


def main(argv: list[str]) -> int:
    if yaml is None:
        print("pyyaml is required: pip install pyyaml", file=sys.stderr)
        return 2

    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "packages" / "gennai_app_kit" / "src"))

    records: list[EvalCaseRecord] = []
    for file_arg in args.files:
        file = Path(file_arg)
        file_records = run_file_records(file)
        for record in file_records:
            print(("✅ " if record.ok else "❌ ") + record.message)
        records.extend(file_records)

    report = build_report(records)
    if args.json_report:
        write_json_report(Path(args.json_report), report)
    if args.markdown_report:
        write_markdown_report(Path(args.markdown_report), report)

    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
