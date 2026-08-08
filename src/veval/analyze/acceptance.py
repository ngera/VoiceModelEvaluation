"""WAV acceptance gate — the guardrail that runs BEFORE any analyzer.

Phase A shipped a defect where a streamed header declared 44,737 seconds
for a 2.80-second clip. Every downstream metric that reads duration from
the header — RTF, VAD, LUFS, TTSDS2 — would have been silently corrupted.
`finalize_wav_header()` in adapters/base.py fixes it going forward; this
module is the safety net that catches any regression before it poisons
analysis.

Per-file checks (spec Phase-E acceptance gate):
    - header_duration ≈ decoded_duration (within 1%)
    - LUFS in a plausible range [-70, -5]
    - VAD finds at least some speech
    - chars_billed is present in the api_log row

Failed checks are recorded as issues on the per-file report; the gate
overall is `passed` only when every file passed every check.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from .common import AnalysisWriter, AudioRecord, RunReader

# Plausibility bounds. LUFS below -70 = essentially silence; above -5 =
# hot clipping-risk territory. Neither should exist in a clean synthesis.
LUFS_MIN = -70.0
LUFS_MAX = -5.0

# Header vs decoded duration tolerance. 1% is generous — the Phase A
# defect was ~16,000× off; a real mismatch is either <0.1% or catastrophic.
DURATION_MISMATCH_TOL = 0.01

# Minimum WAV size (bytes). Anything shorter is almost certainly a
# truncated response, not real audio.
MIN_WAV_BYTES = 200

# Silero-VAD singleton — loaded lazily on first call so `import` stays cheap.
_VAD_MODEL: Any = None


def _get_vad() -> Any:
    global _VAD_MODEL
    if _VAD_MODEL is None:
        from silero_vad import load_silero_vad

        _VAD_MODEL = load_silero_vad()
    return _VAD_MODEL


@dataclass
class FileAcceptance:
    provider: str
    use_case: str
    item_id: str
    draw: int
    wav_path: str
    header_duration_s: float | None = None
    decoded_duration_s: float | None = None
    duration_mismatch_pct: float | None = None
    lufs: float | None = None
    vad_speech_seconds: float | None = None
    chars_billed: int | None = None
    passed: bool = False
    issues: list[str] = field(default_factory=list)


def _header_duration_seconds(path: Path) -> float | None:
    """Walk the RIFF/WAVE chunks and read the `data` chunk size.

    Some providers (Cartesia) emit a `LIST` metadata chunk before `data`,
    so a "bytes 40-44 = data-size" assumption reads the wrong number.
    """
    try:
        with path.open("rb") as f:
            head = f.read(12)
            if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WAVE":
                return None
            channels = sample_rate = bits_per_sample = 0
            data_bytes: int | None = None
            # Iterate chunks: 4-byte id, 4-byte little-endian size, payload
            for _ in range(64):  # safety cap; a well-formed WAV has few chunks
                header = f.read(8)
                if len(header) < 8:
                    break
                chunk_id = header[:4]
                chunk_size = int.from_bytes(header[4:8], "little")
                if chunk_id == b"fmt ":
                    fmt = f.read(chunk_size)
                    if len(fmt) < 16:
                        return None
                    channels = int.from_bytes(fmt[2:4], "little")
                    sample_rate = int.from_bytes(fmt[4:8], "little")
                    bits_per_sample = int.from_bytes(fmt[14:16], "little")
                    # fmt chunks are padded to an even byte count
                    if chunk_size % 2:
                        f.seek(1, 1)
                elif chunk_id == b"data":
                    data_bytes = chunk_size
                    break
                else:
                    # Skip unknown chunks (LIST, JUNK, bext, ...)
                    f.seek(chunk_size + (chunk_size % 2), 1)
            if data_bytes is None or channels == 0 or sample_rate == 0 or bits_per_sample == 0:
                return None
            bytes_per_sample = bits_per_sample // 8
            if bytes_per_sample == 0:
                return None
            # 0xFFFFFFFF is the streaming/unknown placeholder — treat as unreadable
            # so the acceptance report flags "header_unreadable" rather than
            # producing a fake huge duration.
            if data_bytes == 0xFFFFFFFF:
                return None
            n_samples = data_bytes // (channels * bytes_per_sample)
            return n_samples / sample_rate
    except OSError:
        return None


def analyze_file(record: AudioRecord) -> FileAcceptance:
    """Run the acceptance checks against one WAV. Never raises for content
    errors — issues are collected into `issues` and `passed` is set to False.
    """
    r = FileAcceptance(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        wav_path=str(record.wav_path),
    )

    if not record.wav_path.exists():
        r.issues.append("wav_missing")
        return r

    size = record.wav_path.stat().st_size
    if size < MIN_WAV_BYTES:
        r.issues.append(f"wav_too_small_bytes={size}")
        return r

    r.header_duration_s = _header_duration_seconds(record.wav_path)

    try:
        samples, sr = sf.read(str(record.wav_path), dtype="float32", always_2d=False)
    except (RuntimeError, sf.LibsndfileError) as e:
        r.issues.append(f"soundfile_decode_error={e.__class__.__name__}")
        return r
    if samples.ndim > 1:
        samples = samples.mean(axis=1)  # collapse to mono for measurement
    if samples.size == 0:
        r.issues.append("decoded_zero_samples")
        return r

    r.decoded_duration_s = samples.size / sr

    if r.header_duration_s is None:
        r.issues.append("header_unreadable")
    elif r.decoded_duration_s > 0:
        diff = abs(r.header_duration_s - r.decoded_duration_s) / r.decoded_duration_s
        r.duration_mismatch_pct = diff * 100.0
        if diff > DURATION_MISMATCH_TOL:
            r.issues.append(
                f"duration_mismatch header={r.header_duration_s:.2f}s "
                f"decoded={r.decoded_duration_s:.2f}s "
                f"({r.duration_mismatch_pct:.1f}%)"
            )

    try:
        meter = pyln.Meter(sr)  # ITU-R BS.1770-4
        r.lufs = float(meter.integrated_loudness(samples))
    except (ValueError, RuntimeError) as e:
        r.issues.append(f"lufs_error={e.__class__.__name__}")

    if r.lufs is not None and (r.lufs < LUFS_MIN or r.lufs > LUFS_MAX):
        # -inf shows up for pure silence; pyloudnorm returns -inf in that case.
        r.issues.append(f"lufs_out_of_range={r.lufs:.1f}")

    # Silero-VAD wants 16 kHz mono float32. Downsample crudely — the exact
    # timestamps don't matter, we just need speech-vs-not.
    try:
        from silero_vad import get_speech_timestamps

        vad = _get_vad()
        if sr != 16000:
            step = sr / 16000
            idx = (np.arange(0, samples.size, step)).astype(int)
            idx = idx[idx < samples.size]
            vad_samples = samples[idx].astype(np.float32)
        else:
            vad_samples = samples.astype(np.float32)
        import torch

        speech = get_speech_timestamps(
            torch.from_numpy(vad_samples), vad, sampling_rate=16000
        )
        r.vad_speech_seconds = sum(s["end"] - s["start"] for s in speech) / 16000.0
    except Exception as e:  # noqa: BLE001 — VAD failure is a data point, not a crash
        r.issues.append(f"vad_error={e.__class__.__name__}")

    if r.vad_speech_seconds is not None and r.vad_speech_seconds <= 0.0:
        r.issues.append("vad_no_speech_detected")

    if record.api_row is not None:
        chars = record.api_row.get("chars_billed")
        if isinstance(chars, int):
            r.chars_billed = chars
        else:
            r.issues.append("chars_billed_missing")
    else:
        r.issues.append("api_log_row_missing")

    r.passed = not r.issues
    return r


def run(run_dir: Path, *, writer: AnalysisWriter | None = None) -> dict[str, Any]:
    """Run the acceptance gate over one run dir. Writes `acceptance.json`."""
    reader = RunReader(run_dir)
    reports: list[FileAcceptance] = []
    for record in reader.records():
        reports.append(analyze_file(record))

    total = len(reports)
    passed = sum(1 for r in reports if r.passed)
    failed = total - passed

    payload = {
        "run_id": run_dir.name,
        "total_files": total,
        "passed": passed,
        "failed": failed,
        "gate_ok": failed == 0,
        "files": [asdict(r) for r in reports],
    }

    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("acceptance.json", payload)
    return payload
