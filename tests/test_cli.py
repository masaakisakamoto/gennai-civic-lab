from pathlib import Path

from gennai_cli.create_app import sanitize_app_name, scaffold_app


def test_sanitize_app_name() -> None:
    assert sanitize_app_name("Document-Risk Checker") == "document_risk_checker"
    assert sanitize_app_name("123-demo") == "app_123_demo"


def test_scaffold_app_creates_expected_files(tmp_path: Path) -> None:
    result = scaffold_app("demo-app", root=tmp_path)
    assert result.app_name == "demo_app"
    assert (tmp_path / "apps" / "demo_app" / "app.py").exists()
    assert (tmp_path / "manifests" / "demo_app.gennai.json").exists()
    assert (tmp_path / "evals" / "demo_app.yaml").exists()
    assert (tmp_path / "tests" / "test_demo_app.py").exists()
