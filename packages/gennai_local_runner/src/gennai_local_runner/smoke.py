from __future__ import annotations

import json
import sys

from .client import EndpointError, call_gennai_endpoint


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: smoke.py URL JSON_PAYLOAD", file=sys.stderr)
        return 2
    url, payload_json = argv[0], argv[1]
    try:
        payload = json.loads(payload_json)
        body = call_gennai_endpoint(url, payload)
    except (json.JSONDecodeError, EndpointError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(body["outputs"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
