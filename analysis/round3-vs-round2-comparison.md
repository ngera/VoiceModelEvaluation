warning: `VIRTUAL_ENV=C:\Users\njger\AppData\Local\Programs\Python\Python311` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
# Round-2 (2026-08-09) vs Round-3 (2026-08-31) — replication comparison

- R2 run: `campaign-20260809T204608Z` — campaign-20260809T204608Z
- R3 run: `campaign-20260831T175358Z` — campaign-20260831T175358Z

## Cost totals
- R2 total_observed_cost_usd: **$7.8457**
- R3 total_observed_cost_usd: **$7.8427**
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
| orpheus | 0.4500 | 0.4470 | -0.0030 | -0.7% |
| speechify | 0.3892 | 0.3892 | +0.0000 | +0.0% |

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
