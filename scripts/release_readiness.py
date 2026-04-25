from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

REQUIRED_PATHS = [
    "README.md",
    "CHANGELOG.md",
    "Makefile",
    "Dockerfile",
    "apps/citizen_faq_rag/indexing.py",
    "packages/gennai_observability/src/gennai_observability/__init__.py",
    "docs/release-and-launch.md",
    "launch/social/x-thread-v0.7.md",
    "launch/social/instagram-carousel-v0.7.md",
    "launch/social/launch-calendar.md",
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReleaseReadinessReport:
    schema_version: str
    release: str
    passed: int
    failed: int
    checks: list[CheckResult]

    @property
    def release_ready(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["release_ready"] = self.release_ready
        return data


def _git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *cmd], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def build_report(release: str = "v0.7") -> ReleaseReadinessReport:
    checks: list[CheckResult] = []
    for item in REQUIRED_PATHS:
        checks.append(CheckResult(f"required:{item}", Path(item).exists(), item))

    dockerfile = Path("Dockerfile").read_text(encoding="utf-8") if Path("Dockerfile").exists() else ""
    checks.append(CheckResult("docker:observability-installed", "packages/gennai_observability" in dockerfile, "Dockerfile installs observability package"))

    readme = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""
    checks.append(CheckResult("readme:v0.7", "v0.7" in readme, "README mentions v0.7"))
    checks.append(CheckResult("readme:launch-ready", "Launch-ready" in readme or "launch-ready" in readme or "Launch readiness" in readme, "README explains launch readiness"))

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8") if Path("CHANGELOG.md").exists() else ""
    checks.append(CheckResult("changelog:v0.7", "v0.7" in changelog, "CHANGELOG includes v0.7"))

    status = _git(["status", "--porcelain"])
    checks.append(CheckResult("git:working-tree-visible", True, "working tree has changes" if status else "working tree clean"))

    passed = sum(1 for check in checks if check.passed)
    failed = len(checks) - passed
    return ReleaseReadinessReport("gennai.release_readiness.v1", release, passed, failed, checks)


def write_markdown(path: Path, report: ReleaseReadinessReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Release Readiness",
        "",
        f"- release: `{report.release}`",
        f"- release_ready: **{str(report.release_ready).lower()}**",
        f"- passed: **{report.passed}**",
        f"- failed: **{report.failed}**",
        "",
        "| check | result | detail |",
        "|---|---:|---|",
    ]
    for check in report.checks:
        lines.append(f"| `{check.name}` | {'✅' if check.passed else '❌'} | {check.detail} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a lightweight release-readiness report")
    parser.add_argument("--release", default="v0.7")
    parser.add_argument("--output", default="reports/release-readiness.md")
    parser.add_argument("--json-output", default="reports/release-readiness.json")
    args = parser.parse_args(argv)

    report = build_report(args.release)
    write_markdown(Path(args.output), report)
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"release_ready": report.release_ready, "passed": report.passed, "failed": report.failed}, ensure_ascii=False))
    return 0 if report.release_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
