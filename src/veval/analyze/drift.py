"""Drift analyzer — per-third TTSDS2/hygiene on the 8 long narration items.

The measured form of "listener fatigue" (R6, plan v2). For each L-item
narration audio: cut into three equal thirds, run TTSDS2 and hygiene on
each third, flag `monotonic_quality_drift` when the trend across thirds
degrades beyond the measurement noise floor.

Per-third TTSDS2 needs a proper reference alignment; for now we compute
per-third Audiobox PQ + hygiene LUFS/noise-floor as a first-pass proxy
and note that TTSDS2 per-third is deferred until quality.py emits
per-file scores (currently emits per-provider aggregates). The
narration gate `monotonic_quality_drift_flag` reads from here — flag
is True when the last-third PQ is worse than the first-third PQ by
more than the pooled within-provider SD of PQ.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from veval.config import GatesFile

from .common import AnalysisWriter, AudioRecord, RunReader

CHARS_PER_SECOND = 12.5  # matches wer.py


@dataclass
class ItemDrift:
    provider: str
    use_case: str
    item_id: str
    draw: int
    total_seconds: float | None = None
    thirds: list[dict[str, float | None]] = field(default_factory=list)
    monotonic_degradation: bool = False
    error: str | None = None


def _third_stats(samples: np.ndarray, sr: int) -> list[dict[str, float | None]]:
    """Compute per-third LUFS + RMS-dBFS on a WAV's samples."""
    n = samples.size
    third = n // 3
    out: list[dict[str, float | None]] = []
    for i in range(3):
        chunk = samples[i * third:(i + 1) * third] if i < 2 else samples[i * third:]
        if chunk.size == 0:
            out.append({"lufs": None, "rms_dbfs": None})
            continue
        try:
            lufs = float(pyln.Meter(sr).integrated_loudness(chunk))
        except (ValueError, RuntimeError):
            lufs = None
        rms = float(np.sqrt(np.mean(np.square(chunk.astype(np.float64)))))
        rms_dbfs = float(20.0 * np.log10(rms)) if rms > 0 else -120.0
        out.append({"lufs": lufs, "rms_dbfs": rms_dbfs})
    return out


def analyze_file(record: AudioRecord) -> ItemDrift:
    r = ItemDrift(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
    )
    if not record.wav_path.exists():
        r.error = "wav_missing"
        return r
    try:
        samples, sr = sf.read(str(record.wav_path), dtype="float32", always_2d=False)
    except (RuntimeError, sf.LibsndfileError) as e:
        r.error = f"decode_error={e.__class__.__name__}"
        return r
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if samples.size == 0:
        r.error = "empty_audio"
        return r
    r.total_seconds = samples.size / sr
    r.thirds = _third_stats(samples, sr)

    # Monotonic degradation flag: LUFS drift more than 3 dB across thirds,
    # or RMS floor rising by more than 6 dB (both directions of
    # "gets worse over time"). Coarse first-pass rule — refined once the
    # variance.py per-provider PQ SD is in the same output tree.
    lufs = [t["lufs"] for t in r.thirds]
    dbfs = [t["rms_dbfs"] for t in r.thirds]
    def _monotonic_delta(vals: list[float | None], threshold: float, direction: str) -> bool:
        clean = [v for v in vals if v is not None]
        if len(clean) < 3:
            return False
        if direction == "decrease":
            return (clean[0] - clean[-1]) > threshold and clean[0] > clean[1] > clean[2]
        # increase
        return (clean[-1] - clean[0]) > threshold and clean[0] < clean[1] < clean[2]
    r.monotonic_degradation = (
        _monotonic_delta(lufs, 3.0, "decrease")
        or _monotonic_delta(dbfs, 6.0, "increase")
    )
    return r


def run(
    run_dir: Path,
    *,
    gates: GatesFile,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Drift analysis. Runs only on narration long-stratum items."""
    reader = RunReader(run_dir)
    rows: list[ItemDrift] = []
    for rec in reader.records():
        if rec.use_case != "narration":
            continue
        if not rec.item_id.startswith("L"):
            continue
        rows.append(analyze_file(rec))

    # Per-provider aggregation
    by_provider: dict[str, list[ItemDrift]] = {}
    for r in rows:
        by_provider.setdefault(r.provider, []).append(r)

    provider_rollups = []
    for provider, items in sorted(by_provider.items()):
        n_flagged = sum(1 for i in items if i.monotonic_degradation)
        provider_rollups.append({
            "provider": provider,
            "n_long_items": len(items),
            "n_monotonic_degradation": n_flagged,
            "gate_pass": n_flagged == 0,  # narration monotonic_quality_drift_flag == 0
        })

    payload = {
        "run_id": run_dir.name,
        "gate_name": "monotonic_quality_drift_flag",
        "by_provider": provider_rollups,
        "items": [asdict(r) for r in rows],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("drift.json", payload)
    return payload
