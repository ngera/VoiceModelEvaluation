---
title: "Choosing a Text-to-Speech Provider: A Pre-Registered, Uncertainty-Aware Evaluation of Six Commercial and Open TTS Systems Across Two Contrasting Use Cases"
short_title: Voice AI Provider Evaluation
author: Neeraj Gera
date: 2026-08-06
version: "0.1 — template, pre-results"
status: TEMPLATE. Design sections populated; results, discussion and conclusions are placeholders.
prereg: git tag `prereg-v1` (to be created in Phase B)
companion_documents:
  - voice_ai_eval_spec_v2.md (specification — WHAT and HOW)
  - IMPLEMENTATION_PLAN.md (build sequence)
  - eval_harness_architecture.mermaid (system architecture)
  - EXTERNAL_REVIEW_2026-08-06.md (second red-team pass)
---

# Choosing a Text-to-Speech Provider

### A pre-registered, uncertainty-aware evaluation of six TTS systems across two contrasting use cases

---

> ## How to use this template
>
> This document is the reporting shell for the study described in
> `voice_ai_eval_spec_v2.md`. Sections 1–6, 8A, 8B, 9, 10, 12 and Appendices A–D are **substantially populated
> now** (two design-stage placeholders remain, in §5.3 and Appendix B.2), because they describe design decisions that are already made and that
> pre-registration requires to be fixed before data exists. Sections 7, 8 and 11 are
> **placeholders**, because filling them before the campaign runs would be the exact
> failure this study is built to avoid.
>
> **Placeholder convention.** Every slot awaiting data is marked `[[FILL: description]]`.
> They are greppable:
>
> ```bash
> grep -n "\[\[FILL" RESEARCH_REPORT.md          # list every outstanding slot
> grep -c "\[\[FILL" RESEARCH_REPORT.md          # count them
> ```
>
> §12 holds the completion checklist. A `[[FILL]]` count of zero plus a checked §12 is
> the definition of a finished report.
>
> **Rule for filling.** Numbers enter this document only from `analysis/<run_id>/` and
> `decisions/` outputs, never retyped by hand. Where a figure is quoted in prose it must
> match the table it came from. Any deviation from the pre-registered design is recorded
> in `DEVIATIONS.md` and referenced from the section it affects — never silently absorbed.

---

## Abstract

Selecting a text-to-speech provider is a procurement decision, but the public evidence
available to make it is benchmark-shaped: single perceptual scores, on single scripts,
for single voices, with no measurement methodology published and no cost or latency
modelling attached. This study evaluates six TTS systems — ElevenLabs, Cartesia, Fish
Audio, Google Cloud TTS, Deepgram and the open-weights Canopy Orpheus — across two
deliberately opposed use cases, a conversational support agent and long-form narration,
using eight measurement dimensions spanning latency, intelligibility, distributional
quality, perceptual preference, audio hygiene, cost, developer experience and capability
surface.

**Status: no data has been collected.** This document is the pre-registered design and its
reporting shell; §§7, 8 and 11 are placeholders.

Three design commitments distinguish it from the boards it compares against. First,
**pre-registration**: acceptance gates, voice selections, corpus and analyzer parameters
will be committed to version control and tagged before any result exists, and the tag
ordering is machine-verified against committed result artifacts rather than asserted. Second,
**uncertainty propagation**: the perceptual axis is derived from a single rater, so its
confidence intervals are bootstrapped and carried into every downstream claim — a
provider is declared dominated only where intervals do not overlap. Third, a **measured
noise floor**: a subset of items is synthesised repeatedly per provider so the study can
state which differences it is not entitled to report.

The decision layer replaces weighted composite scoring with pre-committed hard gates
followed by Pareto frontier analysis, on the grounds that weights are unfalsifiable while
gates are not. Results are reported as frontier position with uncertainty. Row order in the results
tables carries no quality claim.

[[FILL: two-to-three sentence results summary — the headline finding per use case, the
divergence between them, and the reproduction result against the public leaderboard]]

[[FILL: one-sentence conclusion]]

---

## 1. Introduction

### 1.1 The problem

A team building voice features faces a concrete question: which TTS provider, for which
surface, at what cost, and with what risk. The question is ordinary procurement. The
available evidence is not fit for it.

Public TTS leaderboards rank systems on perceptual "humanness" — typically crowd-sourced
blind A/B voting on a single script, using a single cloned voice, for the subset of
providers that support cloning. They are genuinely useful for what they measure, and they
have statistical power no individual evaluation can match. But a buyer cannot act on them
alone, for reasons that compound:

- **They measure one perceptual dimension.** A voice can be preferred in a blind listening test and
  still drop words in currency amounts, ship audio that clips, take 400ms to first byte,
  or cost two orders of magnitude more per million words than an alternative that scores
  three points lower.
- **Their latency and price figures are single points, and their coverage is partial.**
  This is a weaker criticism than an earlier draft of this report made, and the correction
  is worth stating plainly: the principal comparison board *does* publish its latency
  method — the median of 50 sequential live streaming trials, measured rather than
  vendor-supplied, with a per-model `checked` date. What it does not publish is any
  percentile above the median, multi-day or multi-time sampling, the benchmark machine's
  region, or any throughput measure; and its price is one rate with no volume tiers,
  minimums or per-session modelling. The gap is real but narrower than "no methodology",
  and a report about measurement rigour cannot afford to overstate it.
- **Their inclusion criteria are structural.** A cloning-capable-models-only gate excludes
  an entire class of full-stack and budget providers, whose absence is invisible to a
  reader.
- **They go stale, and they know it.** An earlier draft of this report asserted that a
  major board still ranked a provider whose platform had shut down. **Checked 2026-08-06:
  it does not.** The claim came from planning notes and did not survive verification; it is
  recorded as withdrawn rather than deleted, on the same standard this study applies to its
  own results. The surviving version of the point is milder and better evidenced: the board
  stamps each model with a `checked` date precisely because standings and prices move, and
  a static snapshot — including this one — begins ageing on publication.

The gap is not that these benchmarks are wrong. It is that a *ranking* is not a
*decision*, and nothing published bridges the two.

### 1.2 What this study does

This study is that bridge, at deliberately modest scale. It evaluates six providers
across two use cases chosen because they pull in opposite directions, measures eight
dimensions rather than one, and terminates in two one-page decision memos rather than a
leaderboard.

It also audits the leaderboard it positions against: several of the six providers appear
on a public board with listed latency figures, and the study reports whether those
figures reproduce under measurement with published methodology.

### 1.3 Contributions

1. **A decision framework that survives its own uncertainty.** Pre-committed gates
   followed by Pareto analysis, with domination claims required to clear non-overlapping
   confidence intervals — so a single-rater perceptual study cannot over-claim.
2. **A measured noise floor for TTS evaluation.** Repeat synthesis quantifies
   within-provider generation variance, letting the study state the threshold below which
   it reports no difference. No comparable evaluation known to the author publishes
   one; no systematic survey was conducted, so this is an observation rather than a
   priority claim.
3. **An independent replication** of a public board's latency figures against its own
   published protocol, with an interval attached to our estimate and the coverage limit
   stated.
4. **A two-judge intelligibility protocol with an explicit independence constraint**,
   which substantially reduces — though does not eliminate — the ASR-error confound that makes
   single-judge round-trip word error rate unreliable (§5.1, A.2).
5. **A fully re-runnable, pre-registered harness**, with configuration committed before
   results and a re-run scheduled four weeks after the campaign to quantify provider
   drift (reported in §7.16).

### 1.4 What this study is not

It is not a statistically powered perceptual benchmark. The perceptual dimension rests on
one rater, disclosed throughout, with intervals published rather than hidden. It is not a
general TTS quality claim: two use cases, one language, one voice per provider per use
case. It is not an endorsement of any provider, and its measurements are dated snapshots
of systems that change without notice.

---

## 2. Background and related work

### 2.1 How synthetic speech is normally evaluated

Evaluation of synthetic speech divides into four families, each with a characteristic
failure mode at the current state of the art.

**Human listening tests** — mean opinion score (MOS) and its comparative variants — remain
the reference standard for perceptual quality. Their weakness is cost and, at small
panel sizes, statistical thinness: a three-rater panel produces a number with an interval
wide enough to be uninformative, while carrying the rhetorical weight of "human-rated."
Pairwise comparison designs are materially more reliable than absolute rating scales at
small sample sizes, because humans judge "which is better" more consistently than "how
good is this on a fixed scale," where responses drift with mood, sequence and anchoring.

**Learned MOS predictors** — UTMOS, NISQA, DNSMOS and their descendants — estimate human
ratings from audio directly. They are free and reproducible, which is why they are
ubiquitous. Their failure mode is **saturation**: predictors trained on 2022-era synthesis
compress modern frontier systems into a narrow band near the top of their scale, at which
point ranking becomes noise. NISQA carries an additional construct problem — it is a
telephony *degradation* model measuring noisiness, coloration and discontinuity, not a
naturalness judge, and is frequently misapplied as one.

**Distributional metrics** take a different approach: rather than predicting a rating for
one clip, they measure how closely the statistical distribution of a system's speech
matches real human speech. TTSDS2 is the current representative for TTS, reporting
correlation with human judgment across domains where single-model predictors degrade.
The design trade-off is that a distributional metric introduces a parameter a per-clip
predictor does not have — the reference distribution — which must be chosen, justified and
disclosed.

**Objective signal metrics** — PESQ, STOI, SI-SDR, mel-cepstral distortion — are
full-reference measures requiring a time-aligned clean reference. They are the correct
tools for speech enhancement, codecs and voice conversion. They are **not applicable to
this study**: synthetic speech is not a degraded copy of a reference recording but a
different waveform with different timing and prosody, so the alignment assumption
underlying PESQ fails, and MCD penalises prosodic variation that may be equally good or
better than the reference. Both are explicitly excluded here, and the exclusion is stated
because reporting them would signal an evaluation designed for a different problem.

### 2.2 Evaluation toolkits

Several toolkits aggregate these metrics. VERSA, from CMU's WAVLab, wraps 80+
speech, audio and music metrics behind a single configuration interface and is among the
most comprehensive of them; SHEET focuses specifically on training and running learned MOS
predictors; smaller community repositories bundle the common TTS metric set. The
alternative to a toolkit is invoking the underlying metric libraries directly.

This study evaluated VERSA, adopted it, and subsequently removed it. The reasoning is
recorded in Appendix B.1, because the reversal is methodologically informative: the
credibility of a metric attaches to its implementation, not to the dispatch layer above
it, and a dependency lockfile pins a metric stack more precisely than a toolkit
configuration does.

### 2.3 Public leaderboards as related work

Crowd-sourced perceptual leaderboards are treated here as **related work to be integrated
and audited, not replicated**. Their rankings enter the analysis as an external column;
agreement with them is evidence for the perceptual method used here, and divergence is a
finding to explain in terms of script, voice and use-case differences. Their published
latency figures enter as a reproduction target.

### 2.4 Positioning

| | Public leaderboards | Academic TTS papers | This study |
|---|---|---|---|
| Perceptual power | High (crowd-scale) | Moderate (recruited panels) | Low, disclosed, interval-quantified |
| Dimensions measured | Typically 1 | Typically 2–4 | 8 |
| Measurement methodology published | Partially — latency method published, region and percentile not | Typically yes | Yes, and pre-registered |
| Cost modelling | List price, one number | None | Three volumes + per-session |
| Latency methodology | Median of 50 sequential streaming trials; no percentile above median, no region | Rarely measured | 50 serial trials, p50 **and p90**, multi-day and multi-time, region disclosed, plus throughput |
| Terminates in a decision | No | No | Yes — two memos |
| Re-runnable | No | Rarely | Yes, one command |

The lane this study occupies is the bottom four rows — cost modelling included, since §7.13
expects the cost spread to dwarf the quality differences measured everywhere else.

---

## 3. Research questions

**RQ1 — Selection.** For each of two contrasting use cases, which providers survive
pre-committed acceptance gates, and which of the survivors lie on the quality–cost and
quality–latency Pareto frontiers?

**RQ2 — Divergence.** Do the two use cases select different providers? The design
predicts they will: the gates and the dominant dimensions differ by construction. A
provider winning both would itself be a finding.

**RQ3 — Replication.** The principal comparison board publishes its latency as the median
of 50 sequential live streaming trials. Does that median fall within a bootstrap confidence
interval on our independently measured p50, under a protocol that additionally reports p90,
samples across days and times, and discloses its region?

*This is a like-for-like replication of a documented measurement, which is a stronger and
cleaner question than the one an earlier draft asked ("does their figure fall inside our
p50–p90 range?"). That version compared a point estimate against a descriptive spread of
individual trials, which licenses no inference in either direction. **Coverage limit,
stated in advance:** only systems with a reachable API at their benchmark time carry a
measured latency on their board, so the replication covers at most three of our six.*

**RQ4 — Metric agreement.** How well do distributional quality scores agree with
blind pairwise human judgment, and with public crowd rankings? Agreement licenses the
use of automated scores on items the human protocol cannot cover; divergence bounds it.

**RQ5 — Measurement floor.** What is the within-provider variance of repeated synthesis,
and how many of the observed between-provider differences survive it?

**RQ6 — Failure incidence.** How often does each provider produce output that is not
merely lower quality but unusable — dropped words, repetition loops, truncation — and does
that rate track average intelligibility?

---

## 4. Study design

### 4.1 Scenario

The study is framed as a decision memo for a stated scenario rather than an open-ended
benchmark:

> "We are building (a) a customer-support voice agent and (b) an audio version of our
> written content. Which TTS provider should we use for each, at what cost, and what are
> the risks?"

### 4.2 Use cases

| Use case | Dominant criteria | Largely irrelevant |
|---|---|---|
| **Conversational support agent** | Time-to-first-audio, cost per session, failure incidence | Emotional range, long-session consistency |
| **Long-form narration** | Naturalness, quality stability over minutes, cost per 1K words, real-time factor | Latency |

The two were chosen because the same measurement carries opposite weight in each. This is
the mechanism by which the study tests whether a single leaderboard number can
drive a provider decision.

### 4.3 Systems under test

Six systems, one per market archetype, so that the frontier chart has an interpretable
story at every position.

| System | Archetype | Rationale for inclusion |
|---|---|---|
| ElevenLabs | Quality leader | The reference point most teams benchmark against |
| Cartesia | Latency leader | Tests the speed–quality trade-off directly |
| Fish Audio | Value pick | Strong published claims at low price |
| Google Cloud TTS | Hyperscaler baseline | The default many enterprises already have procurement for |
| Deepgram | **Off-index control** | Excluded from cloning-gated leaderboards by construction — included here precisely to show what such gates hide |
| Canopy Orpheus | Open-weights floor | Answers "how close is free?" |

**Measurement constraints that travel with specific systems.** These change what a number
*means*, so each is footnoted wherever the affected number appears rather than being
noted once and forgotten:

| System | Constraint | Consequence for the reported number |
|---|---|---|
| Google | Streaming is gRPC-only, flagship-model-only, preview status | Latency measured on **buffered REST**; not comparable to the streaming figures, and never averaged in with them |
| Orpheus | Hosted per-generation | Latency would measure the host's cold start and queue rather than the model — reported **N/A**. Variance subset reduced to 5 items for the same billing reason |
| Deepgram | REST request length cap | Long-stratum items chunked and reassembled; boundaries recorded, RTF computed over the reassembled audio |
| Cartesia | Low concurrency caps | Campaign concurrency capped to match; latency trials are serial regardless |
| Fish | Free tier is best-effort with no SLA | **Quality and intelligibility measured on the free model string, latency on the paid string.** Whether the two share weights is verified during onboarding; if they do not, or if it cannot be confirmed, every Fish quality cell carries an explicit caveat |

### 4.4 Voice selection

Benchmarking "default settings" benchmarks each provider's default voice, which is the
single largest confound in naive comparisons. Instead, for each provider × use case, the
voice **the provider itself recommends** for that use case is selected from documentation
and voice-library tags, recorded with its selection reasoning, and locked before any
scoring.

The alternative — cloning one voice across all systems, as cloning-gated leaderboards do —
was considered and rejected: cloning support varies, cloning fidelity becomes its own
confound, and the design structurally excludes non-cloning providers. The trade-off is
that this study measures what a buyer would actually deploy, at the cost of not holding
voice identity constant. Both choices are defensible; the choice is disclosed rather than
assumed.

### 4.5 Corpus

75 items per use case: ~60 original items plus ~15 famous public-domain sentences.

| Stratum | Count | Role |
|---|---|---|
| Short (< 15 words) | 12 | Latency measurement, rapid pairwise comparison |
| Medium (15–60 words) | 20 | Bulk quality and intelligibility signal |
| Long (> 200 words) | 8 | Real-time factor, within-item quality drift, long-passage hygiene |
| Jargon battery | 12 | Domain terms, proper nouns |
| Edge battery | 8 | Numbers, dates, currency, acronyms, URLs |
| Famous-sentence probe | 15 | Training-contamination probe |

The novel items are derived from private enterprise source material and curated for this
study, so they are not present in any public corpus a provider is likely to have trained
on. This is a weaker claim than "guaranteed unseen" and is stated as such. The famous-sentence set functions as a **contamination probe**:
if a provider renders well-known text measurably better than novel text of comparable
difficulty, that is suggestive of memorisation benefit. This is reported as a directional
observation only — famous and novel sentences differ in difficulty, vocabulary and era, so
no clean causal claim is available at n=15.

### 4.6 Generation protocol

**Primary campaign.** One generation per item per provider per use case at the highest
quality tier, sampling parameters at documented defaults, every request parameter recorded
in the run manifest. 75 × 2 × 6 = **900 primary audio files**.

**Variance subset.** A fixed 10-item subset per use case is synthesised **three times per
provider** — 10 × 2 × 3 × 6 = **360 additional generations** — to establish within-provider
variance. All six systems run the full subset. An earlier draft cut one provider to five
items on a per-generation hosting cost estimate that was wrong by roughly 24×; at the
verified rate its full share is about $0.20, so the reduction bought nothing and cost
precision. This
yields two things the primary campaign cannot: the **noise floor** used to suppress
over-reporting of small differences, and a **determinism** flag per provider, which
matters to any buyer intending to regression-test their own pipeline.

**Pre-committed significance rule.** The subset measures *per-generation* variability,
while the differences reported in §7.4–§7.5 are aggregates over 75 items. The rule is
therefore stated at the level actually reported: a between-provider difference counts as a
difference only when it exceeds **1.96 × the standard error of the difference between the
two provider aggregates**, that standard error being the measured within-provider SD
divided by √(item count). An earlier draft applied a raw 2× the per-generation SD directly
to provider aggregates, which is roughly an order of magnitude too conservative and would
have suppressed essentially every real difference — the opposite of the intent.

**Scope, also pre-committed.** The rule governs the two metrics where variance is actually
measured: the distributional score and item-level WER. It does not extend to perceptual
preference (which uses the difference-interval test of §5.2), nor to latency, cost,
hygiene, developer experience or capability, where no repeat-draw variance exists. Floors
are reported **per provider** rather than pooled, since pooling would export one noisy
system's variance onto everyone else's comparisons, and the estimate rests on two degrees
of freedom per item, so its own uncertainty is published beside it.

---

## 5. Measurement methodology

Eight dimensions. Full instrument-level detail — what each measures, why it was chosen,
how it is invoked, and what it cannot tell us — is in **Appendix A**. Summary:

| ID | Dimension | Instrument | Primary output |
|---|---|---|---|
| D1 | Latency | Harness timing, pinned cloud region | TTFA p50/p90; RTF on long items |
| D2 | Intelligibility + failure incidence | Two independent ASR judges + `jiwer` | Comparative WER band; % items over threshold; typed catastrophic-event counts |
| D3 | Distributional quality | TTSDS2 (primary), Audiobox Aesthetics (secondary) | Per-provider distributional score; per-third drift on long items |
| D4 | Perceptual preference | Blind pairwise A/B, Bradley–Terry, bootstrap CIs | Human-anchored 0–100 score with 95% interval |
| D5 | Audio hygiene | silero-VAD, pyloudnorm, numpy/scipy | Noise floor (dBFS), clipping count, unnatural pauses, LUFS |
| D6 | Cost | Logged character counts × dated published rates | $/1K words at three volumes; $/session |
| D7 | Developer experience | Timed integration session + friction log | Minutes to first audio; enumerated friction events |
| D8 | Capability surface | Structured desk research | ✓/✗/partial matrix with per-cell source and date |

### 5.1 Two-judge intelligibility and the independence constraint

Round-trip word error rate has a structural weakness: measured error is the sum of the
synthesis system's errors and the transcribing model's errors, and a single judge cannot
separate them. This study uses two ASR judges and attributes an error to the TTS system
only when **both** judges hear it; single-judge errors are discarded as transcription
noise.

That filter works only to the degree the judges are independent. Two correlated judges
produce a protocol that looks like two-judge and behaves like one. The constraint is
therefore stated explicitly rather than assumed:

> **Judge independence constraint.** The two judges must differ in *all three* of:
> originating organisation, encoder architecture family, and training-data pipeline.

The selected pair — NVIDIA's Parakeet TDT and OpenAI's Whisper large-v3 (via the
faster-whisper runtime) — satisfies all three. A candidate replacement considered during
development, NVIDIA Canary, satisfies none of the three relative to Parakeet, sharing its
encoder family and data pipeline; it was rejected as second judge and is admissible only
as an optional third. Commercial ASR APIs are excluded entirely: two of the systems under
test also sell ASR, and grading competitors with a participant's model is a conflict of
interest, quite apart from the reproducibility problem of APIs that update silently.

### 5.2 Perceptual measurement and its uncertainty

Perceptual preference is measured by blind pairwise comparison rather than absolute
rating. All clips are **loudness-normalised to −18 LUFS before presentation** — without
this, louder clips systematically win A/B comparisons and the test measures gain staging
rather than voice quality. Human-recorded anchors are seeded into the pair pool to pin
the top of the scale and to make "distance from human" interpretable.

Seven systems (six providers plus the human anchor) yield 21 unique pairs, × 2 use cases ×
5 repetitions on different corpus items = **210 judgments**, approximately two hours across
five to six sessions. Pairs are randomised across sessions rather than blocked by
provider, so that within-session preference drift does not load onto particular systems.
A 10% subsample is re-judged after at least a week, and the resulting self-consistency
figure is published together with the session gap that produced it.

**Minimum acceptable volume is 3 repetitions (126 judgments).** If schedule pressure
forces the reduction, the report must say so explicitly and state the consequence —
wider intervals, and correspondingly fewer domination claims available — rather than
reporting the smaller set as though it were the design.

**This axis is the y-axis of all four frontier charts and it comes from one rater.** Its
uncertainty is therefore propagated rather than acknowledged in prose:

- **Bootstrap intervals for display.** 2,000 resamples, **clustered by corpus item** since
  judgments on the same item are not independent. The fit carries a small penalty so that
  resamples producing an all-win or all-loss record stay finite, and the affected fraction
  is reported.
- **Domination is tested on the bootstrap interval of the pairwise *difference***, requiring
  it to exclude zero — not on overlap of marginal intervals. Bradley–Terry strengths come
  from one joint fit, so they are correlated and identified only up to the anchoring
  constraint; comparing marginal intervals is neither the right object nor a consistent
  test, and non-overlap of two 95% marginals corresponds to roughly p < 0.006, far more
  conservative than intended.
- **Where the difference interval includes zero, the outcome is "no difference detected at
  this n"** — deliberately not "indistinguishable" or "equivalent". Failure to detect is not
  evidence of absence, and the wording is chosen so no table can be read as claiming it.
- **Minimum detectable difference is estimated before the campaign**, by simulating
  judgments under plausible strength spreads and bootstrapping at both 210 and 126
  judgments, and recorded in the pre-registered configuration. If the MDD exceeds the
  plausible spread between systems, the study says so up front; "powered to detect X" is a
  more useful sentence than a chart of overlapping bars.

### 5.3 Cross-metric agreement

Three perceptual signals exist: the distributional score (every file), the pairwise
judgment (a sample of items), and the public crowd ranking ([[FILL: number of our systems
present on the board at retrieval]] of six). Rank correlation between each pair is computed
and published **with n and an exact permutation p-value beside it**.

**The power limit is stated in advance rather than discovered afterwards.** At the provider
level these correlations run over six systems, and fewer for the board comparisons. At n=4
even a perfect ρ cannot reach two-sided p<0.08; at n=6 only near-perfect rank agreement
clears conventional thresholds. The board comparisons are therefore reported as a
**qualitative concordance check** — do we agree on the ordering of the overlapping systems,
yes / no / partially — and explicitly not as validation of anything.

The comparison with real power is **distributional ↔ pairwise at the item level**, pairing
per-item scores against per-item pairwise outcomes for an n in the dozens rather than six.
That is the analysis that can license relying on the distributional score for items the
human protocol never reached, and it is the one pre-registered as confirmatory. **The unit
of analysis is fixed now**, because choosing it after seeing the data would be the cleanest
available way to manufacture a favourable correlation.

---

## 6. Decision framework

Weighted composite scoring was considered and rejected. Weights are unfalsifiable — any
reader can dispute them and no evidence settles the dispute — and a blended score conceals
the trade-offs a buyer is actually navigating. The framework instead mirrors how
procurement decisions are made: requirements first, then trade-offs among qualified
options.

**Step 1 — Hard gates, pre-committed.** Per use case, each with a one-sentence rationale,
committed to version control and tagged before results exist. Every gate is numeric;
"no audible artifacts" is not a pre-registrable criterion, "noise floor ≤ −40 dBFS and
zero clipped samples" is. A system failing a gate is out of that use case regardless of
performance elsewhere. The full gate table is reproduced below rather than deferred to an
appendix, because printing the acceptance criteria before the data exists is the single
thing pre-registration most requires.

| Use case | Gate | Threshold | Rationale |
|---|---|---|---|
| Conversational | Time-to-first-audio | p90 < 400 ms | Perception degrades above ~500–600 ms; 400 ms is deliberate headroom, since synthesis is one term in an agent's end-to-end budget |
| Conversational | Failure incidence | < 2% of items | A mangled currency amount is a support escalation, not a quality nitpick |
| Conversational | Clipping | zero clipped samples | Unfixable downstream |
| Conversational | Commercial terms | permitted on an accessible tier | A capability fact that eliminates otherwise-qualified systems before quality is discussed |
| Narration | Real-time factor | ≥ 3× (audio ÷ synthesis time; higher is faster) | Generating hours of audio is throughput-bound, not first-byte-bound |
| Narration | Within-item drift | no monotonic degradation across passage thirds beyond the significance rule | The measured form of listener fatigue |
| Narration | Acoustic noise floor | ≤ −40 dBFS, zero clipped samples, across the long stratum | Corrosive over ten minutes in a way it is not over ten seconds (A.5) |

**Non-measurable gate inputs have a pre-committed policy.** Some inputs are structurally
unavailable for some systems — a per-generation-hosted model has no meaningful latency of
its own, and a measurement taken by a different protocol is not comparable to the rest. A
gate cannot be silently passed or failed on missing data, so each carries an explicit
policy: **exempt-and-annotate** (the system stays in the use case, the gate is recorded as
not assessed with a reason, and it is plotted only on the frontier where its axes exist),
**exclude-from-use-case**, or **fail**. The default is exempt-and-annotate. *"Not assessed
— reason"* is a reportable status alongside on-frontier, dominated, no-difference-detected
and gated.

**Step 2 — Pareto frontier on survivors.** Quality against cost, and quality against
latency, per use case. A system is *dominated* when another survivor is better on both
axes; dominated systems eliminate themselves without any weighting debate. What remains is
the set of defensible choices, each representing a different trade-off.

**Step 3 — Uncertainty gates the verdict.** Domination requires the bootstrap interval on
the pairwise *difference* to exclude zero (§5.2). Where quality is not resolved, it is
treated as **unresolved** — so a cost-or-latency domination claim may be made only when the
dominating system also ties or beats on quality's point estimate, with the unresolved
status printed alongside. Treating an undetected quality difference as quality *equality*
would be the same absence-of-evidence error one axis over. Latency differences are tested
on a bootstrap interval over the 50 trials; cost domination must hold at all three volume
points. This is the step that prevents a single-rater study from manufacturing distinctions
it cannot support.

**Step 4 — Gate robustness.** Each gate carries an explicit list of alternate thresholds —
for conversational latency, 300 / 400 / 500 / 600 ms — rather than a blanket percentage
band. A ±20% sweep around 400 ms tops out at 480 ms and would never reach the 500–600 ms
range the gate's own rationale cites, which is precisely the value a reader will ask about.
This is the sensitivity analysis appropriate to a gates design, replacing weight
sensitivity in a composite design.

**Step 5 — Decision memo per use case.** Recommendation, the trade-off it accepts, cost at
three scale points, top three risks, and revisit triggers.

**On why a human makes the final call.** Pareto analysis eliminates dominated options and
quantifies remaining trade-offs; it does not choose among them, and with six systems the
frontier may retain three or four. The memo chooses, in prose, naming the trade-off
accepted. This is more honest than burying the choice inside weights, and it is the
artifact the decision is actually for.

---

## 7. Results

> **Status: awaiting the campaign.** Every table and figure below exists as a shell with
> its structure, units and footnotes fixed in advance. Fixing the reporting format before
> the data exists is part of pre-registration: it removes the freedom to select a
> presentation that flatters a conclusion.

### 7.1 Campaign execution summary

| Item | Value |
|---|---|
| Run ID | [[FILL: run_id]] |
| Campaign dates | [[FILL: start – end]] |
| Audio files generated (primary / variance) | [[FILL: n / n]] |
| Total characters synthesised | [[FILL: n]] |
| Total spend | [[FILL: $n, against a $50 ceiling]] |
| Analysis hardware | [[FILL: GPU model, driver, interpreter version from manifest]] |
| Failed / re-run generations | [[FILL: n, with reasons — errors are logged as data, never hand-patched]] |
| Deviations from pre-registration | [[FILL: reference DEVIATIONS.md entries, or "none"]] |

### 7.2 Measurement noise floor (RQ5)

| Provider | Items × draws | Within-provider SD, distributional score | Within-provider SD, item WER | Deterministic? |
|---|---|---|---|---|
| [[FILL: one row per provider. Orpheus is 5 × 3 rather than 10 × 3 — flag its reduced precision here and wherever its noise floor is used]] | | | | |

**Pooled noise floor:** [[FILL: value]]. Per the pre-registered rule, between-provider
differences below **twice** this value are reported as within noise floor throughout.

[[FILL: prose — how many of the observed between-provider differences survive this
threshold, and on which dimensions. If the answer is "few," that is the finding.]]

### 7.3 Instrument validation

| Check | Result | Consequence |
|---|---|---|
| TTSDS2 split-half stability | [[FILL: divergence value vs pre-committed threshold]] | [[FILL: headline-eligible / demoted to supporting signal]] |
| Two-judge ASR agreement rate | [[FILL: % of errors both judges heard]] | [[FILL: interpretation]] |
| D4 self-consistency (10% re-judge) | [[FILL: % agreement, session gap in days]] | [[FILL: interpretation]] |
| Human anchor placement | [[FILL: anchor's Bradley–Terry score and interval vs the best system]] | [[FILL: whether the anchor pinned the scale as intended; values above the anchor are permitted and reported if they occur]] |
| Minimum detectable difference achieved | [[FILL: MDD at the achieved judgment count, vs the pre-registered simulation]] | [[FILL: how many domination claims this makes available in principle]] |
| Bootstrap degeneracy | [[FILL: fraction of resamples with an all-win or all-loss record]] | [[FILL: whether the penalty term was load-bearing]] |

### 7.4 Results table — Use case A: conversational support agent

**Row order carries no quality claim.** Rows are grouped by gate and frontier status, then
ordered alphabetically within group. An earlier draft sorted by the perceptual point
estimate and numbered the rows, which re-imported through the back door exactly the ranking
the difference-interval test (§5.2) exists to forbid. Quality relations are read from the
Status column and the frontier figures, never from row position.

| Provider · model (voice)¹² | Perceptual, ours ± 95% CI¹ | Board² | Rank Δ | Distributional³ | TTFA p50/p90 ms⁴ | Board latency² | Replicates?⁵ | WER band⁶ | Failure %⁷ | Hygiene | DX min | $/1K words @100K/mo⁸ | $/session⁸ | Status⁹ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Human anchor | 100 ± CI | 100 | — | — | — | — | — | — | — | — | — | — | — | — |
| [[FILL: one row per provider]] | | | | | | | | | | | | | | |

### 7.5 Results table — Use case B: long-form narration

Narration-specific column set. Carried over: perceptual and distributional scores,
intelligibility band, failure incidence, hygiene. Replaced: time-to-first-audio by
real-time factor, per-session cost by cost at 1M words per month. Added: within-item
drift. Dropped: the board-comparison columns, because the board scores a conversational
script and a narration comparison would not be like-for-like; and developer-experience
minutes, which are use-case-invariant and already reported in §7.4.

| Provider · model (voice)¹² | Perceptual ± CI¹ | Distributional³ | RTF¹¹ | Drift across thirds¹⁰ | WER band⁶ | Failure %⁷ | Hygiene | $/1K words @1M/mo⁸ | Status⁹ |
|---|---|---|---|---|---|---|---|---|---|
| [[FILL: one row per provider]] | | | | | | | | | |

**Footnotes (published with both tables).** 1. Blind pairwise A/B, Bradley–Terry fit, anchored to 100, clips loudness-normalised to −18 LUFS; ± is a bootstrap 95% CI over [[FILL: n]] judgments from [[FILL: n]] rater(s). 2. Public leaderboard values as of [[FILL: date]], their methodology. 3. TTSDS2 against [[FILL: named reference set]]; split-half stability [[FILL: value]]. 4. TTFA: 50 serial trials, ≥2 days, ≥2 times of day, streaming, [[FILL: region]] — **buffered REST for Google**, not comparable to the streaming figures; Orpheus N/A-hosted. 5. Whether the board's published median (of 50 sequential streaming trials) falls inside a bootstrap 95% interval on our p50. 6. Two-judge agreement WER, comparative band, not absolute accuracy. 7. Share of items whose agreement error rate exceeds 5%, or containing an agreed error inside a numeric, currency or date span. 8. Published rates as of [[FILL: date]] × logged character counts; minimums and per-request fees noted. 9. Gate and frontier status; domination requires a bootstrap interval on the pairwise difference to exclude zero. "Not assessed — reason" appears where a gate input is structurally unavailable. 10. Monotonic change in distributional score across passage thirds. **11.** RTF = audio duration ÷ total synthesis time (**higher is faster**), measured on the 8-item long stratum — a different protocol from the TTFA trials in footnote 4; Orpheus N/A-hosted. **12.** Fish quality and intelligibility are measured on the free model string while its latency is measured on the paid string; [[FILL: state the resolution of the weight-sharing check from onboarding]].

### 7.6 Gate outcomes (RQ1)

| Use case | Gate | Threshold | Systems passing | Systems failing |
|---|---|---|---|---|
| [[FILL: one row per gate, both use cases]] | | | | |

[[FILL: prose — which eliminations were surprising, and whether any gate eliminated
nothing, which would indicate a threshold set too loose to discriminate]]

### 7.7 Pareto frontiers (RQ1)

**Figure 1.** Use case A — perceptual quality (with 95% CI error bars) against $/session.
Dominated systems greyed; frontier points labelled with the trade-off each represents.
[[FILL: figure reference — decisions/frontier_conversational_cost.png]]

**Figure 2.** Use case A — perceptual quality against TTFA p90.
[[FILL: figure reference]]

**Figure 3.** Use case B — perceptual quality against $/1K words @1M/mo.
[[FILL: figure reference]]

**Figure 4.** Use case B — perceptual quality against real-time factor.
[[FILL: figure reference]]

| Use case | On frontier | Dominated (by whom, on which axes) | Indistinguishable at this n | Gated out |
|---|---|---|---|---|
| Conversational | [[FILL]] | [[FILL]] | [[FILL]] | [[FILL]] |
| Narration | [[FILL]] | [[FILL]] | [[FILL]] | [[FILL]] |

### 7.8 Gate robustness

[[FILL: for each gate, whether a ±20% move changes the frontier, in the form "X only makes
the support frontier because the 400ms gate excludes Y — at 500ms, Y re-enters and
dominates it"]]

### 7.9 Use-case divergence (RQ2)

[[FILL: do the two use cases select different systems? Which system wins one and loses the
other, and which measurement drives the reversal? If a single system wins both, say so and
explain why the predicted divergence did not materialise.]]

### 7.10 Leaderboard reproduction (RQ3)

| Provider | Board median (50 sequential streaming trials) | Our p50 ± 95% CI | Our p90 | Board median inside our p50 interval? | Notes |
|---|---|---|---|---|---|
| [[FILL: one row per provider carrying a measured latency on the board — at most three of six]] | | | | | |

[[FILL: prose — systematic direction of any discrepancy, and the plausible methodological
explanations, e.g. region, percentile choice, streaming vs buffered]]

### 7.11 Metric agreement (RQ4)

| Pair | Spearman ρ | n | Interpretation |
|---|---|---|---|
| Distributional ↔ pairwise | [[FILL]] | [[FILL]] | [[FILL]] |
| Distributional ↔ public board | [[FILL]] | [[FILL]] | [[FILL]] |
| Pairwise ↔ public board | [[FILL]] | [[FILL]] | [[FILL]] |

[[FILL: prose — does agreement license the distributional score on items pairwise never
reached? Where it diverges, what explains it?]]

### 7.12 Failure incidence (RQ6)

| Provider | Failure % | Word drops | Repetition loops | Truncations | Hallucinated content | Tracks mean WER? |
|---|---|---|---|---|---|---|
| [[FILL: one row per provider]] | | | | | | |

[[FILL: prose — does failure incidence track average intelligibility, or does a system with
a good average WER carry a bad tail? The latter is the more interesting outcome and the
more consequential one for a buyer.]]

### 7.13 Cost model

| Provider | $/1K words @10K/mo | @100K/mo | @1M/mo | $/session | Minimums and fees |
|---|---|---|---|---|---|
| [[FILL: one row per provider]] | | | | | |

[[FILL: prose — the spread at 1M words/month, stated as a ratio. If it is the expected one
to two orders of magnitude, note that it dwarfs the quality differences measured elsewhere
in this report, and what that implies for how the decision should be weighted.]]

### 7.14 Developer experience and capability surface

| Provider | Minutes to first audio | Friction events | Notable obstacles |
|---|---|---|---|
| [[FILL: one row per provider]] | | | |

[[FILL: capability matrix reference — the ✓/✗/partial table with per-cell sources and
dates. Highlight any capability gap that eliminated or nearly eliminated a system
independently of its measured quality.]]

### 7.15 Contamination probe

[[FILL: directional observation only — whether famous sentences rendered measurably better
than novel items of comparable difficulty, per provider. State the n=15 limitation in the
same breath as the observation.]]

### 7.16 Provider drift (+4 weeks)

| Provider | Model/voice version change | Price change | Perceptual Δ | Latency Δ |
|---|---|---|---|---|
| [[FILL: one row per provider, from the cached re-run]] | | | | |

[[FILL: prose — what changed in a month, and what that implies about the shelf life of any
static TTS leaderboard, including this report]]

---

## 8. Discussion

> **Status: awaiting results.** Prompts below are the questions the discussion must
> answer; they are recorded now so the discussion cannot quietly narrow to whichever
> questions the data happened to answer well.

**8.1 What the frontier analysis showed that a ranking would have hidden.** [[FILL]]

**8.2 Did uncertainty change any conclusion?** [[FILL: specifically — how many domination
claims were blocked by overlapping intervals, and would a point-estimate ranking have
asserted them? This is the direct test of whether §5.2's machinery earned its cost.]]

**8.3 How much of the measured difference survived the noise floor?** [[FILL]]

**8.4 Automated versus human perceptual measurement.** [[FILL: what the rank correlations
imply about when a practitioner can rely on the distributional score alone]]

**8.5 Where the public leaderboard reproduced, and where it did not.** [[FILL]]

**8.6 What a buyer should take from this.** [[FILL: the practitioner-facing summary,
including which dimension turned out to matter most per use case — and whether that
matched the design's prediction in §4.2]]

**8.7 What the study got wrong.** [[FILL: honest register — instruments that
underperformed, thresholds set badly, analyses that produced nothing. A study that reports
only what worked has not reported its method.]]

---

## 8A. Ethics, consent and declarations

Recorded before data collection, because consent obtained retrospectively is not consent.

**Human participants.** The study collects perceptual judgments from one rater — the
author — and uses a recorded human voice as a scale anchor. **The anchor is deliberately
not the author's own voice**: with a single rater, using their own recording would defeat
blinding for the one clip that pins the top of the scale (A.4). The anchor speaker gives
written consent covering how the recordings are used and retained. No IRB or ethics-board
review was sought; the study involves no vulnerable participants, no sensitive personal
data, and no intervention, and is conducted outside an institutional research setting. A
reader who considers that insufficient has the facts to disagree.

**Identifiability.** Any rater beyond the author is identified by pseudonym only, with
aggregate judgments reportable and individual identity not. Voice recordings are
biometric-adjacent personal data and are handled as such: they stay on local storage, are
not published, and are deleted on request.

**Corpus data.** Corpus items are reviewed so that all names, amounts, order numbers and
identifiers are synthetic. No real individual is referenced.

**Provider-side data handling.** One provider's free tier retains inputs for model
training. This is acceptable *only* because the corpus is non-sensitive text written for
this study, and it is recorded as a conscious decision rather than an oversight. No
proprietary or personal content passes through any test account.

**Funding and competing interests.** Self-funded; total spend is reported in §7.1. The
author has no financial relationship with, employment by, or equity in any system under
test. Paid subscriptions were purchased at public rates with two vendors under test for the
duration of the campaign and cancelled afterwards; no vendor was contacted for access,
discounts or comment, and no vendor reviewed this report before publication.

**Author roles — stated because it is a limitation, not a formality.** One person designed
the study, implemented the harness, provided the sole perceptual judgment, and interpreted
the results. These roles are ordinarily separated for good reason. The mitigations are
pre-registration (the design cannot be adjusted after seeing results), blinding of the
pairwise interface, and publication of intervals rather than point estimates. The
mitigations are partial and the concentration of roles is disclosed in §9.4 as a validity
threat rather than treated as solved.

**Data and code availability.** The harness, configuration and analysis code are intended
for publication under an open licence. Analysis outputs and decision artifacts are
committed to version control; generated audio is not, both for repository size and because
provider terms on redistributing synthesised audio vary and were not cleared for
publication. Per-run manifests with content hashes are committed so provenance is
verifiable without the audio. Human voice recordings are not published. What a reproducer
needs — configuration, corpus, code, and the pre-registration tag — is available; what they
cannot obtain is the author's own judgments, which is inherent to the design.

---

## 8B. What would falsify this study's methodological claims

Pre-committed, so that the discussion in §8 cannot narrow to whichever claims the data
happened to support.

This study makes two methodological claims beyond its provider recommendations: that a
gates-plus-Pareto-plus-uncertainty framework yields a materially different decision than a
leaderboard ranking would, and that a measured noise floor is informative rather than
decorative.

**The first claim is refuted if** the frontier verdicts on all four charts are identical to
those a naive ranking on point estimates would have produced, and no domination claim is
blocked by the difference-interval test. In that case the uncertainty machinery cost effort
and changed nothing, and §8.2 must say so.

**The second is refuted if** the measured within-provider variance is negligible relative to
every between-provider difference — that is, if the significance rule suppresses nothing.
The rule would then be a formality, and the honest report is that repeat synthesis was not
worth its cost for this roster.

**A weaker but still reportable outcome** is that the perceptual axis proves too imprecise
to separate any pair of systems. That is not a refutation of the method — it is the method
working — but it would mean the frontier analysis reduces to cost and latency, and the
report must present it that way rather than leaning on point estimates it has argued are
not separable.

---

## 9. Threats to validity

Recorded before results, per pre-registration, so that no threat can be added or omitted
in response to what the data showed.

### 9.1 Construct validity

| Threat | Status |
|---|---|
| **Perceptual quality proxied by one rater.** Pairwise-with-anchors is the most defensible single-rater design available, but it is not a panel | Mitigated by design (pairwise, blinding, anchors, randomised ordering, consistency re-judge) and by **publishing intervals rather than point estimates**. Not eliminated. Disclosed in every table |
| **Distributional score depends on a reference corpus.** If the reference is out of domain relative to this corpus, distance may reflect domain mismatch rather than synthesis quality | Reference set named and justified in the pre-registered config; split-half stability tested before headline use; cross-use-case comparison declared unsupported if only one reference is available |
| **Round-trip WER measures TTS + ASR jointly** | Two-judge agreement rule under an explicit independence constraint (§5.1); reported comparatively, never as absolute accuracy; flagged files manually reviewed |
| **"Recommended voice" is a provider-defined construct** and varies in how carefully each provider curates it | Disclosed as a deliberate choice with its alternative documented (§4.4) |

### 9.2 Internal validity

| Threat | Status |
|---|---|
| **Single-draw generation confounds provider differences with generation variance** | Directly addressed — variance subset and pre-committed noise-floor rule (§4.6) |
| **Loudness differences bias pairwise comparison** | All clips normalised to −18 LUFS before presentation |
| **Rater preference drift across sessions** | Pairs randomised across sessions rather than blocked; consistency re-judge reports its session gap |
| **Latency contaminated by concurrency** | All latency trials strictly serial, one request in flight |
| **Latency geography** | Single pinned region; each provider's serving region published; structurally distant providers annotated rather than presented as cleanly comparable |
| **Tier mismatch** — one provider's quality measured on a free model string, latency on paid | Verified during onboarding; if the strings differ, every affected cell carries a caveat |

### 9.3 External validity

| Threat | Status |
|---|---|
| Two use cases, one language, one voice per system | Stated scope limit; not generalised beyond |
| Six of many available providers | Archetype-based selection disclosed; five named systems explicitly deferred |
| Findings are a dated snapshot | Every measurement date-stamped; the +4-week re-run quantifies drift directly |

### 9.4 Conclusion validity

| Threat | Status |
|---|---|
| **Over-claiming from an undetected difference** | Domination requires a bootstrap interval on the pairwise difference to exclude zero; where it does not, the outcome is reported as "no difference detected at this n", never as equivalence |
| **Over-claiming from small differences** | The §4.6 significance rule, applied at the level of the reported aggregate and scoped to the two metrics where variance is measured |
| **Contamination probe over-read** | Reported as directional only; n=15 stated alongside |
| **Researcher degrees of freedom** | Gates, voices, models, corpus, analyzer parameters and reporting format all tagged in version control before results; deviations logged with reasons |
| **Multiplicity** | Dozens of pairwise domination tests plus three correlations, with **no correction applied**. The position is stated rather than silently adopted: RQ1's frontier verdicts are **confirmatory**; the contamination probe, within-item drift and the correlation analyses are **exploratory** and labelled as such wherever reported. A reader who wants a family-wise correction has the raw comparison count to apply one |
| **Anchor treated as error-free** | The anchor's own strength is estimated with error; pinning it to 100 is an identification choice, not a finding, and transfers that error invisibly onto every other system. Scores are therefore also reported on the native Bradley–Terry scale with the anchor carrying its interval, and values above the anchor are permitted and will be reported if they occur |
| **Rater is also the designer** | One person designs the study, implements it, provides the sole perceptual judgment and interprets the result. Blinded filenames do not blind a rater who can recognise a system's house voice. Disclosed rather than mitigated; the anchor is deliberately **not** the rater's own voice (A.4), which would have removed blinding entirely for the clip that sets the top of the scale |

---

## 10. Limitations and future work

**Acknowledged limitations.** Single rater on the perceptual axis. Single language.
Single voice per provider per use case. Latency measured from one region. Six providers.
No agent-layer or telephony testing. No on-premises or self-hosted latency, which
requires enterprise access unavailable here. Accent robustness, domain-expert
pronunciation, and reliability-over-time are not measured; each would materially change
the picture for some buyers.

**Future work, in priority order.**

1. **Accent robustness** — the most underserved area in public voice evaluation. Minimum
   viable version: three accents with recruited raters.
2. **External rater panel** (n = 10–25). The largest credibility upgrade available **per
   unit of cost** — no additional API spend, and the intervention that would most narrow
   the intervals in §7.4. Placed second only because accent robustness addresses a gap
   nobody has filled, whereas additional raters improve a measurement that already exists.
   It would require a hosted rating interface with access-controlled audio, which v1
   deliberately does not build, and a fitting model with a rater term rather than pooled
   judgments.
3. A third contrasting use case with different structure — navigation-style ultra-short
   utterances.
4. Agent-platform evaluation as a separately scoped project.
5. Phoneme-level forced alignment for more precise drop and repeat detection.
6. Scheduled monthly re-runs producing longitudinal drift tracking.

---

## 11. Conclusion

[[FILL: three to five sentences. Must state the recommendation per use case, the trade-off
each accepts, and the confidence attached. Must not assert any difference the noise floor
or the confidence intervals do not support.]]

---

## 12. Completion checklist

The report is finished when `grep -c "\[\[FILL" RESEARCH_REPORT.md` returns 0 **and**
every box below is checked.

- [ ] Every number in prose matches the table it came from
- [ ] Every number sourced from `analysis/<run_id>/` or `decisions/`, none hand-typed
- [ ] `prereg-v1` tag verified to predate all result files in git history
- [ ] All four frontier figures render, **with error bars**
- [ ] Noise floor published; no difference below 2× pooled SD reported as a difference
- [ ] Every domination claim verified against a bootstrap interval on the pairwise difference excluding zero
- [ ] Distributional reference set named; split-half stability published
- [ ] Failure incidence published per provider
- [ ] Self-consistency figure published **with its session gap**
- [ ] Rank correlations published for all three metric pairs
- [ ] Per-provider measurement caveats present wherever the affected numbers appear
- [ ] Every deviation from pre-registration logged in `DEVIATIONS.md` and cross-referenced
- [ ] §8.7 ("what the study got wrong") written and non-empty
- [ ] Dates stamped on all pricing and leaderboard figures
- [ ] Cold read completed by a second person; points of confusion addressed
- [ ] Total spend logged against the ceiling
- [ ] **Appendix E populated** from the `prereg-v1` tag, with `git log` and `git diff` output pasted as verification
- [ ] **Every reference verified** against the published record — venue, authors, identifiers — per the note in the References header
- [ ] **External leaderboard source confirmed to exist and publish per-model latency and price**, or RQ3 formally dropped from the design and the Δ / "Reproduces?" columns removed
- [ ] **Pairwise repetition count stated**; if reduced from 5 to 3 (126 judgments), the reduction and its interval consequence are disclosed in §5.2 and §7.4
- [ ] **Budget-driven corpus reduction disclosed** if the pre-committed $50 rule fired — §4.6's 900-file symmetry no longer holds and every affected provider's cells are flagged
- [ ] **Per-third drift analysis run**, or the drift column removed from §7.5 rather than left empty
- [ ] **Orpheus's reduced variance subset** (5 items, not 10) flagged in §7.2 and wherever its noise floor is used
- [ ] **RTF direction checked against `gates.yaml`** — higher is faster; a gate written against the inverse convention selects the slowest systems
- [ ] **Citation markers inserted in the body text** at first mention of each work — the References list is currently unanchored
- [ ] **Drift re-run executed and §7.16 populated**, or §7.16 removed with its reason stated
- [ ] **§7.14 (developer experience and capability matrix) populated**, including the missing-provider note if any D7 session could not be re-run
- [ ] **§7.15 contamination probe reported as directional only**, with n=15 stated in the same sentence
- [ ] **§7.3 instrument-validation rows all filled**, including judge agreement rate, achieved MDD and bootstrap degeneracy fraction
- [ ] **Appendix B.2's leaderboard retrieval date filled**, or the claim removed
- [ ] **Every gate input recorded as measured, not-assessed, or failed** — no gate silently skipped
- [ ] **Confirmatory vs exploratory labelling applied** to every reported comparison (§9.4)
- [ ] **Ethics section reconciled with what actually happened** — anchor consent obtained, rater identity handling as described

---

## References

**These entries were assembled during design and are not yet verified.** Venues, author
lists and identifiers must each be checked against the published record before this
document is shown to anyone — a report arguing for measurement rigour cannot carry a
misattributed citation. Entries carrying a `[[FILL]]` are ones already known to be
doubtful; the absence of a marker is not a guarantee of correctness.

Note also that **no reference is currently cited from the body text**. Numbered citation
markers should be inserted at first mention of each work — VERSA and TTSDS2 in §2,
Bradley–Terry and the bootstrap in §5.2, the ASR models in §5.1 — before distribution.

1. Shi, J. et al. *VERSA: A Versatile Evaluation Toolkit for Speech, Audio, and Music.*
   NAACL 2025 (System Demonstrations). https://aclanthology.org/2025.naacl-demo.19/ ·
   arXiv:2412.17667 · https://github.com/wavlab-speech/versa
2. Minixhofer, C. et al. *TTSDS2: Resources and Benchmark for Evaluating Human-Quality
   Text to Speech Systems.* [[FILL: confirm the single venue of record — an ISCA workshop
   and ICLR cannot both be it; design notes carry both]].
   https://www.isca-archive.org/ssw_2025/minixhofer25_ssw.pdf · arXiv:2506.19441 ·
   https://github.com/ttsds/ttsds
3. Huang, W.-C. et al. *SHEET: A Multi-purpose Open-source Speech Human Evaluation
   Estimation Toolkit.* Interspeech 2025. https://arxiv.org/html/2505.15061
4. *Towards Responsible Evaluation for Text-to-Speech.* arXiv:2510.06927.
   https://arxiv.org/html/2510.06927v1 — [[FILL: authors and venue; this entry was
   retrieved by title during design and its attribution is unconfirmed]]
5. NVIDIA. *Parakeet ASR model family.* Model card: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2 ·
   NeMo ASR documentation: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/intro.html ·
   [[FILL: Open ASR Leaderboard standing and retrieval date, checked at analysis time]]
6. Radford, A. et al. *Robust Speech Recognition via Large-Scale Weak Supervision*
   (Whisper). arXiv:2212.04356. Runtime: `faster-whisper` (CTranslate2 reimplementation).
7. Bradley, R. A. and Terry, M. E. *Rank Analysis of Incomplete Block Designs: I. The
   Method of Paired Comparisons.* Biometrika 39(3/4), 1952.
8. ITU-R BS.1770 / EBU R128 — loudness measurement standards. Implementation:
   `pyloudnorm`.
9. Silero Team. *silero-vad: pre-trained enterprise-grade voice activity detector.*
   https://github.com/snakers4/silero-vad
10. Meta AI. *Audiobox Aesthetics: Unified Automatic Quality Assessment for Speech, Music,
    and Sound.* arXiv:2502.05139 — [[FILL: verify arXiv ID and author list against the
    published record]]
11. `jiwer` — word error rate computation. https://github.com/jitsi/jiwer
12. [[FILL: the public leaderboard used as the external comparison — exact name, URL,
    operator and retrieval date. **Verify before `prereg-v1` is tagged, not before
    distribution**: RQ3 and the Δ / "Reproduces?" columns depend entirely on this source
    existing and publishing per-model latency and price figures. If it does not, RQ3 must
    be dropped from the pre-registered design rather than quietly abandoned later.]]
13. Efron, B. and Tibshirani, R. J. *An Introduction to the Bootstrap.* Chapman & Hall,
    1993.

---

# Appendices

The appendices are the technical record: what each instrument measures, why it was
selected over the alternatives, how it is invoked, and — importantly — what it cannot tell
us. They are written to be read by someone deciding whether to trust, reuse or criticise
the method.

---

## Appendix A — Measurement instruments

Each dimension is documented under a fixed schema: **what it measures**, **how it is
measured**, **why this instrument**, **what it cannot tell us**, and **how it enters the
decision**. The fourth heading is the one most evaluations omit, and it is the reason this
appendix exists.

### A.1 · D1 — Latency: time-to-first-audio and real-time factor

**What it measures.** TTFA is the elapsed time from issuing a synthesis request to
receiving the first byte of audio, in streaming mode. RTF is **output audio duration
divided by total synthesis time** — a *speed factor*, so **higher is faster**, and "3×
real-time" means three seconds of audio produced per second of compute. The direction is
stated explicitly because the inverse convention is also in circulation, and a gate
written against the wrong direction would select the slowest systems rather than the
fastest.

**How it is measured.** The harness timestamps immediately before the request and on
arrival of the first audio byte. 50 trials per provider on a short corpus item, spread
across at least two days and two times of day, from a single pinned cloud region,
**strictly serial with one request in flight**. Medium and long items are spot-checked to
detect TTFA degradation with input length. Reported as p50 and p90. RTF is measured on the
long stratum.

**Why these two, and why not one.** TTFA and RTF answer different questions and the study
needs both because its two use cases need different ones. A conversational agent begins
playback on the first chunk, so first-byte latency governs perceived responsiveness and
total generation time is nearly irrelevant. Narration generates hours of audio ahead of
playback, so throughput governs and first-byte latency is nearly irrelevant. An evaluation
reporting only TTFA — as most do — is silently optimised for one of these and misleading
for the other.

**Why 50 trials, p50/p90, serial, multi-day.** Fifty samples support median and 90th
percentile estimates but cannot support a p99 claim, so none is made. Serial execution is
required because concurrent trials contend and inflate the measurement. Multi-day, multi-
time sampling captures load variation that a single session would miss. A pinned region
holds the network term approximately constant so that differences reflect provider stacks
rather than geography.

**What it cannot tell us.** It cannot separate the four components of TTFA — network
round-trip, provider queueing and cold start, model time-to-first-token, and chunk
encoding — so a slow provider cannot be diagnosed, only observed. It cannot speak to
performance from regions other than the pinned one, and it structurally disadvantages
providers whose nearest endpoint is distant, which is why serving regions are published
alongside. It says nothing about behaviour under concurrent production load. And for
per-generation-hosted models it measures the host, not the model, which is why one system
is reported N/A rather than given a misleading number.

**How it enters the decision.** A hard gate on the conversational use case (TTFA p90
below threshold); the x-axis of one frontier chart; RTF is a hard gate on narration.

---

### A.2 · D2 — Intelligibility (round-trip WER) and failure incidence

**What it measures.** Whether the system says the words it was given, and how often it
fails badly enough to be unusable.

**How it is measured.** Each generated file is transcribed by two independent ASR models.
Transcripts are normalised (lowercased, punctuation stripped, numbers expanded) and scored
against the source text with `jiwer`. **An error is attributed to the TTS system only when
both judges produce it**; single-judge errors are discarded as transcription noise. Files
above a flag threshold enter a manually reviewed queue, hard-timeboxed. Separately, and
pre-committed before results: the **percentage of items exceeding a per-item WER
threshold**, and **typed counts of catastrophic events** — word drops, repetition loops,
truncation, hallucinated content.

**Why two judges, and why this pair.** Measured error in a round-trip design is the sum of
synthesis error and transcription error, and one judge cannot separate them. Two models
with unrelated architectures and training pipelines rarely produce the *same* error on
clean audio, so requiring agreement removes most of the transcription term at no cost.
The independence constraint stated in §5.1 is what makes this work, and it is the reason
a candidate judge sharing an encoder family with the primary was rejected despite being
operationally convenient.

**Why open models, never commercial ASR APIs.** Two providers under test also sell ASR;
using a participant's model to grade its competitors is a conflict of interest that a
hostile reader finds in minutes. Commercial APIs additionally update without notice,
which breaks reproducibility. Both selected judges are version-pinned in the dependency
lockfile.

**Why failure incidence is reported separately from the WER band.** A mean-like statistic
hides its tail, and the tail is what ends deployments. "One item in two hundred mangles a
currency amount" is a different procurement fact from "band A versus band B," and it is
the one a buyer acts on. The data already exists in the flagged-file queue; publishing it
as a column rather than leaving it as an internal QA step costs nothing and changes what
the report can be used for.

**What it cannot tell us.** It is comparative, not absolute — reported as bands against
identical items and judges, never as "this provider has X% accuracy," because residual
ASR error remains after the agreement filter. It cannot detect errors both judges make
identically, which is the residual confound the design accepts. It says nothing about
whether the audio is pleasant, only whether it is correct. And normalisation choices
(number expansion in particular) affect the result, which is why the pipeline is pinned.

**How it enters the decision.** A hard gate on failure incidence for the conversational
use case; a reported band in both results tables; the source of the manual-listen queue.

---

### A.3 · D3 — Distributional quality

**What it measures.** How closely the statistical distribution of a system's speech —
prosody patterns, speaker characteristics, intelligibility factors — matches that of real
human speech. Secondarily, aesthetic quality axes from an architecturally unrelated model.

**How it is measured.** TTSDS2 as primary and Audiobox Aesthetics as secondary, run over
every generated file, aggregated per provider per use case. Long narration items are
additionally chunked into thirds and scored per third, producing a **within-item quality
drift** measure. All outputs are labelled "predicted" in every table and chart, never
presented as human ratings.

**Why a distributional metric rather than a MOS predictor.** Learned MOS predictors of the
UTMOS generation were trained on 2022-era synthesis and saturate on current frontier
systems — everything lands in a narrow band near the ceiling and the ranking degenerates
into noise. Since this study compares six current systems, a saturating instrument would
produce a useless axis. A distributional design remains discriminative on human-quality
systems because it is measuring distance between distributions rather than predicting a
bounded rating. NISQA was rejected on a second ground: it is a telephony degradation model
measuring noisiness, coloration and discontinuity, which is a different construct from
naturalness and is frequently misapplied as if it were not.

**Why a second, unrelated model.** Any single predictor carries its own biases. Agreement
between two architecturally unrelated models is evidence; disagreement is a flag worth
investigating rather than averaging away.

**The parameter this instrument introduces.** A distributional metric compares against a
reference corpus of real speech, which makes that corpus part of the measurement. If the
reference is out of domain relative to the corpus under test, the measured distance may be
dominated by domain mismatch rather than synthesis quality, compressing exactly the
differences the study needs to resolve. The reference set is therefore **named and
justified in the pre-registered configuration**, chosen to match each use case's register
where possible, and the benchmark's documented minimum sample size is confirmed before
the campaign. If only one reference is available for both use cases, cross-use-case
comparison is declared unsupported while within-use-case ranking remains valid.

**Validation before headline use.** Each provider's item set is split in half and scored
separately; divergence beyond a pre-committed absolute threshold demotes the metric from
headline to supporting signal. This runs on pilot output, before the campaign, so that
the outcome can still change the design. The threshold is absolute rather than
noise-floor-relative because the noise floor is not computed until after the campaign, and
using it here would be circular.

**What it cannot tell us.** It cannot hear register fit — whether a voice is *right for
this use case*, as opposed to generally natural — which is precisely why the human pairwise
dimension exists alongside it. It produces a distribution-level score, so it is weaker at
identifying which individual clips are bad. It is sensitive to the reference choice, as
above. And its correlation with human judgment is an empirical claim that this study tests
rather than assumes (§5.3).

**How it enters the decision.** A reported column; the drift measure feeds a narration
gate; its rank correlation against human judgment determines how far it is trusted on
items the human protocol never covered.

---

### A.4 · D4 — Perceptual preference (blind pairwise, Bradley–Terry)

**What it measures.** Which system's rendering of the *same* text a listener prefers,
judged blind, aggregated onto a human-anchored 0–100 scale.

**How it is measured.** A builder generates randomised A/B pairs — same corpus item, two
systems, filenames reduced to opaque codes — with **all clips loudness-normalised to
−18 LUFS beforehand**. The rater selects "more natural / better register fit for this use
case." Human-recorded items are seeded into the pool as hidden anchors. Judgments are fit
with a Bradley–Terry model; the anchor pins the top of the scale. 21 pairs × 2 use cases ×
5 repetitions = 210 judgments; pairs are randomised across sessions rather than blocked by
system; 10% are re-judged after at least a week for self-consistency.

**Why pairwise rather than absolute rating.** Humans are substantially more consistent at
"which of these two is better" than at "rate this from 1 to 5." Absolute scales drift with
mood, sequence and anchoring, and at small n that drift dominates the signal. Pairwise
comparison also has the property that confidence grows with the number of *comparisons*
rather than the number of *raters*, which is what makes a single-rater design tractable at
all — and which is why judgment volume, not rater recruitment, is the lever this study
pulls.

**Why Bradley–Terry.** It converts win/loss records into latent strength scores on a
single scale — the same family of model underlying chess Elo — which is what allows
non-exhaustive pairings to produce a coherent ranking with quantifiable uncertainty.

**Why loudness normalisation is mandatory, not optional.** Listeners systematically prefer
louder audio. Providers ship at markedly different levels. Without normalisation, an A/B
test measures gain staging and reports it as voice quality. This single preprocessing step
is the difference between a valid perceptual measurement and an invalid one.

**Why a human anchor.** Without one, scores are relative to the best system present and
"how far from human is this?" cannot be asked. The anchor pins the scale and makes the
score comparable in kind to public boards that use the same device. The anchor must clear
a recording-quality bar — quiet room, decent microphone, normalised identically — because a
poor anchor would measure the microphone rather than humanness, and is pilot-tested
against the best system before being locked.

**How its uncertainty is handled.** This is the y-axis of every frontier chart and it
comes from one rater. Bootstrap resampling (2,000 iterations) produces 95% intervals on
every score; frontier points carry error bars; **domination requires non-overlapping
intervals**; overlapping pairs are reported as *no difference detected at this n*. The
self-consistency figure is published with the session gap that produced it, because a
consistency number without an elapsed-time denominator is not interpretable.

**What it cannot tell us.** With n=1 it cannot represent population preference — it
represents one listener's preference, measured carefully. It cannot resolve differences
smaller than its intervals, which is why those intervals are published rather than
described. It covers only a sample of corpus items, which is why cross-metric agreement
with the distributional score matters (§5.3). And it is subject to the rater's own
familiarity with the systems, mitigated by blinding but not eliminated.

**How it enters the decision.** The quality axis of all four frontier charts; the Δ column
against the public leaderboard; the arbiter of domination.

---

### A.5 · D5 — Audio hygiene

**What it measures.** Technical cleanliness: noise floor, clipping, clicks and pops, and
unnatural silences that do not correspond to sentence boundaries.

**How it is measured.** Clipping (samples pinned at the ceiling) and click detection via
numpy/scipy; speech/silence segmentation via a neural voice-activity detector, so that a
gap over 400ms is flagged only when confirmed to be a true non-speech span; loudness per
EBU R128; noise floor taken from the quietest VAD-confirmed non-speech window.

**Pre-committed thresholds.** Clean synthesis should show a noise floor below
approximately −60 dBFS; above −40 dBFS is audibly hissy and fails the narration hygiene
gate. Hard clipping is binary. These are numbers rather than adjectives because a gate
that must be committed before results cannot be phrased as "no audible artifacts."

**Why a neural VAD rather than an energy threshold.** Energy thresholds classify quiet
speech as silence, which false-flags soft and breathy delivery — exactly the styles that
narration rewards. A trained detector distinguishes quiet *speech* from actual silence;
a threshold cannot, and would systematically penalise the providers doing narration best.

**Why LUFS rather than RMS or peak.** LUFS is a perceptual standard, matching how
loudness is actually heard and how broadcast platforms regulate it. RMS is not perceptual
and has no standard behind it. This measurement serves two purposes: a reported production
defect in its own right, and the enabling measurement for the normalisation that makes
D4 valid.

**What it cannot tell us.** It detects technical defects, not aesthetic ones — a system can
be perfectly clean and unpleasant. Thresholds are conventions, so borderline cases are
judgment calls, which is why flagged files are manually reviewed. And it operates
per-file, so slow degradation across a long passage is caught by the drift measure in D3
rather than here.

**How it enters the decision.** Hard gates in both use cases; the loudness measurement is
a prerequisite for D4.

---

### A.6 · D6 — Cost

**What it measures.** The modelled bill at realistic volumes, not the list price.

**How it is measured.** The harness logs actual character counts from every API response.
Published rates are pulled and date-stamped on analysis day into a pricing configuration,
including per-request fees, monthly minimums, tier cliffs and "contact sales" boundaries.
A code path — not a spreadsheet — joins the two to produce $/1K words at 10K, 100K and 1M
words per month, plus per-session cost computed over a representative eight-turn support
exchange.

**Why modelled rather than listed.** Providers price in mutually incompatible units — per
character, per million characters, per second of audio, per hour of agent time — and differ
quietly on whether whitespace, markup tags and retries are billable. Applying published
rates to *our own logged counts* normalises these into comparable figures and exposes the
gap between headline and effective price.

**Why three volumes and a per-session figure.** Unit economics invert across tiers. A
provider that is cheapest at 10K words per month may be most expensive at 1M because of
tier structure or minimums, and per-session cost is the unit a conversational product
actually budgets in. One price figure — which is what public boards publish — cannot
express this.

**Why code rather than a spreadsheet.** Cost is a frontier axis, and the frontier must
regenerate on the four-week drift re-run without anyone reopening a workbook.

**What it cannot tell us.** It models published self-serve pricing, so it says nothing
about negotiated enterprise rates, which is where large deployments actually land. It
excludes engineering integration cost (partially captured by D7) and any egress or
storage cost downstream. And it is a snapshot: pricing changes, which the drift re-run
measures directly.

**How it enters the decision.** The x-axis of one frontier chart per use case; three cost
points in each decision memo.

---

### A.7 · D7 — Developer experience

**What it measures.** Elapsed time from opening a provider's documentation to hearing
first audio in a fresh environment, plus an enumerated log of every obstacle encountered.

**How it is measured.** One timed session per provider. Clock starts at "open docs," stops
when audio plays from a working script. Every friction event is logged as it happens —
signup hurdles, key provisioning, incorrect code samples, undocumented headers,
unhelpful errors. Same developer throughout, consistent ordering, both facts disclosed.

**Why a scoped proxy.** The parent design called for building integrations across three
platforms per provider, which is a second project. One environment sacrifices breadth but
retains the discriminating signal: documentation accuracy, authentication design, error
message quality and SDK ergonomics all compress into that single wall-clock number and its
friction list.

**Why it must be measured live.** It cannot be reconstructed afterwards. Once a developer
knows a provider's quirks, the measurement is unrecoverable — which is why it is scheduled
during adapter development rather than during analysis.

**What it cannot tell us.** A single developer with a specific background produces a
figure with an obvious ordering effect — later providers benefit from accumulated
familiarity, which is disclosed rather than corrected. It measures onboarding, not
long-run maintenance burden. And it does not generalise to other languages or frameworks.

**How it enters the decision.** A reported column and a source of risk notes in the memos:
a provider whose documentation is wrong at hello-world is a documented integration risk.

---

### A.8 · D8 — Capability surface

**What it measures.** The factual feature surface per provider: voice count, languages,
cloning availability and gating, SSML and style controls, streaming protocols, word-level
timestamps, SLA and compliance terms, pricing-model shape, and generation determinism
(inherited from the variance subset).

**How it is measured.** Structured desk research against official documentation,
approximately 30 minutes per provider, recorded as a ✓/✗/partial matrix with a source link
and retrieval date **per cell**. Unscored — facts, not judgments.

**Why per-cell sourcing and dating.** It makes the matrix auditable and makes staleness
visible. A capability claim without a date is not checkable, and provider feature surfaces
move quickly.

**Why it is not scored.** Converting capability facts into a score would require weights,
which the decision framework rejects. The matrix feeds the gates directly instead — a
gate such as "commercial use permitted on an accessible tier" is a capability fact, not a
measurement.

**What it cannot tell us.** It records documented capability, not capability quality — that
a provider offers SSML says nothing about how well it honours it. Documentation is
sometimes wrong, which is partially caught by D7. And it cannot cover terms behind
enterprise sales conversations.

**How it enters the decision.** Feeds gates; supplies the half of a buying memo that
measurements cannot answer. Ten measurements cannot establish that a feature does not
exist.

---

### A.9 · Instruments deliberately excluded

Documented because the exclusions are methodological choices, and because their presence
in a TTS evaluation would signal a design borrowed from a different problem.

| Instrument | Why excluded |
|---|---|
| **PESQ** | Full-reference and intrusive: requires a time-aligned clean reference and a degraded copy of it. Synthetic speech is not a degraded copy of a reference recording but a different waveform with different timing, so the alignment assumption fails. Correct for enhancement and codecs; not for TTS |
| **Mel-cepstral distortion (MCD)** | Requires parallel reference audio and penalises prosodic difference. Since many renderings of a sentence are equally good, MCD punishes valid variation. Appropriate for voice conversion and same-architecture ablations; not for cross-system TTS comparison |
| **STOI / SI-SDR** | Same full-reference limitation as PESQ |
| **UTMOS / UTMOSv2** | Saturates on current frontier systems; ranking degenerates into noise (A.3) |
| **NISQA** | Telephony degradation model, not a naturalness judge — construct mismatch |
| **Speaker similarity** | Meaningful only when cloning a target voice. This study locks provider-recommended stock voices, so there is no target to measure similarity against. Would be required if the design changed to cloning |
| **Audio-LLM-as-judge** | Promising but bias-prone and not yet well characterised. Listed as future work, never as a primary instrument |
| **Human MOS panel at scale** | Cut for cost and feasibility; the pairwise design is the affordable substitute, and its limitations are disclosed rather than papered over |

---

## Appendix B — Software stack

Each entry gives **role in this study**, **why selected**, **rejected alternatives**, and
**how invoked** — the last column names the module that calls it, so a reader can go from
this table to the code without searching. Exact versions are pinned in the dependency
lockfile committed to the repository; the lockfile, not this appendix, is the
authoritative record, because metric implementations move and a moving instrument
invalidates the drift comparison.

**Analyzer module map.** Every library below is reached through exactly one of these
entry points, all of them pure functions over the immutable run store:

| Module | Dimension | Libraries it drives |
|---|---|---|
| `analyze/wer.py` | D2 | `transformers` (Parakeet), `faster-whisper`, `jiwer` |
| `analyze/quality.py` | D3 | TTSDS2, Audiobox Aesthetics |
| `analyze/hygiene.py` | D5 | `silero-vad`, `pyloudnorm`, `numpy`/`scipy` |
| `analyze/latency.py` | D1 | none — pure Python over `api_log.jsonl` |
| `analyze/variance.py` | RQ5 | TTSDS2, `jiwer`, `numpy` |
| `analyze/drift.py` | D3 (within-item) | TTSDS2, `silero-vad` |
| `analyze/cost.py` | D6 | none — `pricing.yaml` × logged counts |
| `human/` | D4 | `pyloudnorm` (normalisation), `choix` (Bradley–Terry), `scipy` (bootstrap) |
| `score/` | decision layer | `scipy` (Spearman, bootstrap), `matplotlib` (frontiers) |

### B.1 Analyzer architecture — and a reversed decision

**Decision: no aggregating toolkit. Metric libraries are invoked directly, one analyzer
module per dimension.**

This reverses an earlier decision to use VERSA as the analyzer backbone, and the reversal
is documented because the reasoning is transferable.

VERSA was originally selected on three grounds. **Credibility** — "scored with VERSA's
standard implementations" is a stronger claim than "scored with my own scripts."
**Reproducibility** — a single committed YAML configuration means a re-runner gets an
identical metric stack. **Leverage** — it collapses six separately-versioned metric
repositories into one maintained dependency.

Two things then changed: native Windows support became a project requirement, and a
dependency lockfile was committed. Re-testing each ground against the new situation:

| Original ground | Holds? |
|---|---|
| Credibility | **No longer load-bearing.** Credibility attaches to the underlying metric implementations, which are the same libraries either way and are cited individually. A dispatch layer does not make a measurement more valid |
| Reproducibility | **Better served by the lockfile**, which pins WER normalisation behaviour, ASR runtime and distributional-metric revisions directly — which was the actual objective |
| Leverage | **Inverted.** The toolkit and one ASR framework were the only Linux-first dependencies. The toolkit had become the dependency forcing a container, in exchange for roughly five of its ninety-odd metrics |

Removing it makes the analysis stage run natively on the primary development platform,
removes a second Linux-first dependency alongside it, and costs nothing that the lockfile
was not already providing.

**This is not "hand-rolled metrics"** — the alternative originally rejected, and still
rejected. These are standard implementations invoked directly; nothing about the
computation changes, only the dispatch. Writing bespoke WER or loudness code remains out
of the question.

**VERSA remains a sound recommendation in general.** It is peer-reviewed, actively
maintained, from a strong lab, and for an evaluation running twenty-plus metrics across
speech, audio and music it would earn its place. It did not earn it here.

### B.2 ASR judges

| Component | Role | Why | Rejected alternatives | How invoked |
|---|---|---|---|---|
| **Parakeet RNNT 0.6B** (NVIDIA), via HuggingFace `transformers` | Primary WER judge | Sits in the highest throughput tier among open ASR models by a wide margin — which is what a judge needs, alongside architectural independence from judge 2. Its *accuracy* standing is contested and turns over in months, so no leaderboard claim is made. Loaded through `transformers` rather than **NVIDIA NeMo**, which is Linux-first and would force a container for no accuracy benefit | **Parakeet TDT** — the faster decoder, but `ParakeetForTDT` exists only on `transformers` `main`, and NVIDIA's own model card says it must be installed from source until it reaches a release; depending on an unreleased revision would undercut the claim that the lockfile pins the instrument. **NeMo-hosted Parakeet** — identical weights, worse portability | `analyze/wer.py`, batched over `runs/<id>/audio/`; pinned by released version in the lockfile. Re-checked at Phase B: if TDT has landed in a release, it is adopted and logged |
| **faster-whisper** (Whisper large-v3 weights, CTranslate2 runtime) | Second WER judge, adjudicator | Different organisation, different architecture, different training pipeline — satisfies the independence constraint on all three axes. CTranslate2 is roughly 4× faster than the reference implementation and ships Windows wheels | Legacy `openai-whisper` (slow, effectively unmaintained); **NVIDIA Canary-1B** — rejected as second judge because it shares Parakeet's FastConformer encoder family and NVIDIA's training pipeline, which would silently weaken the agreement rule while preserving its appearance; commercial ASR APIs — conflict of interest and silent updates | `analyze/wer.py`, same batch pass as judge 1 |
| **jiwer** | WER computation | Standard, well-tested implementation; normalisation behaviour is explicit and pinnable | Hand-rolled edit distance — no reason to reimplement a solved problem, and normalisation is where the subtle bugs live | `analyze/wer.py` and `analyze/variance.py`, after a shared normalisation step |

### B.3 Quality models

| Component | Role | Why | Rejected alternatives | How invoked |
|---|---|---|---|---|
| **TTSDS2** | Primary distributional quality | Purpose-built to remain discriminative on human-quality systems, where rating-predictors saturate; peer-reviewed with cross-domain correlation evidence | UTMOS/UTMOSv2 (saturation); NISQA (construct mismatch — a degradation model, not a naturalness judge); audio-LLM-as-judge (promising, bias-prone, not yet well characterised — future work only) | `analyze/quality.py` over every file; `analyze/drift.py` over passage thirds; `analyze/variance.py` over repeat draws. Reference set and revision pinned in `analyzers.yaml` |
| **Audiobox Aesthetics** (Meta) | Secondary quality opinion | Architecturally unrelated to TTSDS2, trained on large-scale human aesthetic ratings; provides a second signal whose agreement is evidence and whose divergence is a flag | A second distributional metric — would share failure modes with the primary and add little | `analyze/quality.py`, same pass as the primary |

### B.4 Audio analysis

| Component | Role | Why | Rejected alternatives | How invoked |
|---|---|---|---|---|
| **silero-VAD** | Speech/silence segmentation for pause detection and noise-floor windowing | Neural detector distinguishes quiet speech from true silence; energy thresholds cannot, and would false-flag exactly the soft delivery styles narration rewards | librosa energy heuristics — a dependency without a capability gain, and a source of systematic false flags | `analyze/hygiene.py` for pause detection and noise-floor windowing; `analyze/drift.py` for per-third segmentation |
| **pyloudnorm** | EBU R128 / ITU-R BS.1770 loudness measurement and normalisation | Perceptual standard; serves both as a reported hygiene metric and as the mandatory preprocessing step for valid pairwise comparison. Keeps the measurement inside the Python pipeline where it is unit-testable | RMS (not perceptual, no standard); ffmpeg `loudnorm` (works, but moves the measurement outside the testable pipeline) | `analyze/hygiene.py` to measure; `human/loudness_normalize.py` to normalise every clip to −18 LUFS before pairwise presentation |
| **numpy / scipy** | Clipping and click detection | Ceiling-pinned samples and short high-amplitude transients need nothing more sophisticated | Heavier audio libraries for a task that is a handful of array operations | `analyze/hygiene.py` |

### B.5 Statistics

| Component | Role | Why | Rejected alternatives | How invoked |
|---|---|---|---|---|
| **Bradley–Terry implementation** (`choix` or equivalent) | Fit pairwise judgments to latent strength scores | Standard implementation of a standard model; no bespoke inference | Elo updated online (order-dependent, and this study has no meaningful arrival order); raw win-rate (ignores opponent strength, which matters badly at 21 pairs) | `human/` fitting step over `judgments/*.csv` |
| **scipy / numpy** | Bootstrap resampling; Spearman rank correlation | Bootstrap requires no distributional assumptions, which suits a small non-normal judgment set. Spearman rather than Pearson because the quantity of interest is rank agreement, and the underlying scales are not linearly comparable | Parametric CIs (assumptions unsupportable at this n); Pearson (assumes linear comparability the scales do not have) | `human/` for the 2,000-resample CIs; `score/` for the three rank correlations |

### B.6 Harness and infrastructure

| Component | Role | Why | Rejected alternative |
|---|---|---|---|
| **Python 3.11**, `uv`, committed lockfile | Runtime and dependency management | The lockfile *is* the instrument specification — WER normalisation, ASR runtime and quality-model revisions all shift results, so a drift re-run can only attribute change to a provider if the toolchain is pinned | Unpinned `requirements.txt` — makes the +4-week comparison uninterpretable |
| **Pydantic v2 over YAML** | Configuration loading and validation | Pre-registered configuration must fail loudly on malformed or unexpected input; strict schemas catch a typo in a gate threshold before it silently changes a result | Raw `yaml.safe_load` into dicts — a mistyped key becomes a silent default |
| **httpx (async)** | Provider API client | Concurrency for the bulk campaign, with strict serialisation available for latency trials where concurrency would contaminate the measurement | `requests` (no async, so the campaign runs serially and takes hours longer) |
| **Custom adapters** (one module per provider, shared interface) | Normalise six incompatible APIs to one return shape | The genuinely project-specific layer. Shared base class carries cross-cutting fixes — for example, streamed WAV headers that declare placeholder durations, which corrupt every downstream duration-dependent metric if not repaired centrally | Per-provider SDKs — six incompatible return shapes and six places for the same bug |
| **Immutable run store** | Provenance | Run directories are never mutated. Analyzers are pure functions over the store, re-runnable without regenerating audio. Failed runs are re-run cleanly under a new manifest, never patched into a partial mix | In-place correction — destroys the provenance the pre-registration claim rests on |
| **Content-hash cache** | Incremental re-runs | Makes the four-week drift re-run cost only what changed, which is what makes the longitudinal claim affordable | Full regeneration each time — multiplies the budget by the number of re-runs |
| **Typer CLI + Streamlit panel** | Two front doors | Both call the same underlying functions; the panel never duplicates logic. Scripting and CI use the CLI; interactive inspection and demonstration use the panel | A panel with its own logic — two implementations that drift apart |
| **pytest** | Regression net | Specifically targets silent-corruption defects — the class of bug that produces plausible wrong numbers rather than an error | Manual verification — the defects this targets are by definition invisible to inspection |
| **Static A/B voting interface** | Pairwise judgment collection | Serves blinded, loudness-normalised pairs; batched submission; tokened access rather than open voting. Deployed only for this dimension — everything else stays local | Open public voting (unverifiable raters); a local-only page (cannot reach remote raters at all) |
| **Optional container** | Reproducibility artifact | Retained as a pinned-environment fallback for reproducers, no longer required for the primary workflow | Mandatory containerisation — the v1 position, reversed once its two Linux-first dependencies were removed |

### B.7 Rejected infrastructure

| Considered | Why not |
|---|---|
| **LLM evaluation frameworks** (promptfoo, DeepEval, Inspect, Braintrust, LangSmith) | Built for text-in/text-out with LLM-judge scorers. An audio API assessed by acoustic models is the wrong shape; adapting one would cost more than the thin harness it replaced |
| **Experiment-tracking SaaS** (Weights & Biases, Braintrust) | The immutable file-based run store provides provenance with zero infrastructure, and a self-contained repository is the more useful artifact for this project's purpose |
| **A database for results** | Analysis outputs are pure functions of an immutable store; files are sufficient, diffable, and require no service to read three years from now |

---

## Appendix C — Reproducibility

**Pre-registration.** Provider list, voice selections, corpus, acceptance gates, the
noise-floor reporting rule, the per-item failure threshold, analyzer parameters including
the distributional reference set, and the reporting format of §7 are all committed to
version control and tagged before any result file exists. Git history is the receipt.
Amendments made *before* the campaign, in response to pilot findings, are re-tagged with
the reason logged; amendments after results exist are not made.

**Deviation log.** Every departure from the pre-registered design is recorded with its
rationale and referenced from the affected section. Deviations are expected; silent
deviations are the failure mode.

**Run provenance.** Each run directory records date, region, model and voice versions,
interpreter version, hardware, complete API logs including errors, and the generated
audio. Nothing in a run directory is ever modified.

**Re-execution.**

```bash
veval doctor                      # verify all provider adapters end-to-end
veval generate --mode campaign    # primary corpus × providers
veval generate --mode latency     # 50 serial trials, pinned region
veval generate --mode variance    # repeat-synthesis subset → noise floor
veval analyze  --run <run_id>     # all analyzers; pure functions over the run store
veval score    --run <run_id>     # gates → frontiers with CIs → robustness → correlations
veval report   --run <run_id>     # tables, figures, memo scaffolds
```

**Cost of reproduction.** A demonstration path runs a five-item corpus across all six
systems, reaching a toy frontier chart for approximately one dollar. Full reproduction
requires paid accounts with three of them — the quality leader, the latency leader, and
per-generation hosting for the open-weights model — plus an account with the value-tier
provider at whatever pricing applies once its free window has closed.

**What is not reproducible, and why.** The measurement pipeline is reproducible for D1–D3,
D5, D6 and D8 given the same configuration and credentials. **Two dimensions are not
reproducible by construction.** D4 rests on one person's judgment; the rating interface and
the fitting pipeline reproduce, the human does not. D7 is destroyed by the act of measuring
it — once a developer knows a provider's quirks, "time from opening the docs to first
audio" cannot be measured again by that person (A.7). D6 and D8 reproduce as *procedures*
but not as *values*, since prices and feature surfaces move; both are date-stamped for
exactly that reason.

---

## Appendix D — Adversarial review record

Two critical passes — one self-directed, one external — were run against the design before
data collection. Both
are reproduced in full in the repository. They are included here because a method's
robustness is evidenced by what its critics found, not by its author's confidence.

**First pass — self-directed red team.** Ten findings, covering toolchain portability
risk, unstated GPU requirements, unperformed pairwise volume arithmetic, missing hosting
plan for the voting interface, latency geography confounds, unspecified trial concurrency,
an overstated contamination-probe claim, a missing quality bar for the human anchor,
mid-project model deprecation, and the absence of a pilot run. All ten resolved in the
current design.

**Second pass — external review.** Ten findings. Grouped below by the reviewer's own
severity rating; note that the specification groups them differently, by impact on what
the study can *claim*, which promotes within-item drift measurement and computed
cross-metric agreement into the substantive set. The four rated most severe: a proposed ASR judge substitution that would have broken the
two-judge design's independence assumption while preserving its appearance; perceptual
uncertainty that was measured but never propagated into the frontier analysis; an
unspecified reference set for the distributional metric; and the absence of any
within-provider variance measurement, leaving the study unable to state its own noise
floor. Findings on failure-incidence reporting, within-item drift measurement, computed
rather than asserted metric agreement, session ordering, tier assumptions and document
consistency were also adopted.

Notably, nine of ten concerns raised in that review *before* the reviewer read the full
design did not survive contact with it — latency methodology, hard-input coverage,
cross-metric checking, licensing review, and the deliberate exclusion of speaker
similarity were all already addressed, several more rigorously than the reviewer's own
recommendation. This is recorded because it is evidence about the design, and because
selective reporting of only the criticisms that landed would misrepresent the review.

---

## Appendix E — Pre-registered configuration snapshot

[[FILL: paste the contents of the tagged configuration at `prereg-v1` — providers, voices,
gates with rationales, analyzer parameters including the reference set and thresholds, and
the corpus manifest hash. This appendix exists so the reader can verify the pre-registered
design against the reported results without leaving the document.]]

**Verification command:**

```bash
git log -1 --format='%H %ci' prereg-v1
git diff prereg-v1 --stat -- configs/ corpus/    # must be empty, or every change logged in DEVIATIONS.md
```

[[FILL: output of the above, demonstrating the tag predates all result files]]
