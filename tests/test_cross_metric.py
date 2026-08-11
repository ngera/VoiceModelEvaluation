"""Regression tests for cross_metric.py.

Covers rank tie handling, matrix shape/symmetry, cross-pipeline pair
counting, and the end-to-end run() → cross_metric.json wire-up. No
model calls; fixtures are hand-built dicts mimicking quality.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veval.analyze import cross_metric
from veval.analyze.common import AnalysisWriter
from veval.analyze.cross_metric import SIGNALS, _rank_desc, run


def test_rank_desc_ties_get_average_rank() -> None:
    ranks = _rank_desc({"a": 5.0, "b": 5.0, "c": 4.0, "d": 3.0})
    assert ranks["a"] == 1.5
    assert ranks["b"] == 1.5
    assert ranks["c"] == 3.0
    assert ranks["d"] == 4.0


def test_rank_desc_best_gets_rank_one() -> None:
    ranks = _rank_desc({"x": 9.0, "y": 8.0, "z": 7.0})
    assert ranks["x"] == 1.0
    assert ranks["y"] == 2.0
    assert ranks["z"] == 3.0


def test_run_writes_cross_metric_json_with_expected_shape(tmp_path: Path) -> None:
    run_dir = tmp_path / "campaign-20260810T000000Z"
    (run_dir).mkdir()
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name}))
    (run_dir / "api_log.jsonl").write_text("")

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    quality_payload = {
        "audiobox_by_provider": [
            {"provider": p, "use_case": "conv", "n_valid": 10,
             "audiobox_means": {"production_quality": pq, "content_enjoyment": ce}}
            for p, pq, ce in [
                ("p1", 7.5, 6.1),
                ("p2", 7.2, 5.9),
                ("p3", 7.9, 6.3),
                ("p4", 7.0, 5.8),
            ]
        ],
        "dnsmos_by_provider": [
            {"provider": p, "use_case": "conv", "n_valid": 10,
             "dnsmos_means": {"p808_mos": p808, "ovrl_mos": ovrl,
                               "sig_mos": sig, "bak_mos": bak}}
            for p, p808, ovrl, sig, bak in [
                ("p1", 3.8, 3.3, 3.6, 4.1),
                ("p2", 3.7, 3.2, 3.5, 4.0),
                ("p3", 4.0, 3.5, 3.7, 4.2),
                ("p4", 3.6, 3.1, 3.4, 3.9),
            ]
        ],
    }
    (writer.dir / "quality.json").write_text(json.dumps(quality_payload))

    payload = run(run_dir, writer=writer)

    assert set(r["use_case"] for r in payload["by_use_case"]) == {"conv"}
    uc = payload["by_use_case"][0]
    assert uc["n_providers"] == 4

    # Spearman matrix is 6 × 6, symmetric, diagonal = 1.0
    m = uc["spearman_matrix"]
    signal_ids = [sid for sid, _, _ in SIGNALS]
    assert set(m.keys()) == set(signal_ids)
    for sid in signal_ids:
        assert set(m[sid].keys()) == set(signal_ids)
        assert m[sid][sid] == 1.0
    for a in signal_ids:
        for b in signal_ids:
            assert m[a][b] == pytest.approx(m[b][a])

    # Cross-pipeline pairs: 2 audiobox × 4 dnsmos = 8 pair correlations
    # collapsed into cross_pipeline_mean_rho. Fixture is monotone across
    # both pipelines (p3>p1>p2>p4), so cross-pipeline ρ should be ~1.0.
    assert uc["cross_pipeline_mean_rho"] == pytest.approx(1.0)

    # 15 unique unordered pairs of 6 signals
    assert len(uc["pairs"]) == 15


def test_run_writes_output_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "campaign-20260810T000001Z"
    run_dir.mkdir()
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name}))
    (run_dir / "api_log.jsonl").write_text("")

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    (writer.dir / "quality.json").write_text(json.dumps({
        "audiobox_by_provider": [],
        "dnsmos_by_provider": [],
    }))

    run(run_dir, writer=writer)
    out = tmp_path / "analysis" / run_dir.name / "cross_metric.json"
    assert out.exists()


def test_run_raises_without_quality_json(tmp_path: Path) -> None:
    run_dir = tmp_path / "campaign-20260810T000002Z"
    run_dir.mkdir()
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name}))
    (run_dir / "api_log.jsonl").write_text("")

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    with pytest.raises(FileNotFoundError):
        cross_metric.run(run_dir, writer=writer)
