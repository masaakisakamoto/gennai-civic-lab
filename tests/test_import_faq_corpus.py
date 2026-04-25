import csv
import json
import subprocess
import sys
from pathlib import Path

from scripts.import_faq_corpus import render_markdown


def test_render_markdown_from_rows() -> None:
    markdown = render_markdown(
        [
            {
                "id": "FAQ-101",
                "title": "犬の登録",
                "department": "環境衛生課",
                "required_items": "申請書;手数料",
                "flow": "窓口へ行く;手数料を払う",
                "notes": "最新情報を確認してください。",
            }
        ],
        title="Test FAQ",
    )

    assert "# Test FAQ" in markdown
    assert "## FAQ-101 犬の登録" in markdown
    assert "- 申請書" in markdown
    assert "注意: 最新情報を確認してください。" in markdown


def test_import_faq_corpus_cli_csv(tmp_path: Path) -> None:
    source = tmp_path / "faq.csv"
    output = tmp_path / "faq.md"
    with source.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "department", "body"])
        writer.writeheader()
        writer.writerow({"id": "FAQ-001", "title": "住民票", "department": "市民課", "body": "本人確認書類が必要です。"})

    result = subprocess.run(
        [
            sys.executable,
            "scripts/import_faq_corpus.py",
            "--input",
            str(source),
            "--output",
            str(output),
            "--title",
            "Imported",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "wrote 1 FAQ items" in result.stdout
    assert "## FAQ-001 住民票" in output.read_text(encoding="utf-8")
