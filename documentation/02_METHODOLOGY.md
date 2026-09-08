# 02 · Research Methodology

*Why every methodology choice was made the way it was. Different
from [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) which lists the
individual decisions — this document explains the underlying
principles the decisions apply.*

> **⚠ Scope disclaimer** · Methodology described here was applied
> as of 2026-09-01 on 8 vendor accounts (paid public tiers). Full
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

**Honest exception — three unpinned analyzer revisions, one
post-hoc-recorded normaliser hash, two null power-calc values**.
`configs/analyzers.yaml` carries eight TODO placeholders. Three
of them (line 96 `audiobox_revision`, line 179 wav2vec2, line 183
faster-whisper — all `TODO_pin_sha_before_campaign`) are live
and unpinned, and propagate into the committed run outputs
(`analysis/campaign-*/wer.json` `judges[*].revision`,
byte-identical across R2 and R3). The audiobox revision governs
AB.PQ + AB.CE; the two judge revisions govern the two-judge
agreement WER. A fourth line (191, `wer_normaliser_hash:
TODO_compute_hash_when_module_lands`) was left as a TODO in the
config; `wer.py` computes the SHA (`75379ec8…`) at runtime and
writes it into wer.json. That value being byte-identical in R2
and R3 is real evidence the normaliser did not drift across the
interval, but it is a post-hoc receipt, not a pre-committed pin
— the distinction pre-registration turns on. Two lines (34, 46)
are moot under [D-A](06_KEY_FINDINGS.md#d-a) (TTSDS2 skipped).
The remaining two (lines 211, 212, `mdd_at_target: null` /
`mdd_at_minimum: null`) are the Phase-D BT power-analysis MDDs
that were meant to say whether the operative-post-D-009 target
of 216 judgments was adequate (the operative floor, which under
D-009 is the same 216 — the 3-rep count evaluated on the
9-system roster IS the spec's 3-rep floor; the older 126 was the
7-system spec's floor and is superseded)
— the pre-registered power calc that went with the BT panel and
was, like the panel itself, never run. The adjacent
`n_judgments_target: 210 / n_judgments_minimum: 126` rungs on
lines 209-210 are pre-D-009 stale — D-009 (`prereg-v1.7`) raised
the campaign target to 216 for the 9-system roster and named the
`mdd` block as a re-run target that never landed. Vendor models are pinned in `configs/voices.yaml` per D-005.
**Honest mitigation for the neural-model side**: the R2↔R3
replication ran on the same environment three weeks apart and
produced Spearman ρ = 0.905–1.000 across signals, which is
evidence the resolved analyzer stack was stable across that
interval — but a fresh clone re-downloading the three HF repos
today will resolve to whatever `main` serves that day, so
exact-value reproduction outside the R2↔R3 interval is not
guaranteed. See [07 gap 9](07_GAPS_AND_FUTURE_WORK.md) for the
full 8-line inventory + v2 fix.

### 2. Two independent MOS pipelines, not one

Every audio file is scored by **three independent MOS models** —
Meta Audiobox Aesthetics (2 axes: PQ + CE) and Microsoft's DNSMOS
implementation, which ships **two separate predictors**: the P.808
single-model predictor (1 axis: `p808_mos`) and the P.835
three-scale predictor (3 axes: `ovrl_mos` / `sig_mos` / `bak_mos`
from a shared internal representation). Six machine-quality
signals total, from two independent vendor pipelines but three
distinct scoring models. Cross-pipeline agreement is computed as a
first-class result.

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

### 5. Pre-committed hard gates + tie-band ranking, NOT a weighted composite

The v1 plan had `quality_score = 0.4·PQ + 0.3·CE + 0.2·MOS + 0.1·noise`.
Killed it in Phase A. **Weights are always arguable; pre-registered
gates are falsifiable.**

The pre-registered v2 model had **four** components:
- **Hard gates** in [`configs/gates.yaml`](../configs/gates.yaml)
  — pass/fail against numeric thresholds (**executed in v1**;
  adjudicated in 04's [Pre-registered gate outcomes](04_RESULTS.md#pre-registered-gate-outcomes))
- **Gate robustness sweep** — every gate in `gates.yaml` carries
  an explicit `robustness_points` list (spec §5, defect 3.40: a
  ±20% envelope on a 400 ms threshold never reaches the
  500-600 ms perception threshold the rationale cites, so the
  sweep points are named explicitly per gate). The sweep re-applies
  the gate at each adjacent threshold and reports whether the
  survivor set stays the same or shifts — the pre-registered
  answer to "your gate is at 400 ms, but is that arbitrary?"
  (**executed in v1**; [`src/veval/score/robustness.py`](../src/veval/score/robustness.py)
  implements it, `analysis/campaign-20260831T175358Z/score.json`
  is the committed receipt, and the per-gate marginal counts are
  published in 04's [Pre-registered gate outcomes](04_RESULTS.md#pre-registered-gate-outcomes))
- **Pareto frontiers** on the remaining axes — vendors on the
  frontier are non-dominated, vendors off it are worse on some axis
  without being better on any other (**not executed in v1** —
  D-H-blocked: [`src/veval/score/frontier.py`](../src/veval/score/frontier.py)
  consumes BTFit, and no BT panel means no frontier build. Instead
  the docs report per-axis rankings with unpaired SE(diff) tie
  bands — see 04's [Rankings summary](04_RESULTS.md#rankings-summary).
  Full Pareto adjudication is deferred to v2 alongside the BT panel.)
- **Bootstrap 95% CIs** on frontier positions (**not executed in
  v1** — same D-H blocker: bootstrap runs over BTFit strengths, so
  no BT panel means no bootstrap interval on a frontier point)

Both the Pareto adjudication and the Bootstrap CIs are blocked
by the same upstream decision — D-H's deferral of the n≥15-30
BT panel — not by the frontier code itself:
[`src/veval/score/frontier.py`](../src/veval/score/frontier.py)'s
`build_frontier(bt_fit: BTFit, ...)` signature (line 95) consumes
BT strengths + their bootstrap CIs, and the CI-domination check at
lines 124-125 reads `bt_fit.strength_ci_lower` / `strength_ci_upper`
directly. Without a fitted BTFit there is nothing for
`frontier.py` to compute over, and no `analysis/score.json` can
be produced.

The v1 substitute is: per-vendor per-signal unpaired SE(diff) with
a |z| < 2 tie band, published in 04's Rankings summary tables.
This is coarser than a Bootstrap CI on a Pareto point (no frontier
membership statement, no CI-domination test) but is derivable from
the same per-item quality means and — unlike the frontier code
itself — does not require the BT panel that D-H defers.

**Why the model still stands even partially executed**: a reader
who prefers different weights can construct any composite they
want from the raw data. A reader who's given only one composite
can't undo the author's weights. The published per-axis tie bands
carry the same "no domination without evidence" spirit as the
missing Pareto adjudication, just at less structural precision.

---

## <a name="corpus"></a>The corpus (per spec § 3.3)

75 items per use case, in six pre-registered strata. **60 items
were authored to a documented brief; 15 are a pre-registered
contamination probe — Harvard sentences (conversational P01-P15)
and public-domain literary openings (narration P01-P15 —
Dickens, Austen, Tolstoy, Melville, Doyle, Twain, Joyce).** The
probe items are reserved out of D4 pairwise by
[`src/veval/human/pair_builder.py`](../src/veval/human/pair_builder.py)
by design.

| Stratum | n / UC | Purpose |
|---|---:|---|
| `short` | 12 | Baseline utterances, 5-10 words. Where the WER floor sits on well-formed content. |
| `medium` | 20 | Mid-length utterances, 30-60 words. Where most production content sits. |
| `long` | 8 | Multi-paragraph passages (~200 words each). RTF gate, per-third drift analysis (F-6), long-stratum hygiene gates. Raised from the parent corpus's 2-in-42 to **8 per use case** to give the RTF + drift + long-hygiene gates a real sample. |
| `jargon` | 12 | Technical / branded / rare tokens. Where WER stress-tests vocabulary coverage. |
| `edge` | 8 | Adversarial inputs — number-heavy, punctuation-dense, unusual formatting. Where clipping and failure-taxonomy events cluster. |
| `probe` | 15 | Pre-registered contamination probe (see below). Reserved out of D4 pairwise. |

### <a name="probe"></a>Contamination probe — the finding the probe was written to catch

Spec § 3.3 pre-registers the probe as *"~15 famous public
sentences — Harvard sentences and public-domain literary
openings — as a training-contamination probe. Contamination
probe caveat, carried into the write-up."* The probe is fully
implemented in [`corpus/conversational.yaml`](../corpus/conversational.yaml)
+ [`corpus/narration.yaml`](../corpus/narration.yaml) P01-P15.
It ran. It fired. The result was not reported in earlier
revisions of this doc; retracted; see
[CORRECTIONS row 160](../CORRECTIONS.md).

**What the probe measured**: mean two-judge agreement WER by
stratum on R2. The probe items average **24.9 words** on
narration — **3.4× longer** than the `short` stratum's 7.4 — and
still transcribe at roughly **one third** of `short`'s error
rate. Length cannot explain it.

| Stratum | Conv mean words | Conv WER | Narr mean words | Narr WER |
|---|---:|---:|---:|---:|
| `edge` | 12.8 | **0.438** | 16.2 | **0.404** |
| `jargon` | 11.6 | 0.326 | 12.8 | 0.228 |
| `long` | 237.5 | 0.164 | 230.1 | 0.194 |
| `medium` | 46.2 | 0.132 | 44.5 | 0.112 |
| `short` | 7.1 | 0.044 | 7.4 | 0.084 |
| **`probe`** | **7.5** | **0.026** | **24.9** | **0.028** |

Sentences the ASR judges have almost certainly seen during
training transcribe far more accurately than sentences the
project authored — even when the famous ones are longer. That
is precisely the effect the probe was designed to catch.
Reported as *directional*, per spec § 3.3's rule
("never as a headline").

**Impact on published WER figures — the ~3-pp drag**: the probe
is 15 of 75 items — **20% of every WER cell** — at roughly a
fifth of the corpus error rate. Excluding it changes every
published WER by ~3 percentage points and swaps top-1 on
conversational:

| WER band | Published (all 75) | Probe-excluded (60) |
|---|---:|---:|
| Conversational band | 13.7 – 16.7% | 16.9 – 20.0% |
| Narration band | 12.4 – 14.0% | 14.9 – 16.8% |
| Orpheus conversational | 26.9% | 32.5% |

**Conversational top-1 order holds either way — OpenAI leads
probe-included at 0.1370 and probe-excluded at 0.1694; Fish is
#2 in both readings (0.1378 / 0.1701).** What the probe moves
is the 3rd/4th pair: probe-included ElevenLabs is #3 (0.1407)
and Speechify #4 (0.1433); probe-excluded Speechify passes
ElevenLabs (0.1735 vs 0.1758) and takes #3. **Narration
top-8 order is unchanged either way** (Cartesia → ElevenLabs
→ Speechify → Google → OpenAI → Deepgram → Fish → Orpheus in
both readings). The OpenAI–Fish conv margin (0.0008 all-75,
0.0008 probe-excluded) is 40× smaller than the ~3-pp probe
dilution, so **conversational WER rank should be read as
unresolved at this n**, not as a stable ordering — but the
"unresolved" band is #1-#2 (OpenAI/Fish) either way, and the
probe caveat is a rank-order stability issue at 3rd/4th,
not a top-1 swap. **Quality-axis top-1 is unchanged** on all
six axis × use-case combinations under probe exclusion — the
probe caveat is WER-only. See
[04 § WER-gate admission](04_RESULTS.md#wer-gate-admission)
for the full per-vendor bands, both ways.

**How to read WER in this doc going forward**: WER numbers
sourced from `analysis/campaign-*/wer.json` `agreement_wer_mean`
are computed over all 75 items; the ~3 pp probe-dilution
caveat and the conversational top-1 swap are attached wherever
the number is quoted.

---

## The eight measurement dimensions (D1–D8)

Each dimension is designed to be *independent* — a vendor that
wins one shouldn't automatically win another. That's what makes
Pareto framing meaningful. Spec §3.2 pre-registered eight
dimensions; each is named below with the current execution
status inline (four fully executed, one partially, three
reported-not-timed / asserted / matrix). Cost's earlier "D5"
label retracted; see
[CORRECTIONS row 157](../CORRECTIONS.md).

### D1 · Latency

**What we measure**: TTFA (time-to-first-audio-frame) p50 / p90 /
min / max from 50 serial trials per vendor, in dedicated
latency-mode sessions (fresh calls, no cache). RTF was
pre-committed as the narration gate; the R2 campaign ran fully
from cache so `synthesis_time` was unavailable there, but the R3
campaign (`campaign-20260831T175358Z`, `--no-cache`) populated
`long_stratum_rtf_p50` for all 16 cells and **adjudicated the
gate: 5 pass / 3 fail**. See
[04_RESULTS.md § RTF admission](04_RESULTS.md#rtf-admission) for
the full per-vendor table.

**Why serial not parallel**: parallel trials measure the vendor's
concurrency handling; serial trials measure the tail of an
individual user's experience. For a support-agent product, the tail
per-user matters more than aggregate throughput.

**Why multiple sessions**: a single session of TTFA cannot
distinguish "vendor is fast" from "vendor happened to be fast
during our measurement window." **Six sessions** were run in
total on the two speed-critical vendors (OpenAI + ElevenLabs)
across four dates: S1a + S1b (2026-08-09), S2 (2026-08-11), S3
(2026-08-12, with concurrent ping-to-Cloudflare-1.1.1.1 baseline
to rule out ISP jitter), S4 + S5 (2026-09-01). Both vendors moved
50-90% p50 between S2 and S3; S4/S5 landed back in the S1
baseline range. See
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11)
for the full session-by-session data and the "latency absolute
values are not stable" finding.

The methodology takeaways:
- **TTFA rank is stable across all 6 sessions**: rank tests are
  robust at low session counts (ElevenLabs faster than OpenAI in
  every session)
- **TTFA absolute values are not**: publish as a range across
  sessions with per-session n and spend-cap caveats attached, not
  as a point estimate
- **6 sessions cleared the ≥5-session count Phase 1 called out,
  but not the client-side event-loop lag logging that Phase 1
  called for as a control** — that lag logging was not run on any
  of the 6 sessions, so "wide-tail vendor" vs "client-side
  contamination" attribution remains a v2 workstream (F-11)
- **The pre-registered `ttfa_p90_ms < 400` gate is all-fail on
  measured streaming vendors**: see
  [04_RESULTS.md § TTFA-gate admission](04_RESULTS.md#ttfa-gate-admission).
  As with the WER gate below, the gate is retained as
  pre-registration evidence; recommendations use the
  perception-threshold reference (~500 ms) as the softer bar,
  with F-11's session-to-session variance disclosure attached.

### D2 · WER (Word Error Rate)

**What we measure**: two ASR judges (Meta `wav2vec2-large-robust` +
OpenAI `faster-whisper large-v3`), agreement-based error detection.
The pre-registered gate is `agreement_wer < 5% + numeric/currency/
date span exempt` per item, with `failure_incidence_pct < 2.0` as
the aggregate. **Applied strictly, the gate fails every vendor**
(61.3-73.3% failure incidence) — see
[04_RESULTS.md § WER-gate admission](04_RESULTS.md#wer-gate-admission).
As with the TTFA gate, the pre-registered threshold is retained;
recommendations use WER as a **relative ranking only**, never an
absolute pass/fail. Failure taxonomy: `agreed_word_drop_runs`,
`truncation`, `repetition_loop_*`, `agreed_hallucination_runs`.

**Why agreement-based**: single-ASR WER conflates "the audio is bad"
with "the ASR misheard." Two independent ASRs agreeing on an error
location makes the "audio is actually bad" reading much more
credible.

**Why WER is relative-ranking only**: wav2vec2 emits ALL CAPS + no
punctuation and drops articles, inflating absolute WER (F-2). jiwer's
default normaliser hard-codes some of that article-drop as errors
(F-3). The error pattern is *vendor-independent* — every vendor gets
the same inflation — so relative rankings survive even though
absolutes don't.

### D3 · Quality (two MOS pipelines)

**Pipeline A · Meta Audiobox Aesthetics** — 2 pre-registered axes
of the 4 emitted: `production_quality` (technical cleanliness) +
`content_enjoyment` (listener preference/naturalness). Not
`production_complexity` (arrangement density — irrelevant when text
is held constant) or `content_usefulness` (semantic value of the
text — held constant across vendors). Pre-committing 2-of-4 avoids
post-hoc axis selection.

**Pipeline B · Microsoft DNSMOS** — two separate scoring models
in one library: **P.835** (three-scale: `ovrl_mos`, `sig_mos`,
`bak_mos` from a shared internal representation) and **P.808**
(single-model listening-quality MOS: `p808_mos`). All 4 axes
emitted; F-12 in particular hinges on P.808 shifting where P.835
does not, so the two are named separately throughout. See
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

The pre-registered plan target for this campaign was **216
blinded pairwise Bradley-Terry judgments** (36 pairs × 2 use
cases × 3 reps) with clustered bootstrap 95% CIs, per
[`DEVIATIONS.md` D-009](../DEVIATIONS.md#d-009) landed as
`prereg-v1.7` on 2026-08-08 (spec's original 210 target reflected
the 6-provider + anchor roster; D-003 grew the roster to 8
providers + anchor → 9 systems, so C(9,2) = 36 pairs, and reps
compressed from 5 to 3 kept the total near the same schedule
budget). Under D-009 the target and the spec's 3-rep minimum
floor collapse to the same number for the 9-system roster:
216 = 36 pairs × 2 UC × **3 reps** IS the 3-rep floor, not a
margin above it. The 5-rep design would have been 360; D-009
compressed to the spec's minimum-viable rep count. That
strengthens rather than weakens D-H's deferral case — the panel
was already at its minimum-viable rep count *before* the
n=1-rater problem was even reached. Note: [`configs/analyzers.yaml`
lines 209-210](../configs/analyzers.yaml) still pin
`n_judgments_target: 210 / n_judgments_minimum: 126` — the
`mdd` block was never re-synced when D-009 landed; the operative
pre-registered target is D-009's 216 per the last-tagged
amendment rule. **Not executed in v1**
— see D-H in [06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)
for the full reasoning. Short version: n=1 rater bootstrap CIs are
conditional on the single rater, and cannot license
"human-preference" claims at population level. Executing the
ceremony and disclaiming the result would be over-claim disguised
as rigor.

**Substitutes v1 relies on instead**:
- 6 machine quality signals + cross-pipeline agreement (F-8)
- 9-test Phase 2c verification pack (F-9)
- F-4a's two-independent-code-paths corroboration on the Cartesia
  mastering finding (sample-level peak scan in the hygiene analyzer
  + DNSMOS's peak-out-of-range refusal — two paths, not three; see
  CORRECTIONS row B5)

### D5 · Audio hygiene

**What we measure**: waveform-level defects across the whole
corpus, per file, that are hard to detect from listener-quality
scoring alone: `clipped_samples` (peaks at ±1.0 full-scale),
`acoustic_noise_floor_dbfs` (dBFS of the quiet regions between
speech), and a long-stratum companion enforced on the 8
long-narration items (`long_stratum_clipped_samples`,
`long_stratum_acoustic_noise_floor_dbfs`). Three of the eight
pre-registered gates in [`configs/gates.yaml`](../configs/gates.yaml)
live here.

**Why the two-stratum split**: a stray clipped sample is
tolerable across 8 seconds of conversational IVR; the same
defect across a 10-minute audiobook chapter is corrosive.
Long-stratum gates enforce zero clipping and ≤ −40 dBFS noise
floor at the passage level; the whole-corpus versions catch
per-item outliers.

**What the data supports**: F-4 (Cartesia's mastering-chain
peak-out-of-range on both use cases, cross-corroborated by F-4a
— sample-level peak scan + DNSMOS peak-refusal counts, two
independent code paths agreeing on the same defect) and N2
(Fish's conversational noise floor +12.6 dB above the 8-vendor
median). The dBFS values themselves are analyzer measurements;
plain-language reader mapping to "audible hiss" lives in 08 §
9 per the graded rubric named in DISCLAIMER's language-and-
framing block.

**Why hygiene is not folded into D3 quality**: MOS predictors
score subjective *sounds*; hygiene analyzers count objective
*bytes*. The two disagree — Cartesia's DNSMOS OVRL rankings are
high on the surviving-subset while its clipping defect gates it
out; that's the point of publishing both.

### D6 · Cost

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

### D7 · Developer experience — friction reported, timing descoped (D-I)

**What we measure — friction (reported)**: a per-vendor log of
integration events on a shared taxonomy (signup · auth · first
call · undocumented behaviour · errors-as-data · streaming
ergonomics · model/voice mapping · audio-format quirks). The
live log is at [`dx/friction_log.md`](../dx/friction_log.md) —
8 vendors, dated, status per row, with an audio-format
fact-sheet verified through Phase F and 4 cross-provider
patterns + 3 environment gotchas.

**What we DO NOT publish — timing (descoped, D-I)**: spec § A.7
also pre-registers "DX minutes" (docs-open to first-audio wall
clock, per provider). The friction_log's own header rule states
*"Cannot be reconstructed later — event timestamps and specific
errors are the measurement,"* and three separate entries
(Fish, Google, OpenAI) explicitly declare their own wall-clock
figures void (*"NOT a D7 measurement," "not a true D7
measurement," "wall-clock isn't a valid D7 measurement"*). All 8
DX-minutes cells read `TODO`. **Timing is formally descoped
in [D-I in 06 § decisions](06_KEY_FINDINGS.md#d-i)** — a
concrete, checkable descope, not a hand-wave: the measurement
is unrecoverable by the log's own pre-registered rule.

**What the friction half already earned its keep for — [F-1a
credit](06_KEY_FINDINGS.md#f-1a)**: the Deepgram integration
event surfaced a **0x7FFFAC00 placeholder length WAV header**
declaring 44,737 seconds for a 2.8-second clip. Caught in the
friction log; fixed by
[`finalize_wav_header()`](../src/veval/adapters/base.py) in
`adapters/base.py`. **Every duration-derived number in the
project rests on it**: RTF, speech-ratio, the Orpheus 14.59-s
output-cap discovery (F-5 / T8), the per-third drift analysis
(F-6). Without D7-friction the entire speed + duration surface
of the study would have been silently wrong.

### D8 · Capability audit — desk research matrix

**What we measure**: the factual feature surface per vendor —
what a buying decision needs that no amount of audio scoring
answers. Per spec § A.8: *"desk research against official docs,
~30 minutes per provider, recorded as a ✓/✗/partial matrix with
a source link and date per cell. No scoring — facts, not
judgments."* Nine columns: voice count · languages · cloning
(and its gating tier) · SSML / style / speed controls · streaming
protocol · word-level timestamps · SLA + data-residency terms ·
pricing-model shape · determinism.

**Where**: [`configs/capabilities.yaml`](../configs/capabilities.yaml)
— per (vendor, column) with `value` (`yes` / `no` / `partial`),
`source_url`, and `date_verified`, same per-cell provenance
shape [`configs/pricing.yaml`](../configs/pricing.yaml) uses.

**Three rules in the build**: *(1) Facts, not judgments* — no
"good/poor", just the value and where it was read. *(2) Date
every cell* — vendor feature pages change faster than findings,
and an undated ✓ is worthless in six months. *(3) `partial`
honestly* — where a capability exists but sits behind an
enterprise tier not bought, record `partial` with the tier
named, never `no`; that distinction is what a procurement
reader actually needs.

**What D8 closes**: `commercial_use_permitted == 1` — the fourth
pre-registered conversational gate in `gates.yaml`, whose
rationale explicitly reads "From D8 capability matrix" — is
adjudicated against the `commercial_use` column here. See
[04 § Pre-registered gate outcomes](04_RESULTS.md#pre-registered-gate-outcomes)
row for `commercial_use_permitted` for the current per-vendor
verdicts + source links.

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
  overstated ~35%), and **F-11 (the third latency session that
  showed both vendors' absolute TTFA is not stable across
  sessions)**
- The most consequential is T8 — mechanically resolved T2 (Orpheus's
  high WER = truncation cap, not intelligibility) without a manual
  listen
- F-11 is the strongest verification-surfaced finding; it
  established that ISP jitter is not the driver of the observed
  session-to-session TTFA variance (concurrent ping baseline was
  clean)

**Cost**: ~$0.63 spend + ~2 hours of work (including the third
latency session with concurrent ping baseline). Cheap replication
is the highest-leverage step in a portfolio evaluation.

---

## Honest limits

Where the methodology cannot support the claim, name it.

### What we can claim

- **Vendor rankings** on any single measurement axis, subject to
  the per-comparison SE(diff) test documented in
  [04_RESULTS.md § Rankings summary](04_RESULTS.md#rankings-summary).
  The test is applied as an unpaired formula on paired data (same
  75 corpus items rendered by every vendor), which is conservative
  for SIG_DIFF calls and anti-conservative for TIE calls; 04 also
  publishes the paired-vs-unpaired sensitivity table (paired ratios
  1.29×–2.40×, no SIG_DIFF verdict flips) and applies Bonferroni
  across the 8 top-1-vs-top-2 comparisons (Bonferroni threshold
  ≈ 2.73σ; every SIG_DIFF Audiobox call clears it; the one comparison
  sensitive to multiplicity is OpenAI vs ElevenLabs conv DNSMOS OVRL
  at 2.0σ paired, which flips back to TIE under Bonferroni).
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
  ceilings.
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
- **"You benchmarked on old models"** → every **vendor** model
  version pinned in [`configs/voices.yaml`](../configs/voices.yaml)
  with SHA where available (Orpheus D-005); measurement date on
  every finding. The three **analyzer** neural models (Audiobox,
  wav2vec2, faster-whisper) were not SHA-pinned in the campaign
  — an honest exception to the pre-registration discipline,
  disclosed in §1 above and tracked as
  [07 gap 9](07_GAPS_AND_FUTURE_WORK.md); the R2↔R3 replication
  (ρ = 0.905-1.000) is evidence the resolved analyzer stack was
  stable across the campaign interval but does not guarantee
  fresh-clone reproduction outside it
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
- [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) — findings F-1 through
  F-9 + F-11 (F-10 slot documented in-doc) + decision log
  D-A..D-H (the flip side of this document — the specific
  decisions rather than the underlying principles)
- [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) — where
  the methodology falls short and what a v2 would fix
