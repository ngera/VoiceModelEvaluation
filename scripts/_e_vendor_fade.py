"""E per-vendor fade breakdown from drift.json."""
import json
from collections import defaultdict

d = json.load(open("analysis/experiments-2026-09-01/drift.json", encoding="utf-8"))
e = [x for x in d["items"] if "E_altvoice" in x["wav"]]

vf = defaultdict(lambda: [0, 0, []])
for x in e:
    v = x["wav"].replace(chr(92), "/").split("/")[-2]
    delta = x.get("delta_t1_t3")
    mono = x.get("monotonic_decreasing")
    fade = delta is not None and delta >= 2.0 and mono
    vf[v][0] += 1
    if fade:
        vf[v][1] += 1
        item = x["wav"].replace(chr(92), "/").split("/")[-1].replace(".wav", "")
        vf[v][2].append((item, delta))

print(f"{'vendor':12s}  {'fade/total':>12s}  {'fade_rate':>10s}  fading items")
print("-" * 100)
for v, (tot, fd, items) in sorted(vf.items()):
    pct = fd / tot * 100 if tot else 0
    it_str = ", ".join(f"{i} ({d:.2f}dB)" for i, d in items) if items else "-"
    print(f"  {v:11s}  {fd}/{tot:<9d}  {pct:>9.0f}%   {it_str}")
