"""Latency S4+S5 summary vs the F-11 session-to-session data."""
import json
import glob
import statistics
from collections import defaultdict


def _percentile(values, p):
    vs = sorted(values)
    if not vs:
        return None
    idx = min(int(p * len(vs)), len(vs) - 1)
    return vs[idx]


# Historical sessions
HIST = {
    "elevenlabs": {
        "S1a (2026-08-09 21:41)": (439, 479, 50),
        "S1b (2026-08-09 22:23)": (440, 474, 50),
        "S2  (2026-08-11)":       (424, 469, 40),
        "S3  (2026-08-12)":       (694, 816, 40),
    },
    "openai": {
        "S1a (2026-08-09 21:41)": (736, 956, 50),
        "S1b (2026-08-09 22:23)": (762, 946, 50),
        "S2  (2026-08-11)":       (936, 1493, 50),
        "S3  (2026-08-12)":       (1369, 1882, 50),
    },
}

# New sessions today (S4 + S5)
new_sessions = defaultdict(list)
for r in sorted(glob.glob("runs/latency-20260901*/api_log.jsonl")):
    rows = [json.loads(l) for l in open(r, encoding="utf-8")]
    provider = rows[0]["provider"]
    ttfa = [row.get("ttfa_ms") for row in rows if row.get("ttfa_ms") is not None]
    p50 = _percentile(ttfa, 0.5)
    p90 = _percentile(ttfa, 0.9)
    run_dir = r.replace("\\", "/").split("/")[-2]
    ts = run_dir.split("T")[1][:6]  # HHMMSS
    new_sessions[provider].append((f"S? ({ts}Z)", int(round(p50)) if p50 else None, int(round(p90)) if p90 else None, len(ttfa)))

# Assign S4/S5 by ordering within provider
for provider, sessions in new_sessions.items():
    sessions.sort()  # chronological
    for i, s in enumerate(sessions):
        label = "S4" if i == 0 else "S5" if i == 1 else f"S{i+4}"
        new_sessions[provider][i] = (f"{label} ({s[0].split('(')[1]}", s[1], s[2], s[3])

print("# D — 2 more latency sessions (S4 + S5) on 2026-09-01\n")
print("Note: S4 and S5 both landed the same day (2026-09-01), separated by ~1 hour.")
print("Per F-11's methodology note, characterising session-to-session variance properly needs")
print("≥5 sessions across ≥2 weeks. S4+S5 on the same day is a partial fulfillment; they add")
print("2 more data points to the 4 existing (S1a, S1b, S2, S3) for 6 total sessions per vendor.\n")

for provider in ["elevenlabs", "openai"]:
    print(f"## {provider}\n")
    print("| session | p50 (ms) | p90 (ms) | n |")
    print("|---|---:|---:|---:|")
    for label, (p50, p90, n) in HIST[provider].items():
        print(f"| {label} | {p50} | {p90} | {n} |")
    for label, p50, p90, n in new_sessions.get(provider, []):
        s5 = f"**{label}**"
        p50s = f"**{p50}**" if p50 is not None else "-"
        p90s = f"**{p90}**" if p90 is not None else "-"
        print(f"| {s5} | {p50s} | {p90s} | {n} |")
    # Range across all 6 sessions
    all_p50 = [v[0] for v in HIST[provider].values()] + [v[1] for v in new_sessions.get(provider, []) if v[1] is not None]
    all_p90 = [v[1] for v in HIST[provider].values()] + [v[2] for v in new_sessions.get(provider, []) if v[2] is not None]
    if all_p50 and all_p90:
        lo, hi = min(all_p50), max(all_p50)
        pct = (hi - lo) / lo * 100
        print(f"\n**{provider} p50 range across 6 sessions**: {lo} – {hi} ms (spread = {pct:.0f}% of the low value)")
        lo90, hi90 = min(all_p90), max(all_p90)
        pct90 = (hi90 - lo90) / lo90 * 100
        print(f"**{provider} p90 range across 6 sessions**: {lo90} – {hi90} ms (spread = {pct90:.0f}% of the low value)")
    print()
