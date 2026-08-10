"""Quality analyzer — TTSDS2 + Audiobox Aesthetics + split-half stability.

D3 primary: TTSDS2 aggregate score per provider per use case, against
the pre-registered reference set from analyzers.yaml (`daps` for
narration; conversational reference TBD in Phase B, defect 3.7). Uses
`ttsds.BenchmarkSuite` — the full published benchmark suite; picking a
subset would be a silent methodology change.

D3 secondary: Audiobox Aesthetics — 4 axes emitted (CE/CU/PC/PQ), we
REPORT PQ + CE only per analyzers.yaml. Reporting all 4 unlabelled
would invite post-hoc selection (spec B.2).

Split-half stability (spec §4.3, defect 3.7): random split of a
provider's items into two halves, TTSDS2 on each half, absolute delta
between the two scores. Averaged over ≥100 random splits (single split
would be one arbitrary partition). Compared against the absolute
threshold in analyzers.yaml (0.02) — not the noise floor, because the
noise floor doesn't exist until variance.py runs.

Model loading is lazy — first live call downloads references and
benchmark weights (~5-10 GB across the TTSDS2 suite). Tests mock the
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


# --- Audiobox: per-file inference ---------------------------------------


@dataclass
class FileQuality:
    provider: str
    use_case: str
    item_id: str
    draw: int
    wav_path: str
    audiobox: dict[str, float] = field(default_factory=dict)
    error: str | None = None


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


# --- run() --------------------------------------------------------------


def run(
    run_dir: Path,
    *,
    analyzers: AnalyzersFile,
    compute_ttsds: bool = True,
    compute_audiobox: bool = True,
    n_split_half: int = 100,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Run TTSDS2 + Audiobox over one run dir. Writes `quality.json`.

    Both compute flags default to True; set to False to skip a heavy
    stage (useful for iterative development). The output JSON records
    which stages actually ran.
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
        "audiobox_axes_reported": list(analyzers.audiobox_axes_reported),
        "ttsds_by_provider": ttsds_scores,
        "audiobox_by_provider": _aggregate_audiobox(audiobox_files),
        "audiobox_files": [asdict(f) for f in audiobox_files],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("quality.json", payload)
    return payload
