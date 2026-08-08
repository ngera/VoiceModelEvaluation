"""Cost analyzer — pricing.yaml × logged character counts → cost_model.json.

Plan v2 line 297: "$/1K words at 10K / 100K / 1M words per month, plus
$/session." Cost is a frontier axis (D6) and must regenerate on the
drift re-run (per plan) — hence code, not a spreadsheet.

Model per provider:
    - Pick the tier that a buyer would deploy for our two archetypes. If
      pricing.yaml has multiple tiers, we prefer paid > monthly plan >
      free, matching how a portfolio buyer actually scales up. Fish is
      the special case (D-004): free for quality, paid for latency —
      the caller can pass `tier_hint` to override the default.
    - Compute observed_cost_usd from the campaign's actual chars_billed.
    - Project monthly cost at 10K / 100K / 1M words × 5 chars/word
      (English ≈ 5 chars/word incl. spaces), respecting included
      allowance, minimum monthly, and per-request fee.
    - Emit dollars-per-1K-words so provider comparisons are per-unit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from veval.config import PricingCell, PricingFile, load_pricing

from .common import AnalysisWriter, RunReader

CHARS_PER_WORD = 5.0

TierPref = Literal["default", "prefer_free", "prefer_paid"]


@dataclass
class ProviderCost:
    provider: str
    tier_used: str
    unit: str
    rate_usd: float
    minimum_monthly_usd: float
    included_units_per_month: float | None
    per_request_fee_usd: float
    observed_units: int  # chars OR generations, per `unit`
    observed_generations: int
    observed_cost_usd: float
    dollars_per_1k_words_at: dict[str, float] = field(default_factory=dict)
    monthly_usd_at: dict[str, float] = field(default_factory=dict)
    note: str = ""


def _pick_tier(cells: list[PricingCell], preference: TierPref = "default") -> PricingCell:
    """Choose the tier for a provider.

    Default preference: paid over free (a buyer at any real volume is
    on a paid tier); if there's a monthly plan with an included
    allowance, that wins over pure per-unit paid. If nothing matches,
    return the first cell — pricing.yaml is authoritative and empty
    lists are impossible.
    """
    if not cells:
        raise ValueError("pricing.yaml has no cells for this provider")

    def score(c: PricingCell) -> int:
        s = 0
        if preference == "prefer_free":
            s += -100 if c.tier == "free" else 0
        elif preference == "prefer_paid":
            s += -100 if c.tier != "free" else 0
        else:  # default
            if c.tier == "free":
                s += 10
            if "monthly" in c.tier:
                s -= 5
            # everything else: paid > monthly
        return s

    return sorted(cells, key=score)[0]


def _monthly_cost(
    cell: PricingCell,
    words_per_month: float,
    avg_chars_per_generation: float,
) -> float:
    """Compute a buyer's monthly cost at the given volume.

    Unit semantics from pricing.yaml — the `unit` field disambiguates.
    Included allowance is subtracted from the billable amount but a
    provider's `minimum_monthly_usd` still applies (that's the point of
    a subscription floor).
    """
    chars = words_per_month * CHARS_PER_WORD
    per_request = words_per_month * CHARS_PER_WORD / max(avg_chars_per_generation, 1.0)

    included = cell.included_units_per_month or 0.0

    if cell.unit in ("per_1M_chars", "per_1M_bytes"):
        billable = max(0.0, chars - included)
        variable = billable * cell.rate_usd / 1_000_000
    elif cell.unit == "per_1M_seconds":
        # Rough proxy — 1 word ≈ 0.35s spoken (spec A.6-adjacent). Kept
        # here so a provider that bills by audio seconds gets a number
        # rather than crashing; refined on drift re-run if needed.
        seconds = words_per_month * 0.35
        billable = max(0.0, seconds - included)
        variable = billable * cell.rate_usd / 1_000_000
    elif cell.unit == "per_generation":
        billable = max(0.0, per_request - included)
        variable = billable * cell.rate_usd
    elif cell.unit == "per_1M_tokens":
        # Tokens ≈ 4 chars for English (OpenAI rule of thumb)
        tokens = chars / 4.0
        billable = max(0.0, tokens - included)
        variable = billable * cell.rate_usd / 1_000_000
    else:
        raise ValueError(f"Unknown pricing unit: {cell.unit}")

    fees = per_request * cell.per_request_fee_usd
    return max(cell.minimum_monthly_usd, variable + fees)


def _observed(
    api_log: list[dict[str, Any]],
    provider: str,
    cell: PricingCell,
) -> tuple[int, int, float]:
    """(units_used, generations, dollars) from actual api_log rows.

    `units_used` is chars for char-based providers and generation-count
    for per_generation providers.
    """
    rows = [
        r for r in api_log
        if r.get("provider") == provider and r.get("status") == "ok"
    ]
    chars = sum(int(r.get("chars_billed", 0) or 0) for r in rows)
    generations = len(rows)

    if cell.unit in ("per_1M_chars", "per_1M_bytes"):
        observed_units = chars
        observed_cost = chars * cell.rate_usd / 1_000_000
    elif cell.unit == "per_generation":
        observed_units = generations
        observed_cost = generations * cell.rate_usd
    elif cell.unit == "per_1M_tokens":
        observed_units = chars // 4
        observed_cost = (chars / 4.0) * cell.rate_usd / 1_000_000
    elif cell.unit == "per_1M_seconds":
        # Can't observe audio seconds without decoding every file here;
        # approximate from chars.
        observed_units = int(chars * 0.35 / CHARS_PER_WORD)
        observed_cost = observed_units * cell.rate_usd / 1_000_000
    else:
        observed_units = chars
        observed_cost = 0.0

    return observed_units, generations, observed_cost


def analyze_provider(
    provider: str,
    api_log: list[dict[str, Any]],
    pricing: PricingFile,
    preference: TierPref = "default",
) -> ProviderCost:
    cells = pricing.for_provider(provider)
    if not cells:
        raise KeyError(f"No pricing cells for provider `{provider}`")
    cell = _pick_tier(cells, preference)

    units, generations, observed_cost = _observed(api_log, provider, cell)

    # Average chars/generation for per-request-fee and per_generation math
    avg_chars = (units / generations) if (
        cell.unit in ("per_1M_chars", "per_1M_bytes") and generations > 0
    ) else CHARS_PER_WORD * 100  # 100-word default session for per_generation providers

    projections = {
        "10K_words_per_month": _monthly_cost(cell, 10_000, avg_chars),
        "100K_words_per_month": _monthly_cost(cell, 100_000, avg_chars),
        "1M_words_per_month": _monthly_cost(cell, 1_000_000, avg_chars),
    }
    # $/1K words = monthly / (words_in_thousands)
    dollars_per_1k_words = {
        "10K_words_per_month": projections["10K_words_per_month"] / 10.0,
        "100K_words_per_month": projections["100K_words_per_month"] / 100.0,
        "1M_words_per_month": projections["1M_words_per_month"] / 1000.0,
    }

    return ProviderCost(
        provider=provider,
        tier_used=cell.tier,
        unit=cell.unit,
        rate_usd=cell.rate_usd,
        minimum_monthly_usd=cell.minimum_monthly_usd,
        included_units_per_month=cell.included_units_per_month,
        per_request_fee_usd=cell.per_request_fee_usd,
        observed_units=units,
        observed_generations=generations,
        observed_cost_usd=round(observed_cost, 4),
        dollars_per_1k_words_at=dollars_per_1k_words,
        monthly_usd_at=projections,
        note=cell.notes,
    )


def run(
    run_dir: Path,
    *,
    pricing_path: Path,
    tier_hints: dict[str, TierPref] | None = None,
    writer: AnalysisWriter | None = None,
) -> dict[str, Any]:
    """Compute cost projections for one run dir. Writes `cost_model.json`."""
    pricing = load_pricing(pricing_path)
    reader = RunReader(run_dir)
    api_log = list(reader.api_log())
    tier_hints = tier_hints or {}

    providers_in_run = sorted({row["provider"] for row in api_log if "provider" in row})
    provider_costs = [
        analyze_provider(
            provider=p,
            api_log=api_log,
            pricing=pricing,
            preference=tier_hints.get(p, "default"),
        )
        for p in providers_in_run
    ]

    payload = {
        "run_id": run_dir.name,
        "pricing_source": str(pricing_path),
        "chars_per_word_assumption": CHARS_PER_WORD,
        "total_observed_cost_usd": round(
            sum(pc.observed_cost_usd for pc in provider_costs), 4
        ),
        "providers": [asdict(pc) for pc in provider_costs],
    }
    if writer is None:
        writer = AnalysisWriter(run_dir.name)
    writer.write_json("cost_model.json", payload)
    return payload
