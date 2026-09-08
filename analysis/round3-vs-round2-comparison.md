# R2 (2026-08-09) vs R3 (2026-08-31) — replication comparison

- R2 run: `campaign-20260809T204608Z` — campaign-20260809T204608Z
- R3 run: `campaign-20260831T175358Z` — campaign-20260831T175358Z

## Cost totals
- R2 vs R3 `total_observed_cost_usd` agree to within 0.04% — expected,
  since modelled cost is `chars × rate` and both runs used the same
  corpus, so cost is not a replication signal (values in the committed
  `cost_model.json` files).
- Δ: **-0.0030** (-0.04%)

### Per-vendor observed cost (delta)
| Vendor | R2 $ | R3 $ | Δ$ | % change |
|---|---:|---:|---:|---:|
| cartesia | 1.5566 | 1.5566 | +0.0000 | +0.0% |
| deepgram | 1.1675 | 1.1675 | +0.0000 | +0.0% |
| elevenlabs | 1.9458 | 1.9458 | +0.0000 | +0.0% |
| fish | 0.5854 | 0.5854 | +0.0000 | +0.0% |
| google | 1.1675 | 1.1675 | +0.0000 | +0.0% |
| openai | 0.5837 | 0.5837 | +0.0000 | +0.0% |
| orpheus | 0.4500 | 0.4470¹ | -0.0030 | -0.7% |
| speechify | 0.3892 | 0.3892 | +0.0000 | +0.0% |

¹ Orpheus R3 = **149 generations, not 150** — one **conversational**
call failed in the R3 fresh run. `observed_generations = 149` and
`observed_cost_usd = $0.447` in
[`campaign-20260831T175358Z/cost_model.json`](campaign-20260831T175358Z/cost_model.json).
The -$0.003 R2→R3 delta is exactly one Orpheus generation at
$0.003/call, not a per-call price change. The **conversational**
quality tables handle the missing item as a missing draw in
aggregation; the Orpheus conversational per-vendor mean is over the
74 items that succeeded, and Orpheus narration is a full 75.
Confirmed in three independent analyzer outputs — `wer.json`,
`hygiene.json` and `quality.json` all report Orpheus R3 at
`n_items = 74` conversational / `75` narration. This is also why the
R3 campaign totals **1,199 files, not 1,200**; the R2 baseline is a
full 1,200.

### AB.PQ

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 7.437 | 7.459 | +0.023 | +0.3% |
| cartesia | narration | 7.986 | 7.995 | +0.009 | +0.1% |
| deepgram | conversational | 7.621 | 7.638 | +0.017 | +0.2% |
| deepgram | narration | 7.860 | 7.843 | -0.016 | -0.2% |
| elevenlabs | conversational | 7.755 | 7.681 | -0.074 | -1.0% |
| elevenlabs | narration | 7.929 | 7.855 | -0.074 | -0.9% |
| fish | conversational | 7.701 | 7.710 | +0.009 | +0.1% |
| fish | narration | 7.631 | 7.605 | -0.027 | -0.3% |
| google | conversational | 7.624 | 7.616 | -0.008 | -0.1% |
| google | narration | 7.966 | 7.954 | -0.011 | -0.1% |
| openai | conversational | 7.742 | 7.739 | -0.003 | -0.0% |
| openai | narration | 7.618 | 7.632 | +0.014 | +0.2% |
| orpheus | conversational | 7.405 | 7.441 | +0.036 | +0.5% |
| orpheus | narration | 8.002 | 7.992 | -0.010 | -0.1% |
| speechify | conversational | 7.897 | 7.880 | -0.017 | -0.2% |
| speechify | narration | 8.150 | 8.153 | +0.003 | +0.0% |

**Top-1 flip check (AB.PQ):**
  conversational: R2 #1 = speechify     R3 #1 = speechify   
  narration     : R2 #1 = speechify     R3 #1 = speechify   

**Rank stability (Spearman ρ R2 vs R3):**
  conversational: ρ = +0.905  (n=8 vendors)
  narration: ρ = +0.952  (n=8 vendors)

### AB.CE

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 5.961 | 5.963 | +0.002 | +0.0% |
| cartesia | narration | 6.324 | 6.342 | +0.018 | +0.3% |
| deepgram | conversational | 6.214 | 6.233 | +0.018 | +0.3% |
| deepgram | narration | 6.404 | 6.397 | -0.007 | -0.1% |
| elevenlabs | conversational | 5.957 | 5.912 | -0.045 | -0.8% |
| elevenlabs | narration | 6.466 | 6.418 | -0.048 | -0.7% |
| fish | conversational | 6.242 | 6.239 | -0.003 | -0.0% |
| fish | narration | 6.311 | 6.289 | -0.022 | -0.3% |
| google | conversational | 6.176 | 6.170 | -0.007 | -0.1% |
| google | narration | 6.437 | 6.437 | +0.000 | +0.0% |
| openai | conversational | 6.107 | 6.117 | +0.009 | +0.2% |
| openai | narration | 6.178 | 6.181 | +0.003 | +0.1% |
| orpheus | conversational | 6.012 | 6.042 | +0.030 | +0.5% |
| orpheus | narration | 6.259 | 6.247 | -0.012 | -0.2% |
| speechify | conversational | 6.462 | 6.451 | -0.011 | -0.2% |
| speechify | narration | 6.662 | 6.638 | -0.024 | -0.4% |

**Top-1 flip check (AB.CE):**
  conversational: R2 #1 = speechify     R3 #1 = speechify   
  narration     : R2 #1 = speechify     R3 #1 = speechify   

**Rank stability (Spearman ρ R2 vs R3):**
  conversational: ρ = +1.000  (n=8 vendors)
  narration: ρ = +0.976  (n=8 vendors)

### DN.p808

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 3.886 | 3.927 | +0.041 | +1.1% |
| cartesia | narration | 4.132 | 4.126 | -0.006 | -0.1% |
| deepgram | conversational | 3.772 | 3.778 | +0.006 | +0.2% |
| deepgram | narration | 4.073 | 4.063 | -0.010 | -0.2% |
| elevenlabs | conversational | 4.120 | 4.079 | -0.041 | -1.0% |
| elevenlabs | narration | 4.051 | 4.004 | -0.047 | -1.2% |
| fish | conversational | 3.859 | 3.864 | +0.006 | +0.1% |
| fish | narration | 4.123 | 4.150 | +0.027 | +0.7% |
| google | conversational | 3.819 | 3.786 | -0.033 | -0.9% |
| google | narration | 4.024 | 4.011 | -0.013 | -0.3% |
| openai | conversational | 4.006 | 4.022 | +0.016 | +0.4% |
| openai | narration | 3.984 | 3.979 | -0.005 | -0.1% |
| orpheus | conversational | 3.873 | 3.886 | +0.014 | +0.3% |
| orpheus | narration | 4.062 | 4.067 | +0.004 | +0.1% |
| speechify | conversational | 3.983 | 3.976 | -0.008 | -0.2% |
| speechify | narration | 4.049 | 4.047 | -0.002 | -0.1% |

**Top-1 flip check (DN.p808):**
  conversational: R2 #1 = elevenlabs    R3 #1 = elevenlabs  
  narration     : R2 #1 = cartesia      R3 #1 = fish          ⚠ FLIP

### DN.ovrl

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 3.253 | 3.260 | +0.006 | +0.2% |
| cartesia | narration | 3.197 | 3.235 | +0.038 | +1.2% |
| deepgram | conversational | 3.308 | 3.333 | +0.026 | +0.8% |
| deepgram | narration | 3.442 | 3.428 | -0.014 | -0.4% |
| elevenlabs | conversational | 3.467 | 3.456 | -0.011 | -0.3% |
| elevenlabs | narration | 3.337 | 3.314 | -0.022 | -0.7% |
| fish | conversational | 3.146 | 3.179 | +0.034 | +1.1% |
| fish | narration | 3.397 | 3.405 | +0.008 | +0.2% |
| google | conversational | 3.273 | 3.264 | -0.010 | -0.3% |
| google | narration | 3.354 | 3.341 | -0.013 | -0.4% |
| openai | conversational | 3.489 | 3.483 | -0.006 | -0.2% |
| openai | narration | 3.463 | 3.469 | +0.006 | +0.2% |
| orpheus | conversational | 3.328 | 3.316 | -0.012 | -0.4% |
| orpheus | narration | 3.453 | 3.461 | +0.008 | +0.2% |
| speechify | conversational | 3.295 | 3.316 | +0.020 | +0.6% |
| speechify | narration | 3.420 | 3.455 | +0.035 | +1.0% |

**Top-1 flip check (DN.ovrl):**
  conversational: R2 #1 = openai        R3 #1 = openai      
  narration     : R2 #1 = openai        R3 #1 = openai      

### DN.sig

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 3.481 | 3.486 | +0.005 | +0.2% |
| cartesia | narration | 3.454 | 3.479 | +0.024 | +0.7% |
| deepgram | conversational | 3.580 | 3.599 | +0.019 | +0.5% |
| deepgram | narration | 3.677 | 3.667 | -0.010 | -0.3% |
| elevenlabs | conversational | 3.686 | 3.680 | -0.006 | -0.2% |
| elevenlabs | narration | 3.614 | 3.600 | -0.014 | -0.4% |
| fish | conversational | 3.413 | 3.438 | +0.025 | +0.7% |
| fish | narration | 3.667 | 3.680 | +0.013 | +0.3% |
| google | conversational | 3.574 | 3.583 | +0.009 | +0.3% |
| google | narration | 3.603 | 3.596 | -0.007 | -0.2% |
| openai | conversational | 3.697 | 3.696 | -0.001 | -0.0% |
| openai | narration | 3.679 | 3.685 | +0.006 | +0.2% |
| orpheus | conversational | 3.618 | 3.606 | -0.012 | -0.3% |
| orpheus | narration | 3.643 | 3.650 | +0.008 | +0.2% |
| speechify | conversational | 3.564 | 3.568 | +0.004 | +0.1% |
| speechify | narration | 3.625 | 3.659 | +0.034 | +0.9% |

**Top-1 flip check (DN.sig):**
  conversational: R2 #1 = openai        R3 #1 = openai      
  narration     : R2 #1 = openai        R3 #1 = openai      

### DN.bak

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 4.130 | 4.133 | +0.003 | +0.1% |
| cartesia | narration | 4.051 | 4.090 | +0.039 | +1.0% |
| deepgram | conversational | 4.069 | 4.087 | +0.018 | +0.4% |
| deepgram | narration | 4.149 | 4.146 | -0.003 | -0.1% |
| elevenlabs | conversational | 4.180 | 4.174 | -0.007 | -0.2% |
| elevenlabs | narration | 4.072 | 4.052 | -0.020 | -0.5% |
| fish | conversational | 4.045 | 4.064 | +0.019 | +0.5% |
| fish | narration | 4.097 | 4.093 | -0.005 | -0.1% |
| google | conversational | 4.019 | 3.982 | -0.037 | -0.9% |
| google | narration | 4.108 | 4.094 | -0.014 | -0.3% |
| openai | conversational | 4.191 | 4.185 | -0.005 | -0.1% |
| openai | narration | 4.183 | 4.183 | +0.001 | +0.0% |
| orpheus | conversational | 4.104 | 4.104 | +0.000 | +0.0% |
| orpheus | narration | 4.213 | 4.213 | -0.000 | -0.0% |
| speechify | conversational | 4.066 | 4.101 | +0.034 | +0.8% |
| speechify | narration | 4.174 | 4.183 | +0.009 | +0.2% |

**Top-1 flip check (DN.bak):**
  conversational: R2 #1 = openai        R3 #1 = openai      
  narration     : R2 #1 = orpheus       R3 #1 = orpheus     

### WER (agreement mean)

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 0.1645 | 0.1490 | -0.015 | -9.4% |
| cartesia | narration | 0.1239 | 0.1285 | +0.005 | +3.7% |
| deepgram | conversational | 0.1665 | 0.1636 | -0.003 | -1.7% |
| deepgram | narration | 0.1350 | 0.1346 | -0.000 | -0.3% |
| elevenlabs | conversational | 0.1407 | 0.1472 | +0.007 | +4.6% |
| elevenlabs | narration | 0.1281 | 0.1302 | +0.002 | +1.7% |
| fish | conversational | 0.1378 | 0.1438 | +0.006 | +4.4% |
| fish | narration | 0.1399 | 0.1319 | -0.008 | -5.7% |
| google | conversational | 0.1512 | 0.1567 | +0.006 | +3.7% |
| google | narration | 0.1305 | 0.1328 | +0.002 | +1.8% |
| openai | conversational | 0.1370 | 0.1495 | +0.013 | +9.1% |
| openai | narration | 0.1330 | 0.1335 | +0.000 | +0.3% |
| orpheus | conversational | 0.2689 | 0.2637 | -0.005 | -1.9% |
| orpheus | narration | 0.2723 | 0.2746 | +0.002 | +0.8% |
| speechify | conversational | 0.1433 | 0.1403 | -0.003 | -2.1% |
| speechify | narration | 0.1302 | 0.1310 | +0.001 | +0.6% |

**Top-1 flip check (WER, lower is better):**
  conversational: R2 #1 = openai        R3 #1 = speechify     ⚠ FLIP
  narration     : R2 #1 = cartesia      R3 #1 = cartesia    

### WER failure_incidence_pct

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 66.7 | 65.3 | -1.333 | -2.0% |
| cartesia | narration | 62.7 | 62.7 | +0.000 | +0.0% |
| deepgram | conversational | 70.7 | 66.7 | -4.000 | -5.7% |
| deepgram | narration | 66.7 | 65.3 | -1.333 | -2.0% |
| elevenlabs | conversational | 62.7 | 68.0 | +5.333 | +8.5% |
| elevenlabs | narration | 65.3 | 64.0 | -1.333 | -2.0% |
| fish | conversational | 61.3 | 64.0 | +2.667 | +4.3% |
| fish | narration | 70.7 | 66.7 | -4.000 | -5.7% |
| google | conversational | 65.3 | 70.7 | +5.333 | +8.2% |
| google | narration | 65.3 | 65.3 | +0.000 | +0.0% |
| openai | conversational | 62.7 | 65.3 | +2.667 | +4.3% |
| openai | narration | 66.7 | 66.7 | +0.000 | +0.0% |
| orpheus | conversational | 73.3 | 78.4 | +5.045 | +6.9% |
| orpheus | narration | 73.3 | 76.0 | +2.667 | +3.6% |
| speechify | conversational | 61.3 | 65.3 | +4.000 | +6.5% |
| speechify | narration | 66.7 | 65.3 | -1.333 | -2.0% |

### DNSMOS coverage: n_valid per (vendor, use case)

Cells where R2 or R3 `n_valid < n_items = 75` — the DNSMOS
per-vendor means below are computed on the survivors, not the
full item set. Any R2↔R3 comparison for a vendor whose n_valid
differs across runs is **unpaired** — the two runs' means come
from different item subsets. Cartesia conversational is the
load-bearing case: 43 valid on R2 vs 51 on R3, so the R2↔R3 Δ
on Cartesia conv DNSMOS is a difference of unmatched subsets.

| Vendor | Use case | R2 n_valid | R3 n_valid | R2↔R3 paired? |
|---|---|---:|---:|---|
| cartesia | conversational | 43 | 51 | **no** (subsets differ by 8) |
| cartesia | narration | 38 | 37 | **no** (subsets differ by 1) |
| google | narration | 71 | 72 | approximately (differ by 1) |
| speechify | narration | 75 | 74 | approximately (differ by 1) |
| elevenlabs | conversational | 75 | 74 | approximately (differ by 1); this is the n=74 in F-12's conv DNSMOS row |

Pooled DNSMOS refusal rate (both use cases): **R2 = 46.0% (69/150)**;
**R3 = 41.3% (62/150)**. Every "46%" figure in the docs is R2;
R3 is 41.3% and travels alongside per row 168.

### Hygiene: total clipped samples

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 406 | 377 | -29.000 | -7.1% |
| cartesia | narration | 429 | 420 | -9.000 | -2.1% |
| deepgram | conversational | 0 | 0 | +0.000 | +0.0% |
| deepgram | narration | 0 | 0 | +0.000 | +0.0% |
| elevenlabs | conversational | 0 | 1 | +1.000 | +0.0% |
| elevenlabs | narration | 0 | 0 | +0.000 | +0.0% |
| fish | conversational | 0 | 0 | +0.000 | +0.0% |
| fish | narration | 0 | 0 | +0.000 | +0.0% |
| google | conversational | 0 | 0 | +0.000 | +0.0% |
| google | narration | 39 | 30 | -9.000 | -23.1% |
| openai | conversational | 0 | 0 | +0.000 | +0.0% |
| openai | narration | 0 | 0 | +0.000 | +0.0% |
| orpheus | conversational | 0 | 0 | +0.000 | +0.0% |
| orpheus | narration | 0 | 0 | +0.000 | +0.0% |
| speechify | conversational | 1 | 0 | -1.000 | -100.0% |
| speechify | narration | 5 | 12 | +7.000 | +140.0% |

### Hygiene: mean noise floor (dBFS)

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | -57.1 | -57.0 | +0.115 | -0.2% |
| cartesia | narration | -55.3 | -52.6 | +2.684 | -4.9% |
| deepgram | conversational | -46.2 | -46.1 | +0.028 | -0.1% |
| deepgram | narration | -46.8 | -46.9 | -0.060 | +0.1% |
| elevenlabs | conversational | -52.0 | -52.4 | -0.400 | +0.8% |
| elevenlabs | narration | -41.5 | -40.9 | +0.570 | -1.4% |
| fish | conversational | -39.7 | -38.5 | +1.144 | -2.9% |
| fish | narration | -46.6 | -47.9 | -1.356 | +2.9% |
| google | conversational | -33.7 | -32.9 | +0.797 | -2.4% |
| google | narration | -36.8 | -36.8 | +0.094 | -0.3% |
| openai | conversational | -52.5 | -51.5 | +0.944 | -1.8% |
| openai | narration | -54.5 | -55.1 | -0.592 | +1.1% |
| orpheus | conversational | -53.2 | -53.8 | -0.631 | +1.2% |
| orpheus | narration | -78.7 | -75.8 | +2.956 | -3.8% |
| speechify | conversational | -57.0 | -56.6 | +0.403 | -0.7% |
| speechify | narration | -55.2 | -58.4 | -3.159 | +5.7% |

### Hygiene: mean speech ratio

| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |
|---|---|---:|---:|---:|---:|
| cartesia | conversational | 0.886 | 0.888 | +0.002 | +0.2% |
| cartesia | narration | 0.894 | 0.891 | -0.002 | -0.3% |
| deepgram | conversational | 0.903 | 0.894 | -0.009 | -1.0% |
| deepgram | narration | 0.896 | 0.903 | +0.007 | +0.8% |
| elevenlabs | conversational | 0.938 | 0.931 | -0.007 | -0.7% |
| elevenlabs | narration | 0.924 | 0.923 | -0.001 | -0.1% |
| fish | conversational | 0.968 | 0.972 | +0.004 | +0.4% |
| fish | narration | 0.964 | 0.966 | +0.002 | +0.2% |
| google | conversational | 0.877 | 0.888 | +0.011 | +1.2% |
| google | narration | 0.862 | 0.862 | -0.000 | -0.0% |
| openai | conversational | 0.800 | 0.804 | +0.005 | +0.6% |
| openai | narration | 0.862 | 0.853 | -0.009 | -1.0% |
| orpheus | conversational | 0.749 | 0.739 | -0.010 | -1.3% |
| orpheus | narration | 0.901 | 0.899 | -0.001 | -0.2% |
| speechify | conversational | 0.915 | 0.908 | -0.007 | -0.7% |
| speechify | narration | 0.875 | 0.878 | +0.003 | +0.3% |

## F-8 (cross-pipeline mean Spearman ρ)
| Use case | R2 mean ρ | R3 mean ρ | Δ |
|---|---:|---:|---:|
| conversational | -0.134 | -0.143 | -0.009 |
| narration | -0.271 | -0.220 | +0.051 |

### F-8 decomposition (PQ vs DNSMOS mean ρ, CE vs DNSMOS mean ρ per use case)
| Use case | Axis | R2 mean ρ | R3 mean ρ | Δ |
|---|---|---:|---:|---:|
| conversational | PQ vs DNSMOS (4 pairs) | +0.238 | +0.190 | −0.048 |
| conversational | CE vs DNSMOS (4 pairs) | −0.506 | −0.476 | +0.030 |
| narration | PQ vs DNSMOS (4 pairs) | −0.167 | −0.131 | +0.036 |
| narration | CE vs DNSMOS (4 pairs) | −0.375 | −0.310 | +0.065 |

**F-8 replicates**: PQ agrees with DNSMOS on conv in both runs
(+0.238 → +0.190); CE anti-correlates with DNSMOS on both use cases
in both runs (mean ρ stays between −0.31 and −0.51). The "aggregate
ρ of −0.13/−0.27 is a mix of two constructs" story is present in
R3 with a similar magnitude split. Reproduction: same
`by_use_case[*].pairs[].rho` grouping computed on
[R2 cross_metric.json](campaign-20260809T204608Z/cross_metric.json)
and [R3 cross_metric.json](campaign-20260831T175358Z/cross_metric.json).

### ElevenLabs R2→R3 shift: significant on Audiobox + DNSMOS P.808, not on the P.835 triad

Under the paired per-item test (Δ_i on matched 75 items, SE_diff
on per-vendor SD of item differences, z = mean_diff / SE_diff),
ElevenLabs has significant R3−R2 shifts on **6 of 12 quality-axis
× use-case cells**, all downward. The 6 significant cells are
the outputs of two scoring models (Meta's Audiobox — PQ + CE — and
Microsoft's DNSMOS P.808 single-model predictor), on both use
cases. The 6 non-significant cells are the outputs of the third
scoring model (Microsoft's DNSMOS P.835 three-scale predictor —
ovrl + sig + bak, all derived from a shared internal
representation), on both use cases:

| use case | axis | Δ (R3 − R2) | SE_diff | paired z | significant (|z| > 2) |
|---|---|---:|---:|---:|---|
| conv | AB.PQ | −0.074 | 0.017 | **−4.36σ** | ✓ |
| conv | AB.CE | −0.045 | 0.015 | **−2.92σ** | ✓ |
| conv | DN.p808 | −0.039 | 0.017 | **−2.26σ** | ✓ (not after Bonferroni) |
| conv | DN.ovrl | −0.010 | 0.010 | −0.98σ | not |
| conv | DN.sig | −0.006 | 0.008 | −0.80σ | not |
| conv | DN.bak | −0.006 | 0.008 | −0.76σ | not |
| narr | AB.PQ | −0.074 | 0.010 | **−7.32σ** | ✓ |
| narr | AB.CE | −0.048 | 0.009 | **−5.09σ** | ✓ |
| narr | DN.p808 | −0.047 | 0.013 | **−3.69σ** | ✓ |
| narr | DN.ovrl | −0.023 | 0.014 | −1.56σ | not |
| narr | DN.sig | −0.014 | 0.009 | −1.48σ | not |
| narr | DN.bak | −0.020 | 0.014 | −1.38σ | not |

**Under the same paired-z test, three non-ElevenLabs cells cross
the raw |z| > 2 threshold** — Speechify narr AB.CE (−2.49σ),
Speechify narr DN.sig (+2.03σ), Fish narr DN.p808 (+2.06σ).
Across the 96 (vendor × use_case × axis) cells at α = 0.05, you
expect ~5 hits that size by chance under independence; three
observed is fewer than chance, and none survives Bonferroni-12
or -96. Every other axis on every other vendor lands at
|z| < 2. Google, which has a sign-count tilt (10 of 12 axes
negative in the raw delta table below), is uniformly |z| < 1.6
under the paired test: sign-count only, not a statistical shift.
**What distinguishes ElevenLabs is 5 cells surviving
Bonferroni-12 (4 surviving Bonferroni-96) vs 0 for every other
vendor, and the surviving cells partitioning cleanly by
scoring-model architecture: Audiobox + DNSMOS P.808 both detected
the drift; DNSMOS P.835 did not. This is not the F-8 construct
axis — F-8 has PQ and CE on opposite sides of the DNSMOS-agrees
vs DNSMOS-anti-correlates split.**

**Sign-count table (kept as raw material, not as inference)** —
positive = R3 improved, negative = R3 regressed:

| vendor | sign pattern across 12 axes | max |Δ| | note |
|---|---|---:|---|
| **elevenlabs** | **12 of 12 negative** | 0.074 (AB.PQ) | 5 cells surviving Bonferroni-12 (see table above) — the only vendor with any Bonferroni-surviving shift |
| cartesia | 11 of 12 positive | 0.041 (DN.p808 conv) | max |z| < 2.0 under paired-z |
| deepgram | 6 of 12 negative (all narration) | 0.026 (DN.ovrl conv) | max |z| < 2.0 |
| google | 10 of 12 negative | 0.037 (DN.bak conv) | max |z| < 1.6 |
| speechify | mixed 6/6 | 0.035 (DN.bak narr) | narr AB.CE |z| = 2.49 + narr DN.sig |z| = 2.03 (both fail Bonferroni) |
| openai | mixed 6/6 | 0.016 (DN.p808 conv) | max |z| < 2.0 |
| orpheus | mixed 6/6 | 0.036 (AB.PQ conv) | max |z| < 2.0 |
| fish | mixed 7/5 | 0.034 (DN.ovrl conv) | narr DN.p808 |z| = 2.06 (fails Bonferroni) |

**Multiplicity caveat**: 12 axes are NOT 12 independent trials —
the DNSMOS P.835 triad is correlated by construction, AB.CE
anti-correlates with DNSMOS by construct, AB.PQ and CE correlate
at ρ = +0.31. A "12 of 12 same-sign" statement is much weaker
evidence than 2⁻¹² would suggest. Bonferroni across 12 tests
would push DN.p808 conv (z = −2.26) below the α = 0.05 line;
the other 5 significant cells survive Bonferroni.

**Interval**: R3 ran fresh on 2026-08-31. R2 was cache-only
(`n_fresh = 0` in
[`analysis/campaign-20260809T204608Z/latency.json`](campaign-20260809T204608Z/latency.json))
so the manifest records only the cache-hit timestamp
(2026-08-09), not the underlying synthesis date. The honest
R2→R3 interval is **"between R2's unrecorded synthesis date
(≤ 2026-08-09) and 2026-08-31"**, not "between 2026-08-09 and
2026-08-31".

**Two-model observation**: the conv pin
([`configs/voices.yaml`](../configs/voices.yaml)
`elevenlabs.conversational.model`) is `eleven_flash_v2_5`; the
narr pin is `eleven_multilingual_v2`. The `reasoning` field on
the narr row says in capitals "a **DIFFERENT** model from the
conversational entry above". Both models show the same-direction
shift on the same scorer partition (Audiobox + DNSMOS P.808).
**A single-model update does not touch both** — the shared cause
has to sit somewhere the
two models share: voice embeddings, serving / post-processing,
or the adapter. Adapter is ruled out by
`git log --follow src/veval/adapters/elevenlabs.py` — one commit,
`8372dbd`, 2026-08-07, predating both runs.

### Hygiene: noise-floor replication variance is ±3 dB at the mean level
The `mean_noise_floor_dbfs` field on narration items varies R2→R3 by
up to ±3.2 dB on some cells even with the same voice ID and the
same source text:

| vendor | R2 narr mean_nf_dbfs | R3 narr mean_nf_dbfs | Δ |
|---|---:|---:|---:|
| speechify | −55.24 | −58.40 | **−3.16** |
| orpheus | −78.74 | −75.78 | **+2.96** |
| cartesia | −55.32 | −52.63 | **+2.68** |
| fish | −46.57 | −47.93 | −1.36 |
| openai | −54.52 | −55.12 | −0.59 |
| elevenlabs | −41.48 | −40.91 | +0.57 |
| google | −36.84 | −36.75 | +0.09 |
| deepgram | −46.83 | −46.89 | −0.06 |

**Three of eight vendors** show a run-to-run mean-noise-floor shift
of **≥ 2.5 dB**. The direction is not consistent (Speechify quieter,
Orpheus + Cartesia louder). This is genuine within-vendor draw
variance on this specific metric, not a measurement systematics
issue — F-1 already established none of the vendors is byte-
reproducible, and noise floor is one of the metrics most sensitive
to that.

**Consequence for the pre-registered narration hygiene gate**
(`long_stratum_acoustic_noise_floor_dbfs ≤ −40`, worst-of-8): any
vendor whose R2 worst-of-8 lands within ~3 dB of −40 should be
adjudicated with the uncertainty flagged, not as a hard pass. On
R2, Google (−42.01, 2.0 dB margin) is the only such case. On R3,
worst-of-8 shifts add Orpheus as a new failure: R2 worst = −52.78
(passes by 12.8 dB), R3 worst = −27.75 (fails by 12.3 dB) — a
+25.03 dB jump on the worst item, most likely a truncation-artifact
tail on Orpheus's 14.59-s output cap (see F-5), but the gate result
flipped either way.

**R2 vs R3 long-stratum noise-floor gate outcomes** (correcting the
earlier "7 pass / 1 fail | Fish" tally in [04's narration gate table](../documentation/04_RESULTS.md#pre-registered-gate-outcomes),
which named the wrong vendor):

| vendor | R2 worst-of-8 | R2 gate | R3 worst-of-8 | R3 gate |
|---|---:|---|---:|---|
| cartesia | −37.47 | ✗ FAIL | −32.31 | ✗ FAIL |
| elevenlabs | −37.93 | ✗ FAIL | −34.84 | ✗ FAIL |
| orpheus | −52.78 | ✓ PASS | **−27.75** | **✗ FAIL** (R2→R3 flip) |
| google | −42.01 | ✓ pass (2 dB margin) | −41.55 | ✓ pass (1.6 dB margin) |
| deepgram | −44.46 | ✓ PASS | −45.03 | ✓ PASS |
| fish | −46.20 | ✓ PASS | −50.97 | ✓ PASS |
| speechify | −47.10 | ✓ PASS | −54.02 | ✓ PASS |
| openai | −56.47 | ✓ PASS | −55.84 | ✓ PASS |

**R2 result: 6 pass / 2 fail** (Cartesia + ElevenLabs). **R3
result: 5 pass / 3 fail** (add Orpheus). The current 04 gate table
row saying "Fish (persistent noise floor)" is wrong on both counts
— Fish passes cleanly on both runs — and is retracted as
[CORRECTIONS row 31](../CORRECTIONS.md). Orpheus's R2→R3 flip is
logged as [CORRECTIONS row 32](../CORRECTIONS.md).