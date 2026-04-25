from __future__ import annotations

from pathlib import Path


def test_deployment_blueprints_exist():
    root = Path(__file__).resolve().parents[1]
    required = [
        root / "blueprints" / "docker-compose" / "README.md",
        root / "blueprints" / "docker-compose" / "docker-compose.full.yml",
        root / "blueprints" / "aws" / "README.md",
        root / "blueprints" / "azure" / "README.md",
        root / "blueprints" / "local" / "README.md",
    ]
    for path in required:
        assert path.exists(), path


def test_blueprints_document_security_baseline():
    root = Path(__file__).resolve().parents[1]
    text = (root / "blueprints" / "docker-compose" / "README.md").read_text(encoding="utf-8")
    assert "localhost" in text
    assert "PII" in text
    assert "production" in text
