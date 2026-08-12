"""Latency re-measure with concurrent ping baseline (Wave 4b, item 23).

The published T5/T7 finding — "OpenAI latency variable, ElevenLabs
stable" — was measured from a residential ISP with no concurrent
network baseline. A hostile reviewer could argue the observed
per-vendor latency spread was actually ISP jitter with a Poisson-
timing correlation to the OpenAI session.

This script runs the latency campaign with a **concurrent ping baseline**
so the vendor observation can be decontextualized from the network
conditions in the same window.

Design:
    - Start a background daemon thread that pings 1.1.1.1
      (Cloudflare) every 500 ms and appends `{ts_utc, rtt_ms}` rows
      to a JSONL log at `runs/ping-baseline-<start_ts>.jsonl`.
    - Run the latency generation for the specified vendor(s) in the
      foreground. `veval generate --mode latency` runs 50 serial
      TTFA trials.
    - Ping baseline shuts down cleanly when the vendor runs complete.

Post-analysis (separate script or notebook) can:
    - Bracket each vendor TTFA measurement with the concurrent ping
      RTT distribution
    - Compute the per-trial excess over baseline (TTFA - baseline RTT)
    - Compare per-vendor excess variance to raw TTFA variance —
      if the excess is stable but raw TTFA is variable, the ISP was
      the driver

Usage:
    uv run python scripts/latency_with_ping.py [--vendors openai,elevenlabs]

Cost: same as `veval generate --mode latency` (~$0.02 per vendor).
Wall clock: ~5 min per vendor.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows-friendly: use `ping -n 1 -w 1000 1.1.1.1` per iteration.
# We call it in a loop rather than `ping -t` so we can parse RTT
# per-iteration and shut down cleanly.

RUNS_DIR = Path("runs")
STOP = threading.Event()


def _parse_ping_rtt_ms(output: str) -> float | None:
    """Extract RTT ms from a single Windows `ping -n 1` output."""
    # Windows output line: "Reply from 1.1.1.1: bytes=32 time=8ms TTL=57"
    for line in output.splitlines():
        line = line.strip()
        if "time=" in line and "TTL" in line:
            try:
                token = line.split("time=", 1)[1].split(" ")[0]
                if token.endswith("ms"):
                    token = token[:-2]
                return float(token)
            except (ValueError, IndexError):
                continue
        if "time<" in line and "TTL" in line:
            # "time<1ms" case — treat as ~0.5 ms
            return 0.5
    return None


def _ping_loop(log_path: Path, interval_s: float = 0.5) -> None:
    """Ping 1.1.1.1 every `interval_s` and append JSONL rows to log_path."""
    with log_path.open("w", encoding="utf-8") as fh:
        while not STOP.is_set():
            t_start = time.perf_counter()
            ts_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            try:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", "1.1.1.1"],
                    capture_output=True, text=True, timeout=2,
                )
                rtt_ms = _parse_ping_rtt_ms(result.stdout) if result.returncode == 0 else None
                status = "ok" if rtt_ms is not None else "timeout_or_parse_error"
            except (subprocess.TimeoutExpired, Exception) as e:
                rtt_ms = None
                status = f"error: {type(e).__name__}"

            row = {"ts_utc": ts_utc, "rtt_ms": rtt_ms, "status": status,
                    "target": "1.1.1.1"}
            fh.write(json.dumps(row) + "\n")
            fh.flush()

            # Sleep the remainder of the interval
            elapsed = time.perf_counter() - t_start
            remaining = interval_s - elapsed
            if remaining > 0:
                STOP.wait(timeout=remaining)


def _run_latency_for_vendor(vendor: str) -> str:
    """Run `veval generate --mode latency --provider <vendor>` and return the run_id."""
    print(f"\n=== Running latency for {vendor} ===", flush=True)
    result = subprocess.run(
        ["uv", "run", "veval", "generate", "--mode", "latency",
         "--provider", vendor, "--no-cache", "--spend-cap", "0.10"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    # Extract run_id from output — line contains "run_id" and "latency-"
    run_id = None
    for line in (result.stdout or "").splitlines():
        if "latency-" in line and "run_id" in line:
            token = [tok for tok in line.split() if tok.startswith("latency-")]
            if token:
                run_id = token[0]
                break
    if run_id is None:
        # Fallback: newest latency-* run
        latency_runs = sorted(RUNS_DIR.glob("latency-*"), key=lambda p: p.stat().st_mtime)
        if latency_runs:
            run_id = latency_runs[-1].name
    print(f"[{vendor}] run_id = {run_id}", flush=True)
    if result.returncode != 0:
        print(f"[{vendor}] returncode={result.returncode}", flush=True)
        print(f"[{vendor}] stderr: {(result.stderr or '')[:500]}", flush=True)
    return run_id or "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vendors", default="openai,elevenlabs",
        help="Comma-separated vendor list (default: openai,elevenlabs)",
    )
    args = parser.parse_args()
    vendors = [v.strip() for v in args.vendors.split(",") if v.strip()]

    # Start ping logger
    ts_start = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ping_log = RUNS_DIR / f"ping-baseline-{ts_start}.jsonl"
    RUNS_DIR.mkdir(exist_ok=True)
    print(f"Ping baseline log: {ping_log}", flush=True)

    ping_thread = threading.Thread(target=_ping_loop, args=(ping_log,), daemon=True)
    ping_thread.start()

    # Give the ping loop a couple of seconds of pre-roll baseline
    time.sleep(3)

    try:
        run_ids = {}
        for vendor in vendors:
            run_ids[vendor] = _run_latency_for_vendor(vendor)
    finally:
        # Give it a couple of seconds of post-roll then stop
        time.sleep(3)
        STOP.set()
        ping_thread.join(timeout=5)

    # Summary
    print("\n=== Complete ===", flush=True)
    print(f"Ping log: {ping_log}", flush=True)
    for v, rid in run_ids.items():
        print(f"  {v}: {rid}", flush=True)
    print(f"\nNext: uv run veval analyze <run_id> --stages latency for each", flush=True)


if __name__ == "__main__":
    main()
