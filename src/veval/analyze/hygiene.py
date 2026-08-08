"""Hygiene analyzer — clipping, LUFS, silero-VAD pauses, acoustic noise floor.

Per-file metrics feeding the conversational `clipped_samples == 0` gate
and the narration `long_stratum_acoustic_noise_floor_dbfs <= -40` gate.

Everything read here is a pure function of the WAV — no config or api_log
required, so the analyzer runs against any run store without ambiguity.
Thresholds are pulled from gates.yaml for the gate-summary section so the
gate values remain single-source-of-truth (never hardcoded in two places).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from veval.config import GatesFile

from .common import AnalysisWriter, AudioRecord, RunReader

# Silero-VAD singleton — shared with acceptance.py's loader for a single
# model load per process.
_VAD_MODEL: Any = None


def _get_vad() -> Any:
    global _VAD_MODEL
    if _VAD_MODEL is None:
        from silero_vad import load_silero_vad

        _VAD_MODEL = load_silero_vad()
    return _VAD_MODEL


@dataclass
class FileHygiene:
    provider: str
    use_case: str
    item_id: str
    draw: int
    wav_path: str
    stratum: str | None = None  # inferred from item_id prefix; None if unknown

    # Level / loudness
    peak_dbfs: float | None = None
    lufs: float | None = None
    clipped_samples: int = 0
    clipped_runs: int = 0

    # Noise / speech
    acoustic_noise_floor_dbfs: float | None = None
    speech_seconds: float | None = None
    total_seconds: float | None = None
    speech_ratio: float | None = None
    pause_count: int = 0
    long_pause_count: int = 0        # pauses > 2.0s inside speech
    max_pause_seconds: float | None = None

    error: str | None = None


def _stratum_from_item_id(item_id: str) -> str | None:
    """Corpus IDs follow `S01`/`M03`/`L02`/`J07`/`E05`/`P02` — extract prefix."""
    if not item_id:
        return None
    first = item_id[0].upper()
    return {
        "S": "short",
        "M": "medium",
        "L": "long",
        "J": "jargon",
        "E": "edge",
        "P": "probe",
    }.get(first)


def _clipping_stats(samples: np.ndarray, threshold: float = 0.99) -> tuple[int, int]:
    """Count clipped samples and clipped runs (consecutive-sample streaks
    at or past `threshold`).

    Real clipping in a float WAV shows up as a saturated plateau at ±1.0.
    0.99 tolerates the tiniest float-quantization slop without missing
    real clips.
    """
    mask = np.abs(samples) >= threshold
    count = int(mask.sum())
    if count == 0:
        return 0, 0
    # Count runs: transitions from False→True
    padded = np.concatenate([[False], mask, [False]])
    starts = np.flatnonzero(~padded[:-1] & padded[1:])
    return count, int(starts.size)


def _acoustic_noise_floor_dbfs(samples: np.ndarray, speech_mask: np.ndarray) -> float | None:
    """RMS of the non-speech regions, in dBFS.

    dBFS = 20*log10(rms). Full-scale (1.0) = 0 dBFS. Pure silence returns
    -inf, which we clip to -120 so the JSON stays numeric. When there are
    no non-speech samples at all, returns None (nothing to measure).
    """
    non_speech = samples[~speech_mask]
    if non_speech.size == 0:
        return None
    rms = float(np.sqrt(np.mean(np.square(non_speech.astype(np.float64)))))
    if rms <= 0:
        return -120.0
    return float(20.0 * np.log10(rms))


def _speech_mask(samples: np.ndarray, sr: int) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Silero-VAD → boolean mask (per-sample) + list of (start, end) sample indices.

    Downsamples crudely to 16 kHz for VAD; the boolean mask maps VAD
    16 kHz timestamps back to the original sample rate so caller-side
    dB / duration math uses the true samples.
    """
    import torch
    from silero_vad import get_speech_timestamps

    if sr != 16000:
        step = sr / 16000
        idx = (np.arange(0, samples.size, step)).astype(int)
        idx = idx[idx < samples.size]
        vad_samples = samples[idx].astype(np.float32)
    else:
        vad_samples = samples.astype(np.float32)

    vad = _get_vad()
    timestamps_16k = get_speech_timestamps(
        torch.from_numpy(vad_samples), vad, sampling_rate=16000
    )
    # Map back to original sample rate
    ratio = sr / 16000
    mask = np.zeros(samples.size, dtype=bool)
    ranges: list[tuple[int, int]] = []
    for t in timestamps_16k:
        a = int(t["start"] * ratio)
        b = int(t["end"] * ratio)
        a = max(0, min(a, samples.size))
        b = max(0, min(b, samples.size))
        if b > a:
            mask[a:b] = True
            ranges.append((a, b))
    return mask, ranges


def _pauses(ranges: list[tuple[int, int]], sr: int, long_threshold_s: float = 2.0) -> tuple[
    int, int, float | None
]:
    """Pauses = gaps between consecutive speech ranges. Leading/trailing
    silence is NOT counted (buyers don't hear the pre-roll as an
    "unnatural pause" in a support agent).
    """
    if len(ranges) < 2:
        return 0, 0, None
    gaps_samples = [
        b_start - a_end
        for (_, a_end), (b_start, _) in zip(ranges, ranges[1:], strict=False)
    ]
    gaps_s = [g / sr for g in gaps_samples]
    long = sum(1 for g in gaps_s if g > long_threshold_s)
    return len(gaps_s), long, max(gaps_s)


def analyze_file(record: AudioRecord) -> FileHygiene:
    r = FileHygiene(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        wav_path=str(record.wav_path),
        stratum=_stratum_from_item_id(record.item_id),
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
    r.peak_dbfs = _peak_dbfs(samples)
    r.clipped_samples, r.clipped_runs = _clipping_stats(samples)

    try:
        r.lufs = float(pyln.Meter(sr).integrated_loudness(samples))
    except (ValueError, RuntimeError):
        r.lufs = None

    try:
        speech_mask, ranges = _speech_mask(samples, sr)
        r.acoustic_noise_floor_dbfs = _acoustic_noise_floor_dbfs(samples, speech_mask)
        r.speech_seconds = float(speech_mask.sum() / sr)
        if r.total_seconds > 0:
            r.speech_ratio = r.speech_seconds / r.total_seconds
        pauses, long_pauses, max_pause = _pauses(ranges, sr)
        r.pause_count = pauses
        r.long_pause_count = long_pauses
        r.max_pause_seconds = max_pause
    except Exception as e:  # noqa: BLE001 — VAD failure is data, not a crash
        r.error = f"vad_error={e.__class__.__name__}"

    return r


def _peak_dbfs(samples: np.ndarray) -> float:
    peak = float(np.max(np.abs(samples)))
    if peak <= 0:
        return -120.0
    return float(20.0 * np.log10(peak))


def _aggregate_by_provider(
    files: list[FileHygiene],
    hygiene_cfg: Any,
) -> list[dict[str, Any]]:
    """Per-provider summary. Long-stratum items get separate rollup for
    the narration `long_stratum_acoustic_noise_floor_dbfs` gate.
    """
    by_provider: dict[tuple[str, str], list[FileHygiene]] = {}
    for f in files:
        by_provider.setdefault((f.provider, f.use_case), []).append(f)

    thresh_dbfs = hygiene_cfg.acoustic_noise_floor_dbfs_max
    max_clipped = hygiene_cfg.max_clipped_samples

    rollups: list[dict[str, Any]] = []
    for (provider, use_case), rows in sorted(by_provider.items()):
        valid = [f for f in rows if f.error is None]
        long_items = [f for f in valid if f.stratum == "long"]

        rollup = {
            "provider": provider,
            "use_case": use_case,
            "n_files": len(rows),
            "n_valid": len(valid),
            "n_errors": len(rows) - len(valid),
            "total_clipped_samples": sum(f.clipped_samples for f in valid),
            "files_with_clipping": sum(1 for f in valid if f.clipped_samples > 0),
            "gate_clipped_samples_pass": all(
                f.clipped_samples <= max_clipped for f in valid
            ),
            "mean_lufs": _mean_or_none([f.lufs for f in valid]),
            "mean_noise_floor_dbfs": _mean_or_none(
                [f.acoustic_noise_floor_dbfs for f in valid]
            ),
            "mean_speech_ratio": _mean_or_none([f.speech_ratio for f in valid]),
            "total_long_pauses": sum(f.long_pause_count for f in valid),
            # Long-stratum rollup — feeds narration gate directly
            "long_stratum": {
                "n": len(long_items),
                "worst_noise_floor_dbfs": max(
                    (
                        f.acoustic_noise_floor_dbfs
                        for f in long_items
                        if f.acoustic_noise_floor_dbfs is not None
                    ),
                    default=None,
                ),
                "gate_long_stratum_noise_floor_pass": (
                    all(
                        (f.acoustic_noise_floor_dbfs or -120.0) <= thresh_dbfs
                        for f in long_items
                    )
                    if long_items
                    else None
                ),
                "gate_long_stratum_clipped_pass": (
                    all(f.clipped_samples <= max_clipped for f in long_items)
                    if long_items
                    else None
                ),
            },
        }
        rollups.append(rollup)
    return rollups


def _mean_or_none(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None and np.isfinite(v)]
    if not clean:
        return None
    return float(np.mean(clean))


def run(
    run_dir: Path,
    *,
    gates: GatesFile,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Run hygiene analysis over one run dir. Writes `hygiene.json`."""
    reader = RunReader(run_dir)
    reports: list[FileHygiene] = []
    for record in reader.records():
        reports.append(analyze_file(record))

    payload = {
        "run_id": run_dir.name,
        "total_files": len(reports),
        "n_errors": sum(1 for r in reports if r.error is not None),
        "gate_thresholds": {
            "acoustic_noise_floor_dbfs_max": gates.hygiene.acoustic_noise_floor_dbfs_max,
            "max_clipped_samples": gates.hygiene.max_clipped_samples,
        },
        "by_provider": _aggregate_by_provider(reports, gates.hygiene),
        "files": [asdict(r) for r in reports],
    }

    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("hygiene.json", payload)
    return payload
