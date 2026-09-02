"""Item 3: latency sanity check on D S4+S5.

- Ranking hold? (ElevenLabs faster than OpenAI in each session)
- Per-session within-run variance (SD of TTFA across the 50 trials)
- Cross-session mean shift vs S1-S3
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def _percentile(values, p):
    vs = sorted(values)
    if not vs:
        return None
    idx = min(int(p * len(vs)), len(vs) - 1)
    return vs[idx]


def _summarise(rows):
    ttfa = [r.get("ttfa_ms") for r in rows if r.get("ttfa_ms") is not None]
    if not ttfa:
        return None
    return {
        "n": len(ttfa),
        "p50": _percentile(ttfa, 0.5),
        "p90": _percentile(ttfa, 0.9),
        "min": min(ttfa),
        "max": max(ttfa),
        "mean": statistics.mean(ttfa),
        "sd": statistics.stdev(ttfa) if len(ttfa) > 1 else 0,
    }


# All known sessions
SESSIONS = {
    "elevenlabs": {
        "S1a (2026-08-09 21:41)": {"p50": 439, "p90": 479, "n": 50},
        "S1b (2026-08-09 22:23)": {"p50": 440, "p90": 474, "n": 50},
        "S2  (2026-08-11)":       {"p50": 424, "p90": 469, "n": 40},
        "S3  (2026-08-12)":       {"p50": 694, "p90": 816, "n": 40},
    },
    "openai": {
        "S1a (2026-08-09 21:41)": {"p50": 736, "p90": 956, "n": 50},
        "S1b (2026-08-09 22:23)": {"p50": 762, "p90": 946, "n": 50},
        "S2  (2026-08-11)":       {"p50": 936, "p90": 1493, "n": 50},
        "S3  (2026-08-12)":       {"p50": 1369, "p90": 1882, "n": 50},
    },
}

# Load S4+S5 from today's runs
today = sorted(Path("runs").glob("latency-20260901T*"))
for run_dir in today:
    rows = [json.loads(l) for l in (run_dir / "api_log.jsonl").open(encoding="utf-8")]
    provider = rows[0]["provider"]
    stats = _summarise(rows)
    ts = run_dir.name.split("T")[1][:6]
    SESSIONS.setdefault(provider, {})[f"S? (2026-09-01 {ts[:2]}:{ts[2:4]})"] = stats


def print_ranking_table():
    print("## Ranking hold across all 6 sessions")
    print("For each session, is ElevenLabs faster than OpenAI (both p50 AND p90)?\n")
    print("| session date | EL p50 | OA p50 | EL p90 | OA p90 | ranking (EL < OA)? |")
    print("|---|---:|---:|---:|---:|:---:|")
    # Group by date-ish label
    el = SESSIONS["elevenlabs"]
    oa = SESSIONS["openai"]
    el_labels = sorted(el.keys())
    oa_labels = sorted(oa.keys())
    for i, elab in enumerate(el_labels):
        olab = oa_labels[i] if i < len(oa_labels) else None
        e = el[elab]
        o = oa[olab] if olab else {}
        e50 = e.get("p50")
        o50 = o.get("p50")
        e90 = e.get("p90")
        o90 = o.get("p90")
        hold_p50 = "✓" if e50 is not None and o50 is not None and e50 < o50 else "✗"
        hold_p90 = "✓" if e90 is not None and o90 is not None and e90 < o90 else "✗"
        print(f"| {elab.split(' (')[1].rstrip(')')} | {e50:.0f} | {o50:.0f} | {e90:.0f} | {o90:.0f} | p50={hold_p50} / p90={hold_p90} |")


def print_within_run_variance():
    print("\n## Within-run TTFA variance for today's S4+S5")
    print("Higher SD = more jitter within the 50-trial session itself.\n")
    print("| run | provider | n | p50 | p90 | mean | SD | min | max |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run_dir in today:
        rows = [json.loads(l) for l in (run_dir / "api_log.jsonl").open(encoding="utf-8")]
        provider = rows[0]["provider"]
        s = _summarise(rows)
        if not s:
            continue
        print(f"| {run_dir.name} | {provider} | {s['n']} | {s['p50']:.0f} | {s['p90']:.0f} | {s['mean']:.1f} | {s['sd']:.1f} | {s['min']:.0f} | {s['max']:.0f} |")


def print_cross_session_shift():
    print("\n## Cross-session mean p50 shift (S4+S5 vs S1-S3)")
    for provider in ["elevenlabs", "openai"]:
        pre_labels = [k for k in SESSIONS[provider].keys() if "2026-08" in k]
        new_labels = [k for k in SESSIONS[provider].keys() if "2026-09" in k]
        pre_p50 = [SESSIONS[provider][k]["p50"] for k in pre_labels]
        new_p50 = [SESSIONS[provider][k]["p50"] for k in new_labels]
        pre_mean = statistics.mean(pre_p50) if pre_p50 else None
        new_mean = statistics.mean(new_p50) if new_p50 else None
        if pre_mean and new_mean:
            delta = new_mean - pre_mean
            pct = delta / pre_mean * 100
            print(f"\n**{provider}**")
            print(f"- Pre (S1a/S1b/S2/S3, n={len(pre_p50)}) mean p50: {pre_mean:.1f} ms")
            print(f"- New (S4/S5, n={len(new_p50)}) mean p50: {new_mean:.1f} ms")
            print(f"- Shift: {delta:+.1f} ms ({pct:+.1f}%)")
            print(f"- Without S3 outlier: {statistics.mean([p for p in pre_p50 if p < 1000]):.1f} ms  →  new is {'higher' if new_mean > statistics.mean([p for p in pre_p50 if p < 1000]) else 'lower'} than pre-S3 baseline")


if __name__ == "__main__":
    print("# Item 3 — Latency S4+S5 sanity check\n")
    print_ranking_table()
    print_within_run_variance()
    print_cross_session_shift()
