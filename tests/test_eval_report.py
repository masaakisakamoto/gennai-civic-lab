from pathlib import Path

from gennai_evals.runner import build_report, write_json_report, write_markdown_report, EvalCaseRecord


def test_eval_report_writers(tmp_path: Path) -> None:
    report = build_report([
        EvalCaseRecord(file="evals/demo.yaml", app="demo", name="basic", ok=True, message="basic: ok")
    ])

    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    write_json_report(json_path, report)
    write_markdown_report(md_path, report)

    assert '"schema_version": "gennai.eval_report.v1"' in json_path.read_text(encoding="utf-8")
    assert "Gennai Eval Report" in md_path.read_text(encoding="utf-8")
    assert "✅ pass" in md_path.read_text(encoding="utf-8")
