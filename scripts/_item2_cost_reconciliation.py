"""Item 2: reconcile experiment-pack spend from api_log.jsonl files."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

LOGS = Path("analysis/experiments-2026-09-01/logs")
# Also latency runs from today
LATENCY_RUNS = sorted(Path("runs").glob("latency-20260901T*"))


def _cost_from_apilog(path: Path) -> tuple[int, float, dict[str, tuple[int, float]]]:
    """Return (n_ok_rows, total_usd, per_provider={provider: (n, usd)}).

    Experiment logs (A/B/C/E) don't set a `status` field — success is
    inferred from presence of a positive audio_bytes count. Failure rows
    have an `error` key and audio_bytes is missing.
    Campaign / latency logs use the canonical status="ok" contract.
    """
    rows = 0
    total = 0.0
    per_provider: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    if not path.exists():
        return 0, 0.0, {}
    for line in path.open("r", encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        # Explicit failure filter — either status != "ok" OR an error key OR no audio
        status = r.get("status")
        if r.get("error"):
            continue
        if status is not None and status != "ok":
            continue
        if not r.get("audio_bytes"):
            continue
        rows += 1
        usd = r.get("estimated_call_usd", 0) or 0
        if not usd:
            provider = r.get("provider", "")
            chars = r.get("chars_billed") or r.get("n_chars", 0) or 0
            usd = _approx_usd(provider, chars)
        prov = r.get("provider", "?")
        per_provider[prov][0] += 1
        per_provider[prov][1] += usd
        total += usd
    return rows, total, {p: tuple(v) for p, v in per_provider.items()}


# Pricing rates from configs/pricing.yaml (per 1M chars / bytes / etc)
# Fish paid tier is per_1M_bytes but "bytes" ≈ UTF-8 input characters
# for English text. So we use the chars count for approximation.
def _approx_usd(provider: str, chars: int) -> float:
    rates = {
        "openai":     15.0,    # tts-1-hd, per 1M chars
        "elevenlabs": 180.0,   # ~$22/121K credits Creator plan effective
        "deepgram":   15.0,    # Aura-2, per 1M chars
        "google":     16.0,    # Chirp3-HD, per 1M chars
        "cartesia":   15.0,    # Sonic-2, per 1M chars
        "fish":       15.0,    # paid s2.1-pro, per 1M bytes (~chars for English)
        "speechify":  100.0,   # Starter plan effective per 1M chars
    }
    if provider == "orpheus":
        return 0.003  # per_generation
    r = rates.get(provider)
    if r is None:
        return 0.0
    return chars * r / 1_000_000


def main():
    print("# Item 2 — Cost reconciliation from api_logs\n")

    # === Experiment API logs (A, B, C, E) ===
    print("## Experiment logs (A, B, C, E)\n")
    print("| experiment | rows | total USD | per-provider |")
    print("|---|---:|---:|---|")
    grand_total = 0.0
    grand_rows = 0
    for exp in ["A", "B", "C", "E"]:
        p = LOGS / f"{exp}_api_log.jsonl"
        n, usd, per_prov = _cost_from_apilog(p)
        per_str = ", ".join(f"{prov}={v[0]}({v[1]:.4f})" for prov, v in per_prov.items())
        print(f"| {exp} | {n} | ${usd:.4f} | {per_str} |")
        grand_total += usd
        grand_rows += n

    print(f"\n**Experiments subtotal (A+B+C+E)**: {grand_rows} rows, **${grand_total:.4f}**\n")

    # === D latency runs (today) ===
    print("## D latency runs (2026-09-01)\n")
    print("| run | rows | total USD | provider |")
    print("|---|---:|---:|---|")
    d_total = 0.0
    d_rows = 0
    for run_dir in LATENCY_RUNS:
        p = run_dir / "api_log.jsonl"
        n, usd, per_prov = _cost_from_apilog(p)
        provider = list(per_prov.keys())[0] if per_prov else "?"
        # Sum reported USD from the latency api log (has estimated_call_usd)
        print(f"| {run_dir.name} | {n} | ${usd:.4f} | {provider} |")
        d_total += usd
        d_rows += n

    print(f"\n**D subtotal (4 latency runs)**: {d_rows} rows, **${d_total:.4f}**\n")

    # === Grand total ===
    print("## Grand total\n")
    print(f"- Experiments A+B+C+E: {grand_rows} rows, **${grand_total:.4f}**")
    print(f"- D latency S4+S5: {d_rows} rows, **${d_total:.4f}**")
    print(f"- **Total experiment pack spend: {grand_rows + d_rows} rows, ${grand_total + d_total:.4f}**")


if __name__ == "__main__":
    main()
