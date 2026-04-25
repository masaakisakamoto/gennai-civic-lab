from pathlib import Path


def test_launch_assets_exist_and_reference_v07():
    files = [
        Path("docs/release-and-launch.md"),
        Path("launch/social/x-thread-v0.7.md"),
        Path("launch/social/instagram-carousel-v0.7.md"),
        Path("launch/social/launch-calendar.md"),
        Path("docs/assets/release-card-v0.7.svg"),
    ]
    for path in files:
        assert path.exists(), path
        assert "v0.7" in path.read_text(encoding="utf-8")


def test_release_readiness_script_smoke(tmp_path):
    import subprocess
    import sys

    output = tmp_path / "release-readiness.md"
    result = subprocess.run(
        [sys.executable, "scripts/release_readiness.py", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "release_ready" in result.stdout
    assert output.exists()
    assert "Release Readiness" in output.read_text(encoding="utf-8")
