"""Variance analyzer — pooled within-provider SD → measurement noise floor.

Consumes a variance-mode run (10 items × 2 use cases × 3 draws × 8
providers = 480 generations post-roster-expansion). Also consumes the
associated WER + TTSDS2 outputs so per-provider SD is computed on the
same numbers the frontier uses. Byte-identity determinism check is a
pure function of the run store.

The output IS the noise floor per gates.yaml `measurement_noise_floor`:
    z_multiplier × SE(difference) = 1.96 × (SD / √n_items)

Applied per provider — pooling would export a noisy provider's variance
onto everyone else's comparisons (defect 3.19). Scope is EXPLICIT
(ttsds2, item_wer) so scope-drift can't silently expand what the noise
floor governs.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from veval.config import GatesFile

from .common import AnalysisWriter, RunReader


@dataclass
class ProviderVariance:
    provider: str
    use_case: str
    n_items: int
    n_draws: int
    # Per-metric within-provider SD across draws, averaged over items
    within_sd: dict[str, float] = field(default_factory=dict)
    # Noise floor = 1.96 × (SD / √n_items) for each metric
    noise_floor: dict[str, float] = field(default_factory=dict)
    deterministic: bool = False
    identical_across_draws_fraction: float = 0.0


def _wav_hashes_by_key(
    reader: RunReader,
) -> dict[tuple[str, str, str], list[str]]:
    """Return {(provider, use_case, item_id): [sha256 per draw]}.

    Same triple across draws with identical hashes → deterministic
    generation for that item. Used for D8 determinism flagging.
    """
    hashes: dict[tuple[str, str, str], list[str]] = {}
    for record in reader.records():
        key = (record.provider, record.use_case, record.item_id)
        try:
            h = hashlib.sha256(record.wav_path.read_bytes()).hexdigest()
        except OSError:
            continue
        hashes.setdefault(key, []).append(h)
    return hashes


def _load_json_if(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _within_provider_sd(
    per_item_per_draw: dict[str, list[float]],
) -> tuple[float | None, int]:
    """Given {item_id: [value_draw0, value_draw1, value_draw2, ...]},
    compute the pooled within-provider SD across items (root-mean-square
    of the per-item SDs). Returns (sd, n_items_with_variance).
    """
    per_item_sds: list[float] = []
    for _iid, draws in per_item_per_draw.items():
        clean = [v for v in draws if v is not None and math.isfinite(v)]
        if len(clean) < 2:
            continue
        per_item_sds.append(float(np.std(clean, ddof=1)))
    if not per_item_sds:
        return None, 0
    pooled = float(math.sqrt(sum(s * s for s in per_item_sds) / len(per_item_sds)))
    return pooled, len(per_item_sds)


def _noise_floor(sd: float | None, n_items: int, z: float) -> float | None:
    if sd is None or n_items == 0:
        return None
    return float(z * sd / math.sqrt(n_items))


def _extract_wer_by_item_by_draw(
    wer_payload: Any, provider: str, use_case: str
) -> dict[str, list[float]]:
    """Pull item_wer per draw for one (provider, use_case) from wer.json."""
    if not wer_payload:
        return {}
    by: dict[str, list[float]] = {}
    for row in wer_payload.get("items", []):
        if row["provider"] != provider or row["use_case"] != use_case:
            continue
        wer = row.get("agreement_wer")
        if wer is None:
            continue
        by.setdefault(row["item_id"], []).append(float(wer))
    return by


def run(
    run_dir: Path,
    *,
    gates: GatesFile,
    wer_analysis_path: Path | None = None,
    quality_analysis_path: Path | None = None,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Variance rollup. Reads run store + optional prior WER/quality outputs.

    Both wer/quality inputs are optional: missing = "we don't have that
    metric to compute a noise floor on yet"; the byte-identity check
    still runs from the run store alone.
    """
    reader = RunReader(run_dir)
    wer_payload = _load_json_if(wer_analysis_path) if wer_analysis_path else None
    quality_payload = _load_json_if(quality_analysis_path) if quality_analysis_path else None

    # Byte-identity: same item across draws → identical hash?
    hashes = _wav_hashes_by_key(reader)

    # Group by (provider, use_case) → distinct items
    per_provider: dict[tuple[str, str], dict[str, list[str]]] = {}
    for (provider, use_case, item_id), h_list in hashes.items():
        per_provider.setdefault((provider, use_case), {})[item_id] = h_list

    rollups: list[ProviderVariance] = []
    z = gates.measurement_noise_floor.z_multiplier
    for (provider, use_case), items in sorted(per_provider.items()):
        # Determinism: same-item-across-draws identical fraction
        identical = 0
        countable = 0
        for _iid, hs in items.items():
            if len(hs) < 2:
                continue
            countable += 1
            if all(h == hs[0] for h in hs):
                identical += 1
        det_frac = (identical / countable) if countable else 0.0

        n_items = len(items)
        n_draws = max((len(hs) for hs in items.values()), default=0)

        pv = ProviderVariance(
            provider=provider,
            use_case=use_case,
            n_items=n_items,
            n_draws=n_draws,
            deterministic=(countable > 0 and det_frac == 1.0),
            identical_across_draws_fraction=det_frac,
        )

        # WER SD → noise floor
        if wer_payload:
            wer_by_item = _extract_wer_by_item_by_draw(wer_payload, provider, use_case)
            sd, n = _within_provider_sd(wer_by_item)
            if sd is not None:
                pv.within_sd["item_wer"] = sd
                pv.noise_floor["item_wer"] = _noise_floor(sd, n, z) or 0.0

        # TTSDS2 SD → noise floor. TTSDS2 aggregates per-file rarely; the
        # only per-file signal in the current quality.json is Audiobox. So
        # for the first pass we compute SD on Audiobox PQ (per-file), and
        # leave a TODO for wiring per-file TTSDS2 when the analyzer emits it.
        if quality_payload:
            ab_by_item = _audiobox_by_item(quality_payload, provider, use_case)
            sd, n = _within_provider_sd(ab_by_item)
            if sd is not None:
                pv.within_sd["audiobox_pq"] = sd
                pv.noise_floor["audiobox_pq"] = _noise_floor(sd, n, z) or 0.0

        rollups.append(pv)

    payload = {
        "run_id": run_dir.name,
        "z_multiplier": z,
        "measurement_noise_floor_scope": gates.measurement_noise_floor.metrics,
        "by_provider": [asdict(r) for r in rollups],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("variance.json", payload)
    return payload


def _audiobox_by_item(
    quality_payload: Any, provider: str, use_case: str, axis: str = "production_quality"
) -> dict[str, list[float]]:
    if not quality_payload:
        return {}
    by: dict[str, list[float]] = {}
    for f in quality_payload.get("audiobox_files", []):
        if f["provider"] != provider or f["use_case"] != use_case:
            continue
        val = f.get("audiobox", {}).get(axis)
        if val is None:
            continue
        by.setdefault(f["item_id"], []).append(float(val))
    return by
