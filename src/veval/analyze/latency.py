"""Latency analyzer — TTFA p50/p90 + RTF on long items.

Reads the api_log.jsonl (not audio bytes) — timings are what the runner
measured, not something re-derivable from the WAV. Cached rows and error
rows are excluded (TTFA=null / total_ms=0 on cache hits, no timing on
errors).

Buffered-response providers (Speechify per D-008; Google buffered REST)
have `ttfa_ms=null`; they show up as N/A in the TTFA rollup and use
`total_ms` for `total_ms_*` percentiles instead. The conversational
`ttfa_p90_ms < 400` gate has `na_policy: exempt-and-annotate`, so a
provider missing TTFA is annotated on the chart, not dropped from
the use case.

RTF (real-time factor) = decoded audio duration ÷ synthesis time.
HIGHER is faster (spec §A.1, defect 2.13). Computed on long-stratum
items only — throughput matters for hour-long narration; short clips
are dominated by connection setup.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from .common import AnalysisWriter, AudioRecord, RunReader


@dataclass
class ItemLatency:
    provider: str
    use_case: str
    item_id: str
    draw: int
    stratum: str | None
    ttfa_ms: float | None
    total_ms: float | None
    decoded_seconds: float | None
    rtf: float | None
    attempts: int
    cached: bool
    error: str | None = None


def _stratum(item_id: str) -> str | None:
    if not item_id:
        return None
    return {
        "S": "short",
        "M": "medium",
        "L": "long",
        "J": "jargon",
        "E": "edge",
        "P": "probe",
    }.get(item_id[0].upper())


def _decoded_seconds(wav: Path) -> float | None:
    if not wav.exists():
        return None
    try:
        info = sf.info(str(wav))
        return float(info.duration)
    except (RuntimeError, sf.LibsndfileError):
        return None


def _analyze_row(record: AudioRecord) -> ItemLatency:
    row = record.api_row or {}
    ttfa = row.get("ttfa_ms")
    total = row.get("total_ms")
    cached = row.get("cache") == "hit"

    decoded = None
    rtf = None
    if row.get("status") == "ok" and record.wav_path.exists() and total and total > 0:
        decoded = _decoded_seconds(record.wav_path)
        if decoded and decoded > 0:
            rtf = decoded / (total / 1000.0)

    return ItemLatency(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        stratum=_stratum(record.item_id),
        ttfa_ms=float(ttfa) if isinstance(ttfa, (int, float)) else None,
        total_ms=float(total) if isinstance(total, (int, float)) and total > 0 else None,
        decoded_seconds=decoded,
        rtf=rtf,
        attempts=int(row.get("attempts", 0)),
        cached=cached,
    )


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(values, p))


def _by_provider(rows: list[ItemLatency]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[ItemLatency]] = {}
    for r in rows:
        groups.setdefault((r.provider, r.use_case), []).append(r)

    rollups: list[dict[str, Any]] = []
    for (provider, use_case), items in sorted(groups.items()):
        # Only fresh (non-cached, successful) rows contribute to timing
        # percentiles; cached rows have no real timing.
        fresh = [i for i in items if not i.cached]
        ttfa_values = [i.ttfa_ms for i in fresh if i.ttfa_ms is not None]
        total_values = [i.total_ms for i in fresh if i.total_ms is not None]
        long_rtfs = [
            i.rtf for i in fresh if i.stratum == "long" and i.rtf is not None
        ]

        rollups.append(
            {
                "provider": provider,
                "use_case": use_case,
                "n_items": len(items),
                "n_fresh": len(fresh),
                "n_cached": sum(1 for i in items if i.cached),
                "n_with_ttfa": len(ttfa_values),
                "n_with_total": len(total_values),
                "ttfa_p50_ms": _pct(ttfa_values, 50),
                "ttfa_p90_ms": _pct(ttfa_values, 90),
                "ttfa_min_ms": min(ttfa_values) if ttfa_values else None,
                "ttfa_max_ms": max(ttfa_values) if ttfa_values else None,
                "total_p50_ms": _pct(total_values, 50),
                "total_p90_ms": _pct(total_values, 90),
                "long_stratum_n": len(long_rtfs),
                "long_stratum_rtf_p50": _pct(long_rtfs, 50),
                "long_stratum_rtf_p10": _pct(long_rtfs, 10),  # 10th %ile = worst
                # True only when TTFA was captured for at least one fresh
                # call. False on campaign runs (streaming=False by design)
                # AND on buffered-response providers even in latency mode
                # (Speechify per D-008; Google buffered REST). The reader
                # disambiguates via context.kind above.
                "ttfa_measured": bool(ttfa_values),
            }
        )
    return rollups


def run(run_dir: Path, *, writer: AnalysisWriter | None = None) -> dict[str, Any]:
    """Compute latency metrics for one run dir. Writes `latency.json`."""
    reader = RunReader(run_dir)
    rows = [_analyze_row(r) for r in reader.records(only_status=None)]

    # Record run-level context that D1 comparability depends on:
    manifest = reader.manifest()
    kind = manifest.get("kind")
    context = {
        "kind": kind,
        # Only latency-mode runs stream (runner.py sets streaming = mode ==
        # RunMode.latency) — so campaign-mode TTFA fields will be None for
        # every provider by design. Reader interprets accordingly.
        "ttfa_captured_by_mode": kind == "latency",
        "hostname": manifest.get("hostname"),
        "platform": manifest.get("platform"),
        # Serving region cannot be inferred from a WAV — providers rarely
        # expose it in response headers either. Left as a slot the manual
        # runbook fills in via a per-run README when it matters.
        "serving_region": manifest.get("extras", {}).get("serving_region"),
    }

    payload = {
        "run_id": run_dir.name,
        "context": context,
        "total_items": len(rows),
        "by_provider": _by_provider(rows),
        "items": [asdict(r) for r in rows],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("latency.json", payload)
    return payload
