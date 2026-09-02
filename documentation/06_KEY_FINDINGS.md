# 06 · Key findings, friction points, and decisions

*Distilled from the running research log. Every finding here is
backed by a specific artefact under [analysis/](../analysis/) or
[analysis/verification/](../analysis/verification/). Every decision
here is backed by a specific reasoning section reachable from
the entries below.*

> **⚠ Scope disclaimer** · Findings as of 2026-08-12 on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. See
> [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Contents

- [Findings F-1 through F-9 + F-11](#findings) (F-10 slot was
  reserved for BT rating campaign results; unused because Phase 3
  was deferred to v2 per D-H, and the slot number is retained so
  future v2 work can slot in without renumbering)
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

### F-2 · Wav2vec2 is a noisy WER judge on TTS-distribution audio

Two-judge agreement WER lands in **~12–17%** for 7 of 8 vendors
(Orpheus 27%, explained by F-9 T8). This is *inflated* — wav2vec2
emits ALL CAPS + no punctuation and drops articles. The error
pattern is provider-independent, so **relative rankings survive
even though absolute numbers are inflated**. WER "ties" and
"differences" are described qualitatively in these docs; no
per-vendor WER SE is computed in v1, so treat the fine-grained
ordering with caution.

**Impact:** WER is reported as *relative-ranking-only* throughout
the results. Absolute WER numbers should not be quoted without the
"vs the same 2-judge pipeline across other vendors" qualifier. A
stronger judge (NeMo Parakeet once integrated) would tighten
absolutes but reproduce the ordering.

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
  Fish 13.78 / ElevenLabs 14.07 / Speechify 14.33). No vendor
  cleanly leads; the spread is smaller than the F-2 / F-3
  WER-judge inflation. Orpheus at 26.9% is the only vendor
  categorically outside the pack.
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

**F-4** (original observation): Cartesia produced 429 clipped samples
on narration + 406 on conversational — **100× the next-worst
provider**. `hygiene.json`, sample-level peak detection.

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
recovers the audio; without it, ~46% of Cartesia's output is
silently unusable in a quality-check pipeline.

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
- **Hard 14.59-s output cap per call** — 22/75 narration items
  (29%) exceed this cap; 8 of those (11%) are catastrophically
  truncated (~84% content loss). See
  [F-9 T8](#f-9--outlier-verification-verdicts-phase-2c) and
  [04 footnote ¹](04_RESULTS.md#footnote-1).
- **Worst WER** in the roster (27% mean, ~2× next-worst) —
  the mechanism is the output cap, not intelligibility
- **Widest between-draw variance** on quality signals

**But not artefact-driven on quality**: per-stratum recompute
(04 footnote ¹) shows Orpheus's narration AB.PQ mean of 8.002
is essentially identical across complete-audio (8.008) and
truncated-audio (7.974-8.009) strata. Its per-call rendering
is genuinely uniform-quality; the aggregate is earned.

**Impact:** Orpheus is a legitimate choice when: (a) every turn
comfortably fits under 14.59 s of audio (so the cap never
bites), AND (b) worst-WER + no-cost-advantage is acceptable
(e.g., an experimental prototype, an open-weights preference,
or a specific voice character the closed vendors don't offer).
For narration or any long-form use, T8's output cap makes it
structurally unsuitable. **The old "budget dominates → pick
Orpheus" heuristic is retired** — on this data, if budget
dominates, OpenAI at $0.075 is the pick (peer-priced to Orpheus
and passes the cap).

### F-6 · ElevenLabs L03 monotonic fadeout

Item L03 in the narration corpus produces a **reproducible monotonic
loudness fadeout** across the audio on ElevenLabs — every fresh
regeneration shows loudness decreasing across thirds. Mean delta
across 4 total draws: **2.7 dB** (original campaign observation was
3.6 dB, on the high side of the natural range — see F-9 T4).

**Impact:** ElevenLabs has text-dependent quirks that can't be
predicted from marketing materials. A production quality-check
step that flags monotonic loudness drift catches this class of
issue cheaply.

**Evidence:** [`analysis/campaign-20260809T204608Z/drift.json`](../analysis) +
[T4 verdict](../analysis/verification/T4_elevenlabs_L03_fadeout.md)

### F-7 · Speechify's Audiobox lead is consistent AND transferable

Speechify tops **both** Audiobox axes on **both** use cases with
the pre-registered voice picks. Verification (F-9 T6) confirmed
the ranking with a deliberately-different alt voice — the alt
voice scored *higher* than the pinned voice, not lower.

**Impact:** Speechify's Audiobox #1 rank is a **Simba-3.2 model**
property, not a lucky voice pick. Vendor-agnostic buyers can
select from Speechify's 8 Simba-3.2 voices based on brand fit
without worrying about a big quality drop-off.

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
- **N2 Fish noise floor** — Confirmed automatically (+12.6 dB above
  median; 3rd independent pipeline)
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
### F-11 · Latency absolute values are not stable session-to-session

TTFA rank is portable across sessions; absolute values are not.
Four latency-mode runs per speed-critical vendor across three
dates (2026-08-09, -11, -12); S3 ran with a concurrent
ping-to-Cloudflare-1.1.1.1 baseline (274 probes during the window)
to separate vendor-side from last-mile-link variance.

| vendor | S1a p50 | S1b p50 | S2 p50 | S3 p50 | S3 vs S1a | n per session |
|---|---:|---:|---:|---:|---:|---:|
| ElevenLabs | 439 | 440 | 424 | **694** | +58% | 50 / 50 / **40**¹ / **40**¹ |
| OpenAI | 736 | 762 | 936 | **1369** | +86% | 50 / 50 / 50 / 50 |

Two same-day S1 runs exist (2026-08-09T21:41 and T22:23; both n=50)
committed in `analysis/latency-20260809T214106Z/latency.json` and
`analysis/latency-20260809T222356Z/latency.json`. Six vendor-session
cells across two vendors.

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

**What n=3 sessions can and cannot support**:

- **Can support**: rank stability (ElevenLabs faster than OpenAI in
  all 3 sessions). Rank tests are robust at low n.
- **Cannot support**: characterisation of the session-to-session
  variance distribution. n=3 cannot distinguish "wide-tail vendor"
  from "unlucky session" from "client-side contamination." Any
  distributional claim (e.g., "ElevenLabs is more stable than
  OpenAI") needs ≥5-10 sessions across ≥2 weeks with the layer
  controls above.

**Load-bearing claims**:

- ElevenLabs is **consistently faster than OpenAI** across all 3
  sessions (424/694 vs 736/1369 range on p50). Ranking is stable.
- OpenAI TTFA is high — always at least 736 ms p50 on our
  measurements — which is the load-bearing claim for the "provision
  capacity for OpenAI's worst percentile" advice.

**Claims the data does not support**:

- "ElevenLabs Flash reliably hits sub-500 ms p90" — held only in
  the first 2 sessions and moved to 816 ms in S3.
- "Stability is a distinct vendor axis" as a portfolio-worthy
  headline. On our data, both vendors' session-to-session variance
  is 50-90% of the p50; neither is "stable" in an operational sense.
- Any capacity-planning implication that reads ElevenLabs' 470 ms
  p90 as an upper bound in either direction (the S3 measurement
  exceeded it substantially).

**Impact on PM recommendations**: don't provision from one
measurement session. For a real deployment plan, budget the tail
observation across ≥5 sessions on the vendor's serving region from
your actual deployment environment, with client-side lag logged and
warm-up trials excluded — public-tier measurements at n=1-3 sessions
are not enough to characterise the tail. Rank claims survive at n=3;
variance claims do not.

**Evidence**:
- Session 3 run IDs: `latency-20260812T191143Z` (OpenAI, 50/50 trials)
  and `latency-20260812T191323Z` (ElevenLabs, 40/50). `runs/` is
  gitignored (regenerable + large — see
  [.gitignore](../.gitignore)); reproduce per
  [03_RUNBOOK § latency + ping](03_RUNBOOK.md)
- Ping baseline log: `ping-baseline-20260812T191138Z.jsonl` — 274
  probes to Cloudflare 1.1.1.1 during the S3 window. Committed as
  [`analysis/ping-baseline-20260812T191138Z.jsonl`](../analysis/ping-baseline-20260812T191138Z.jsonl)
  so the network-baseline receipt survives without the audio
- Analysis: [`scripts/latency_with_ping.py`](../scripts/latency_with_ping.py)

**Portfolio takeaway**: the T5/T7 pair demonstrates both the value
of a third replication session and the limits of a three-session
pass. Three-session data suffices to falsify a distributional claim
but not to make one.

---

## Friction points

*Portfolio-worthy narratives that emerged during the work. Every
one is backed by a specific artefact.*

### The killed weighted-composite score

The v1 plan had `quality_score = 0.4·PQ + 0.3·CE + 0.2·MOS + 0.1·noise`.
Cut it in Phase A. **Weights are always arguable; pre-registered
gates are falsifiable.** The v2 model has hard gates (pass/fail
against thresholds committed in `configs/gates.yaml`) + Pareto
frontiers on remaining axes. A reader who prefers their own
weighting can construct one from the raw data; nobody can undo a
pre-registered hard gate.

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

The pre-registered plan called for a 168-judgment human perceptual
BT panel. Executable at n=1 self-rater, but the bootstrap CIs
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

The original 168-judgment BT plan included an anchor recording (the
evaluator's own voice, unprocessed) as a reference point for
"human-like." Cut the anchor from the plan — the recording overhead
and consent complications aren't worth the additional axis for
portfolio scope. Retained the 168-judgment BT plan (before D-H
subsequently deferred it entirely).

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
region, across ≥3 sessions per venue) is a 1-3 day workstream not
justified at portfolio scope; deferred to v2.

<a name="d-h-bt-deferred-to-v2"></a>
### D-H · Phase 3 BT deferred to v2

The full 168-judgment Bradley-Terry rating campaign is **not
executed** in v1. Deferred to a proper v2 multi-rater pass.

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

**Reversibility**: Fully reversible. The BT machinery
(`veval rate build/score`, judgment ingest, bootstrap CIs) is
implemented and tested. A v2 pass at n≥15-30 raters can run against
the existing infrastructure without code changes.

See [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md) for
the full v2 roadmap.

---

## Threats to validity

*What could make the findings wrong. Each threat is either
mitigated (mitigation named) or documented as a v2 workstream.*

### Structural

- **n=1 rater for human perceptual dimension** (D-H) → deferred to v2
- **One voice per vendor** — voice choice can shift scores by up to
  ~35% of cross-vendor spread on Audiobox (measured for Speechify
  via T6); other vendors untested → deferred to v2 alt-voice sweep
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
- **Single-session latency** → the T5 + T7 second-session pass was
  the design intended to mitigate this; F-11 (300 lines above)
  documents that the two-session design was itself too weak — the
  third session with concurrent ping baseline refuted the "stability"
  reading the two-session pass had produced. Full mitigation would
  require ≥5 sessions across ≥2 weeks (v2 workstream)
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
