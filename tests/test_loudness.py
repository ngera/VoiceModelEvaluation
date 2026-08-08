"""Regression tests for human/loudness.py.

Loudness normalization must hit target within 0.5 LUFS on any input
that isn't peak-limited, and must NOT introduce clipping. The peak
ceiling has to actually kick in when a hot input would overshoot.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from veval.human.loudness import (
    PEAK_CEILING_DBFS,
    TARGET_LUFS,
    normalize_file,
)


def _write_sine(path: Path, seconds: float = 2.0, sr: int = 24000, amp: float = 0.2) -> None:
    n = int(sr * seconds)
    samples = (amp * np.sin(2 * np.pi * 440 * np.arange(n) / sr)).astype(np.float32)
    sf.write(str(path), samples, sr, subtype="PCM_16")


def test_normalize_quiet_input_hits_target_lufs(tmp_path: Path) -> None:
    src = tmp_path / "quiet.wav"
    dst = tmp_path / "quiet_norm.wav"
    _write_sine(src, amp=0.05)  # very quiet
    r = normalize_file(src, dst)
    assert r.error is None
    assert r.output_lufs is not None
    # 2 seconds of a 440 Hz sine is inside pyloudnorm's tolerance
    assert abs(r.output_lufs - TARGET_LUFS) < 0.5
    assert r.gain_applied_db > 0  # gained UP


def test_normalize_loud_input_gets_gained_down(tmp_path: Path) -> None:
    src = tmp_path / "loud.wav"
    dst = tmp_path / "loud_norm.wav"
    _write_sine(src, amp=0.5)
    r = normalize_file(src, dst)
    assert r.error is None
    assert r.output_lufs is not None
    assert abs(r.output_lufs - TARGET_LUFS) < 0.5
    assert r.gain_applied_db < 0  # gained DOWN


def test_normalize_caps_gain_when_peak_would_clip(tmp_path: Path) -> None:
    """A very-quiet clip that ALSO has a big transient shouldn't be
    gained to full-scale just to hit -18 LUFS."""
    src = tmp_path / "spiky.wav"
    dst = tmp_path / "spiky_norm.wav"
    sr = 24000
    n = 2 * sr
    # RMS very low → LUFS very low; but a single peak near full-scale
    samples = np.zeros(n, dtype=np.float32)
    samples[100] = 0.9   # a big transient
    samples[n // 2] = 0.9
    # add tiny noise so pyloudnorm has something to measure
    samples += (0.001 * np.random.RandomState(0).randn(n)).astype(np.float32)
    sf.write(str(src), samples, sr, subtype="PCM_16")

    r = normalize_file(src, dst)
    if r.error == "silent_input":
        pytest.skip("noise floor too low for pyloudnorm at this length")
    # Read output and verify peak did NOT exceed the ceiling
    out, _ = sf.read(str(dst), dtype="float32")
    peak_dbfs = 20 * np.log10(np.max(np.abs(out)))
    assert peak_dbfs <= PEAK_CEILING_DBFS + 0.05  # tiny float tolerance
    assert r.peak_capped is True


def test_normalize_missing_src_returns_error(tmp_path: Path) -> None:
    r = normalize_file(tmp_path / "nope.wav", tmp_path / "out.wav")
    assert r.error == "src_missing"


def test_normalize_silent_input_flagged(tmp_path: Path) -> None:
    src = tmp_path / "silence.wav"
    dst = tmp_path / "silence_norm.wav"
    sf.write(str(src), np.zeros(24000, dtype=np.float32), 24000, subtype="PCM_16")
    r = normalize_file(src, dst)
    assert r.error == "silent_input"


def test_normalize_preserves_sample_rate(tmp_path: Path) -> None:
    src = tmp_path / "in.wav"
    dst = tmp_path / "out.wav"
    _write_sine(src, sr=48000)
    r = normalize_file(src, dst)
    assert r.error is None
    _, sr_out = sf.read(str(dst))
    assert sr_out == 48000


def test_normalize_creates_output_dir(tmp_path: Path) -> None:
    src = tmp_path / "in.wav"
    dst = tmp_path / "nested" / "dir" / "out.wav"
    _write_sine(src)
    r = normalize_file(src, dst)
    assert r.error is None
    assert dst.exists()


def test_target_lufs_is_minus_18() -> None:
    """The target is load-bearing (spec §D4 line 393). Changing it
    silently would shift every published rating."""
    assert TARGET_LUFS == -18.0
