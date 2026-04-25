from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from gennai_red_team_lite.runner import run_file


def test_red_team_file_passes() -> None:
    assert run_file(ROOT / "evals/red_team.yaml") == 0
