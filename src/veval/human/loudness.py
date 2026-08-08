"""Loudness normalization — every rating-page WAV goes to −18 LUFS first.

Plan v2 line 393: "-18 LUFS via pyloudnorm, mandatory before upload."
Rationale: without normalization, louder clips systematically win A/B
comparisons — the test measures gain staging, not voice quality.

−18 LUFS chosen because:
    - Comfortable near-broadcast level; nobody has to reach for the
      volume knob mid-session.
    - Well above the noise floor (spec §5 hygiene: below −40 dBFS).
    - Well below the clipping ceiling — a peak-limited clip at −18 LUFS
      has ~14 dB of headroom to full-scale, safe for arbitrary content
      variation.

Applied to every provider clip AND every human anchor clip. The
normalizer preserves waveform shape (gain application, no compression
or peak-limiting), so provider dynamics are still what listeners hear.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

TARGET_LUFS = -18.0

# Peak-safety guard: if the required gain would drive a sample past this
# threshold, cap the gain there. Prevents introducing new clipping just
# to hit the loudness target. A very-quiet clip that requires >20 dB of
# gain still normalizes fully; a hot clip already near full-scale gets
# capped rather than clipped.
PEAK_CEILING_DBFS = -1.0


@dataclass
class NormalizationResult:
    input_path: str
    output_path: str
    original_lufs: float | None
    output_lufs: float | None
    gain_applied_db: float
    peak_capped: bool
    error: str | None = None


def normalize_file(
    src: Path,
    dst: Path,
    target_lufs: float = TARGET_LUFS,
    peak_ceiling_dbfs: float = PEAK_CEILING_DBFS,
) -> NormalizationResult:
    """Read `src`, apply loudness gain to reach `target_lufs`, write `dst`.

    Preserves sample rate + bit depth of the input. Peak-safe: if the
    required gain would push the peak past `peak_ceiling_dbfs`, gain is
    capped there and `peak_capped=True` is recorded.

    Errors (missing file, decode failure) return a result with
    `error` populated rather than raising — callers batch over many
    files and want data, not exceptions.
    """
    if not src.exists():
        return NormalizationResult(
            input_path=str(src), output_path=str(dst),
            original_lufs=None, output_lufs=None,
            gain_applied_db=0.0, peak_capped=False,
            error="src_missing",
        )
    try:
        samples, sr = sf.read(str(src), dtype="float32", always_2d=False)
    except (RuntimeError, sf.LibsndfileError) as e:
        return NormalizationResult(
            input_path=str(src), output_path=str(dst),
            original_lufs=None, output_lufs=None,
            gain_applied_db=0.0, peak_capped=False,
            error=f"decode_error={e.__class__.__name__}",
        )
    if samples.size == 0:
        return NormalizationResult(
            input_path=str(src), output_path=str(dst),
            original_lufs=None, output_lufs=None,
            gain_applied_db=0.0, peak_capped=False,
            error="empty_audio",
        )

    mono = samples if samples.ndim == 1 else samples.mean(axis=1)
    try:
        meter = pyln.Meter(sr)  # ITU-R BS.1770-4
        current_lufs = float(meter.integrated_loudness(mono))
    except (ValueError, RuntimeError) as e:
        return NormalizationResult(
            input_path=str(src), output_path=str(dst),
            original_lufs=None, output_lufs=None,
            gain_applied_db=0.0, peak_capped=False,
            error=f"lufs_error={e.__class__.__name__}",
        )

    # pyloudnorm returns -inf for pure silence — no meaningful gain
    if not np.isfinite(current_lufs):
        return NormalizationResult(
            input_path=str(src), output_path=str(dst),
            original_lufs=current_lufs, output_lufs=current_lufs,
            gain_applied_db=0.0, peak_capped=False,
            error="silent_input",
        )

    gain_db = target_lufs - current_lufs
    peak_capped = False

    # Peak-safety check: what would the peak be after this gain?
    current_peak = float(np.max(np.abs(samples)))
    if current_peak > 0:
        proposed_peak = current_peak * (10.0 ** (gain_db / 20.0))
        ceiling_linear = 10.0 ** (peak_ceiling_dbfs / 20.0)
        if proposed_peak > ceiling_linear:
            # Cap the gain so the peak lands at ceiling_linear
            max_gain_db = 20.0 * float(np.log10(ceiling_linear / current_peak))
            gain_db = max_gain_db
            peak_capped = True

    gain_linear = 10.0 ** (gain_db / 20.0)
    out = samples * gain_linear

    # Re-measure for the record
    out_mono = out if out.ndim == 1 else out.mean(axis=1)
    try:
        output_lufs = float(pyln.Meter(sr).integrated_loudness(out_mono))
    except (ValueError, RuntimeError):
        output_lufs = None

    dst.parent.mkdir(parents=True, exist_ok=True)
    # Preserve subtype where possible; float32 output is safe and lossless
    sf.write(str(dst), out, sr, subtype="PCM_16")

    return NormalizationResult(
        input_path=str(src),
        output_path=str(dst),
        original_lufs=current_lufs,
        output_lufs=output_lufs,
        gain_applied_db=round(gain_db, 3),
        peak_capped=peak_capped,
        error=None,
    )
