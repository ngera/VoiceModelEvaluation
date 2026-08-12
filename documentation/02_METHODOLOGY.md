# 02 · Research Methodology

*Why every methodology choice was made the way it was. Different
from [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) which lists the
individual decisions — this document explains the underlying
principles the decisions apply.*

> **⚠ Scope disclaimer** · Methodology described here was applied
> as of 2026-08-12 on 8 vendor accounts (paid public tiers). Full
> scope in [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Method philosophy in one sentence

**Pre-register everything you can, publish the noise floor,
triangulate every headline finding, and be willing to kill your
own decisions when the data says the design was wrong.**

Every specific choice below follows from that principle.

---

## The five methodology non-negotiables

Choices that were fixed early and couldn't be traded off without
compromising the validity of the whole exercise.

### 1. Pre-registration with git tags

Every measurement parameter — corpus, vendors, voices, gates,
analyzer settings, judges, cost model — is committed and
**git-tagged before results exist**. Amendments before the campaign
runs are logged in [../DEVIATIONS.md](../DEVIATIONS.md) with
rationale and re-tagged (`prereg-v1.1` through `prereg-v1.10`).
Amending post-hoc is not done — it's the opposite of what
pre-registration is for.

**Why**: without this, "we found Speechify #1 on the warm axis" is
indistinguishable from "we selected the measurement configuration
that made Speechify #1." With the git-tag receipt, a reader can
verify the parameters predate the data.

### 2. Two independent MOS pipelines, not one

Every quality signal is measured by **two independent MOS
predictors** (Meta Audiobox Aesthetics + Microsoft DNSMOS P.835),
plus their cross-pipeline agreement computed as a first-class result.

**Why**: F-8 shows the two pipelines rank vendors *differently*
(cross-pipeline mean Spearman ρ = −0.13 conv, −0.27 narr). A
single-pipeline design would have produced a confident-looking
ranking that a reader would take as *the* ranking. Two pipelines
prevent that specific error by making the pipeline-choice the
finding.

### 3. Two-judge WER with agreement + independence

WER is not a single-judge measurement. It's the **agreement** between
two ASRs that must differ in **organisation**, **encoder architecture
family**, AND **training-data pipeline**. The judge-independence
constraint is a Pydantic model_validator, not a lucky property (see
D-010 in [../DEVIATIONS.md](../DEVIATIONS.md#d-010) for the near-miss
that made this constraint explicit).

**Why**: a single ASR trained on similar audio to what the vendors
produce inflates or deflates errors in vendor-specific ways. Two
independent ASRs agreeing on an error location makes it much more
likely to be a real error in the audio, not a judge artefact.

### 4. Loudness normalization before any A/B or MOS input

Every clip that goes into a comparison is normalized to **−18 LUFS**
first (broadcast standard). Louder clips systematically win human A/B
comparisons up to a threshold; MOS predictors are similarly
level-sensitive. Without this normalization, the test measures gain
staging rather than voice quality.

**Why**: this is a well-known failure mode in TTS evaluation. The
"louder = better" bias is real and the fix is cheap; skipping it
would invalidate the quality rankings.

### 5. Pre-committed hard gates + Pareto frontiers, NOT a weighted composite

The v1 plan had `quality_score = 0.4·PQ + 0.3·CE + 0.2·MOS + 0.1·noise`.
Killed it in Phase A. **Weights are always arguable; pre-registered
gates are falsifiable.**

The v2 model:
- **Hard gates** in [`configs/gates.yaml`](../configs/gates.yaml)
  — pass/fail against numeric thresholds
- **Pareto frontiers** on the remaining axes — vendors on the
  frontier are non-dominated, vendors off it are worse on some axis
  without being better on any other
- **Bootstrap 95% CIs** on frontier positions — a vendor is
  reported as "on" the frontier only if the CI supports it

**Why**: a reader who prefers different weights can construct any
composite they want from the raw data. A reader who's given only
one composite can't undo the author's weights. Publishing the
frontier is portable; publishing a weighted composite locks in
one worldview.

---

## The five measurement dimensions (D1–D5)

Each dimension is designed to be *independent* — a vendor that
wins one shouldn't automatically win another. That's what makes
Pareto framing meaningful.

### D1 · Latency

**What we measure**: TTFA (time-to-first-audio-frame) p50 / p90 /
min / max from 50 serial trials per vendor. **Second session two
days apart** for the two speed-critical vendors (OpenAI + ElevenLabs)
to separate speed from stability. RTF (real-time-factor) on long
narration items.

**Why serial not parallel**: parallel trials measure the vendor's
concurrency handling; serial trials measure the tail of an
individual user's experience. For a support-agent product, the tail
per-user matters more than aggregate throughput.

**Why multiple sessions**: a single session of TTFA cannot
distinguish "vendor is fast" from "vendor happened to be fast
during our measurement window." The plan called for two sessions
on different days. Post-review, a third session (2026-08-12) with
concurrent ping baseline was added; it refuted the two-session
"stability" reading — see
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11-retraction-of-the-latency-stability-is-a-distinct-axis-finding).
The methodology takeaway that survives: **TTFA is
session-variable; report absolute values as a range across ≥3
sessions, not as a point estimate**. What the design of two
sessions was too weak to catch is documented in F-11 as a
first-class finding, not concealed.

### D2 · WER (Word Error Rate)

**What we measure**: two ASR judges (Meta `wav2vec2-large-robust` +
OpenAI `faster-whisper large-v3`), agreement-based error detection.
Threshold for pass: `agreement_wer < 5% + numeric/currency/date span
exempt`. Failure taxonomy: `agreed_word_drop_runs`, `truncation`,
`repetition_loop_*`, `agreed_hallucination_runs`.

**Why agreement-based**: single-ASR WER conflates "the audio is bad"
with "the ASR misheard." Two independent ASRs agreeing on an error
location makes the "audio is actually bad" reading much more
credible.

**Why WER is relative-ranking only**: wav2vec2 emits ALL CAPS + no
punctuation and drops articles, inflating absolute WER (F-2). The
error pattern is *vendor-independent* — every vendor gets the same
inflation — so relative rankings survive even though absolutes
don't.

### D3 · Quality (two MOS pipelines)

**Pipeline A · Meta Audiobox Aesthetics** — 2 pre-registered axes
of the 4 emitted: `production_quality` (technical cleanliness) +
`content_enjoyment` (listener preference/naturalness). Not
`production_complexity` (arrangement density — irrelevant when text
is held constant) or `content_usefulness` (semantic value of the
text — held constant across vendors). Pre-committing 2-of-4 avoids
post-hoc axis selection.

**Pipeline B · Microsoft DNSMOS P.835** — all 4 axes emitted:
`p808_mos`, `ovrl_mos`, `sig_mos`, `bak_mos`. Reports the full
three-scale + the standalone P.808 single-model prediction. See
[../DEVIATIONS.md § D-011](../DEVIATIONS.md#d-011).

**Cross-pipeline agreement** (Spearman ρ between the pipelines) is
computed and reported as a **first-class result** — not a
methodology diagnostic. F-8 is *the* headline finding of the
project.

**What was rejected**:
- **UTMOS** — attempted, blocked on Windows by fairseq install
  cliff (no Windows wheels for any version)
- **NISQA** — pins `torch==2.2.1`, would cascade-break the env
- **TTSDS2** — deferred (D-A); the pre-registered plan named this
  as an escape hatch; 30 GB reference-set download blocks the
  pipeline

**Why two pipelines**: F-8 justifies this in retrospect. The a
priori reason: single-pipeline MOS reporting is easy to bias
(intentionally or unintentionally) by choice of predictor.
Publishing two forces the reader (and author) to confront the
choice.

### D4 · Human perceptual (deferred to v2)

The pre-registered plan included **168 blinded pairwise Bradley-Terry
judgments** with clustered bootstrap 95% CIs. **Not executed in v1**
— see D-H in [06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)
for the full reasoning. Short version: n=1 rater bootstrap CIs are
conditional on the single rater, and cannot license
"human-preference" claims at population level. Executing the
ceremony and disclaiming the result would be over-claim disguised
as rigor.

**Substitutes v1 relies on instead**:
- 6 machine quality signals + cross-pipeline agreement (F-8)
- 9-test Phase 2c verification pack (F-9)
- F-4a's three-pipeline triangulation on the Cartesia mastering finding

### D5 · Cost

**What we measure**: per-1K-words cost at 10K / 100K / 1M
words/month volume tiers, factoring in monthly minimums, included-unit
tiers, and per-request fees. Sourced from
[`configs/pricing.yaml`](../configs/pricing.yaml) with `date_verified`
per row.

**Why volume tiers matter**: a vendor cheap at 100K/mo may not be
cheapest at 1M/mo (Speechify's tier structure scales well; ElevenLabs
stays flat). A vendor's ranking on cost can flip between tiers if
you don't model the full curve.

**Effective cost, not sticker cost**: T8 showed Orpheus's
$0.003/call sticker translates to a real per-1K-word cost that
depends on the cap-per-call, not the input length. See the
[04 cost calculus](04_RESULTS.md#cost-calculus) note on the
Orpheus row for the current arithmetic — sticker rates without
that qualification will mislead.

---

## The verification pattern

Every headline outlier from the primary campaign gets a **targeted
verification test** that can *confirm* or *refute* the finding on
fresh data — winners and losers same scrutiny.

**Design principles**:

1. **Hypothesis + falsifiable success criterion stated BEFORE
   regeneration** — prevents "we saw what we wanted to see"
2. **Fresh calls, no cache** — different day / time where relevant
3. **Winner-side tests get the same scrutiny as loser-side** — kills
   the "cherry-picked eliminations" critique
4. **Verdict buckets**: Confirmed / Refuted / Inconclusive as the
   base, with modifiers when the fresh data forced a refinement
   (e.g., "Confirmed with reversal" for T6 when the winning vendor
   held rank but under a different voice; "Refuted with a bigger
   finding" for T8 when the cost story broke on an output-cap
   discovery). The
   [verdict tally in 04_RESULTS](04_RESULTS.md#verification-pack-outcomes-phase-2c)
   lists the six-way execution outcome explicitly rather than
   collapsing to the base three
5. **Per-test JSON + Markdown artefact** in
   [analysis/verification/](../analysis/verification/) so the
   evidence is directly citable

**What the pack produced** (verdict table + full narrative in
[04_RESULTS.md § verification pack outcomes](04_RESULTS.md#verification-pack-outcomes-phase-2c)):

- **Four findings that would not have surfaced from the primary
  campaign**: T8 (Orpheus's 14.59s output cap at the hosted endpoint),
  T6 (Speechify's alt-voice reversal), T4 (L03 fadeout magnitude
  overstated ~35%), and **F-11 (the after-review third latency
  session that refuted the initial "ElevenLabs is stable" claim)**
- The most consequential is T8 — mechanically resolved T2 (Orpheus's
  high WER = truncation cap, not intelligibility) without a manual
  listen
- F-11 is the strongest "published-headline-refuted-by-verification"
  case; it directly answered an external-review objection about ISP
  confounding

**Cost**: ~$0.63 spend + ~2 hours of work (including the
after-review third latency session with concurrent ping baseline).
Cheap replication is the highest-leverage step in a portfolio
evaluation.

---

## Honest limits

Where the methodology cannot support the claim, name it.

### What we can claim

- **Vendor rankings** on any single measurement axis, subject to the
  per-comparison SE(diff) test documented in
  [04_RESULTS.md § Rankings summary](04_RESULTS.md#rankings-summary).
  Earlier drafts of this doc used a single-number "0.035 noise floor"
  heuristic — that's been retired in favor of per-vendor per-signal
  SD(75) / √75, with a σ-based test. Caveat: the current SE(diff)
  test uses the unpaired formula on paired data (same 75 items
  rendered by both vendors), which is conservative but not optimal;
  a paired test would tighten TIE calls further. Multiplicity across
  the 9 pairs tested is not corrected.
- **Cross-pipeline disagreement** (F-8) — the *fact* that two
  independent MOS pipelines rank vendors differently, with named
  rank inversions
- **Presence or absence of specific technical properties** — Cartesia
  peaks-at-1.0, Orpheus 14.59s output cap, ElevenLabs L03 fadeout,
  Fish elevated noise floor. These are directly measured, not
  inferred.
- **Effective cost** at specific volume tiers with named caveats
  (Orpheus's cap, Cartesia's limiter overhead, OpenAI's latency-
  provisioning cost)

### What we cannot claim

- **"Humans prefer vendor X"** — no human perceptual panel in v1
  (D-H). The two machine pipelines disagree (F-8); we cannot say
  from our data which pipeline aligns with human perception.
- **"Vendor X's model is universally better than vendor Y"** — every
  vendor wins on some axis and loses on another (F-3). Rankings are
  axis-conditional.
- **Absolute values on latency** — measured from residential
  Windows 11; rankings are portable. Absolute values are one
  point in a session-to-session distribution (see F-11) — not
  ceilings. Prior drafts treated them as ceilings; that was
  refuted by S3.
- **Absolute WER** — inflated by wav2vec2's LibriSpeech distribution
  (F-2); relative rankings valid, absolutes are not.
- **Findings generalize to other voices / other tiers / other
  regions** — we tested one voice per vendor (except Speechify's T6
  alt) on paid public tiers from one location. Voice space and tier
  space are largely untested.

### The BT deferral is the biggest limit

Explicitly named. See D-H. The strongest position the project takes
is: "when the two machine pipelines disagree, we don't know which
one aligns with human perception; a proper v2 with a 15-30 rater
panel would answer this question."

---

## Why this is defensible (not just "rigorous-looking")

A hostile reviewer's job is to dismantle the methodology. Every
substantive attack surface has an explicit defense already committed
to git:

- **"You cherry-picked the voice"** → T6 tested Speechify's alt voice
  (edmund_32); Speechify still #1 of 9, alt voice actually higher
- **"You cherry-picked the corpus"** → corpus committed to
  [corpus/](../corpus/), reproducible with any alternate. The
  authoring bias is explicitly logged as
  [D-002](../DEVIATIONS.md#d-002).
- **"You used a bad ASR judge"** → two independent judges with
  agreement rule; judge-independence is a
  [Pydantic validator](../src/veval/config.py) not a lucky property
- **"Your quality scores are gamed to favour X"** → 6 signals from 2
  independent pipelines; F-8 shows the pipelines disagree
- **"You didn't normalize loudness"** → −18 LUFS normalization on
  every clip before A/B or MOS input, in the analyzer chain
- **"You benchmarked on old models"** → every model version pinned in
  [`configs/voices.yaml`](../configs/voices.yaml) with SHA where
  available (Orpheus D-005); measurement date on every finding
- **"You paid to get better results"** → paid public tiers only,
  full pricing model in [`configs/pricing.yaml`](../configs/pricing.yaml),
  no vendor gave free credits or discounted access
  ([../DISCLAIMER.md](../DISCLAIMER.md))
- **"You didn't test human perception"** → correct; documented as
  D-H with explicit reasoning; v2 workstream planned
- **"You expanded the roster after the fact and the two vendors
  you added won"** → **The two headline winners (Speechify on
  Audiobox both use cases; OpenAI on DNSMOS both use cases) were
  added in D-003 (prereg-v1.1, git-tagged 2026-08-07) — before any
  campaign result existed.** The `prereg-v1.1` tag is the timestamp
  receipt: it precedes `campaign-20260809T204608Z` by two days.
  Every result comes from the 8-vendor roster locked in `prereg-v1.1`;
  we do not report anything under the 6-vendor `prereg-v1` roster
  and then reveal 2 new winners. The archetypes named for the two
  additions were **"LLM-ecosystem default" (OpenAI) + "consumer-
  storytelling / warm narrator" (Speechify)** — see
  [../DEVIATIONS.md § D-003](../DEVIATIONS.md#d-003). These are
  categorical claims about market positioning made before the
  campaign, not outcome-specific claims. That the two headline
  winners (Speechify on Audiobox, OpenAI on DNSMOS) are the same
  two vendors that were added post-lock is a pattern a hostile
  reader will notice — the pre-registration receipt is what makes
  the claim defensible, but naming the coincidence up front is
  more honest than letting a reader spot it.
- **"You changed almost every measurement-defining parameter
  post-lock"** → true for the roster (D-003), WER judge (D-010),
  primary quality instrument (TTSDS2→DNSMOS via D-A/B/011), and
  OpenAI model/voice (D-006/D-007). Full amendments in
  [../DEVIATIONS.md](../DEVIATIONS.md). Each amendment predates
  the campaign result that uses it, but the substantive question
  is: **did any pilot data inform the amendments?** The honest
  answer: **D-006 and D-007 did.** The $1 pilot returned 5/10
  OpenAI-narration HTTP errors (D-006: model `gpt-4o-tts` returned
  404; D-007: voice `cedar` not in the `tts-1-hd` enum). Those
  amendments were made in response to observed pilot failures, not
  from prior specification — genuinely pilot-informed. D-004/D-005
  (Orpheus fork slug + version pinning) came from live API schema
  probes, not pilot data. D-010 (wav2vec2 judge) came from the
  analyzer failing to load parakeet_rnnt, not from any performance
  observation.

  **D-011 (DNSMOS as second MOS pipeline) is the one requiring the
  most precision.** Explicit timeline:
    - 2026-08-09: campaign audio generated (`campaign-20260809T204608Z`)
    - 2026-08-09 to 2026-08-11: campaign audio analyzed with Audiobox
      only; Audiobox per-vendor numbers existed by the time D-011
      was drafted
    - 2026-08-11: `prereg-v1.10` tagged, adding DNSMOS via speechmos
    - 2026-08-11 (evening): campaign quality re-analyzed with DNSMOS
      added

  So DNSMOS was added *after* Audiobox scores were visible. The
  honest question is: was the choice of DNSMOS specifically informed
  by seeing the Audiobox rankings? **No** — DNSMOS was selected
  because UTMOS (the first-choice second pipeline) was blocked on
  Windows by fairseq's install cliff and NISQA was blocked by a
  `torch==2.2.1` pin (both in the archived RESEARCH_LOG). DNSMOS was
  the only remaining candidate that met the "second independent
  pipeline" criterion without breaking the environment. The choice
  was cross-platform-driven, not outcome-driven. But a reader is
  correct to want that stated rather than inferred.

  **No amendment was made after the DNSMOS numbers themselves
  existed.** That is a stronger, more precise claim than "nothing
  was amended after Phase 2." Committed as prereg-vN tags before
  the campaign result that uses each amendment.

None of these defenses were added after publication — every one is
committed to git with a timestamp that predates results.

---

## Where to go next

- [01_ARCHITECTURE.md](01_ARCHITECTURE.md) — the harness architecture
  that implements this methodology
- [03_RUNBOOK.md](03_RUNBOOK.md) — how to install + reproduce the
  measurements
- [04_RESULTS.md](04_RESULTS.md) — the full data these methods produced
- [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) — findings F-1..F-9 +
  decision log D-A..D-H (the flip side of this document — the
  specific decisions rather than the underlying principles)
- [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) — where
  the methodology falls short and what a v2 would fix
