# 04 · Results Summary

*Full per-provider measurements across 8 vendors × 2 use cases,
plus the verification-pack verdicts and the cost calculus a
decision-maker needs.*

> **⚠ Scope disclaimer** · Results as of 2026-08-11 on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. No financial
> relationship with any vendor. Not legal/business/purchasing
> advice. Full scope in [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Headline in one line

**There is no universal winner.** Every vendor dominates at least
one measurement axis and loses at least one. The right pick
depends on which axis your listener use case maps to, and on which
failure mode you can absorb. See [05_CASE_STUDY.md](05_CASE_STUDY.md)
for the full narrative and [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md)
for the F-8 / T8 / T5+T7 headline findings.

---

## Full per-provider results

Two quality raters (Meta Audiobox + Microsoft DNSMOS), hygiene
noise-floor, WER via two-judge agreement, latency (conversational
only, 50-trial session), and public-tier cost per 1K words at 100K
words/month.

### Conversational

| Vendor | AB.PQ | AB.CE | DN.p808 | DN.ovrl | DN.sig | DN.bak | clip samples | noise floor (dBFS) | WER % | TTFA p50 (ms) | $/1K words |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| speechify | **7.90** | **6.46** | 3.98 | 3.30 | 3.56 | 4.07 | 1 | −57.0 | 14.3 | — | 0.100 |
| elevenlabs | 7.76 | 5.96 | **4.12** | 3.47 | 3.69 | 4.18 | 0 | −52.0 | 14.1 | **439** | 0.220 |
| openai | 7.74 | 6.11 | 4.01 | **3.49** | **3.70** | **4.19** | 0 | −52.5 | 13.7 | 736 | **0.075** |
| fish | 7.70 | 6.24 | 3.86 | 3.15 | 3.41 | 4.05 | 0 | −39.7 | 13.8 | — | **0.075** |
| deepgram | 7.62 | 6.21 | 3.77 | 3.31 | 3.58 | 4.07 | 0 | −46.2 | 16.6 | 583 | 0.150 |
| google | 7.62 | 6.18 | 3.82 | 3.27 | 3.57 | 4.02 | 0 | −33.7 | 15.1 | — | 0.150 |
| cartesia | 7.44 | 5.96 | 3.89 | 3.25 | 3.48 | 4.13 | **406** | −57.1 | 16.4 | 467 | 0.160 |
| orpheus | 7.41 | 6.01 | 3.87 | 3.33 | 3.62 | 4.10 | 0 | −53.2 | **26.9** | — | **0.030** |

### Narration

| Vendor | AB.PQ | AB.CE | DN.p808 | DN.ovrl | DN.sig | DN.bak | clip samples | noise floor (dBFS) | WER % | $/1K words |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| speechify | **8.15** | **6.66** | 4.05 | 3.42 | 3.63 | 4.17 | 5 | −55.2 | 13.0 | 0.100 |
| orpheus | 8.00 | 6.26 | 4.06 | 3.45 | 3.64 | **4.21** | 0 | −78.7 | **27.2** | **0.030** |
| cartesia | 7.99 | 6.32 | **4.13** | 3.20 | 3.45 | 4.05 | **429** | −55.3 | 12.4 | 0.160 |
| google | 7.97 | 6.44 | 4.02 | 3.35 | 3.60 | 4.11 | 39 | −36.8 | 13.0 | 0.150 |
| elevenlabs | 7.93 | 6.47 | 4.05 | 3.34 | 3.61 | 4.07 | 0 | −41.5 | 12.8 | 0.220 |
| deepgram | 7.86 | 6.40 | 4.07 | 3.44 | 3.68 | 4.15 | 0 | −46.8 | 13.5 | 0.150 |
| fish | 7.63 | 6.31 | 4.12 | 3.40 | 3.67 | 4.10 | 0 | −46.6 | 14.0 | 0.075 |
| openai | 7.62 | 6.18 | 3.98 | **3.46** | **3.68** | 4.18 | 0 | −54.5 | 13.3 | **0.075** |

Rows sorted by AB.PQ (Audiobox production_quality) descending.
Bold cells = axis winner (best or, for cost/WER/latency, most
favorable). See [08 · Glossary](#glossary) for column definitions.

---

## Rankings summary

**Top-2 per quality axis per use case** — the "who's actually
worth paying for?" table. Δ = gap between #1 and #2. Same-voice
run-to-run noise floor is ~0.035 on Audiobox and ~0.035 on DNSMOS
(measured on Speechify T6 control), so any Δ below ~0.05 is a
statistical tie.

### Conversational

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | Meaningful? |
|---|---|---:|---|---:|---:|---|
| Audiobox PQ (warm) | speechify | 7.90 | elevenlabs | 7.76 | +0.14 | ✅ ~4× noise |
| Audiobox CE (warm) | speechify | 6.46 | fish | 6.24 | +0.22 | ✅ ~6× noise |
| DNSMOS OVRL (clean) | openai | 3.49 | elevenlabs | 3.47 | +0.02 | **❌ tied** |
| DNSMOS SIG (clean) | openai | 3.70 | elevenlabs | 3.69 | +0.01 | **❌ tied** |

### Narration

| Axis | #1 vendor | #1 score | #2 vendor | #2 score | Δ | Meaningful? |
|---|---|---:|---|---:|---:|---|
| Audiobox PQ (warm) | speechify | 8.15 | orpheus¹ | 8.00 | +0.15 | ✅ ~4× noise |
| Audiobox CE (warm) | speechify | 6.66 | elevenlabs | 6.47 | +0.20 | ✅ ~6× noise |
| DNSMOS OVRL (clean) | openai | 3.46 | orpheus¹ | 3.45 | +0.01 | **❌ tied** |
| DNSMOS SIG (clean) | openai | 3.68 | fish | 3.67 | +0.01 | **❌ tied** |

¹ Orpheus is disqualified for narration by its 14.59-second output
cap (see F-9 T8) — the audio scored is truncated to ~16% of the
expected duration. Real narration #2 on DNSMOS OVRL is deepgram at
3.44 (Δ +0.02 vs OpenAI, still tied).

---

## Cross-pipeline agreement (F-8)

Two independent MOS pipelines rank the 8 vendors **differently**.
Cross-pipeline mean Spearman ρ across the 8 vendors:

| Use case | Cross-pipeline mean ρ | Interpretation |
|---|---:|---|
| Conversational | **−0.13** | Essentially uncorrelated |
| Narration | **−0.27** | Weakly inverse |

See [documentation/figures/f1_rank_inversion.png](figures/f1_rank_inversion.png)
for the vendor-by-vendor rank comparison. Perfect-inversion case:
**OpenAI narration ranks #8/8 on Audiobox PQ and #1/8 on DNSMOS OVRL**.
The two raters measure different constructs (warmth/aesthetic vs
signal cleanliness/P.835); they are not two attempts at the same
number. See [06_KEY_FINDINGS.md § F-8](06_KEY_FINDINGS.md#f-8).

---

## Cost calculus

Cost per 1K words at the 100K-words/month tier, from
[configs/pricing.yaml](../configs/pricing.yaml). Full pricing model
in [`analysis/campaign-*/cost_model.json`](../analysis) — includes
monthly minimums, included tiers, and rates at 10K/100K/1M words
per month tiers.

| Vendor | $/1K @ 10K/mo | $/1K @ 100K/mo | $/1K @ 1M/mo | Notes |
|---|---:|---:|---:|---|
| orpheus | 0.030 | 0.030 | 0.030 | Replicate pay-per-use; hard 14.59s cap per call (F-9 T8) → real narration cost ~$0.18-0.60/1K chars once chunked |
| **openai** | 0.075 | **0.075** | **0.075** | tts-1-hd (narration) + gpt-4o-mini-tts (conv) |
| fish | 0.075 | 0.075 | 0.075 | s2.1-pro (paid); split-model design (quality vs latency) |
| **speechify** | 0.100 | **0.100** | **0.040** | Starter $10/mo covers 100K; scales well at 1M+ |
| deepgram | 0.150 | 0.150 | 0.150 | Aura-2; $200 signup credit covers early volume |
| google | 0.150 | 0.150 | 0.150 | Chirp3-HD |
| cartesia | 0.500 | 0.160 | 0.196 | Pro $5/mo = 100K credits, then per-1M rate |
| **elevenlabs** | **2.200** | **0.220** | 0.244 | Creator $22/mo = 121K credits; expensive at low volume |

**Three cost-driven conclusions:**

1. **DNSMOS conversational is a tie between OpenAI and ElevenLabs** —
   OpenAI at **$0.075** beats ElevenLabs at **$0.22** at every
   meaningful volume tier. **~66% saving** for essentially
   indistinguishable quality on the clean-rater axis.
2. **DNSMOS narration is a tie between OpenAI and Deepgram** —
   OpenAI at $0.075 beats Deepgram at $0.15 for tied-on-quality
   results. **~50% saving**.
3. **Speechify wins Audiobox AND is cheap** on both use cases —
   $0.10/1K at 100K/mo, $0.04/1K at 1M/mo. Unusual combination
   (quality winner is usually the priciest).

See [documentation/figures/f2_cost_vs_quality.png](figures/f2_cost_vs_quality.png)
for the visual.

---

## Latency + stability

Time-to-first-audio-frame (TTFA), 50 serial trials, conversational
S01 corpus item. Two independent sessions two days apart on the
two speed-critical vendors.

| Vendor | Session 1 p50 | Session 1 p90 | Session 2 p50 | Session 2 p90 | Session-to-session |
|---|---:|---:|---:|---:|---|
| **elevenlabs** (Flash v2.5) | **439 ms** | **479 ms** | **424 ms** | **469 ms** | **−3% p50 / −2% p90** ← stable |
| openai (tts-1-hd) | 736 ms | 956 ms | 936 ms | 1493 ms | +27% p50 / +56% p90 ← variable |
| deepgram | ~180 ms | ~230 ms | not re-measured | — | — |
| cartesia | 467 ms | — | not re-measured | — | — |
| speechify | not applicable* | | | | |
| fish | not applicable* | | | | |
| google | not applicable* | | | | |
| orpheus | not applicable* | | | | |

*"Not applicable" here means the adapter doesn't stream (Speechify
JSON envelope per D-008; Fish's paid model split; Google's non-streaming;
Orpheus's hosted-inference-poll pattern on Replicate). TTFA is
`total_ms` for these, not the streaming TTFA the other providers report.
See [../DEVIATIONS.md](../DEVIATIONS.md#d-008).

**Portable finding**: **latency *speed* and latency *stability* are
distinct axes**. See
[documentation/figures/f3_latency_stability.png](figures/f3_latency_stability.png)
for the visual. Verdict details in
[analysis/verification/T5](../analysis/verification/T5_openai_latency.md)
and [T7](../analysis/verification/T7_elevenlabs_ttfa.md).

---

## Verification pack outcomes (Phase 2c)

9 targeted tests re-checked the primary campaign's headline
outliers on fresh data.

| # | Outlier | Vendor | Verdict | Evidence |
|---|---|---|---|---|
| T1 | Clipping 429/406 samples (100× next) | Cartesia | **Confirmed** (via F-4a — 2nd independent pipeline) | [T1](../analysis/verification/T1_cartesia_clipping.md) |
| T2 | WER ~27% (2× next) | Orpheus | **Answered by T8** — 14.59s output cap = mechanical incompletion | [T2](../analysis/verification/T2_orpheus_wer.md) |
| T3 | Narration PQ 7.41 conv → 8.00 narr | Orpheus | **Retired** — DNSMOS #2 narr confirms direction, satisfies exit criterion | (retired) |
| T4 | L03 monotonic fadeout (3.6 dB) | ElevenLabs | **Confirmed with refinement** — 3/3 fresh regens fade monotonically; mean delta 2.7 dB, not 3.6 dB | [T4](../analysis/verification/T4_elevenlabs_L03_fadeout.md) |
| T5 | Latency 762/946 ms (2× next) | OpenAI | **Confirmed with direction-caveat** — session-2 was even slower | [T5](../analysis/verification/T5_openai_latency.md) |
| T6 | Audiobox #1 both UC | Speechify | **Confirmed with reversal** — alt voice edmund_32 scores *higher* than pinned voices; still #1 of 9 | [T6](../analysis/verification/T6_speechify_voice_bias.md) |
| T7 | Fastest TTFA (440/474 ms) | ElevenLabs | **Confirmed cleanly** — sub-500 ms p90 across 2 sessions | [T7](../analysis/verification/T7_elevenlabs_ttfa.md) |
| T8 | Cheapest $0.030/1K | Orpheus | **Refuted with a bigger finding** — 14.59s hard output cap; cost is fixed-per-call not linear-with-text | [T8](../analysis/verification/T8_orpheus_cost.md) |
| N1 | Audiobox #8/#8 vs DNSMOS #1/#1/#2 narr | OpenAI | Pending (manual listen) | [N1](../analysis/verification/N1_openai_narration_inversion.md) |
| N2 | DNSMOS OVRL+SIG #8/#8 conv | Fish | **Confirmed** — Fish noise floor +12.6 dB above 8-vendor median (2× threshold); 3rd independent pipeline agrees | [N2](../analysis/verification/N2_fish_conv_dnsmos.md) |

**Confirmed: 5 · Confirmed-with-refinement/caveat: 3 · Refuted-with-bigger-finding: 1 · Pending: 1**

Total Phase 2c spend: **~$0.61** across 40 items × 3 fresh regen
campaigns + 2 new latency sessions.

---

## Decision framework (three questions)

Answer these in order. Only proceed once the previous question has
a clear answer for your use case.

### Q1 — Hard constraints

- **Any turn ≥ 15s?** Orpheus is out (14.59s output cap).
- **Any downstream ASR / MOS / resample pipeline?** Cartesia needs a
  −1 dBFS peak-limiter first, or accept ~46% loss to DNSMOS refusals.
- **Sub-500 ms p90 required?** ElevenLabs Flash + Deepgram only.
- **Byte-identical caching?** Impossible with any of the 8; save the
  audio yourself.

### Q2 — Which "quality" matches your users?

- **Warm / engaging** (consumer storytelling, audiobook, brand voice) →
  **Speechify** wins Audiobox on both use cases AND is cheapest on
  the paid tier.
- **Clean / pristine** (enterprise IVR, accessibility, transactional
  voice) → **OpenAI** wins DNSMOS narration and ties for #1
  conversational at 50-70% of the tied competitor's cost.

### Q3 — Is #1 quality worth the cost premium over #2?

If the Δ between #1 and #2 is ~0.05 or less (see the rankings
tables above), the two are **statistically tied** — pick the
cheaper one.

If the Δ is 0.10+, the quality gap is real. Whether it's worth the
cost premium is a call only you can make — but framing it
explicitly beats a vague "premium feels worth it."

Full plain-language walkthrough in
[05_CASE_STUDY.md § "What this means for a PM"](05_CASE_STUDY.md#what-this-means-for-a-pm-buying-voice-ai).

---

## <a name="glossary"></a>Glossary

- **AB.PQ** — Meta Audiobox Aesthetics *production_quality* axis
  (0–10). Trained on aesthetic ratings; rewards *warmth,
  expressiveness, engagement*.
- **AB.CE** — Meta Audiobox Aesthetics *content_enjoyment* axis (0–10).
- **DN.p808** — Microsoft DNSMOS *p808_mos* — ITU-T P.808 overall
  MOS from a single-model predictor (1–5).
- **DN.ovrl** — Microsoft DNSMOS *ovrl_mos* — ITU-T P.835 overall
  MOS from a three-scale predictor (1–5).
- **DN.sig** — Microsoft DNSMOS *sig_mos* — P.835 speech-signal
  quality (1–5).
- **DN.bak** — Microsoft DNSMOS *bak_mos* — P.835 background-noise
  intrusiveness (higher = less intrusive, 1–5).
- **clip samples** — Total audio samples with amplitude ≥ ±1.0 across
  all 75 files (hygiene analyzer, `pyloudnorm`-based).
- **noise floor (dBFS)** — Mean noise floor across 75 files (hygiene
  analyzer). Less-negative = noisier.
- **WER %** — Mean word-error-rate on items with judge agreement
  (two-judge design: wav2vec2 + faster-whisper). Reported as
  relative ranking only; absolute inflated by wav2vec2's LibriSpeech
  training distribution.
- **TTFA p50 (ms)** — Time-to-first-audio-frame, 50th percentile,
  50-trial session, S01 corpus. **Residential Windows 11
  measurement — absolute values are upper bounds.**
- **$/1K words** — Cost per 1,000 words at the specified monthly
  volume tier (see full cost table).

Full measurement methodology in
[02_METHODOLOGY.md](02_METHODOLOGY.md).

---

## Reproducing these numbers

```powershell
# From the immutable run stores (regenerable)
uv run veval analyze campaign-20260809T204608Z --stages all
uv run veval analyze latency-20260809T214106Z --stages latency
uv run veval analyze latency-20260811T183028Z --stages latency
uv run veval analyze latency-20260811T183202Z --stages latency

# Cross-metric analysis
uv run veval analyze campaign-20260809T204608Z --stages cross_metric

# Regenerate the figures
uv run python scripts/generate_figures.py
```

See [03_RUNBOOK.md](03_RUNBOOK.md) for full install + reproduce
instructions.
