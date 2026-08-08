"""Regression tests for cost.py.

Cost projections must respect: included allowance, minimum monthly, and
unit type (per-char vs per-generation). Getting any of these wrong
skews the D6 frontier axis and misranks providers by 1-2 orders of
magnitude — the whole "cost dominates quality differences" story
depends on this arithmetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from veval.analyze.common import AnalysisWriter
from veval.analyze.cost import (
    CHARS_PER_WORD,
    _monthly_cost,
    _pick_tier,
    analyze_provider,
    run,
)
from veval.config import PricingCell, load_pricing


# --- unit maths ---------------------------------------------------------


def _cell(**kw: object) -> PricingCell:
    defaults = dict(
        provider="faux",
        tier="paid",
        unit="per_1M_chars",
        rate_usd=30.0,
        source_url="https://example.com",
        date_verified="2026-08-08",
    )
    defaults.update(kw)
    return PricingCell.model_validate(defaults)


def test_monthly_cost_per_million_chars_no_floor() -> None:
    cell = _cell(rate_usd=15.0, minimum_monthly_usd=0.0)
    # 100K words × 5 chars/word = 500K chars → $7.50
    got = _monthly_cost(cell, 100_000, avg_chars_per_generation=250)
    assert got == pytest.approx(7.5, rel=0.001)


def test_monthly_cost_respects_minimum_when_under_allowance() -> None:
    cell = _cell(
        rate_usd=10.0,
        included_units_per_month=1_000_000,
        minimum_monthly_usd=10.0,
    )
    # 100K words × 5 chars = 500K chars, well inside the 1M allowance
    # → variable = $0, minimum floor = $10
    got = _monthly_cost(cell, 100_000, avg_chars_per_generation=250)
    assert got == pytest.approx(10.0)


def test_monthly_cost_includes_overage_above_minimum() -> None:
    cell = _cell(
        rate_usd=10.0,
        included_units_per_month=1_000_000,
        minimum_monthly_usd=10.0,
    )
    # 1M words × 5 chars = 5M chars → 4M billable × $10/1M = $40
    got = _monthly_cost(cell, 1_000_000, avg_chars_per_generation=250)
    assert got == pytest.approx(40.0)


def test_monthly_cost_per_generation_uses_avg_chars() -> None:
    cell = _cell(unit="per_generation", rate_usd=0.003)
    # 100K words / (500 chars per gen / 5 chars/word) = 100K / 100 = 1000 gens × $0.003 = $3.00
    got = _monthly_cost(cell, 100_000, avg_chars_per_generation=500)
    assert got == pytest.approx(3.0)


def test_pick_tier_default_prefers_paid_over_free() -> None:
    free = _cell(tier="free", rate_usd=0.0)
    paid = _cell(tier="paid", rate_usd=15.0)
    got = _pick_tier([free, paid])
    assert got.tier == "paid"


def test_pick_tier_prefer_free_hint() -> None:
    free = _cell(tier="free", rate_usd=0.0)
    paid = _cell(tier="paid", rate_usd=15.0)
    got = _pick_tier([free, paid], preference="prefer_free")
    assert got.tier == "free"


# --- analyze_provider (observed cost from api_log) --------------------


def test_analyze_provider_per_char_cost_matches_log(tmp_path: Path) -> None:
    pricing_yaml = tmp_path / "pricing.yaml"
    pricing_yaml.write_text(
        yaml.safe_dump(
            {
                "pricing": [
                    {
                        "provider": "faux",
                        "tier": "paid",
                        "unit": "per_1M_chars",
                        "rate_usd": 30.0,
                        "source_url": "https://ex",
                        "date_verified": "2026-08-08",
                    }
                ]
            }
        )
    )
    pricing = load_pricing(pricing_yaml)
    api_log = [
        {"provider": "faux", "status": "ok", "chars_billed": 1000},
        {"provider": "faux", "status": "ok", "chars_billed": 2000},
        # error row is excluded
        {"provider": "faux", "status": "error", "chars_billed": 500},
    ]
    pc = analyze_provider("faux", api_log, pricing)
    assert pc.observed_units == 3000
    assert pc.observed_generations == 2
    # 3000 chars × $30/1M = $0.09
    assert pc.observed_cost_usd == pytest.approx(0.09, rel=0.001)


def test_analyze_provider_per_generation_counts_calls(tmp_path: Path) -> None:
    pricing_yaml = tmp_path / "pricing.yaml"
    pricing_yaml.write_text(
        yaml.safe_dump(
            {
                "pricing": [
                    {
                        "provider": "orpheus",
                        "tier": "replicate_l40s",
                        "unit": "per_generation",
                        "rate_usd": 0.003,
                        "source_url": "https://ex",
                        "date_verified": "2026-08-08",
                    }
                ]
            }
        )
    )
    pricing = load_pricing(pricing_yaml)
    api_log = [{"provider": "orpheus", "status": "ok", "chars_billed": 100} for _ in range(5)]
    pc = analyze_provider("orpheus", api_log, pricing)
    assert pc.observed_generations == 5
    assert pc.observed_cost_usd == pytest.approx(0.015, rel=0.001)


# --- end-to-end run() ---------------------------------------------------


def test_run_writes_cost_model_json(tmp_path: Path) -> None:
    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "campaign"}))
    api_log = [
        {"provider": "faux", "use_case": "conversational", "item_id": "S01",
         "draw": 0, "status": "ok", "chars_billed": 1000,
         "audio_path": "audio/faux/S01.wav"},
    ]
    (run_dir / "audio" / "faux" / "S01.wav").write_bytes(b"RIFF" + b"\x00" * 40)  # dummy
    (run_dir / "api_log.jsonl").write_text(json.dumps(api_log[0]) + "\n")

    pricing_yaml = tmp_path / "pricing.yaml"
    pricing_yaml.write_text(
        yaml.safe_dump(
            {
                "pricing": [
                    {
                        "provider": "faux",
                        "tier": "paid",
                        "unit": "per_1M_chars",
                        "rate_usd": 30.0,
                        "source_url": "https://ex",
                        "date_verified": "2026-08-08",
                    }
                ]
            }
        )
    )

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, pricing_path=pricing_yaml, writer=writer)

    assert payload["total_observed_cost_usd"] == pytest.approx(0.03, rel=0.001)
    assert len(payload["providers"]) == 1
    pc = payload["providers"][0]
    assert pc["provider"] == "faux"
    assert pc["dollars_per_1k_words_at"]["100K_words_per_month"] == pytest.approx(0.15, rel=0.001)
    out = tmp_path / "analysis" / run_dir.name / "cost_model.json"
    assert out.exists()


def test_chars_per_word_constant_is_five() -> None:
    """English averages ~5 chars/word incl spaces — this is a load-bearing
    constant for the frontier chart. Changing it silently would shift
    every provider's $/1K-word number.
    """
    assert CHARS_PER_WORD == 5.0
