from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "gennai_observability" / "src"))

from gennai_observability.ops_report import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
