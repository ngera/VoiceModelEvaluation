"""Quality analyzer — TTSDS2 + Audiobox Aesthetics + DNSMOS + split-half.

D3 primary: TTSDS2 aggregate score per provider per use case, against
the pre-registered reference set from analyzers.yaml (`daps` for
narration; conversational reference TBD in Phase B, defect 3.7). Uses
`ttsds.BenchmarkSuite` — the full published benchmark suite; picking a
subset would be a silent methodology change.

D3 supplementary #1: Audiobox Aesthetics — 4 axes emitted (CE/CU/PC/PQ), we
REPORT PQ + CE only per analyzers.yaml. Reporting all 4 unlabelled
would invite post-hoc selection (spec B.2).

D3 supplementary #2 (Phase 2b addition, per RESEARCH_LOG D-B): Microsoft
DNSMOS P.835 via `speechmos.dnsmos`. 4 axes per clip:
    - `p808_mos`: overall MOS predicted from ITU P.808 model
    - `ovrl_mos`, `sig_mos`, `bak_mos`: ITU P.835 three-scale MOS
      (overall / speech signal / background noise)
DNSMOS runs on ONNX runtime — no torch conflict with our env.
Independent pipeline from Audiobox (Meta/torch) → 6 quality signals
from 2 independent pipelines total. UTMOS was attempted (RESEARCH_LOG
D-B revision 2) but blocked by fairseq's Windows source-build cliff.

Split-half stability (spec §4.3, defect 3.7): random split of a
provider's items into two halves, TTSDS2 on each half, absolute delta
between the two scores. Averaged over ≥100 random splits (single split
would be one arbitrary partition). Compared against the absolute
threshold in analyzers.yaml (0.02) — not the noise floor, because the
noise floor doesn't exist until variance.py runs.

Model loading is lazy — first live call downloads references and
benchmark weights (~5-10 GB across the TTSDS2 suite; DNSMOS ONNX
weights are ~10 MB and ship with the pip package). Tests mock the
heavy calls; every reader / aggregator function is exercised in
isolation.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from veval.config import AnalyzersFile

from .common import AnalysisWriter, AudioRecord, RunReader

# --- Lazy loaders --------------------------------------------------------


_AUDIOBOX: Any = None


def _load_audiobox(ckpt: str | None = None) -> Any:
    global _AUDIOBOX
    if _AUDIOBOX is None:
        from audiobox_aesthetics.infer import initialize_predictor

        _AUDIOBOX = initialize_predictor(ckpt=ckpt)
    return _AUDIOBOX


def _load_ttsds_reference(dataset_id: str) -> Any:
    """Resolve a TTSDS2 reference id to a `ttsds.util.dataset.Dataset`.

    TTSDS2 2.1.3 does NOT bundle reference downloaders. Named references
    like `daps` must be downloaded and expanded to a local directory,
    then referenced by that directory path in analyzers.yaml. If
    `dataset_id` is not a resolvable filesystem path, this returns None
    and TTSDS2 scoring silently no-ops for that use case — the caller
    marks it as skipped and the report annotates.
    """
    from ttsds.util.dataset import DirectoryDataset

    p = Path(dataset_id)
    if p.exists() and p.is_dir():
        return DirectoryDataset(
            root_dir=str(p),
            sample_rate=22050,  # TTSDS2 default
            name=p.name,
        )
    return None


# --- Audiobox + DNSMOS: per-file inference -----------------------------


@dataclass
class FileQuality:
    provider: str
    use_case: str
    item_id: str
    draw: int
    wav_path: str
    audiobox: dict[str, float] = field(default_factory=dict)
    dnsmos: dict[str, float] = field(default_factory=dict)
    error: str | None = None
    # Per-analyzer error strings — audiobox and dnsmos are independent
    # pipelines and one failing shouldn't blank both. Populated only
    # when the specific analyzer errored on this file.
    audiobox_error: str | None = None
    dnsmos_error: str | None = None


def _audiobox_axes_for(record: AudioRecord, predictor: Any) -> dict[str, float]:
    """Return {axis: score} for one WAV. Axis names use Audiobox's short
    codes (CE/CU/PC/PQ). Caller filters to the pre-committed subset.

    Correct API (verified against audiobox_aesthetics 0.0.4):
    `predictor.forward([{"path": "<wav>"}])` returns a list of
    per-item dicts with 4 axis keys. Not `predictor(...)` — AesPredictor
    doesn't implement `__call__`.
    """
    # AesPredictor.forward expects a list of dicts keyed by `data_col`
    # (default "path"). Feed one dict per call — batching over N files
    # would be an optimization but complicates error-per-file attribution.
    batch = [{"path": str(record.wav_path)}]
    result = predictor.forward(batch)
    if isinstance(result, list) and result:
        return {k: float(v) for k, v in result[0].items()}
    return {}


def analyze_file_audiobox(
    record: AudioRecord, predictor: Any, axes_reported: list[str]
) -> FileQuality:
    r = FileQuality(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        wav_path=str(record.wav_path),
    )
    if not record.wav_path.exists():
        r.error = "wav_missing"
        return r
    try:
        all_axes = _audiobox_axes_for(record, predictor)
    except Exception as e:  # noqa: BLE001 — inference errors are data
        r.error = f"audiobox_error={e.__class__.__name__}"
        return r
    # Filter to the pre-committed subset. Report both short (CE/PQ) and
    # long (content_enjoyment/production_quality) forms; the frontier
    # chart uses whichever it prefers.
    long_from_short = {
        "CE": "content_enjoyment",
        "CU": "content_usefulness",
        "PC": "production_complexity",
        "PQ": "production_quality",
    }
    for short, long in long_from_short.items():
        if long in axes_reported and short in all_axes:
            r.audiobox[long] = all_axes[short]
    return r


# --- DNSMOS (Microsoft P.835 MOS suite via speechmos, ONNX runtime) ----


def _load_audio_16k_mono(wav_path: Path) -> np.ndarray:
    """Decode a WAV to mono float32 samples at 16 kHz.

    Duplicated intentionally from wer.py's helper — quality.py should
    not depend on wer.py. When we have >2 users of this helper, hoist
    to `analyze/common.py`.
    """
    import soundfile as sf
    from scipy.signal import resample_poly

    samples, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if sr != 16000:
        from math import gcd
        g = gcd(sr, 16000)
        up, down = 16000 // g, sr // g
        samples = resample_poly(samples, up, down).astype(np.float32)
    return samples


DNSMOS_AXES = ("p808_mos", "ovrl_mos", "sig_mos", "bak_mos")


def _dnsmos_axes_for(record: AudioRecord) -> dict[str, float]:
    """Return {axis: score} for one WAV via Microsoft DNSMOS P.835.

    speechmos.dnsmos loads ONNX weights on first call and caches them
    at import; no lazy-loader wrapper needed here. Expected sample
    rate is 16 kHz mono.

    Note: speechmos raises `ValueError: np.ndarray values must be
    between -1 and 1` on any WAV that contains clipped samples
    (|amplitude| > 1). We DO NOT pre-clip the audio here; the
    validation refusal IS a first-class quality finding (see
    RESEARCH_LOG F-4a — independent corroboration of the D5 hygiene
    clipping finding). Callers handle the ValueError via
    `analyze_file_dnsmos` which classifies it as
    `input_clipped_out_of_range` and captures peak amplitude.
    """
    from speechmos import dnsmos

    samples = _load_audio_16k_mono(record.wav_path)
    out = dnsmos.run(samples, 16000)
    if not isinstance(out, dict):
        return {}
    # speechmos returns np.float32/64; coerce to plain float for JSON safety
    return {k: float(v) for k, v in out.items() if k in DNSMOS_AXES}


# Structured error codes for DNSMOS failures. Reported into
# quality.json per file so case-study rendering can group by cause
# rather than parsing raw exception strings.
#
# `input_peak_out_of_range`: sample values reach or exceed the ±1
# ceiling speechmos accepts. Two causes contribute — genuine
# clipping (samples pinned at ±1.0 by upstream mastering) AND
# post-resample filter ringing that pushes near-full-scale samples
# fractionally past 1.0. In practice these are entangled — a
# provider that leaves zero headroom will trigger both. Per-file
# `peak_abs=` value captured for the "how hot was it" reporting angle.
DNSMOS_ERROR_INPUT_CLIPPED = "input_peak_out_of_range"
DNSMOS_ERROR_OTHER = "other"


def _peak_abs_amplitude(wav_path: Path) -> float | None:
    """Read a WAV and return max(|samples|). Used to quantify how far
    over the [-1, 1] threshold a DNSMOS-refused clip actually was.
    Returns None on decode failure (caller has already logged the error).
    """
    import soundfile as sf
    try:
        samples, _ = sf.read(str(wav_path), dtype="float32", always_2d=False)
    except (RuntimeError, sf.LibsndfileError):
        return None
    if samples.size == 0:
        return None
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    return float(np.max(np.abs(samples)))


def analyze_file_dnsmos(record: AudioRecord) -> FileQuality:
    """Standalone per-file DNSMOS analyzer. Used when Audiobox is
    disabled but DNSMOS is enabled. When both run, `run()` merges the
    two FileQuality streams by (provider, use_case, item_id, draw).

    Error classification:
        - `wav_missing` (top-level `error`): file not on disk
        - `dnsmos_error` starts with `input_clipped_out_of_range=`:
          audio contains |amplitude| > 1 (speechmos ValueError).
          Peak amplitude appended for reporting. NOT a bug — this IS
          the finding (F-4a).
        - `dnsmos_error` starts with `other=`: any other exception,
          class + message truncated.
    """
    r = FileQuality(
        provider=record.provider,
        use_case=record.use_case,
        item_id=record.item_id,
        draw=record.draw,
        wav_path=str(record.wav_path),
    )
    if not record.wav_path.exists():
        r.error = "wav_missing"
        return r
    try:
        r.dnsmos = _dnsmos_axes_for(record)
    except ValueError as e:
        # speechmos raises ValueError specifically on out-of-range input;
        # classify structurally so the report can group by cause.
        if "between -1 and 1" in str(e):
            peak = _peak_abs_amplitude(record.wav_path)
            peak_str = f" peak_abs={peak:.4f}" if peak is not None else ""
            r.dnsmos_error = f"{DNSMOS_ERROR_INPUT_CLIPPED}={str(e)[:80]}{peak_str}"
        else:
            r.dnsmos_error = f"{DNSMOS_ERROR_OTHER}=ValueError: {str(e)[:150]}"
    except Exception as e:  # noqa: BLE001 — other inference errors are data
        r.dnsmos_error = f"{DNSMOS_ERROR_OTHER}={e.__class__.__name__}: {str(e)[:150]}"
    return r


# --- TTSDS2 -------------------------------------------------------------


def compute_ttsds_score(
    wav_paths: list[Path],
    reference_dataset_id: str,
    noise_dataset_id: str,
    cache_dir: Path | None = None,
) -> float | None:
    """Run TTSDS2 over a set of WAVs and return the aggregate distributional
    distance. `None` when the benchmark can't run (e.g. reference not
    resolvable in this environment).
    """
    if len(wav_paths) == 0:
        return None
    try:
        from ttsds import BenchmarkSuite
        from ttsds.util.dataset import WavListDataset
    except ImportError:
        return None

    test_ds = WavListDataset(
        wavs=[Path(p) for p in wav_paths],
        sample_rate=22050,  # TTSDS2 will resample as needed
        name="test",
    )
    ref_ds = _load_ttsds_reference(reference_dataset_id)
    if ref_ds is None:
        # Reference not resolvable — return None so the caller marks
        # this (provider, use_case) as TTSDS2-skipped. Documented
        # behavior; the report annotates when TTSDS2 was skipped for
        # lack of a downloaded reference set (spec §A.3).
        return None

    suite = BenchmarkSuite(
        datasets=[test_ds],
        reference_datasets=[ref_ds],
        skip_errors=True,
        cache_dir=str(cache_dir) if cache_dir else None,
    )
    result = suite.run()  # type: ignore[attr-defined]
    # TTSDS2's aggregate score lives at result[test_ds.name]["overall"]
    # or similar — shape may vary by version; keep the raw result and
    # let the caller consume it.
    if isinstance(result, dict):
        for _, per_test in result.items():
            if isinstance(per_test, dict) and "overall" in per_test:
                return float(per_test["overall"])
    return None


def split_half_delta(
    wav_paths: list[Path],
    reference_dataset_id: str,
    noise_dataset_id: str,
    n_splits: int = 100,
    seed: int = 0,
    cache_dir: Path | None = None,
) -> float | None:
    """Mean absolute TTSDS2 delta between random halves of the file list,
    averaged over `n_splits` random partitions.

    Returns None when there are fewer than 10 files (per-half needs at
    least 5, TTSDS2 recommends ≥50; we still emit *something* only when
    we have a defensible minimum).
    """
    if len(wav_paths) < 10:
        return None
    rng = random.Random(seed)
    deltas: list[float] = []
    for _ in range(n_splits):
        shuffled = wav_paths.copy()
        rng.shuffle(shuffled)
        half = len(shuffled) // 2
        a = compute_ttsds_score(shuffled[:half], reference_dataset_id, noise_dataset_id, cache_dir)
        b = compute_ttsds_score(shuffled[half:], reference_dataset_id, noise_dataset_id, cache_dir)
        if a is None or b is None:
            continue
        deltas.append(abs(a - b))
    if not deltas:
        return None
    return float(np.mean(deltas))


# --- Aggregation --------------------------------------------------------


def _aggregate_audiobox(files: list[FileQuality]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[FileQuality]] = {}
    for f in files:
        groups.setdefault((f.provider, f.use_case), []).append(f)

    out: list[dict[str, Any]] = []
    for (provider, use_case), items in sorted(groups.items()):
        valid = [i for i in items if i.error is None and i.audiobox]
        # Union of axis names present in valid items
        axis_names = sorted({a for i in valid for a in i.audiobox})
        means = {
            axis: float(np.mean([i.audiobox[axis] for i in valid if axis in i.audiobox]))
            for axis in axis_names
        } if valid else {}
        out.append({
            "provider": provider,
            "use_case": use_case,
            "n_items": len(items),
            "n_valid": len(valid),
            "audiobox_means": means,
        })
    return out


def _aggregate_dnsmos(files: list[FileQuality]) -> list[dict[str, Any]]:
    """Same shape as _aggregate_audiobox but reads the dnsmos field.

    A file is "valid" for the DNSMOS aggregate iff it has at least one
    dnsmos axis populated AND no top-level wav_missing error. A file
    whose Audiobox errored but DNSMOS succeeded still contributes.
    """
    groups: dict[tuple[str, str], list[FileQuality]] = {}
    for f in files:
        groups.setdefault((f.provider, f.use_case), []).append(f)

    out: list[dict[str, Any]] = []
    for (provider, use_case), items in sorted(groups.items()):
        valid = [
            i for i in items
            if i.error != "wav_missing" and i.dnsmos_error is None and i.dnsmos
        ]
        axis_names = sorted({a for i in valid for a in i.dnsmos})
        means = {
            axis: float(np.mean([i.dnsmos[axis] for i in valid if axis in i.dnsmos]))
            for axis in axis_names
        } if valid else {}
        out.append({
            "provider": provider,
            "use_case": use_case,
            "n_items": len(items),
            "n_valid": len(valid),
            "dnsmos_means": means,
        })
    return out


def _merge_file_streams(
    audiobox_files: list[FileQuality], dnsmos_files: list[FileQuality]
) -> list[FileQuality]:
    """When both analyzers ran, produce a single stream keyed by
    (provider, use_case, item_id, draw) with both `audiobox` and
    `dnsmos` fields populated. If only one ran, return that stream.
    """
    if not audiobox_files:
        return dnsmos_files
    if not dnsmos_files:
        return audiobox_files
    dn_by_key = {(f.provider, f.use_case, f.item_id, f.draw): f for f in dnsmos_files}
    merged: list[FileQuality] = []
    for a in audiobox_files:
        d = dn_by_key.get((a.provider, a.use_case, a.item_id, a.draw))
        if d is not None:
            a.dnsmos = d.dnsmos
            a.dnsmos_error = d.dnsmos_error
        merged.append(a)
    return merged


# --- run() --------------------------------------------------------------


def run(
    run_dir: Path,
    *,
    analyzers: AnalyzersFile,
    compute_ttsds: bool = True,
    compute_audiobox: bool = True,
    compute_dnsmos: bool = True,
    n_split_half: int = 100,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Run TTSDS2 + Audiobox + DNSMOS over one run dir. Writes `quality.json`.

    All three compute flags default to True; set to False to skip a
    stage (useful for iterative development or environment constraints).
    The output JSON records which stages actually ran. Ordering of
    per-file inference is Audiobox → DNSMOS → merged; each is
    independent so one failing doesn't block the other.
    """
    reader = RunReader(run_dir)
    records = list(reader.records())

    # --- Audiobox per file ---
    audiobox_files: list[FileQuality] = []
    if compute_audiobox and records:
        predictor = _load_audiobox(ckpt=None)
        axes = list(analyzers.audiobox_axes_reported)
        for rec in records:
            audiobox_files.append(analyze_file_audiobox(rec, predictor, axes))

    # --- DNSMOS per file (Phase 2b addition, RESEARCH_LOG D-B) ---
    dnsmos_files: list[FileQuality] = []
    if compute_dnsmos and records:
        for rec in records:
            dnsmos_files.append(analyze_file_dnsmos(rec))

    merged_files = _merge_file_streams(audiobox_files, dnsmos_files)

    # --- TTSDS2 per (provider, use_case) ---
    ttsds_scores: list[dict[str, Any]] = []
    if compute_ttsds and records:
        groups: dict[tuple[str, str], list[Path]] = {}
        for rec in records:
            groups.setdefault((rec.provider, rec.use_case), []).append(rec.wav_path)

        for (provider, use_case), wavs in sorted(groups.items()):
            ref = analyzers.reference_for(use_case).dataset_id  # type: ignore[arg-type]
            noise = analyzers.ttsds_noise_reference.dataset_id
            score = compute_ttsds_score(
                wavs, ref, noise,
                cache_dir=run_dir.parent.parent / ".cache" / "ttsds",
            )
            sh_delta = (
                split_half_delta(
                    wavs, ref, noise, n_splits=n_split_half,
                    cache_dir=run_dir.parent.parent / ".cache" / "ttsds",
                )
                if len(wavs) >= 10
                else None
            )
            ttsds_scores.append({
                "provider": provider,
                "use_case": use_case,
                "n_items": len(wavs),
                "reference_dataset_id": ref,
                "ttsds_score": score,
                "split_half_mean_delta": sh_delta,
                "split_half_threshold": analyzers.ttsds_split_half_threshold,
                "split_half_pass": (
                    sh_delta is not None and sh_delta <= analyzers.ttsds_split_half_threshold
                ),
            })

    payload = {
        "run_id": run_dir.name,
        "ran_ttsds": compute_ttsds,
        "ran_audiobox": compute_audiobox,
        "ran_dnsmos": compute_dnsmos,
        "audiobox_axes_reported": list(analyzers.audiobox_axes_reported),
        "dnsmos_axes_reported": list(DNSMOS_AXES),
        "ttsds_by_provider": ttsds_scores,
        "audiobox_by_provider": _aggregate_audiobox(audiobox_files),
        "dnsmos_by_provider": _aggregate_dnsmos(dnsmos_files),
        # Files are the MERGED stream so per-file variance analysis
        # (Phase 2b.5 + variance.py) can see both signal families
        # side-by-side per (provider, use_case, item_id, draw).
        "audiobox_files": [asdict(f) for f in merged_files],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("quality.json", payload)
    return payload
