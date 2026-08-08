"""Run the WAV acceptance gate against the latest campaign run.

Usage:
    uv run python scripts/check_acceptance.py                  # latest campaign
    uv run python scripts/check_acceptance.py runs/<run_id>    # explicit run
"""

from __future__ import annotations

import sys
from pathlib import Path

from veval.analyze.acceptance import run
from veval.store.run_store import default_run_store


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        run_dir = Path(argv[1])
    else:
        runs = default_run_store().list_runs("campaign")
        if not runs:
            print("no campaign runs under ./runs/")
            return 1
        run_dir = runs[0]
        print(f"latest campaign: {run_dir.name}")

    payload = run(run_dir)
    print(
        f"gate_ok: {payload['gate_ok']} | "
        f"passed {payload['passed']} / {payload['total_files']} "
        f"(failed {payload['failed']})"
    )
    for f in payload["files"]:
        if not f["passed"]:
            print(f"  FAIL {f['provider']}/{f['use_case']}/{f['item_id']}: {f['issues']}")
    return 0 if payload["gate_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
