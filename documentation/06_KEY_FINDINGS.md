# 06 · Key findings, friction points, and decisions

*Distilled from the running research log. Every finding here is
backed by a specific artefact under [analysis/](../analysis/) or
[analysis/verification/](../analysis/verification/). Every decision
here is backed by a specific reasoning section reachable from
the entries below.*

> **⚠ Scope disclaimer** · Findings as of 2026-09-01 on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. See
> [../DISCLAIMER.md](../DISCLAIMER.md).

> **Two-phase structure** · Findings below are from **Phase 1**
> (R2 baseline 2026-08-09 + R3 replication 2026-08-31, 8 vendors ×
> 2 use cases × 75 items each). Phase 1 raised three specific
> follow-up questions that a targeted **Phase 2 experiment pack**
> (2026-09-01) answered — the F-6 fade extent (cross-vendor + cross-
> voice + within-run stochasticity), the F-7 voice-swap consistency
> (whether Speechify's model-family-quality story generalises), and
> the F-11 latency variance (adding S4+S5 to the 4-session baseline).
> Findings that were sharpened or extended by Phase 2 explicitly say
> so; the full experiment-pack report lives at
> [EXPERIMENTS_2026-09-01.md](EXPERIMENTS_2026-09-01.md).

> **R2-vs-R3 replication surfaced three additional signals** beyond
> just reproducing R2's rankings (12 of 14 top-1 positions
> unchanged; per-axis Spearman ρ 0.905–1.000; the two flips are
> DN.p808 narration and WER conv, both inside noise floor). All
> three live in
> [`analysis/round3-vs-round2-comparison.md`](../analysis/round3-vs-round2-comparison.md).
> **(a)** F-8's construct decomposition replicates (conv PQ-vs-DN
> ρ: R2 +0.238 → R3 +0.190; conv CE-vs-DN ρ: R2 −0.506 → R3
> −0.476).
> **(b)** ElevenLabs shifted significantly downward (paired-z
> |z| > 2) on 6 of 12 quality axes — the two Audiobox axes
> (PQ + CE) plus DNSMOS's P.808 single-model MOS, on both use
> cases. The 6 non-significant axes are the DNSMOS P.835 triad
> (ovrl / sig / bak) on both use cases. The partition is by
> scoring-model architecture (two of three scoring models
> detected the drift, the third did not), not by construct —
> F-8 already establishes that PQ and CE track *opposite*
> constructs. Both ElevenLabs models (Flash v2.5 conv,
> Multilingual v2 narr) moved together, so a single-model update
> does not explain the pattern (two independent models updating
> in the same direction in the same window is possible but not
> parsimonious). Written up as [F-12](#f-12) below.
> **(c)** The pre-registered
> `long_stratum_acoustic_noise_floor_dbfs ≤ −40` hygiene gate has
> **R2 = 6 pass / 2 fail** (Cartesia + ElevenLabs) and
> **R3 = 5 pass / 3 fail** (Orpheus's worst-of-8 shifted 25 dB);
> mean noise floor itself has ±3 dB R2/R3 replication variance so
> Google's ~2 dB gate margin is pass-with-uncertainty.

---

## Contents

- [Findings F-1 through F-9 + F-11 + F-12](#findings) (F-10 slot was
  reserved for BT rating campaign results; unused because Phase 3
  was deferred to v2 per D-H, and the slot number is retained so
  future v2 work can slot in without renumbering; F-12 covers the
  R2→R3 ElevenLabs Audiobox+P.808 scorer-partition shift)
- [Friction points — the portfolio narrative bank](#friction-points)
- [Decisions D-A through D-H](#decisions)
- [Threats to validity](#threats-to-validity)
- [Pre-registered amendments](#pre-registered-amendments) *(link to DEVIATIONS.md)*

---

## Findings

### F-1 · Every vendor is non-deterministic across draws

Not one of the 8 vendors produces byte-identical output when the
same text is sent twice. Every one of 16 (vendor, use case) rows in
`variance.json` shows `identical_across_draws_fraction = 0.0`.

**Impact:** If your product needs byte-identical audio playback
(caching by content hash, deterministic replay for regression
tests), you must save the audio yourself. Re-requesting is not
equivalent. This is universal, not vendor-specific.

**Evidence:** [`analysis/variance-20260809T205319Z/variance.json`](../analysis)

<a name="f-1a"></a>
### F-1a · Streaming WAV headers ship placeholder lengths; every duration-derived number in the project rests on the fix

During Phase A adapter integration (captured in
[`dx/friction_log.md`](../dx/friction_log.md)) the Deepgram
adapter's raw WAV output was found to carry a
`0x7FFFAC00` placeholder in the header `data`-chunk length
field — declaring **44,737 seconds** of audio for a **2.8-second
clip**. Anything trusting the header (analyzers that read
duration from the header rather than counting frames) would
divide by a 12-hour "duration" and silently produce nonsense.

**The fix**: every streaming adapter passes bytes through
[`finalize_wav_header()`](../src/veval/adapters/base.py) in
`adapters/base.py`, which recomputes the true `data`-chunk
length from the actual sample count before the audio hits the
run store. Not optional; enforced at the adapter-base level so
new streaming vendors inherit it automatically.

**What rests on this fix**: RTF (needs true duration to divide
wall-clock by), speech-ratio (needs true duration to compute the
speech / silence split), the Orpheus 14.59-s output-cap discovery
(F-5 / T8 — the 14.59-s consistency across long-item calls only
reads as a *cap* once the header lies about length are removed;
otherwise it reads as "Orpheus sometimes generates 12 hours of
audio"), and the per-third loudness drift analysis (F-6 — needs
correct thirds to compare LUFS across). Without F-1a the entire
speed and duration surface of the study would be silently wrong.

**How it was caught**: D7-friction integration log, Phase A
walking skeleton. The provenance is cited in
[01_ARCHITECTURE.md](01_ARCHITECTURE.md) line 211,
[03_RUNBOOK.md](03_RUNBOOK.md) line 541, and
[DEVIATIONS.md](../DEVIATIONS.md) line 282, and by cross-doc
pointers to F-1a from every duration-derived metric.

### F-2 · Wav2vec2 is a noisy WER judge on TTS-distribution audio

Two-judge agreement WER lands in **~12–17%** for 7 of 8 vendors
(Orpheus 27%, explained by F-9 T8). This is *inflated* — wav2vec2
emits ALL CAPS + no punctuation and drops articles. The error
pattern is provider-independent, so **relative rankings survive
even though absolute numbers are inflated**. WER "ties" and
"differences" are described qualitatively in these docs; no
per-vendor WER SE is computed in v1, so treat the fine-grained
ordering with caution.

**Second caveat: ~3-pp probe dilution.** The 12-17% band above
is computed over all 75 items, which includes the 15
pre-registered contamination-probe items (Harvard sentences /
literary openings — spec § 3.3). The probe transcribes at ~1/5
the corpus rate on narration and ~1/2 on conversational, so
excluding it shifts each vendor's WER upward by ~3 pp. **Top-1
order holds either way** — OpenAI leads conversational both
readings (0.1370 all-75, 0.1694 probe-excluded; Fish #2 both
readings), Cartesia leads narration both readings. What the
probe moves is 3rd/4th on conv: Speechify (0.1735 probe-excluded)
passes ElevenLabs (0.1758). Full probe-included vs
probe-excluded bands + per-vendor recompute in
[04 § WER-gate admission](04_RESULTS.md#wer-gate-admission);
per-stratum WER receipt in [02 § Contamination
probe](02_METHODOLOGY.md#probe). **Quality-axis top-1 is
unchanged** on all six axis × use-case combos — the probe
caveat is WER-only.

**Impact:** WER is reported as *relative-ranking-only* throughout
the results. Absolute WER numbers should not be quoted without
both the "vs the same 2-judge pipeline across other vendors"
qualifier AND the "~3 pp probe-dilution" caveat. A stronger judge
(NeMo Parakeet once integrated) would tighten absolutes but
reproduce the ordering.

**Evidence:** [`analysis/campaign-20260809T204608Z/wer.json`](../analysis)

### F-3 · Vendor strengths cluster orthogonally — no universal winner

Across 7 measured dimensions (latency, cost, Audiobox PQ, Audiobox CE,
DNSMOS OVRL, WER conv, WER narr), and one non-dimension (determinism),
different vendors lead:

- Latency (TTFA p50/p90) → **ElevenLabs** Flash (ranking; every
  measured streaming vendor fails the pre-registered 400 ms gate,
  see [04 § TTFA-gate admission](04_RESULTS.md#ttfa-gate-admission))
- Cost per 1K words → **OpenAI / Fish** (tied at $0.075/1K).
  Orpheus's nominal $0.030 in `cost_model.json` is a `cost_model.py`
  artefact under a 100-word-per-call default; T8's per-call
  measurement puts Orpheus's honest per-1K-words cost at
  ~$0.067-0.088 — peer-priced to OpenAI. See
  [04 § Cost calculus § ⚠ Orpheus](04_RESULTS.md#cost-calculus).
- Audiobox PQ (both use cases) → **Speechify**
- DNSMOS OVRL (both use cases) → **OpenAI**
- Cleanest WER (conv) → **cluster** at ~13.7-14.3% (OpenAI 13.70 /
  Fish 13.78 / ElevenLabs 14.07 / Speechify 14.33) — probe-included.
  No vendor cleanly leads; the spread is smaller than the F-2 / F-3
  WER-judge inflation. **Top-1 order is stable under probe
  exclusion** (OpenAI 16.94% still #1, Fish 17.01% still #2 —
  the 0.0008 gap is preserved), but the 3rd/4th pair swaps:
  Speechify (17.35%) passes ElevenLabs (17.58%). The OpenAI-Fish
  margin is 40× smaller than the ~3-pp probe dilution, so the
  conversational top-2 should be read as an unresolved
  OpenAI/Fish pair either way — see F-2 caveat above and
  [02 § Contamination probe](02_METHODOLOGY.md#probe). Orpheus
  at 26.9% (all-75) / 32.5% (probe-excluded) is the only vendor
  categorically outside the pack under either reading.
- Cleanest WER (narr) → **cluster** at ~12.4-13.1% (Cartesia
  12.39 / ElevenLabs 12.81 / Speechify 13.02 / Google 13.05 /
  Openai 13.30 / Fish 13.99). No vendor cleanly leads — Google
  and Speechify differ by 0.03% on absolute WER, well inside
  the F-2 wav2vec2 inflation band, so the cluster is reported
  as a range rather than a leader list. Orpheus 27.23% is the
  only vendor categorically outside the pack.
- Determinism → nobody (F-1)

**No single vendor leads on ≥3 of the 4 "quality" dimensions**
(Audiobox PQ, Audiobox CE, DNSMOS OVRL, WER). ElevenLabs' latency +
2 WER-cluster appearances is a support-agent-conversation strength,
not a quality-headline strength. Every recommended vendor will be a
trade-off, not a dominant choice.

### F-4 + F-4a · Cartesia's clipping is corroborated by two independent code paths

**F-4** (original observation): Cartesia produced 429 clipped
samples on narration (across 68 files) + 406 on conversational
(across 54 files) — **~11× the next-worst vendor on narration**
(Google 39/30) and **~400× on conversational** (Speechify 1 /
ElevenLabs 1). Two other vendors also fail the narration
long-stratum clipping gate at lower magnitudes: Google 36/28
clipped samples across the 8 long items on R2/R3; Speechify 3/10
across 1 long item on R2/R3. Reproducible from `hygiene.json`'s
sample-level peak detection.

**F-4a** (independent-pipeline corroboration): Microsoft DNSMOS
refuses to score any file with peak > 1.0, raising a `ValueError`.
Refusal rates on the campaign:

| Vendor / use case | Refused / total | % |
|---|---|---|
| Cartesia narration | 37 / 75 | **49%** |
| Cartesia conversational | 32 / 75 | **43%** |
| Google narration | 4 / 75 | 5% |
| All 13 other cells | 0 / 75 | 0% |

Ranking on refusal rate is identical to F-4's clipping-sample
ranking. **Two independent measurement code paths (peak_dbfs vs
speechmos ONNX inference) unanimously flag the same vendor.** The
surviving 38 Cartesia narration files (after DNSMOS refused the
peak-out-of-range set) still rank #8/8 on all three DNSMOS
three-scale axes — the mastering signature isn't *just* about
peaks; it affects the whole waveform.

**Impact:** Cartesia's audio breaks common downstream tooling.
Adding a −1 dBFS peak-limiter before any ASR/MOS/resample step
recovers the audio; without it, **~46% of Cartesia's output on
R2 (41.3% on R3, pooled across both use cases) is silently
unusable in a quality-check pipeline** — per-cell rates and both
runs' figures in
[04 § footnote ²](04_RESULTS.md#footnote-2-cartesia-narration-dnsmos).

**Evidence:** [`analysis/campaign-20260809T204608Z/hygiene.json`](../analysis) +
[`quality.json` dnsmos_errors block](../analysis) +
[T1 verdict](../analysis/verification/T1_cartesia_clipping.md)

### F-5 · Orpheus is the "capped-and-peer-priced" archetype — not cheap, output-limited, worst WER

Orpheus's `cost_model.json` figure of **$0.030/1K words** is a
model artefact. `src/veval/analyze/cost.py` line 177 uses a
default "100-word session per generation" for per-generation
vendors; T8 measured Orpheus's actual per-call output as ~35 words
(14.59 s of audio × ~14.6 chars/s ÷ 5.87 chars/word). Under T8's
real per-call output the honest per-1K number is
**~$0.067-0.088** — peer-priced with OpenAI ($0.075). See
[04 § Cost calculus § ⚠ Orpheus](04_RESULTS.md#cost-calculus)
for the full derivation.

**What Orpheus actually is on this data:**

- **Not cheaper than OpenAI**, once you correct for the per-call
  cap
- **14.59-s output cap per call by Replicate wrapper default** —
  **27 of 75 narration items (36%) are truncated** at the default
  cap (long 8/8, medium 18/20, probe 1/15); the 8 long-stratum
  items lose ~84% of their expected content under the default. See
  [F-9 T8](#f-9--outlier-verification-verdicts-phase-2c) and
  [04 footnote ¹](04_RESULTS.md#footnote-1). **T10 (2026-09-07)
  confirmed the cap is a `max_new_tokens` default, not
  model-intrinsic**: passing `max_new_tokens = 2000` (Replicate's
  own wrapper ceiling) produces ~24.32 s per call (1.67× more
  audio). Per-1K cost at the raised cap: ~$0.040-0.053 (down
  from $0.067-0.088 under the default). Bounded fix — long
  narration still needs chunking, at ~1.67× fewer chunks. See
  [T10 verdict](../analysis/verification/T10_orpheus_max_new_tokens.md).
- **Worst WER** in the roster (27% mean, ~2× next-worst) —
  the mechanism is the output cap, not intelligibility
- **Widest between-draw variance** on quality signals

**But not artefact-driven on quality**: per-stratum recompute
(04 footnote ¹) shows Orpheus's narration AB.PQ mean of 8.002 is
essentially identical between the 48 complete items (mean 8.009)
and the 27 truncated items (mean 7.989) — Δ ≈ 0.02. Its per-call
rendering
is genuinely uniform-quality; the aggregate is earned.

**Impact:** Orpheus is a legitimate choice when: (a) every turn
comfortably fits under 14.59 s of audio at the default cap or
~24 s at `max_new_tokens = 2000` (so the cap never bites), AND
(b) worst-WER + no-cost-advantage is acceptable (e.g., an
experimental prototype, an open-weights preference, or a specific
voice character the closed vendors don't offer). For narration
or any long-form use on Replicate's hosted endpoint, the output
cap makes it structurally unsuitable at the default (T8) and
requires ~1.67× fewer but still-multiple chunks at
`max_new_tokens = 2000` (T10). **The old "budget dominates →
pick Orpheus" heuristic is retired** — on this data, if budget
dominates, OpenAI at $0.075 is the pick (peer-priced to Orpheus
even at Orpheus's raised cap, and passes both caps).

<a name="f-6"></a>
### F-6 · Monotonic loudness fade on long-form TTS narration — a cross-vendor phenomenon at ~5-25% base rate

Long-form TTS narration exhibits a monotonic loudness fade on a
subset of generations — the audio gradually loses ~2-3 dB from
first third to last third of a single call. Phase 1 observed it
first on ElevenLabs L03 (2.7 dB mean across 4 draws, 100% direction
reproducible); Phase 2 established it is **not L03-specific, not
ElevenLabs-specific, and not fully deterministic**.

**Phase 2 evidence** — the [F-6 experiment pack](EXPERIMENTS_2026-09-01.md):

| test | design | result |
|---|---|---|
| Follow-up 1 | drift analyzer on R3 primary-campaign L01..L08 for all 8 vendors' pinned narration voices | **4 / 64 (6.2%) fade at threshold** (Δ≥2 dB, monotonic-decr). ElevenLabs 25% (L02, L06), Deepgram 12% (L01), Orpheus 12% (L02), other 5 vendors 0%. **L03 itself does NOT fade on charlotte in R3** (Δ = −0.26 dB, non-monotonic). |
| Experiment A | 20 new long-form paragraphs on ElevenLabs charlotte | 2 / 20 fade at threshold (EMOT02, FACT03). 9 / 20 monotonically decreasing at any magnitude. |
| Experiment B | L03 on 5 different ElevenLabs voices | 2 / 5 voices fade (charlotte 2.79 dB, josh 2.92 dB); 3 / 5 don't (rachel, antoni, bella). Text × voice interaction. |
| Experiment C | L03 split into halves, generated as two independent calls | Full L03 fades 2.79 dB; half 1 fades 1.89 dB (below threshold); half 2 shows no fade. Cumulative state resets on fresh call. |
| Experiment E | alt-voice on OpenAI/Fish/Deepgram/Google on L01..L08 | OpenAI's nova voice fades on 2 / 8 items (25%); Deepgram/Fish/Google alt voices don't fade. |

**Impact:** long-form TTS narration on **at least ElevenLabs,
Deepgram, Orpheus, and OpenAI's affected voices** exhibits this
fade at 6-25% rate — high enough that a production pipeline
using long-form should include a loudness-drift monitor over
every generated audio. **The fade is stochastic across runs of
the same voice on the same text** (L03 fades 2.79 dB in one run
and 0.00 dB in another on the same day, same charlotte voice), so
avoiding specific "problem items" doesn't work — the problem items
shift. **Chunking mitigates**: splitting text at ≤500-char
boundaries drops the fade sharply.

Prior "reproducible L03 quirk on ElevenLabs" framing retracted;
see [CORRECTIONS row 22](../CORRECTIONS.md).

**Evidence:**
[`analysis/campaign-20260809T204608Z/drift.json`](../analysis/campaign-20260809T204608Z) (R2 original),
[`analysis/experiments-2026-09-01/item1_primary_narration_drift.json`](../analysis/experiments-2026-09-01/item1_primary_narration_drift.json) (R3 cross-vendor),
[`analysis/experiments-2026-09-01/drift.json`](../analysis/experiments-2026-09-01/drift.json) (A/B/C/E per-file),
[T4 verdict](../analysis/verification/T4_elevenlabs_L03_fadeout.md) (Phase 1 verification pack).

<a name="f-7"></a>
### F-7 · Voice choice within a vendor shifts AB.PQ at ≥3σ — including under same-gender swap on Speechify (T6 narration)

Speechify tops **both** Audiobox axes on **both** use cases with
the pre-registered voice picks. Verification (F-9 T6) tested
Speechify with a deliberately-different alt voice — `edmund_32`
scored **+0.30 higher on AB.PQ on conversational** (cross-gender:
pre-registered `geffen_32` female → `edmund_32` male) and
**+0.10 higher on narration** (same-gender: pre-registered
`wyatt_32` male → `edmund_32` male, T6 verdict "same gender
(both male)") and still ranked #1 across the 8 vendors on both
use cases.

**Phase 2 extension** — the [F-6 experiment pack's Follow-up 4](EXPERIMENTS_2026-09-01.md#follow-up-4--alt-voice-qualitywer-analysis-on-experiment-e-audio)
ran an alt-voice regeneration on 4 more vendors (OpenAI, Fish,
Deepgram, Google) on the same L01..L08 long-narration items, then
full Audiobox + DNSMOS + WER analysis. The correct inferential test
on n=8 matched pairs is a paired-z on per-item differences — the
same test the project uses everywhere else for quality claims:

| vendor | pinned R3 AB.PQ | alt E AB.PQ | mean Δ | SE_diff | **paired z on AB.PQ** |
|---|---:|---:|---:|---:|---:|
| OpenAI | 7.619 | 7.473 | −0.146 | 0.044 | **−3.28σ** |
| Fish | 7.710 | 7.869 | +0.159 | 0.031 | **+5.06σ** |
| Google | 8.032 | 7.927 | −0.105 | 0.014 | **−7.35σ** |
| Deepgram | 7.948 | 7.468 | −0.480 | 0.036 | **−13.46σ** |

**Every alt voice tested produces a statistically significant AB.PQ
shift on the same 8 items.** The smallest, OpenAI, is 3.28σ; the
largest, Deepgram, is 13.46σ. Direction is not stable (Fish
positive, others negative).

**Gender make-up of the swap pairs**: all four Phase 2 Follow-up 4
alt voices crossed gender against the pinned voice — OpenAI onyx
(male) → nova (female), Deepgram orion (male) → luna (female),
Google Charon (male) → Kore (female). Fish uses opaque UUIDs so
gender is not directly verifiable from the config, but the alt
was Fish's conversational-tagged voice against a narration-tagged
pinned — a different design confound (voice-purpose swap). **T6's
Speechify split by use case**: conversational was cross-gender
(geffen_32 female → edmund_32 male, +6.05σ AB.PQ); **T6 narration
was same-gender** (wyatt_32 male → edmund_32 male, verified in
[T6 verdict](../analysis/verification/T6_speechify_voice_bias.md), which says of the narration pair "same gender (both male)"),
paired-z on the 20-item T6 set = **+4.02σ AB.PQ**. **T6 narration
therefore already establishes a >3σ voice-choice effect that
survives gender matching within one vendor.** The four Follow-up-4
cross-gender pairs do not settle whether the voice-choice
signal survives gender matching *across* vendors (Deepgram's
−13.5σ is 3× OpenAI's −3.3σ; a same-gender sweep on the other
vendors could either flatten that spread or preserve it).

Prior "HOLDS / SHIFTS" verdict framing retracted; see
[CORRECTIONS row 25](../CORRECTIONS.md).

**What the data supports**:

- Every alt voice tested (5 vendors including Speechify's T6)
  produced a statistically significant AB.PQ shift from its
  pinned counterpart on the paired-z test (Speechify T6
  narration +4.02σ same-gender, +6.05σ conv cross-gender;
  Follow-up-4 vendors 3.3–13.5σ under cross-gender confound).
- Speechify's T6 narration result establishes that a within-
  vendor same-gender voice swap can shift AB.PQ at ≥4σ — the
  falsification test Phase 1 originally proposed for v2 is
  already satisfied on one vendor.
- Deepgram's Δ = −0.480 (13.5σ) is roughly 3× OpenAI's Δ = −0.146
  (3.3σ). The magnitude varies substantially across vendors and
  is a real between-vendor signal.
- Speechify's T6 rank-level result — alt scored higher and still
  ranked #1 across the 8 vendors — remains a rank-preservation
  observation (top-1 stable under a voice swap), not a "quality
  holds within noise" claim at the item level.

**What Phase 1 F-7 got right and got wrong**: T6 established that
Speechify's Audiobox #1 rank was not a lucky-voice-pick at the
rank level. Phase 2 + a re-read of T6's own numbers shows that
per-item scores shift under a voice swap in every vendor tested,
including under same-gender swap on the one vendor where the
same-gender test has been done, so the rank-level observation
does not carry to an item-level "quality is a vendor-family
property" claim.

**What a v2 same-gender sweep would need** (T6's Speechify
narration leg already answered this on one vendor at +4.02σ;
the sweep extends to the other 7): 2 same-gender voices per
vendor × 8 vendors × 20 items × 1 draw ≈ 320 fresh generations
(~$0.75, ~2 hours synthesis, ~10 hours analyzer wall-clock, or
a smaller 8-item pilot per vendor to keep it cheap). Compute
paired-z per vendor per axis. If same-gender paired-z stays >3σ
across the 7 other vendors (as it did on Speechify narration),
the current Follow-up-4 shifts are voice-choice effects, not
gender effects; if it drops <2σ on some vendors, those vendors'
Follow-up-4 shifts are attributable to the gender component.

**Evidence:** [`analysis/experiments-2026-09-01-E/quality.json`](../analysis/experiments-2026-09-01-E/quality.json) +
[`analysis/experiments-2026-09-01-E/wer.json`](../analysis/experiments-2026-09-01-E/wer.json) +
[`analysis/campaign-20260831T175358Z/quality.json`](../analysis/campaign-20260831T175358Z/quality.json)
(pinned R3 counterparts) +
[T6 verdict](../analysis/verification/T6_speechify_voice_bias.md) (Phase 1) +
[F-6 experiment pack Follow-up 4](EXPERIMENTS_2026-09-01.md#follow-up-4--alt-voice-qualitywer-analysis-on-experiment-e-audio) (Phase 2).

<a name="f-8"></a>
### F-8 · Audiobox's two axes split across the DNSMOS construct — PQ agrees, CE anti-correlates

The two-construct story the field usually tells about MOS
predictors ("Audiobox rewards warmth, DNSMOS rewards cleanliness")
turns out to be wrong on the axis that carries the Speechify
winner claim. Re-derivation from
`analysis/campaign-20260809T204608Z/cross_metric.json` shows
production_quality agrees with DNSMOS; content_enjoyment
anti-correlates.

**Per-pair Spearman ρ across 8 vendors, conversational**:

| pair | ρ |
|---|---:|
| audiobox.PQ vs dnsmos.p808 | **+0.571** ← strongest positive in the matrix |
| audiobox.PQ vs dnsmos.ovrl | +0.214 |
| audiobox.PQ vs dnsmos.sig | +0.119 |
| audiobox.PQ vs dnsmos.bak | +0.048 |
| **PQ-vs-DNSMOS mean** | **+0.238** (agree) |
| audiobox.CE vs dnsmos.p808 | −0.452 |
| audiobox.CE vs dnsmos.ovrl | −0.405 |
| audiobox.CE vs dnsmos.sig | −0.476 |
| audiobox.CE vs dnsmos.bak | −0.690 |
| **CE-vs-DNSMOS mean** | **−0.506** (anti-correlate) |
| **All 8 pairs mean (published headline)** | **−0.134** |

**Per-pair Spearman ρ across 8 vendors, narration**: PQ mean
**−0.167** (mixed sign — +0.095 with p808 and bak, −0.238 with
ovrl, −0.619 with sig), CE mean **−0.375** (all four negative).

**The published aggregate mean ρ of −0.13 (conv) / −0.27 (narr)
is a mix of two different behaviours**:
- **Audiobox PQ (production_quality) agrees with DNSMOS**,
  especially on conv (mean ρ +0.238, +0.571 with p808). The
  correct plain-English label for PQ is Meta's own:
  **technical cleanliness** (perceived audio quality — pleasant
  timbre, no distortion). 02_METHODOLOGY.md's D3 uses this label
  consistently.
- **Audiobox CE (content_enjoyment) anti-correlates with DNSMOS**,
  especially against bak_mos (background noise) at ρ = −0.690.
  CE is the axis that actually behaves like the "warm / engaging /
  aesthetic" axis in the two-construct story.

**Statistical caveats**:
- At n=8 vendors, Spearman ρ has a very wide 95% CI. **0 of 8
  individual PQ↔DNSMOS or CE↔DNSMOS pairs is significant at
  α=0.05** (min p = 0.058 conv, 0.102 narr for the strongest
  correlations). The aggregate mean ρ we publish is a
  point estimate on a small vendor sample; the CI easily spans
  strong-positive to strong-negative for the aggregate too.
- What the data supports:
  (a) The strongest single cross-pipeline correlation in the
      matrix is a **positive** one (PQ↔p808 at +0.571)
  (b) The CE↔DNSMOS pairs are systematically negative in both
      use cases
  (c) The two pipelines do NOT show a uniform positive rank
      correlation across all axes — but they do agree on one
      axis (PQ) more than a simple "different constructs"
      framing would imply

**Named per-vendor rank inversions** (independent of the
aggregate CI, cite these directly):

- **OpenAI narration**: Audiobox **#8 / #8** on PQ+CE, DNSMOS
  **#1 / #1 / #2** on P.835 three-scale. Perfect inversion.
- **Cartesia narration**: Audiobox #3 on PQ, DNSMOS #8 / #8 / #8
  on the three-scale (over the surviving 38 items)
- **Speechify conversational**: Audiobox #1 / #1, DNSMOS mid-pack
  (#3 / #5 / #6 / #6)
- **Orpheus conversational**: Audiobox #8, DNSMOS #3 on OVRL

**Interpretation:** the two Audiobox axes split across the DNSMOS
construct. PQ measures something DNSMOS also measures (audio-
quality cleanliness); CE measures something DNSMOS actively
de-preferences. **Speechify wins PQ on both use cases** — that's
a cleanliness-axis win, not a warm-axis win, even though
Speechify also wins CE (which is the warm-axis finding). The
two-construct story survives, but between Audiobox's two axes
rather than between the two pipelines in the aggregate.

**Impact:** a MOS score is only interpretable alongside the
construct its predictor rewards. Audiobox's two reported axes do
not measure the same thing as each other — PQ tracks the DNSMOS
cleanliness scales (mean ρ = +0.238; +0.571 against P.808), CE
runs against them (mean ρ = −0.506). Reporting either as "the
Audiobox score", or averaging the two, conceals that split.
Report the axis, not the pipeline.

**Evidence:** [`analysis/campaign-20260809T204608Z/cross_metric.json`](../analysis/campaign-20260809T204608Z/cross_metric.json)
(the `pairs` block per use case has the per-pair ρ; the
`cross_pipeline_mean_rho` field is the aggregate) ·
[figure 1](figures/f1_rank_inversion.png)

### F-9 · Outlier verification verdicts (Phase 2c)

9 targeted tests re-checked every headline outlier from Phase 2 on
fresh data. Full table + methodology in
[04_RESULTS.md § verification pack outcomes](04_RESULTS.md#verification-pack-outcomes-phase-2c).

**Highlights** (verdicts abbreviated):

- **T1 Cartesia clipping** — Confirmed (via F-4a triangulation, no
  regen needed)
- **T2 Orpheus WER** — Answered mechanically by T8 (14.59s output
  cap = incompletion, not intelligibility)
- **T4 ElevenLabs L03 fadeout** — Confirmed with refinement (3/3
  fresh regens fade monotonically; magnitude 2.7 dB not 3.6 dB)
- **T5 OpenAI latency** — Confirmed slower than ElevenLabs (all 3
  sessions). Session progression: 736 → 936 → 1369 ms p50; 956 →
  1493 → 1882 ms p90 across 2026-08-09 / -11 / -12. See F-11 for
  the refuted stability sub-finding.
- **T6 Speechify voice bias** — Confirmed with reversal (alt voice
  edmund_32 scores *higher* than pinned voices; still #1 of 9)
- **T7 ElevenLabs TTFA** — Faster than OpenAI in all 3 sessions
  (confirmed). But **not stable** — S3 showed 694/816 ms p50/p90
  vs S1's 439/479, a +58%/+70% shift. The prior "sub-500 ms p90
  reliably" claim held only for the first 2 sessions and was
  coincidence (see F-11).
- **T8 Orpheus cost** — **Refuted with a bigger finding**: Orpheus
  produces exactly **14.59 seconds** of audio per call regardless of
  input length (std dev 0.000s across 8 items). This is the single
  most-cited verification finding of the project.
- **N2 Fish noise floor** — Confirmed automatically (+12.6 dB
  above median; DNSMOS ONNX + hygiene analyzer are two independent
  code paths agreeing)
- **N1 OpenAI narration inversion** — Pending manual listen (n=1
  observer, low-signal at this scale)

**Meta-finding**: Verification produced 4 findings the primary
campaign didn't: T8's 14.59s output cap, T6's voice-swap reversal,
T4's L03 magnitude refinement, and F-11's session-to-session
latency variance. Of these, T8 and F-11 are the most consequential
— they reshape recommendations. Cheap replication ($0.61 +
~90 min in-scope + $0.02 for a 3rd latency session with concurrent
ping baseline) is where you learn which "findings" are lucky draws.

---

<a name="f-11"></a>
### F-11 · Latency absolute values are not stable session-to-session (6-session data)

TTFA rank is portable across sessions; absolute values are not.
**Six latency-mode runs per speed-critical vendor** across four
dates (2026-08-09, -11, -12, -09-01) — S1a and S1b (same-day pair),
S2, S3 (with concurrent Cloudflare-1.1.1.1 ping baseline), and
Phase 2's S4 + S5 (same-day pair on 2026-09-01, added as
[Follow-up 3](EXPERIMENTS_2026-09-01.md#follow-up-3--d-latency-sanity-check)).

| vendor | S1a p50 | S1b p50 | S2 p50 | S3 p50 | **S4 p50** | **S5 p50** | range | n per session |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ElevenLabs | 439 | 440 | 424 | **694** | **412** | **421** | 412–694 (+68%) | 50/50/40¹/40¹/50/50 |
| OpenAI | 736 | 762 | 936 | **1369** | **772** | **783** | 736–1369 (+86%) | 50/50/50/50/50/50 |

Phase 2's S4+S5 landed in the S1 baseline range for both vendors
— corroborates that **S3 was a real transient outlier, not the
new normal**. Rank held **6 of 6 sessions** (ElevenLabs < OpenAI
on both p50 and p90 in every session).

¹ ElevenLabs S2 **and** S3 both landed 40/50 trials. Verified from
`analysis/latency-20260811T183202Z/latency.json` `n_items = 40`
(S2) and `analysis/latency-20260812T191323Z/latency.json`
`n_items = 40` (S3). Mechanism (subscription credit exhaustion,
spend cap, per-session request cap) not diagnosed. 40 trials still
yields a well-defined p50/p90 at this magnitude (SE of p90 at
n=40 ≈ 1.25 × (SD of trial times / √40) ≈ ~40 ms for ~200 ms
trial-time SD — smaller than the +58% S1→S3 shift), but caps
confidence in tail behaviour beyond p90.

The concurrent ping baseline during S3 was clean (p50 = 8 ms, p90
= 12 ms, max = 29 ms, 0 errors on 274 probes) — **the last-mile
link to Cloudflare 1.1.1.1 was not the driver**. Yet BOTH vendors
slowed dramatically.

**What the ping baseline does NOT rule out** (scope-of-ruleout):

- **DNS resolution jitter** to vendor endpoints (we pinged one
  fixed IP; vendor endpoints resolve through DNS and TLS)
- **TLS-handshake latency** on the vendor endpoint (Cloudflare
  ICMP is unencrypted and shares no code path with an HTTPS
  streaming handshake)
- **Client-side parser / event-loop stalls** on the local Python
  runtime under this specific harness build (see item below)
- **Any specific vendor's serving-region capacity** independently
  of the other vendor

The ping baseline rules out **only the "ISP dropped packets during
the window"** hypothesis. It is a useful ruleout but a narrow one.

**Parsimonious client-side reading** (Occam-preferred, not proved):
both vendors moved in the same direction between S2 and S3. The
simplest single cause consistent with that pattern is **client-side**
(local machine contention, Python event-loop stalls, one-shot
antivirus / OS index scan during the window, or a client-parser
change between session builds). A vendor-side simultaneous slowdown
of two independent SaaS providers on the same day is possible but
not parsimonious. A properly-controlled follow-up would run each
session (a) from an isolated VM, (b) with warm-up trials excluded,
(c) with per-trial client-side CPU / event-loop lag logged, then
attribute variance to layers rather than to vendors.

**What the 6-session data can and cannot support**:

- **Can support**: rank stability (ElevenLabs faster than OpenAI in
  all 6 sessions). Rank tests are robust at low n.
- **Cannot support without further controls**: a per-vendor
  variance distribution claim. Six sessions clears the ≥5-session
  count Phase 1 called out, but Phase 1 also called for
  **client-side event-loop lag logging on each session** as a
  control (see § "What the ping baseline does NOT rule out" above).
  That was not run on any of the 6 sessions, so we cannot cleanly
  separate "wide-tail vendor" from "client-side contamination"
  even at n=6. "ElevenLabs is more stable than OpenAI"
  descriptively holds on this data (ElevenLabs p90 range 461–816,
  OpenAI 946–1,882 across the 6 sessions) but the mechanism is
  not fully attributed.

**Load-bearing claims**:

- ElevenLabs is **consistently faster than OpenAI** across all 6
  sessions (412–694 vs 736–1,369 range on p50). Ranking is
  stable.
- OpenAI TTFA is high — always at least 736 ms p50 on our
  measurements — which is the load-bearing claim for the "provision
  capacity for OpenAI's worst percentile" advice.

**Claims the data does not support**:

- "ElevenLabs Flash reliably hits sub-500 ms p90" — held on 5 of
  6 sessions (461–479 ms) but moved to 816 ms in S3.
- "Stability is a distinct vendor axis" as a portfolio-worthy
  headline without the client-side controls above. Descriptively
  ElevenLabs is tighter (excluding S3: p50 412–440 ms / 6.8%
  variance; p90 461–479 ms / 3.9%) than OpenAI (excluding S3:
  p50 736–936 ms / 27%; p90 946–1,493 ms / 58%); mechanism
  unattributed.
- Any capacity-planning implication that reads ElevenLabs' 461 ms
  p90 (S4) as an upper bound in either direction (S3 exceeded it
  substantially).

**Impact on PM recommendations**: don't provision from one
measurement session. For a real deployment plan, budget the tail
observation across ≥5 sessions on the vendor's serving region from
your actual deployment environment, with client-side lag logged and
warm-up trials excluded — public-tier measurements without lag
logging (which is what we have, at n=6) are not enough to
*attribute* the tail. Rank claims survive at n=6; descriptive
variance ranges are reportable; mechanism attribution still needs
the lag-logged sweep.

**Evidence** — per-session `latency.json` files committed under
`analysis/latency-*/`:

| session | ElevenLabs run ID | OpenAI run ID |
|---|---|---|
| S1a | [`latency-20260809T214106Z`](../analysis/latency-20260809T214106Z/latency.json) | (same run) |
| S1b | [`latency-20260809T222356Z`](../analysis/latency-20260809T222356Z/latency.json) | (same run) |
| S2 | [`latency-20260811T183202Z`](../analysis/latency-20260811T183202Z/latency.json) (n=40) | [`latency-20260811T183028Z`](../analysis/latency-20260811T183028Z/latency.json) |
| S3 | [`latency-20260812T191323Z`](../analysis/latency-20260812T191323Z/latency.json) (n=40) | [`latency-20260812T191143Z`](../analysis/latency-20260812T191143Z/latency.json) |
| S4 | [`latency-20260901T185715Z`](../analysis/latency-20260901T185715Z/latency.json) | [`latency-20260901T190715Z`](../analysis/latency-20260901T190715Z/latency.json) |
| S5 | [`latency-20260901T191000Z`](../analysis/latency-20260901T191000Z/latency.json) | [`latency-20260901T201051Z`](../analysis/latency-20260901T201051Z/latency.json) (T19:10 attempt crashed, rerun at T20:10) |

Ping baseline log: [`analysis/ping-baseline-20260812T191138Z.jsonl`](../analysis/ping-baseline-20260812T191138Z.jsonl)
— 274 probes to Cloudflare 1.1.1.1 during the S3 window.
Analysis: [`scripts/latency_with_ping.py`](../scripts/latency_with_ping.py).

**Portfolio takeaway**: the T5/T7 pair and the 6-session sweep
together demonstrate the value of stacking sessions and the
persistent limit of not running client-side controls. Six
sessions falsifies a distributional stability claim built on 2
and supports the descriptive-variance range; mechanism attribution
still needs client-side lag logging.

---

<a name="f-12"></a>
### F-12 · ElevenLabs shifted downward on both Audiobox axes and DNSMOS P.808, not on the P.835 triad (both use cases) between R2 and R3

Under the paired per-item test the project uses for every other
quality claim (Δ_i on the same 75 items, R3 − R2; SE_diff on the
per-vendor SD of the item-wise differences; z = mean_diff /
SE_diff), ElevenLabs shows a statistically significant downward
shift on **6 of its 12 quality-axis × use-case cells** — and the
6 are structured, not scattered:

| use case | axis | n paired | Δ (R3 − R2) | SE_diff | paired z | |z| > 2 ? |
|---|---|---:|---:|---:|---:|---|
| conv | **AB.PQ** | 75 | −0.074 | 0.017 | **−4.36σ** | ✓ significant |
| conv | **AB.CE** | 75 | −0.045 | 0.015 | **−2.92σ** | ✓ significant |
| conv | **DN.p808** | 74 | −0.039 | 0.017 | **−2.26σ** | ✓ significant |
| conv | DN.ovrl | 74 | −0.010 | 0.010 | −0.98σ | not |
| conv | DN.sig | 74 | −0.006 | 0.008 | −0.80σ | not |
| conv | DN.bak | 74 | −0.006 | 0.008 | −0.76σ | not |
| narr | **AB.PQ** | 75 | −0.074 | 0.010 | **−7.32σ** | ✓ significant |
| narr | **AB.CE** | 75 | −0.048 | 0.009 | **−5.09σ** | ✓ significant |
| narr | **DN.p808** | 75 | −0.047 | 0.013 | **−3.69σ** | ✓ significant |
| narr | DN.ovrl | 75 | −0.023 | 0.014 | −1.56σ | not |
| narr | DN.sig | 75 | −0.014 | 0.009 | −1.48σ | not |
| narr | DN.bak | 75 | −0.020 | 0.014 | −1.38σ | not |

*The 4 conv DNSMOS cells are n=74 because one conversational item
failed DNSMOS scoring on the R3 pass (R3 `n_valid = 74` on all four
DNSMOS axes; R2 was `n_valid = 75`). The paired-z test uses the
intersection of the two rounds' valid-item sets. The 8 Audiobox +
narration DNSMOS cells are the full n=75.*

**The 6 significant axes partition by scoring model, not by
construct.** The three scoring models we run on each audio file
are: (a) Meta's **Audiobox Aesthetics** model, which outputs two
axes PQ + CE that F-8 established are on *opposite* sides of the
DNSMOS construct axis (PQ agrees with DNSMOS at ρ mean +0.24; CE
anti-correlates at ρ mean −0.51); (b) Microsoft's **DNSMOS
P.808** single-model predictor, which outputs one axis
(`p808_mos`); and (c) Microsoft's **DNSMOS P.835** three-scale
predictor, which outputs three axes (`ovrl_mos` / `sig_mos` /
`bak_mos`) from a shared internal representation. The 6
significant ElevenLabs cells are the outputs of models (a) and
(b) on both use cases; the 6 non-significant cells are the
outputs of model (c) on both use cases. **The split is by
scorer architecture — two of three scoring models detected the
ElevenLabs drift, the third didn't.** It is not a construct
split: F-8 already shows Audiobox PQ and Audiobox CE track
different constructs, so bundling them under one "construct
cluster" would contradict F-8. Whether P.835 missed the drift
because it is less sensitive to whatever ElevenLabs changed, or
because ElevenLabs changed something P.835's construct
(overall / signal / background separation) genuinely does not
index, is not separable from this data.

**Multiplicity caveat**: 12 axes are NOT 12 independent trials.
The three DNSMOS P.835 axes are correlated by construction; AB.CE
correlates with DNSMOS at ρ = −0.51 by construct; even within
Audiobox, PQ and CE correlate at Spearman ρ = +0.31 at the
*vendor-mean* level and much more tightly at the *item* level
(Spearman ρ ≈ +0.81 on conv, +0.57 on narr for ElevenLabs' 75
items; Pearson r ≈ +0.79 / +0.71 on the same items) — the
paired-z tests are item-level, so the effective dependence is
even larger than the vendor-level ρ suggests. A sign-count
argument ("12 of 12 negative") is much less than 1-in-4096
impressive on correlated axes. Bonferroni correction within the
12 ElevenLabs tests (threshold |z| > 2.87) moves DN.p808 conv
(z = −2.26) below the line; conv AB.CE (z = −2.92) survives
**marginally** (0.05σ above threshold); the other 4 cells clear
comfortably. Under the sharper Bonferroni-96 correction (all 8
vendors × 12 axes, threshold |z| > 3.47), only the 4 largest-|z|
ElevenLabs cells survive — narr AB.PQ (−7.32σ), narr AB.CE
(−5.09σ), conv AB.PQ (−4.36σ), narr DN.p808 (−3.69σ).

**Comparison vendors under the same paired-z test**: three
non-ElevenLabs cells cross the raw |z| > 2 threshold — Speechify
narration AB.CE (−2.49σ), Speechify narration DN.sig (+2.03σ),
Fish narration DN.p808 (+2.06σ). Across 96 tests at α = 0.05,
you expect roughly 5 cells that size by chance alone, so three
observed under-independence is *fewer* than chance would produce,
and none survives Bonferroni-12 or -96. Every other axis on
every other vendor lands at |z| < 2. **The claim that
distinguishes ElevenLabs is not "only vendor with any |z| > 2
shift"** — that would be false — **but "only vendor with any
Bonferroni-surviving shift, and the surviving cells partition
by scoring-model architecture (Audiobox + DNSMOS P.808 shifted,
DNSMOS P.835 did not)."** That is the stronger and true
claim.

**Mechanism** — and where the naive read gets it wrong:

The ElevenLabs conv pin is [`eleven_flash_v2_5`](../configs/voices.yaml),
the narr pin is [`eleven_multilingual_v2`](../configs/voices.yaml)
(the `reasoning` field for the narr row says in capitals
"**a DIFFERENT model from the conversational entry above**"). Both
show the same-direction, same-scorer-partition shift (narration
is stronger at −7.32σ than conversational's −4.36σ on PQ).
**A single-model update does not explain the pattern** — one
update would touch one model, not both. The two-model
synchronous drift points at something shared:

- **Voice embeddings** (voice IDs are picked from ElevenLabs' voice
  library; the underlying embedding representation may be shared
  across Flash and Multilingual)
- **Serving / post-processing** (audio codec, sample-rate
  resampling, loudness normalisation, or a shared pre-emphasis
  filter on the serving side)
- **Client-side cause specific to the ElevenLabs adapter** —
  ruled out by `git log`: [`src/veval/adapters/elevenlabs.py`](../src/veval/adapters/elevenlabs.py)
  has been unchanged since commit `8372dbd` on 2026-08-07, two
  days before R2 and 24 days before R3. If the adapter was going
  to bias the score, it would have biased both runs the same way.

We have no vendor-side model-version metadata per call, so the
Voice-embedding vs serving-chain question is not settled from
client-side data alone.

**Interval**: R3 ran fresh (`--no-cache`) on 2026-08-31. R2's
`analysis/campaign-20260809T204608Z/latency.json` shows
`n_fresh = 0` for every vendor — R2 was a cache-only replay,
and the manifest records only the cache-hit timestamp (2026-08-09),
not the underlying synthesis date. The honest interval is
**"between R2's unrecorded synthesis date (≤ 2026-08-09) and
2026-08-31"**, not "between 2026-08-09 and 2026-08-31".

**What the data supports**:

- 5 of 6 ElevenLabs shifts on the Audiobox + DNSMOS-P.808
  scorer partition (AB.PQ + AB.CE + p808, both use cases)
  survive Bonferroni-12 (threshold |z| > 2.87). Conv AB.CE
  (z = −2.92) survives **marginally**, 0.05σ above threshold.
  The 6th (DN.p808 conv, z = −2.26) is significant at α = 0.05
  uncorrected but does not survive Bonferroni-12. Under the
  sharper Bonferroni-96 across all 8 vendors × 12 axes, 4
  ElevenLabs cells survive (the two AB.PQ cells + narr AB.CE +
  narr DN.p808).
- No ElevenLabs shift is significant on the DNSMOS P.835 triad
  (ovrl / sig / bak) on either use case.
- **No other vendor has any Bonferroni-surviving shift** — three
  non-ElevenLabs cells cross the raw |z| > 2 threshold (Speechify
  narr AB.CE, Speechify narr DN.sig, Fish narr DN.p808), fewer
  than the ~5 expected across 96 tests under independence, and
  none survives Bonferroni-12 or -96.
- The two ElevenLabs models — Flash v2.5 conv and Multilingual v2
  narr — moved the same direction on the same scorer partition
  (Audiobox + P.808), so a **single-model update does not explain
  the pattern** (two independent models updating in the same
  direction in the same window is possible but not parsimonious).
- The adapter file was unchanged across both runs; a client-side
  adapter-code cause is ruled out cleanly.

**What the data does NOT support**:

- "ElevenLabs regressed on every quality axis" — a sign-count
  claim that does not survive the paired test. Half the axes did
  not move significantly. The correct statement is: ElevenLabs
  regressed significantly on both Audiobox axes and DNSMOS P.808;
  the DNSMOS P.835 triad (ovrl / sig / bak) did not move.
- That ElevenLabs' voice quality *audibly* changed between R2
  and R3 — the shifts are small in absolute terms (max −0.074 on
  an AB.PQ scale of 0–10, ≈ 0.7% of scale). This is a numerical-
  drift observation, not an audible-regression claim.
- A single-model-update explanation (see above).

**Impact on published rankings**: none of R2's headline claims
change under R3. ElevenLabs remains #1 fastest TTFA, its Audiobox
+ DNSMOS ranks are essentially unchanged relative to the pack,
and its leads / gaps over the tie band remain within tie bounds.
But **any absolute-value quotation of an ElevenLabs quality score
should be dated** to the run that measured it.

**Load-bearing takeaway**: this is the finding the "measurement
date on every finding" discipline exists to catch. It is
invisible without a replication campaign, and it is a live
example of why any static single-shot benchmark drifts out of
usefulness over time — the vendor didn't announce a change, but
one appears to have shipped that two of three scoring models
detect (Audiobox + DNSMOS P.808) and the third (DNSMOS P.835)
does not.

**Evidence**:
- Paired-z per axis: reproducible from
  [`analysis/campaign-20260809T204608Z/quality.json`](../analysis/campaign-20260809T204608Z/quality.json)
  and
  [`analysis/campaign-20260831T175358Z/quality.json`](../analysis/campaign-20260831T175358Z/quality.json),
  matched on (provider, use_case, item_id).
- Per-vendor R2 → R3 delta table (raw signs, all 8 vendors):
  [`analysis/round3-vs-round2-comparison.md`](../analysis/round3-vs-round2-comparison.md).
- Two-model pin: [`configs/voices.yaml`](../configs/voices.yaml)
  `elevenlabs.conversational.model` = `eleven_flash_v2_5`,
  `elevenlabs.narration.model` = `eleven_multilingual_v2`.
- Adapter file unchanged since 2026-08-07:
  `git log --follow src/veval/adapters/elevenlabs.py` shows one
  commit, `8372dbd`, predating R2.
- R2 cache-only, no synthesis date: `by_provider[*].n_fresh = 0`
  in
  [`analysis/campaign-20260809T204608Z/latency.json`](../analysis/campaign-20260809T204608Z/latency.json).

---

## Friction points

*Portfolio-worthy narratives that emerged during the work. Every
one is backed by a specific artefact.*

### The killed weighted-composite score

The v1 plan had `quality_score = 0.4·PQ + 0.3·CE + 0.2·MOS + 0.1·noise`.
Cut it in Phase A. **Weights are always arguable; pre-registered
gates are falsifiable.** The v2 model has hard gates (pass/fail
against thresholds committed in `configs/gates.yaml`, adjudicated
in 04) + Pareto frontiers with bootstrap-CI domination on remaining
axes. The **frontier + bootstrap-CI half of that model was not
executed in v1** — the `frontier.py` module exists but no
`analysis/score.json` was produced; 04 reports per-axis SE(diff)
tie bands as the v1 substitute (see [07 § gap 8](07_GAPS_AND_FUTURE_WORK.md)).
A reader who prefers their own weighting can construct one from
the raw data; nobody can undo a pre-registered hard gate.

### The VERSA drop

The v1 plan chose VERSA (aggregation library for 80+ MOS metrics)
partly to reduce dependency friction. VERSA turned out to force a
Linux-container build for **5 of its 80 metrics**. The uv-managed
environment was already doing the reproducibility work VERSA was
hired to do. Killed VERSA, called the underlying libraries directly.
Second "kill your own decision" moment.

### The Canary catch — judge independence as a written constraint

Late in Phase B, considering swapping the second WER judge from
faster-whisper to NVIDIA's Canary-1B (cleaner PyTorch integration,
lower memory). Almost did it. Then noticed: Canary and Parakeet (our
first judge) share NVIDIA's FastConformer encoder family *and* their
Canary-1B-v2 training-data pipeline. Would have quietly gutted the
agreement rule.

**Judge independence is now a Pydantic `model_validator` on
`AnalyzersFile` in
[src/veval/config.py](../src/veval/config.py) that reads the org /
family / pipeline metadata from
[configs/analyzers.yaml](../configs/analyzers.yaml), not a lucky
property.** The validator refuses any pair of judges that share
organisation OR encoder family OR training pipeline.

### The T6 reversal

The T6 test was designed to catch "did I cherry-pick the Speechify
voice?" Answer came back: **the alt voice (`edmund_32`, UK male
bright) scored higher on Audiobox than the pinned voice (`geffen_32`,
US female warm) by +0.30**. Reversal of the test's original
direction — the pre-registered pick was *conservative*.

Wrote it up as *reversal-with-implication* rather than declaring
victory: Speechify's Audiobox lead is a Simba-3.2 model signature,
not a voice property. Portable insight.

### The T8 output-cap discovery

The T8 test was scoped as "does per-call cost scale linearly with
text length?" The data came back with **audio duration = 14.59s
stdev = 0.000s across 8 different inputs**. That's a hard model
output cap, not stochastic behaviour. Simultaneously refuted T8's
"linear cost" hypothesis AND explained T2's mysterious 27% WER
(it's not intelligibility — the model can't say more than ~15
seconds of speech per call).

**One 8-item test resolved two separate outliers.** Full analysis
in [`scripts/_t8_analysis.py`](../scripts/_t8_analysis.py) +
[T8 verdict](../analysis/verification/T8_orpheus_cost.md).

### The BT deferral

The operative pre-registered target for this campaign was
**216 judgments** per
[`DEVIATIONS.md` D-009](../DEVIATIONS.md#d-009) (`prereg-v1.7`)
— 36 pairs across the 9-system roster × 2 use cases × 3 reps.
Under D-009 the target and the spec's 3-rep minimum floor
collapse to the same number for the 9-system roster: 216 IS
the 3-rep floor. The 5-rep design would have been 360; D-009
compressed to the spec minimum-viable rep count. Executable at n=1 self-rater, but the bootstrap CIs
would be *conditional on the single rater* — two n=1 raters could
produce non-overlapping "95% CIs" on opposite preferences.
Publishing such CIs would read to a casual reader as "we confirmed
this with rigor" — a shape of over-claim this project refuses to
make.

Deferred to v2 with written rationale (see D-H below). The
methodology-craft insight is: *naming an epistemic limit and
refusing to fill it dishonestly is a stronger position than
executing the ceremony and disclaiming the result*.

### The 79-defect sweep + external red-team review

A **79-defect internal review** and a separate **external red-team
pass (R1–R10)** happened in Phase B before any campaign data
existed. The output landed in Phase B configs + Pydantic models
(judge independence, WER threshold clauses, noise-floor rule
naming, gate na_policy, Orpheus cost correction 24× down, ElevenLabs
credits corrected, TTSDS2 noise reference, WER normaliser hash).
Nine of the ten external reviewer points were already covered by
the internal sweep — but the tenth (a substantive
after-reading-the-plan critique) is the one that most improved the
final plan.

---

## Decisions

*The decision log. Each entry: what changed, why, alternatives
considered, impact. Roughly ordered by when they were made.*

<a name="d-a"></a>
### D-A · Skip TTSDS2 in first analyzer run

TTSDS2 requires ~30 GB of reference-set downloads that would have
blocked the analyzer pipeline for hours. The v2 plan explicitly
pre-registered this as a fallback: `--skip-ttsds` produces Audiobox-only
output and the split-half stability check runs on Audiobox PQ.
**Not a deviation — plan-anticipated escape hatch.** Mitigated by
D-B (adding DNSMOS as the second MOS pipeline).

<a name="d-b"></a>
### D-B · Add DNSMOS via speechmos (D3 second pipeline)

Added Microsoft DNSMOS as the second independent MOS pipeline
after TTSDS2 deferral. UTMOS was the first choice — blocked on
Windows by fairseq's source-build cliff (no Windows wheels for any
fairseq version, even with Developer Mode + elevated shell).
Rejected NISQA (pins `torch==2.2.1` — would cascade-break our env).
**speechmos** ships ONNX weights (~10 MB) with the pip package, no
torch conflict.

Produced F-8's headline cross-pipeline disagreement finding. Also
enabled F-4a's third pipeline for the Cartesia clipping story via
`speechmos`'s peak-out-of-range refusal behavior.

Landed as `prereg-v1.10` per [D-011 in DEVIATIONS.md](../DEVIATIONS.md#d-011).

### D-C · Reduce BT scope — drop human anchor

The BT plan pinned by [`D-009`](../DEVIATIONS.md#d-009)
(`prereg-v1.7`) at **216 judgments** for the 9-system roster
included an anchor recording (the evaluator's own voice,
unprocessed) as a reference point for "human-like." Cut the
anchor from the plan — the recording overhead and consent
complications aren't worth the additional axis for portfolio
scope. Dropping the anchor takes the roster from 9 systems back
to 8, so the arithmetically consistent judgment count becomes
**168** (28 pairs × 2 use cases × 3 reps). That revision was
logged in the archived RESEARCH_LOG but never landed in its own
`prereg-v1.N` config amendment before D-H deferred the panel
entirely, so no single ratified pre-registered figure survives
the D-C anchor cut. D-009's 216 is the last landed target;
168 is the arithmetic implication D-C would have re-tagged
had the panel not been deferred first.

### D-D · Outlier verification test pack — symmetric winner + loser tests

Every outlier claim from Phase 2 gets a targeted verification test
that can *confirm* or *refute* the finding on fresh data — winners
and losers same scrutiny. Killed the "we only re-verify losers"
asymmetry that leaves winners un-audited. Produced Phase 2c's
9-test pack (F-9), including the T6 reversal and T8 output-cap
discoveries that neither original hypothesis expected.

### D-E · Publish three enterprise decision frameworks, not one composite

Instead of one weighted composite ranking, the report presents
**three decision frameworks** the reader can apply:

1. **Hard-constraint hierarchy** — structural rule-outs first
2. **Risk-adjusted cost** — effective cost after failure-mode overhead
3. **Reader-adjustable weights** — bring your own weights over the
   raw data

Weights are local; the raw data is universal. Publishing the raw
data lets a reader construct any composite they want; publishing
only a composite forces them to accept our weights or discard the
report.

### D-F · CPU-only analyzer execution

Runs the whole analyzer chain on commodity CPU hardware. No
validity impact on scores (deterministic transforms of audio bytes);
GPU reproducers observe identical scores at 5-10× the speed. This
demonstrates the evaluation is reproducible without cloud spend.

Documented as a reproducibility receipt in
[`configs/hardware.yaml`](../configs/hardware.yaml).

<a name="d-g-enterprise-portability"></a>
### D-G · Enterprise portability disclosure

Absolute TTFA / RTF numbers are labeled as **residential Windows 11 measurements taken at
one point in a session-to-session distribution** — F-11 showed
they are not upper bounds. Provider *rankings*
are portable to enterprise deployments; absolute *values* are
session-to-session observations, not ceilings (F-11). Alternative
(re-measure on cloud VMs colocated with each vendor's serving
region, across ≥5-10 sessions per venue to match F-11's evidence
threshold for the client-side environment, not the ≥3 v2 design
target this block previously named) is a 1-3 day workstream not
justified at portfolio scope; deferred to v2.

<a name="d-h-bt-deferred-to-v2"></a>
### D-H · Phase 3 BT deferred to v2

The full Bradley-Terry rating campaign — last pre-registered
at **216 unique judgments** plus a **~10% consistency-repeat
block (~22 rerated items, ≈238 total rated items on the rater's
side)** per [`D-009`](../DEVIATIONS.md#d-009) (`prereg-v1.7`),
implemented by `src/veval/human/pair_builder.build_manifest`
— is **not executed** in v1. Deferred to a proper v2 multi-rater
pass. The 216 figure other passages in this doc refer to is the
distinct-comparison count; the 238 is what a rater would
actually sit through.

**Why**: BT's bootstrap CIs at n=1 rater are conditional on the
single rater — they answer "would this rater still prefer A over B?"
NOT "would a different rater prefer A over B?" Two n=1 raters could
produce non-overlapping "95% CIs" on opposite preferences, both
statistically valid, both worthless as human-preference evidence.

Publishing such CIs would read to a casual reader as "we confirmed
this with statistical rigor." That's a shape of over-claim this
project refuses to make.

**What we have instead**: 6 machine quality signals from 2
independent MOS pipelines + cross-pipeline agreement analysis
(F-8) + 9-test verification pack. The load-bearing PM claim
("pick the MOS pipeline that matches your listener use case") is
directly supported by that data; it doesn't require human
validation.

**Reversibility**: Reversible with two small code additions. The
BT machinery — `veval rate {build,normalize,serve,fit}` driving
[`src/veval/human/`](../src/veval/human/) (`pair_builder.py` for
paired items, `loudness.py` for −18 LUFS normalization, `bt.py`
for the fit + bootstrap CIs) — is implemented and unit-tested. A
v2 pass at n≥15-30 raters would additionally need (a) a
`veval invites` tokened-URL builder (described in the spec, never
written) and (b) a small glue call from `veval rate fit`'s BTFit
output into [`src/veval/score/frontier.py`](../src/veval/score/frontier.py)
to produce the frontier receipt that gap 8 names.

See [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) for
the full v2 roadmap.

<a name="d-i"></a>
### D-I · D7-timing descoped (friction reported, wall-clock unrecoverable)

Spec § A.7 pre-registers **two** D7 outputs: a wall-clock timed
docs-to-first-audio session per provider ("DX minutes"), and a
friction log. Timing is formally **descoped**; friction is
reported.

**Why timing is descoped, not deferred**: unlike D-H (BT panel,
executable at v2), the DX-minutes measurement is *unrecoverable*
by [`dx/friction_log.md`](../dx/friction_log.md)'s own
pre-registered rule: *"Cannot be reconstructed later — event
timestamps and specific errors are the measurement. Start the
clock at 'open provider docs' for each provider and log every
friction event as it happens."* The clock wasn't started. Three
log entries explicitly declare their own wall-clock figures
void — Fish (*"wall-clock time for adapter authoring is NOT [a
D7 measurement]"*), Google (*"user opened Google docs, so
wall-clock time is not a true D7 measurement"*), OpenAI (*"from
prior API knowledge, so wall-clock isn't a valid D7
measurement"*). All 8 `DX minutes` cells in the log read
`TODO`. A v2 run on the same 8 vendors cannot recover the
first-time-onboarding tail because the developer has already
onboarded.

**What was published instead** — friction as a reported
dimension: the 8-vendor friction log, a taxonomy (signup · auth
· first call · undocumented behaviour · errors-as-data ·
streaming ergonomics · model/voice mapping · audio-format
quirks), an audio-format fact-sheet verified through Phase F,
4 cross-provider patterns, 3 environment gotchas. See D7
section in [02](02_METHODOLOGY.md#d7--developer-experience--friction-reported-timing-descoped-d-i)
for the write-up + [F-1a](#f-1a) for the load-bearing catch that
came out of it.

**Reversibility**: not reversible for the R2 + R3 measurement
period (the clock rule makes the measurement recovery-proof).
Fresh timing measurements on a v2 developer + fresh vendor
onboarding *would* be a legitimate DX-minutes v2 run — but that
is a different measurement (a v2 developer's tail, not this
project's), and the honest framing is that the pre-registered
v1 timing metric is void.

---

## Threats to validity

*What could make the findings wrong. Each threat is either
mitigated (mitigation named) or documented as a v2 workstream.*

### Structural

- **n=1 rater for human perceptual dimension** (D-H) → deferred to v2
- **One voice per vendor** — voice choice can shift scores by up
  to ~35% of cross-vendor spread on Audiobox. Phase 2 Follow-up 4
  extended the alt-voice test from 1 vendor (Speechify via T6) to
  5 (adding OpenAI, Fish, Deepgram, Google); every alt-voice pair
  produced a statistically significant AB.PQ shift under the
  paired test (see F-7). T6's Speechify narration leg (wyatt_32
  → edmund_32) is same-gender and shows +4.02σ, so voice-choice
  effects survive gender matching on at least Speechify; the four
  Follow-up-4 pairs are all cross-gender, so on the other 7
  vendors the voice-vs-gender split is not yet separated.
  Residual gap: **same-gender** voice sweep across the other 7
  vendors is a v2 workstream (see
  [07 § gap 2](07_GAPS_AND_FUTURE_WORK.md#2-one-voice-per-vendor-per-use-case-partially-closed-by-phase-2))
- **Corpus authored by evaluator** — committed to git for
  reproducibility with alternate corpora → deferred to v2
- **English only** — multilingual claims untested → deferred to v2
- **Residential Windows 11 measurement environment** (D-G) →
  rankings portable, absolutes are one-session observations (F-11); enterprise VM
  baseline deferred to v2
- **Paid public tiers, not enterprise contracts** — SLA + volume
  discount contracts may produce different behavior → deferred to
  v2 enterprise-tier partner replay

### Fixable within v1

- **wav2vec2 judge inflates absolute WER** (F-2) → mitigated by
  reporting WER as relative-ranking-only
- **TTSDS2 skipped** (D-A) → mitigated by D-B (DNSMOS second pipeline)
- **Ranking depends on MOS predictor family choice** (F-8) →
  mitigated by publishing both matrices and naming rank inversions
  rather than aggregating
- **Single-session latency** → 6 total sessions across 4 dates
  (S1a, S1b, S2, S3, S4, S5) on the two speed-critical vendors;
  descriptive-variance claim is now sustainable (ranking stable
  in all 6 sessions), but the client-side event-loop lag logging
  that Phase 1 called for as a control was not run on any of the
  6 sessions, so mechanism attribution ("wide-tail vendor" vs
  "client-side contamination") remains a v2 workstream. See
  [F-11](#f-11).
- **Cartesia clipping: systemic or batch?** → mitigated by F-4a
  triangulation

### Cannot mitigate in current scope

Full list in [07_GAPS_AND_FUTURE_WORK.md § Deferred by scope](07_GAPS_AND_FUTURE_WORK.md#deferred-by-scope-not-attempted-in-v1).

---

## Pre-registered amendments

Every deviation from the pre-registered plan (`prereg-v1` through
`prereg-v1.10`) is logged with rationale in
[**../DEVIATIONS.md**](../DEVIATIONS.md). Highlights:

- **D-001** — Interpreter pinned to stable Python 3.11 (fixed rc1 leak)
- **D-002** — Corpus authored fresh, not curated from parent
- **D-003** — Provider roster expanded 6 → 8 (added OpenAI + Speechify)
- **D-004** — Orpheus pinned to community fine-tune
- **D-005** — Orpheus version SHA pinned; adapter uses version-explicit endpoint
- **D-006** — OpenAI narration model corrected; Speechify concurrency 3 → 1
- **D-007** — OpenAI narration voice cedar → onyx (not in tts-1-hd enum)
- **D-008** — Speechify endpoint reverted to /v1/audio/speech; TTFA not measurable
- **D-009** — D4 pairwise repetitions 5 → 3 (compressed default)
- **D-010** — Judge 1 swapped from parakeet-rnnt → wav2vec2 (transformers can't load parakeet_rnnt)
- **D-011** — DNSMOS added; UTMOS attempted, blocked on Windows

Each amendment is git-tagged (`prereg-v1.N`) at the commit that
introduced it. Every amendment predates the results that use it —
the "predates the data" property is what makes the pre-registration
falsifiable.

---

## Where to go next

- [04_RESULTS.md](04_RESULTS.md) — full per-provider data tables
  behind these findings
- [05_CASE_STUDY.md](05_CASE_STUDY.md) — the story arc of how
  these findings were extracted, in narrative form
- [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) — what
  wasn't done and what a v2 pass would look like
- [02_METHODOLOGY.md](02_METHODOLOGY.md) — the *why* behind every
  methodology choice
- [../DEVIATIONS.md](../DEVIATIONS.md) — the 11 pre-registered
  amendments with full rationale
- [../analysis/verification/](../analysis/verification/) — per-test
  verdict files for the 9-test Phase 2c pack
