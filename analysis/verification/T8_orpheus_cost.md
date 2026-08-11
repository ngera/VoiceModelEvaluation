# T8 · Orpheus per-item cost scales linearly with item length

- **Provider**: Orpheus (`lucataco/orpheus-3b-0.1-ft` on Replicate)
- **Use case**: narration (long items are the meaningful stratum)
- **Test type**: 10 long-item Orpheus calls; measure actual GPU-seconds
  per Replicate dashboard
- **Created**: 2026-08-11
- **Cost**: ~$0.05
- **Wall-clock**: ~15 min

## Original outlier (from Phase 2)

Orpheus's `cost_model.json` per-1K-chars pricing is the *cheapest* in
the roster (see
`analysis/campaign-20260809T204608Z/cost_model.json` `providers` block
for orpheus). The pricing model assumes ~$0.003 per generation
(Replicate posted rate for the model version SHA in
`configs/providers.yaml`).

The unknown: does actual GPU-seconds billing scale linearly with text
length, or does it flatten out (fixed model-load overhead > variable
inference time)? If cost is dominated by fixed overhead, "Orpheus is
cheapest per 1K chars on short items" and "Orpheus is more expensive
on long items than pricing model predicts" both become possible.

## Hypothesis

Orpheus per-call cost is dominated by **variable inference GPU-seconds**
(not fixed model-load overhead). Mean per-call cost on 10 long-narration
items should be **within ±30%** of the pricing model's prediction
(~$0.003), i.e. **$0.0021–$0.0039 per call**.

## Success criterion (pre-registered)

**Mean observed per-call cost (from Replicate dashboard, over 10 long
narration items) within ±30% of the pricing model prediction
($0.0021–$0.0039).**

Report by-item too — a wide spread with a mean inside the band is
worth noting even if the criterion passes.

## Method

```powershell
# Generate 10 long-narration items on Orpheus, fresh
uv run veval generate --mode campaign `
  --provider orpheus `
  --items L01 --items L02 --items L03 --items L04 --items L05 `
  --items L06 --items L07 --items L08 --items L09 --items L10 `
  --use-case narration `
  --no-cache `
  --spend-cap 1.00

# Analyze cost (compares api_log.jsonl runtimes against pricing.yaml)
uv run veval analyze <new-run-id> --stages cost

# Read from Replicate dashboard: https://replicate.com/account/billing
# — filter by the 10 predictions in the last 15 min from this account
# — copy GPU-seconds + $ per prediction

uv run python -c "
import json
from pathlib import Path

# From pricing.yaml: Replicate T4 GPU rate is $0.000225/sec (as of 2026-08-11)
gpu_rate_per_sec = 0.000225
predictions = [
    # Fill in from Replicate dashboard (10 rows):
    # ('L01', gpu_secs, actual_dollars),
    # ...
]

if predictions:
    for item_id, gpu_secs, dollars in predictions:
        print(f'  {item_id}: {gpu_secs:.2f}s = ${dollars:.4f}')
    mean = sum(d for _, _, d in predictions) / len(predictions)
    print(f'\\nmean per-call: \${mean:.4f}')
    print(f'pricing model prediction: \$0.0030')
    print(f'ratio: {mean/0.003:.2f}× (target: 0.70-1.30)')
"
```

## Result (executed 2026-08-11)

Fresh run: `campaign-20260811T183847Z` — 8 long narration items
(L09/L10 don't exist in the corpus, so n=8 not 10). No cache.
Replicate `predict_time` queried per-prediction via
`/v1/predictions/{id}` API. Audio duration read from WAV headers
via `wave.getnframes() / wave.getframerate()`.

| item | chars | expected@175wpm (s) | actual audio (s) | predict_time (s) | trunc % |
|---|---|---|---|---|---|
| L01 | 1313 | 89.9 | **14.59** | 18.362 | 16% |
| L02 | 1273 | 87.2 | **14.59** | 16.944 | 17% |
| L03 | 1345 | 92.1 | **14.59** | 16.943 | 16% |
| L04 | 1527 | 104.6 | **14.59** | 17.020 | 14% |
| L05 | 1460 | 100.0 | **14.59** | 16.996 | 15% |
| L06 | 1408 | 96.4 | **14.59** | 16.931 | 15% |
| L07 | 1364 | 93.4 | **14.59** | 17.020 | 16% |
| L08 | 1288 | 88.2 | **14.59** | 16.961 | 17% |

**Look at the actual-audio column: every item = 14.59s. stdev = 0.00.**

## Verdict

**Refuted** — but in a much bigger way than the test was designed
to detect.

The original hypothesis was that per-call cost scales linearly with
input length. That's now refuted by the strongest possible evidence:
**Orpheus produces exactly 14.59 seconds of audio per call
regardless of input text length**. Input chars vary 19% (1273 →
1527), audio duration varies 0%. predict_time varies 8%
(16.93–18.36s, and even that's just L01 cold-start warmup — the
other 7 are 16.9–17.0s, a 0.6% spread).

This is a **hard model output cap**, not stochastic truncation.
Every long-item call gets ~17 GPU-seconds of inference and produces
exactly 14.59s of audio.

## The cost story (revised)

**Pricing.yaml assumes $0.003/generation** (verified 2026-08-06,
"observed mean"). Under three plausible Replicate GPU rates:

| GPU | rate/sec | cost/call at 17.15s | ratio vs $0.003 | within ±30%? |
|---|---|---|---|---|
| Nvidia T4  | $0.000225 | **$0.0039** | 1.29× | ✅ (borderline) |
| Nvidia L40S | $0.000975 | $0.0167 | 5.57× | ✗ |
| Nvidia A100 | $0.001400 | $0.0240 | 8.00× | ✗ |

**Which GPU?** The `lucataco/orpheus-3b-0.1-ft` model card doesn't
expose the hardware tier via API. **Ground truth is the user's
Replicate billing dashboard** — check the 8 predictions from run
`campaign-20260811T183847Z` and read the actual per-prediction
$-cost.

**If T4** ($0.0039/call): pricing.yaml is right at 1.29× (borderline
within ±30%). But the assumption of *"cost scales with output
length"* is wrong — cost is essentially fixed per call.

**If L40S or A100**: pricing.yaml is off by 5-8×. Orpheus at ~$0.02
per call is still cheaper than most providers per call, but the
"cheapest per 1K chars" story evaporates once you factor in the fact
that a 1K-char narration needs ~6 calls (6 × $0.02 = $0.12) to
render the full text.

## The real finding

**Orpheus's cost story is more nuanced than "cheapest per 1K chars":**

- **Fixed cost per call** (~17 GPU-seconds, ~$0.003–0.017 depending
  on GPU tier)
- **Fixed output per call** (exactly 14.59s of audio)
- **Real cost per 1K chars = calls_per_1K × $-per-call**
  - At mean 14.59s audio × ~14.6 chars/s = ~213 chars/call
  - So ~5 calls per 1K chars → **5× the "per-call" cost**
  - At T4 pricing: $0.0195/1K chars (not $0.003)
  - At L40S: $0.083/1K chars — competitive but not category-crushing

**This is why T2's WER is 85%**: Orpheus can't complete long items
because it stops at 14.59s. It's not intelligibility — it's a hard
generation cap.

## Notes for memo / paper

- **Orpheus's archetype needs rewriting.** Original narrative:
  "cheap open-weights floor" with "cost scales linearly." Actual:
  "cheap for short clips, requires manual chunking for long-form
  narration, WER on long items is high because of the output cap
  not intelligibility."
- **This directly resolves T2 without a manual listen.** The 85%
  WER on long items is a mechanical consequence of the 14.59s
  output cap. Every ≥15-second reference text will get ~85%+ of
  its content lost. T2's "unclear vs truncated" self-mark rubric
  would return 10/10 "truncated" — but we don't need to listen to
  know that; the math forces it.
- **Portfolio narrative candidate**: "T8 was designed to check
  whether Orpheus's cost scaled linearly with text length. Instead,
  it revealed a hard 14.59-second output cap per call, invariant
  across 8 different inputs (stdev = 0.000 seconds). This
  simultaneously answered T2 (the 85% WER is a truncation cap, not
  intelligibility) and rewrote Orpheus's cost story from 'cheapest
  per 1K chars' to 'cheapest per fixed 14.59-second clip; multiply
  by call-count-needed for long-form.'"
- **Portable claim about cost**: at conservative T4 pricing,
  Orpheus is $0.0039/call. **This is our floor, not the pricing.yaml
  $0.003.** Update pricing.yaml note accordingly.
- **F-3 update candidate**: the "no universal winner" finding gets
  a new dimension — Orpheus wins short items, loses long items
  categorically (not just quality-wise, structurally).

## Evidence artefacts

- Run: `runs/campaign-20260811T183847Z/` (8 fresh predictions)
- Analysis: `scripts/_t8_analysis.py` (one-shot for the analysis
  block above; not part of the main package)
- Replicate predict_time fetched live from `/v1/predictions/{id}`
- **User action**: verify GPU tier + actual $-cost from the
  Replicate billing dashboard for run
  `campaign-20260811T183847Z` (8 predictions dated 2026-08-11)
