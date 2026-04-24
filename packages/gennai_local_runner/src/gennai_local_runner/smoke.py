from __future__ import annotations

import json
import sys
import urllib.request


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: smoke.py URL JSON_PAYLOAD", file=sys.stderr)
        return 2
    url, payload = argv[0], argv[1]
    data = payload.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:  # nosec B310 - developer-supplied local URL
        body = json.loads(res.read().decode("utf-8"))
    print(body.get("outputs", body))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
