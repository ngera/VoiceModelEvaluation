<!--
Case study — Voice AI evaluation, portfolio edition.
Author: Neeraj Gera · Date: 2026-08-11
Audience: PMs, engineers, and buyers who need to choose a
text-to-speech vendor — and anyone interested in what "measuring
quality" actually means when the definition of quality itself is
contested. GitHub renders unknown YAML frontmatter as a raw table
so this metadata lives in an HTML comment instead.
-->

# What we found evaluating 8 voice AI vendors — and what it says about picking one

*A portfolio case study in structured evaluation, self-critical
scoping, and killing your own decisions.*

*A three-week portfolio project. 8 vendors, 2 use cases, 6 machine-quality
signals from 2 independent pipelines, a 9-test outlier verification pack,
and no human perceptual panel. The reason we didn't run the human panel
is one of the findings.*

> **⚠ Scope disclaimer** · Findings as of 2026-08-12 on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. No financial
> relationship with any vendor. Not legal / business / purchasing
> advice. All findings apply to *our specific tested configuration
> of each vendor*, not a universal statement about the vendor's
> technology. Full scope in [DISCLAIMER.md](../DISCLAIMER.md).

---

## The setup

I'd previously written a 400-hour evaluation plan for 12 voice AI
vendors across 10 use cases with a 16-dimension scoring matrix.
Beautiful spec. Wrong for a portfolio project.

The first decision — the sequencing decision that made everything
downstream possible — was to shrink the plan to **8 vendors × 2 use
cases × 75 corpus items**. Two use cases chosen precisely because
they pull in opposite directions: a **support-agent** voice needs
low latency + intelligibility + warmth; a **long-form narration**
voice needs consistency + expressive range. A vendor that wins one
and loses the other is the *expected*, most instructive outcome, and
it is what the two-use-case design was chosen to expose.

Three weeks and roughly **$13 of metered vendor spend later** (see
receipt below), we have:

- 1,200 audio files across the 8 × 2 × 75 grid
- 6 quality signals per (vendor, use case) — Meta's Audiobox on 2
  axes (one anti-correlates with DNSMOS, one agrees with it — see
  F-8) and Microsoft's DNSMOS on 4 signal-cleanliness axes
- A latency dataset with **six 50-trial sessions total** — two
  same-day S1 runs (all 4 streaming vendors), two S2 runs
  (OpenAI 50, ElevenLabs 40), two S3 runs with concurrent ping
  baseline (OpenAI 50, ElevenLabs 40)
- 9 targeted outlier-verification tests confirming or refuting
  specific findings
- A full audit trail (git tags at `prereg-v1`, `prereg-v1.10`, and 11
  logged deviations) proving nothing was cherry-picked post-hoc

**Three headline findings — plus one that got refuted in
verification and became a finding in its own right.**

---

## Method-craft: the decisions I'd defend to a hostile reviewer

For a portfolio project, the choices behind the decisions matter as
much as the findings themselves. A hostile reviewer's job is to
dismantle the plan; every irreversible decision needs a written
reason before the data is collected.

### Killed the weighted-composite score

The v1 plan had a "quality score" = 0.4·PQ + 0.3·CE + 0.2·MOS + 0.1·noise
or similar. Cut it. **Weights are always arguable; pre-registered gates
are falsifiable.** The v2 scoring model has *hard gates* (a vendor either
passes or doesn't on WER/latency/hygiene thresholds committed in
`configs/gates.yaml`) and *Pareto frontiers* on the remaining axes. A
reader can construct their own weighted composite from the raw data;
they can't undo a hard gate.

### Two-judge WER with an agreement rule

Word-error rate is easy to bias — pick an ASR trained on similar
audio and everyone looks accurate. So the WER measure uses **two
independent ASR judges**, `facebook/wav2vec2-large-robust-ft-libri-960h`
(Meta) + `faster-whisper large-v3` (OpenAI's Whisper). Each judge
transcribes the audio; we then compute the **"agreed hypothesis"**
by taking only tokens both judges emitted at the same position
(disputed tokens — where the two judges output different words —
are omitted, treating those positions as errors against the
reference). `agreement_wer = jiwer.wer(reference, agreed_hypothesis)`.
This is a conservative measure: any disagreement between judges
counts against the vendor. A per-item failure is triggered when
`agreement_wer > 5%` (with a numeric/currency/date-span carve-out
per `configs/gates.yaml`). Constraint on the judge choice: judges
must differ in *organisation*, *encoder architecture family*, AND
*training pipeline*.

Late in the project — at the point when NVIDIA's Parakeet was still
the first candidate for judge 1 — I almost added Canary-1B as an
optional third judge. Canary shares Parakeet's FastConformer encoder
family and Canary-1B-v2 training-data pipeline, so it would have
violated the independence rule if it had ever been paired against
Parakeet. Once Parakeet was itself swapped out (D-010, moved to
wav2vec2), the specific violation risk went away — but the general
lesson landed: judge independence needs to be a **written constraint,
not a lucky property**. It now lives as a Pydantic `model_validator`
on `AnalyzersFile` in [`src/veval/config.py`](../src/veval/config.py)
that reads the org/family/pipeline metadata authors supply in
`configs/analyzers.yaml` and rejects incompatible pairs at
config-load time.

### Refused commercial ASRs as judges

Deepgram and Google are *providers under test* in this evaluation.
Using their ASR to grade Cartesia's or ElevenLabs' output is a
conflict a hostile reader would find in five minutes. Only
research-grade open-source ASRs (with no vendor axe to grind) are
admissible as judges.

### Loudness-normalised everything to −18 LUFS

Without loudness normalization, louder clips systematically win A/B
comparisons — the human ear reads "louder" as "better" up to a
threshold. Every clip that goes into any comparison gets normalised
to −18 LUFS first. The test measures voice quality, not gain staging.

### Chose TTSDS2 (with a fallback), then measured the noise floor

Public benchmarks (UTMOS, NISQA) saturate on frontier TTS — every
modern vendor scores 4.3–4.6 out of 5 and the ranking becomes
statistical noise. TTSDS2 is the current best distributional-similarity
benchmark, but it also requires ~30 GB of reference-set downloads.
We ran with a fallback (Audiobox + DNSMOS) and measured the natural
per-item noise floor — the smallest score difference that isn't just
draw-to-draw wobble. That noise floor is what "meaningfully different"
means in every ranking claim we make.

### Killed VERSA after adopting it

The v1 plan chose VERSA (a comprehensive metric aggregation library)
partly to reduce dependency friction. VERSA turned out to force a
Linux-container build for exactly 5 of its 80 metrics. The
uv-managed environment was already doing the reproducibility job
VERSA was hired for. Cut VERSA, called the underlying metric
libraries directly. Second "kill your own decision" moment of the
project.

### Killed the Bradley-Terry human rating campaign

The spec's D4 slot was a 168-judgment blinded pairwise BT rating
campaign, at n=1 self-rater. The bootstrap CIs on those judgments
would be *conditional on the single rater* — two n=1 raters could
produce non-overlapping "95% CIs" on opposite preferences, both
statistically valid, both worthless as human-preference evidence at
population level. Publishing rankings with those CIs would read to
a casual reader as "we confirmed this with rigor." That's a shape
of over-claim we should refuse.

The written rationale is [`D-H` in 06_KEY_FINDINGS.md](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2).
A proper v2 with a 15-30 rater blinded panel is future work.
**Naming the epistemic limit and refusing to fill it dishonestly is
a stronger position for this project than executing the ceremony
and disclaiming it.**

---

## Three headline findings

### 1. The two independent MOS pipelines rank vendors *differently*

We ran two entirely separate machine quality raters on the same
audio: **Audiobox Aesthetics** (Meta, trained on aesthetic ratings
— "warmth, engagement") and **DNSMOS** (Microsoft, trained on ITU
P.835 speech-cleanliness ratings). Both are peer-reviewed. Both are
used in production TTS evaluation.

The Spearman rank correlation *between the two pipelines* across
the 8 vendors: **−0.13 on conversational, −0.27 on narration**.
Both point estimates are negative, not the strong positive we would
expect if the two raters were measuring the same construct.

**Statistical caveat**: n = 8 vendors gives Spearman ρ a very wide
95% CI (roughly [−0.75, +0.60] for conv, [−0.81, +0.51] for narr).
The point estimates are directional but not statistically
significant — we cannot claim the correlation is *significantly*
negative from n = 8. What the data supports is: **the two
pipelines do NOT show the strong positive rank correlation we would
expect if they measured the same construct**, and we have specific
per-vendor rank inversions that are directly citable regardless of
the CI on the aggregate.

![F-8 rank inversion](figures/f1_rank_inversion.png)

The most vivid case: **OpenAI's narration voice ranks dead last
(#8/8) on Audiobox's warmth axis and #1/8 on DNSMOS's cleanliness
axis** — a perfect inversion. The voice is technically pristine (no
hiss, no artefacts, high dynamic range) but sounds a bit flat and
robotic. Speechify is the opposite: #1 warmth, mid-pack cleanliness.
Cartesia narration is #3 warm and #8 clean (over the surviving
subset — 37 of its narration clips were refused by DNSMOS for
peak_out_of_range, so the surviving-subset ranking is what's shown).

**This is not a bug in either measurement.** Both raters are
measuring what they claim to measure. The problem is that "voice
quality" is not one thing:

- **Warmth / engagement / expressiveness** — what a listener notices
  in a bedtime story, a podcast, a brand voiceover
- **Signal cleanliness / clarity** — what a listener notices in a
  phone-tree confirmation, a screen reader, an IVR system

**These are two different constructs, and our own data separates
them.** Audiobox's `content_enjoyment` axis runs against all four
DNSMOS axes (mean ρ = −0.506). Audiobox's `production_quality`
axis runs *with* them (mean ρ = +0.238, and +0.571 against P.808).
The split we set out to measure between two pipelines turns out to
sit between two axes of one of them. Whichever construct a reader
cares about, the number that tracks it has to be named
individually — an aggregate across the two hides exactly the
distinction that motivated running both.

The practical consequence applies to every quality score in this
report as much as anywhere else: **a quality number is
uninterpretable without the construct its predictor rewards.** We
reported six quality signals from two pipelines specifically so
the split would be visible — and still mislabelled which of our
own two Audiobox axes measured what, across four revisions, with
the falsifying correlation matrix committed in the repository the
entire time. The axis label is not a presentational detail; it is
the claim.

### 2. Every Orpheus call at the hosted endpoint stops at exactly 14.59 seconds of audio

The published pricing for Orpheus (`lucataco/orpheus-3b-0.1-ft` via
Replicate) is $0.003 per generation — nominally the cheapest voice
AI vendor by an order of magnitude.

The T8 verification test regenerated 8 long-narration items on Orpheus,
freshly, no cache. Every single item produced audio of **exactly
14.59 seconds** — standard deviation zero, measured to three decimal
places, across inputs varying from 87 to 105 seconds of expected
reading time. Meanwhile Replicate's `predict_time` metric stayed
essentially constant at ~17 GPU-seconds regardless of input length.

This is **not stochastic truncation** — it's a hard, deterministic
cap. Every ≥15-second reference gets ~85% truncated at this
endpoint. **Whether the cap is model-intrinsic or a deployment-config
default** (a `max_new_tokens`-style parameter on the Replicate
deployment) **is not tested**. Constant `predict_time` is consistent
with both. The PM recommendation differs by cause: if config, a
single request parameter fixes it; if model-intrinsic, chunking +
stitching engineering is required. **What we can publish is that the
cap is observed at the hosted endpoint**, not the mechanism.

Two consequences that don't appear on the pricing page (either way):

- **Orpheus is not the cheapest option on this data.** Under T8's
  per-call output measurement (~35 words per call) and 100K
  words/month, Orpheus costs **~$0.067-0.088/1K words** —
  **peer-priced with OpenAI ($0.075)**, not cheap. The $0.030
  in the cost table is a `cost_model.py` artefact under a
  100-word-per-call default that predates T8; it's kept in the
  table as the direct pipeline output, with a † and a ⚠ block
  explaining what it actually represents. See
  [04_RESULTS.md § Cost calculus § ⚠ Orpheus](04_RESULTS.md#cost-calculus).
- **This mechanically resolves a separate finding** — Orpheus's 85%
  WER on long items, which had been logged as a "possible
  intelligibility problem." It's not intelligibility; it's
  structural incompletion.

For a PM building on Orpheus: use it for **conversational turns
under 15 seconds** where OpenAI (peer-priced) isn't preferred for
some reason — voice character, open-weights preference, an
experimental prototype. On this data Orpheus is not cheap: it is
capped-output at peer OpenAI prices with the worst WER in the
roster.

### 3. Latency *ranking* is stable across sessions; latency *absolute values* are not

For a support-agent product, "how fast does the vendor start
speaking?" (time-to-first-audio-frame, or TTFA) is the most
user-noticeable measure. Under 300 ms feels instant; under 500 ms
feels responsive; over 1 second starts feeling awkwardly slow.

Three sessions of TTFA on the same S01 corpus item, 50 trials each,
across four days:

| session | date | OpenAI p50 / p90 | ElevenLabs p50 / p90 |
|---|---|---:|---:|
| S1 | 2026-08-09 | 736 / 956 ms | 439 / 479 ms |
| S2 | 2026-08-11 | 936 / 1493 ms | 424 / 469 ms |
| S3 | 2026-08-12 | **1369 / 1882 ms** | **694 / 816 ms** |

**Session 3 also captured a concurrent ping baseline** to
Cloudflare 1.1.1.1 (274 probes during the S3 window): p50 = 8 ms,
p90 = 12 ms, max = 29 ms, 0 errors. This rules out the specific
"the last-mile link dropped packets" hypothesis; it does **not**
rule out DNS jitter to the vendor's endpoints, TLS-handshake
latency, client-side event-loop stalls, or vendor-side capacity —
none of those share the ping's code path. The parsimonious
single-cause reading for "both vendors slowed together on the
same day" is **client-side** (local machine contention, one-shot
background scan, Python event-loop stall on the harness),
followed by vendor-side capacity as an untested-but-possible
second hypothesis. See [F-11](06_KEY_FINDINGS.md#f-11)
for the full scope-of-ruleout discussion.

**One data caveat**: ElevenLabs S2 **and** S3 both landed n=40
(not 50). The mechanism (subscription credit exhaustion, spend
cap, per-session cap) is not diagnosed here; the fact that both
later sessions stopped at 40 is documented as measured in
[F-11](06_KEY_FINDINGS.md#f-11).
n=40 still yields well-defined p50/p90 at this magnitude, but
caps the confidence on tail behaviour past p90 for those sessions.

**What survives from the original finding:**

- **ElevenLabs is consistently faster than OpenAI** across all three
  sessions (424/694 vs 736/1369 range on p50). The ranking is
  portable. Rank tests are robust at n=3.
- **OpenAI TTFA is always ≥ 736 ms p50** on our measurements. The
  "OpenAI is slow" claim is more robust than ever.

**Claims the three-session data does NOT support:**

- "ElevenLabs is more predictable than OpenAI" — both vendors move
  50-90% p50 session-to-session; the two-session appearance of
  stability was coincidence.
- "ElevenLabs Flash reliably clears sub-500 ms p90" is not
  supported by three-session data.
- Any distributional claim like "ElevenLabs is more stable than
  OpenAI" — **n=3 sessions cannot distinguish a genuine
  wide-tail vendor from a run of unlucky sessions**. A stability
  claim would need ≥5-10 sessions across ≥2 weeks with
  client-side lag controls; see F-11 for the deferred v2 setup.

**What verification is really for.** The T5/T7 pair demonstrates
both the value of a third replication session and the limits of a
three-session pass: two-session agreement was a weaker signal than
it looked, and three sessions suffice to falsify a distributional
claim but not to make one. The load-bearing PM recommendation:
**don't provision from any single measurement session** — budget
the tail across ≥5 sessions on your own deployment environment,
log client-side event-loop lag, exclude warm-up trials, and expect
50-90% session-to-session variance on either vendor. Rank claims
survive at n=3; variance / stability claims do not.

---

## What the verification pack surfaced

> Test IDs (T1–T8, N1, N2) are defined in
> [04_RESULTS.md § Verification pack outcomes](04_RESULTS.md#verification-pack-outcomes-phase-2c).
> Each has a per-test evidence file under `analysis/verification/`.

After the primary campaign, a Phase 2c pack of 9 targeted tests
re-checked every "outlier" from the first pass — winners AND losers,
same scrutiny. Four verdicts worth naming:

### The T6 reversal — Speechify's voice-pick was too conservative

Speechify came out #1 of 8 on both Audiobox axes (PQ and CE) on
both use cases in the primary run. The obvious reviewer objection:
"you got lucky with the voice pick." T6 tested this by
regenerating 40 items with `edmund_32` (UK male, bright, dynamic)
instead of the pre-registered `geffen_32` (US female, warm,
intriguing) — the biggest voice-signature swap available within
Speechify's Simba-3.2 model.

The alt voice scored **+0.30 higher on Audiobox PQ** than the
pre-registered pick. Still ranked #1 of 9 (including both Speechify
voices as separate entries). **Reversal of the test's original
direction**: not "did we cherry-pick?" but "did we
under-cherry-pick?"

Interpretation: Speechify's Audiobox lead is a **model-family
signature**, not a specific-voice property. Voice choice within
Simba-3.2 moves the score up to ~35% of the cross-vendor spread —
meaningful, but not enough to flip vendor rankings. Which means
customers can pick a Speechify voice that fits their brand without
worrying about a big quality drop-off. The lead spans two Audiobox
axes that measure different constructs — PQ (technical cleanliness;
agrees with DNSMOS at ρ = +0.24 mean) and CE (warm / enjoyment;
anti-correlates with DNSMOS). See F-8 for the per-pair receipt.

### The Cartesia triangulation — two independent code paths agree

Cartesia's output audio has zero peak headroom: waveform peaks sit
at or above ±1.0 in the numeric representation. **Two independent
measurement pipelines detect this**:

1. Our sample-level clipping analyzer (numpy peak scan): Cartesia
   has **~100× more clipped samples** than the next-worst vendor
2. Microsoft's DNSMOS ONNX inference **refuses to score 46% of
   Cartesia's files** for peak out of range — a hard `ValueError`

A third observation — that the 54% of Cartesia files DNSMOS *did*
accept still rank **#8 of 8** on all three ITU P.835 axes — is
downstream evidence from the DNSMOS pipeline itself, not a third
independent pipeline. So the correct claim is **two independent
code paths, non-overlapping implementations, flag the same vendor
unanimously — plus a survivor-subset check on the second pipeline
that reinforces the pattern.**

For a PM building on Cartesia: their voice is fast and mid-quality,
but the audio breaks downstream tooling. Add a peak-limiter step
(bring peaks to −1 dBFS) *before* anything else consumes the audio.
Otherwise a meaningful fraction of your pipeline will silently
reject or degrade it.

### T4 confirmed with refinement — headline magnitude was overstated

The primary campaign flagged ElevenLabs' L03 narration item with a
**3.6 dB monotonic loudness fadeout** across thirds. T4 regenerated
L03 three more times fresh, no cache.

**All three fresh regens showed monotonic fade-down direction (100%
reproducible).** But the mean delta across the four total draws was
**2.7 dB, not 3.6 dB**. The original observation was at the high
end of the natural per-draw range.

**Not a refutation — a refinement.** The *phenomenon* is real; the
*specific magnitude* was over-stated. Without verification, the memo
would have said "ElevenLabs has a 3.6 dB deterministic fadeout on
L03." With verification, it says "ElevenLabs shows a reproducible
monotonic-fade pattern on L03; individual draws range 2.2–3.6 dB."
More accurate. More useful.

That's what verification is for: not to bless what's already been
found, but to soften headline claims to what the data actually
supports.

---

## What this means for a PM buying voice AI

Three questions to answer in order:

**Question 1 — hard constraints.** Does your use case rule out any
vendor structurally?

- Long-form narration (>15s per turn)? **Orpheus is out at the
  hosted endpoint** (14.59s cap observed; may be a config parameter
  or a model-intrinsic cap, untested — see § 2)
- Any downstream audio pipeline (MOS check, ASR, resample)?
  **Cartesia needs a peak-limiter step** first
- Sub-500 ms p90 required (real-time voice)? **Unresolved on our
  data.** Two thresholds: the pre-registered gate is
  `ttfa_p90_ms < 400` (`configs/gates.yaml`); the perception-
  threshold reference from the spec's A.1 is ~500 ms. **No
  measured vendor clears the pre-registered 400 ms gate in any
  session.** ElevenLabs Flash's best measurement was 469 ms p90
  (S2); everything else fails more clearly (Cartesia 529,
  Deepgram 670, OpenAI 946+). Against the softer 500 ms perception
  reference, ElevenLabs cleared it in S1+S2 (469-479 ms) but
  failed S3 (816 ms). **Do not provision from any of our
  measurements** — real-time TTFA is session-variable enough that
  you need ≥5 sessions on your own deployment before committing
  (F-11, § 3 below).
- Byte-identical caching? **Impossible with any of the 8** — none
  produces the same bytes twice

**Question 2 — which "quality" matches your users?**

- Warm/engaging (audiobook, storytelling, brand voice) → **Speechify
  wins both Audiobox axes on both use cases** at **3.7–9.5σ vs
  the numerical #2, 3.7–7.3σ vs the deployable #2**. The two
  Audiobox axes measure different constructs: PQ (technical
  cleanliness, agrees with DNSMOS at ρ = +0.24 mean) and CE
  (warm / enjoyment, anti-correlates with DNSMOS at ρ ≈ −0.5 mean).
  Speechify wins both. Numerical vs deployable #2 differs on
  narration AB.PQ, where Orpheus (8.002) numerically beats Cartesia
  (7.986) but is Q1-disqualified from narration workflows by its
  14.59-s output cap. The per-stratum recompute in 04's footnote ¹
  shows Orpheus's 8.002 mean is earned, not a truncation artifact
  (per-stratum means: complete 8.008 / lightly truncated 7.974 /
  catastrophically truncated 8.009). Full writeup in
  [04_RESULTS.md § Rankings summary](04_RESULTS.md#rankings-summary)
  and [06_KEY_FINDINGS.md § F-8](06_KEY_FINDINGS.md#f-8).
  At $0.10/1K words (100K/mo tier), Speechify is the cheaper of
  the top-2 CE (warm/enjoyment) vendors (ElevenLabs at $0.22 is
  #2 CE and 2.2× more expensive). **At 10K/mo Speechify is
  $1.00/1K** (the Starter subscription amortized over low volume) —
  more expensive than OpenAI's pay-per-use $0.075 at that volume.
  Orpheus's nominal $0.030/1K words in the table is a
  `cost_model.py` artefact under a 100-word-per-call default;
  under T8's per-call output measurement the honest Orpheus price
  is **~$0.067-0.088/1K words** — peer-priced to OpenAI ($0.075).
  See
  [04_RESULTS.md § Cost calculus § ⚠ Orpheus](04_RESULTS.md#cost-calculus).
- Clean/pristine (IVR, accessibility, transactional voice) → **OpenAI
  ties for #1 on DNSMOS OVRL on both use cases** (0.7–1.3σ vs the
  tied competitor). At $0.075/1K words, OpenAI is 34% of ElevenLabs'
  $0.22 (tied on conv) and 50% of Deepgram's $0.15 (tied on narr) —
  a **~50–66% saving** on tied-on-cleanliness quality. Caveat: our
  SE(diff) test is unpaired and doesn't correct for multiplicity;
  the "tie" verdict is a conservative reading of the current
  evidence, not a positive statement of equality — see the Rankings
  summary in 04 for the full method disclosure.

**Question 3 — is #1 on quality worth the cost premium over #2?**

Look at the cost-vs-quality frontier:

![Cost vs quality](figures/f2_cost_vs_quality.png)

Use [04's Rankings summary](04_RESULTS.md#rankings-summary) for the
per-pair statistical test (|Δ| / SE(diff), where SE_i = SD(75) / √75).

**Under 2σ**: the pair is statistically tied at α=0.05 — pick the
cheaper vendor. **Between 2σ and 4σ**: the evidence is real but the
observed Δ is small in absolute terms — decide from your own
listener-preference judgment. **Above 4σ**: strong evidence, but
note that **σ measures precision of the estimate, not perceptual
magnitude**: Speechify's 3.7σ Audiobox lead is a Δ of 0.14 on a
0–10 scale, which is 1.4% of scale. Whether that gap is *audible*
to a listener is untested (no human panel — see
[D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)). See
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) for the
perceptual-calibration gap.

The clearest cost tie-break: **OpenAI vs ElevenLabs on DNSMOS
conversational** — Δ = 0.022 at 1.3σ (tied at α=0.05). OpenAI
$0.075/1K words vs ElevenLabs $0.22/1K words = **66% saving on
tied-on-cleanliness quality**. That recommendation stands
independent of latency; ElevenLabs' latency profile is now itself
uncertain (see § 3 / F-11).

---

## What the audit found

This is an independent study. Its output is a set of observations
made under stated constraints — 8 vendors, one voice each, 75 items
per use case, paid public tiers, a single residential measurement
environment. We do not claim the observations generalise beyond
that configuration, and § "What wasn't done and why" below sets out
where they stop.

Given that, the meaningful test of this work is narrow and checkable:
**do the observations reported in these documents match the
observations actually recorded in the artifacts?**

We ran that check by recomputing the published figures directly from
the committed JSON, independently of the prose.

### The measurement layer reproduced

Every quantitative result regenerates exactly from committed
artifacts:

- all **96** quality cells (Audiobox PQ/CE + four DNSMOS axes ×
  8 vendors × 2 use cases) match `quality.json` to the reported
  precision
- all **16** per-vendor WER means match `wer.json`
- both cross-pipeline Spearman coefficients (−0.13 conversational,
  −0.27 narration) match `cross_metric.json`
- all **8** paired-vs-unpaired σ values and their ratios regenerate
  by re-running `scripts/_paired_test.py`
- DNSMOS per-cell validity counts (Cartesia 43 conv / 38 narr,
  Google 71 narr) match the F-4a refusal counts exactly

No measurement in this study was found to be wrong.

### The reporting layer did not

Six reported observations did not match the artifacts they were
derived from:

| Reported | Recorded | Artifact |
|---|---|---|
| Deepgram TTFA ~180 ms p50 / ~230 ms p90 | 583 / 674 and 564 / 670 ms; no session under 500 ms | `analysis/latency-20260809T*/latency.json` |
| Orpheus $0.030 / 1K words | ~$0.070–0.088 / 1K words under the measured per-call output | `src/veval/analyze/cost.py` line 177 + T8 |
| Speechify $0.100 / 1K words at 10K/mo | $1.000 / 1K words | `cost_model.json` |
| Audiobox `production_quality` is the warmth axis | PQ correlates **+0.571** with DNSMOS p808 and +0.238 across all four DNSMOS axes — it tracks cleanliness; CE is the axis that runs against DNSMOS at −0.506 | `cross_metric.json` |
| ElevenLabs 469 ms p90 as a stable ceiling | S3 measured 816 ms p90; both vendors moved 50–90% p50 across sessions | `analysis/latency-20260812T*/latency.json` |
| Project spend ~$56 | $7.85 for the primary campaign, ~$12.60 across all committed runs | `analysis/*/cost_model.json` `total_observed_cost_usd` |

In every case the underlying value was correct in its JSON at the
time the report said otherwise. These are not measurement errors.
They are failures of the step between the artifact and the sentence.

### The kinds of failure

Sorting them by mechanism rather than by severity is more useful,
because the mechanisms recur:

| Mechanism | Instance in this study |
|---|---|
| A figure that was never traced to a source | Deepgram ~180 ms — origin still unidentified; no run in the repository produces it |
| A tool default mistaken for a measurement | Orpheus $0.030, which is `cost.py`'s 100-word-per-call assumption — an assumption T8 had already falsified at ~35 words per call |
| A planning estimate published as a result | "~$56 project spend", carried from the pre-project budget line |
| A transcription error that inverts a reading | Speechify $0.100 vs $1.000 — a 10× slip that moves the vendor from near-cheapest to second-most-expensive at that tier |
| A frame imposed on data that contradicts it | The warm/clean axis labels, contradicted by a correlation matrix committed before the framing was written |
| A mechanism invented to explain a real number | "−78.7 dBFS is silence padding" — `speech_ratio` is 0.901, higher than Speechify's 0.875; the clips are 90% speech and the quiet floor is a real property |
| A configuration asserted rather than read | Five conversational gates reported; `configs/gates.yaml` defines four |
| A verification step with a structural blind spot | A phrase-level grep against text hard-wrapped at ~70 characters, which cannot match a two-word phrase split across a newline |

### Why the verification pack did not catch them

The Phase 2c pack was designed to re-test headline outliers on fresh
data, and it did that: T8 established the 14.59-second output cap,
T4 corrected the L03 fadeout magnitude, T6 reversed the voice-bias
hypothesis, and the third latency session refuted the stability
reading in F-11.

Every one of those tests asked the same question — *is this
measurement real?* None of them could have caught the six above,
because in each case the measurement was real and correctly stored.
The failure was downstream of measurement entirely.

**Nothing in the methodology tested the join between an artifact and
a sentence about it.** That step had no ceremony around it, appears
in none of the pre-registered procedures, and is where all six
survived.

### What changed as a result

- Every retraction is logged in
  [CORRECTIONS.md](../CORRECTIONS.md) — one row per claim, naming
  the original assertion, the artifact that falsified it, and the
  retracting commit. Twenty-six rows at time of writing.
- The reports carry no inline correction narrative. A corrected
  number appears as a number; its history lives in the register.
- The verification step for that register normalises whitespace
  before matching, after three retracted phrases survived a
  phrase-level grep by being hard-wrapped across a newline.

### The limitation this leaves

We can state that the measurement layer reproduces, and that
twenty-six reporting errors were found and logged. We **cannot**
state that no others remain. The six above were found by auditing
against artifacts; an audit finds what it looks for. The honest
position is that this study's reported observations have been
checked against their sources once, systematically, with the result
recorded — not that they are now known to be correct.

That is itself an observation worth recording. A measurement
pipeline can be pre-registered, version-pinned, reproducible, and
fully covered by tests, and still emit a report that says something
its own data does not support. The pipeline and the prose are
different artifacts, and only one of them was under test.

---

## What wasn't done and why

**A proper multi-rater human perceptual evaluation.** The spec called
for 168 blinded pairwise judgments with bootstrap CIs. Executable at
n=1 rater — but the CIs would be conditional on that one rater, and
publishing them as "human preference" evidence would be a shape of
over-claim this project refuses to make. Full protocol
implementation is in `src/veval/rate/`; only the execution is
deferred. See [`D-H` in 06_KEY_FINDINGS.md](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)
for the reasoning.

**Cross-lingual, accent-varied, streaming, or interrupted-conversation
measurements.** All out of scope for v1. Each is a real gap and each
is a legitimate v2 workstream. Named in
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) rather than
glossed over.

**Enterprise-VM-colocated latency baseline.** The TTFA numbers here
were measured from a residential Windows 11 environment; enterprise
deployments in a cloud region colocated with each vendor's serving
region would see 10-30% lower absolute numbers. Vendor *rankings* on
latency are portable; absolute values are one point in a
session-to-session distribution (see F-11). See `D-G`.

---

## Closing note

A portfolio project that reads as "look at all the confirmations"
demonstrates only that the author is good at post-hoc rationalisation.
The load-bearing decisions in this project came from applying that
same critical view to a plan I'd already written — killing the
weighted composite, killing VERSA, killing the BT rating campaign,
and reporting the T4/T6 verification results as *refinements to my
own headline claims* rather than confirmations. The receipts for
those decisions are in [DEVIATIONS.md](../DEVIATIONS.md) and
[06_KEY_FINDINGS.md](06_KEY_FINDINGS.md).

---

## Where to find things

- **[04_RESULTS.md](04_RESULTS.md)** — full per-provider data table +
  cost calculus + decision framework
- **[06_KEY_FINDINGS.md](06_KEY_FINDINGS.md)** — findings F-1
  through F-9 + F-11 (F-10 slot is documented in-doc), friction-point
  stories, decision log D-A..D-H
- **[02_METHODOLOGY.md](02_METHODOLOGY.md)** — why every methodology
  choice was made (weighted-composite killed, two-pipeline design,
  loudness normalization, judge independence, BT deferral)
- **[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md)** — what
  wasn't done and why; deferred items; a proper v2 outline
- **[03_RUNBOOK.md](03_RUNBOOK.md)** — install + reproduce the
  evaluation on your own hardware
- **[01_ARCHITECTURE.md](01_ARCHITECTURE.md)** — the harness's
  technical design
- **[../DEVIATIONS.md](../DEVIATIONS.md)** — 11 pre-registered
  amendments made before results existed, each with rationale
- **[../analysis/verification/](../analysis/verification/)** —
  per-test hypothesis + method + result + verdict for the 9-test
  Phase 2c outlier verification pack
- **Source of everything**: prereg tag
  [`prereg-v1.10`](https://github.com/ngera/VoiceModelEvaluation/tree/prereg-v1.10)
  contains the configs at the moment the campaign ran.

*Total metered project spend: **~$12.60 across 8 vendor accounts**
(pilot campaigns $0.61 + primary campaign $7.85 + variance run
$3.16 + two S1 latency sessions $0.34 + verification pack $0.63 +
S3 latency ~$0.02, all sourced from committed
`analysis/*/cost_model.json` `total_observed_cost_usd` fields).
Time: ~60 hours part-time across three weeks.
Codebase:
[github.com/ngera/VoiceModelEvaluation](https://github.com/ngera/VoiceModelEvaluation)*
