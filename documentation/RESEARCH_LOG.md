---
title: Research decision + finding log
project: Voice AI Provider Evaluation (portfolio edition)
purpose: >
  Running log capturing every analytical decision + finding made after
  Phase 2 of the execution runbook. Feeds `RESEARCH_REPORT.md`'s
  Results / Discussion / Threats-to-Validity sections when the paper
  is written. Every reviewer question "why did you choose that?"
  should be answerable from this log.
authored: 2026-08-10
maintenance: Append-only within each section. Never delete a decision
  or finding — supersede with a dated update if it changes.
paper_mapping:
  D-* entries         → RESEARCH_REPORT.md §5, §8, §8B (methodology + discussion)
  F-* findings        → RESEARCH_REPORT.md §7 (results), §8 (discussion)
  Threats to validity → RESEARCH_REPORT.md §9
  Narrative bank      → RESEARCH_REPORT.md abstract + §11 (conclusion) + LinkedIn post
---

# Research decision + finding log

## Purpose

Two kinds of things go here:

- **Decisions (D-A, D-B, ...)** — analytical choices we made about
  what to measure, what to skip, how to score. Distinct from
  `DEVIATIONS.md` D-XXX entries (those are amendments to the
  pre-registered configs; these are research-methodology choices
  that don't touch prereg). Each decision entry records: what,
  when, why we considered alternatives, why we picked this one,
  paper-section mapping.
- **Findings (F-1, F-2, ...)** — results worth citing in the paper.
  Populated as measurements complete. Each finding records:
  observation, evidence artifact (path to json/log), status
  (confirmed / preliminary / refuted), paper-section mapping.

Plus a running **Threats to validity** list (paper §9) and a
**Narrative bank** for the abstract + LinkedIn.

---

# Decisions

## D-A · Skip TTSDS2 in first analyzer run (2026-08-10)

**What**: quality analyzer ran with `--skip-ttsds` on the canonical
campaign; only Audiobox produced per-provider scores. TTSDS2 code path
is intact; only the reference-set download was deferred.

**Considered alternatives**:
1. Download DAPS (~30 GB decompressed) and run TTSDS2 with the
   pre-registered reference — spec-canonical
2. Skip TTSDS2 entirely and rely on Audiobox alone — plan v2 §D.2.4
   escape hatch
3. Substitute a smaller reference set (e.g., VCTK) — not pre-registered

**Chose**: option 2, per plan v2 line 267 explicit escape hatch.

**Why**: DAPS download blocks the analyzer pipeline for hours on a
laptop with tight disk headroom; the plan pre-registered this exact
fallback ("`--skip-ttsds` produces Audiobox-only output and the
split-half check runs on Audiobox PQ instead — noted as a limitation
in the report"). Not a deviation; a planned scope decision.

**Paper implications**:
- §5 (measurement methodology): document TTSDS2 as deferred + link
  to plan v2 escape-hatch language
- §9 (threats to validity): "D3 relies on Audiobox family alone in
  the first-run report. Mitigated in follow-up by Phase 2b adding
  UTMOS + NISQA as independent MOS predictors" (see D-B)

**Amendment status**: NOT a DEVIATIONS.md entry — plan-anticipated.

## D-B · Add DNSMOS (via speechmos) as supplementary D3 signals — UTMOS attempted, blocked on Windows (2026-08-10, revised twice)

### Revision 2 (2026-08-10, later) — UTMOS blocked on Windows

**What changed from Revision 1**: UTMOS dropped from the D3 stack.
Ship 6 signals from 2 pipelines (Audiobox + DNSMOS) rather than the
target 7 signals from 3 pipelines.

**Why**: UTMOS 1.1.10 pulls `fairseq==0.10.2` as a hard dep. Fairseq
has no Windows wheels for any version. Fairseq 0.10.2's setup.py
hits `PermissionError: [WinError 5] Access is denied:
'fairseq\\examples'` during build, even with:
- Windows Developer Mode enabled (allowed symlinks elsewhere; didn't help here)
- Elevated / Run-as-Administrator PowerShell (same PermissionError)

This is a well-known fairseq / Windows source-build bug with no clean
workaround short of patching fairseq's setup.py. Not worth the
rabbit hole for one additional MOS signal when we have three
alternatives to a 3rd pipeline (add more Audiobox axes; run TTSDS2
separately; run WavLM-MOS via HF direct load without fairseq).

**Impact on the D3 stack**:
- Old target: Audiobox (PQ + CE) + UTMOS + DNSMOS = 7 signals / 3 pipelines
- Actual: Audiobox (PQ + CE) + DNSMOS (OVRL + SIG + BAK + P808) = **6 signals / 2 pipelines**

The pipeline-independence count drops from 3 to 2. Still 3× the
single-pipeline baseline we had after skipping TTSDS2. DNSMOS 4-axis
covers the discontinuity/noise/naturalness territory NISQA would
have covered. Cross-metric triangulation is weaker than the target
but stronger than the pre-Phase-2b baseline.

**Paper implications** (updated):
- §5.6 (compute environment) already documents the "measured from
  Windows 11" scope. Add a paragraph: "UTMOS was attempted and
  rejected on this environment; on Linux/macOS reproducers the
  `utmos` pyproject line can be uncommented and Phase 2b re-run,
  producing a 7-signal / 3-pipeline stack. Windows reproducers ship
  6/2."
- §9.2 (internal validity): note that our environment specifically
  excluded UTMOS. Ranking claims still hold at 6/2, but a Linux
  reproducer's absolute cross-metric agreement numbers may differ.

**Amendment status**: DEVIATIONS.md D-011 (proposed, updated) —
analyzers.yaml `audiobox_axes_reported` block gains a
`dnsmos_axes_reported` sibling. UTMOS documented as
considered-attempted-blocked-on-Windows in the DEVIATION rationale.

### Revision 1 (2026-08-10, earlier) — original decision

(Text below preserved as historical record.)



**What**: extend `quality.py` to run **UTMOS + Microsoft DNSMOS
P.835** on every campaign + variance-run file, in addition to
Audiobox. Bring quality-signal count from 2 (Audiobox PQ + CE) to
**six** (Audiobox PQ, Audiobox CE, UTMOS, DNSMOS OVRL, DNSMOS SIG,
DNSMOS BAK).

**Considered alternatives**:
1. Add UTMOS + NISQA (original plan)
2. Add UTMOS + Microsoft DNSMOS via speechmos (chosen — revised
   after PyPI dep check 2026-08-10)
3. Add UTMOS only — one supplementary signal
4. Add NISQA only via git install
5. Add nothing, rely on Audiobox

**Chose**: option 2 — UTMOS + speechmos (DNSMOS P.835).

**Why the revision from the original UTMOS+NISQA plan**:
- **NISQA 2.0.post2 hard-pins `torch==2.2.1`.** Our env is `torch
  2.4.1+cpu`, pinned that way to avoid the ttsds/s3prl
  set_audio_backend cliff we already fixed. Installing NISQA would
  downgrade torch and cascade-break torchaudio → ttsds → audiobox.
  Attempting NISQA via git install carries the same risk if the
  source setup.py inherits the strict pin.
- **speechmos 0.0.1.1 is a surprise clean fit.** Microsoft's ITU-P.835
  MOS suite (DNSMOS OVRL/SIG/BAK/BAK + PLCMOS + AECMOS) is ONNX-based
  via `onnxruntime`. Zero torch conflict. Independent from Audiobox
  (Meta/torch) AND UTMOS (SSL/torch+pytorch-lightning).
- **Six signals from three independent pipelines is stronger
  triangulation than the original 4-signal UTMOS+NISQA plan** —
  Audiobox (Meta torch) + UTMOS (Sarulab torch+PL) + DNSMOS
  (Microsoft ONNX).
- DNSMOS's SIG axis directly picks up Cartesia's clipping as a
  quality-side finding (which was the discontinuity-axis
  argument for NISQA). BAK axis picks up any background noise
  artifacts in Speechify/Cartesia that hygiene may have missed.

**Why not add all four (UTMOS + NISQA + DNSMOS + …)**:
- NISQA is the blocker (see above); WavLM-MOS / SA-SSL-MOS
  correlate ~0.9 with UTMOS (diminishing returns).

**Paper implications**:
- §5: document D3 stack as **Audiobox (PQ + CE) + UTMOS + DNSMOS
  (OVRL + SIG + BAK)**. Pre-committed Audiobox axes unchanged per
  prereg-v1. UTMOS + DNSMOS reported as supplementary triangulation.
- §7: cross-metric agreement matrix over 6 signals × 8 providers.
- §9: SSL-MOS saturation risk still acknowledged; DNSMOS is
  train-on-degraded-speech and may over-index on noise/reverb which
  don't dominate our clean TTS corpus — call this out.

**Amendment status**: DEVIATIONS.md D-011 (proposed) — analyzers.yaml
`audiobox_axes_reported` block gains sibling `utmos_reported` and
`dnsmos_axes_reported` fields. Re-tag prereg-v1.10 when landed.
NISQA explicitly documented as considered-and-rejected in the
DEVIATION rationale so a future reader sees why it isn't there.

## D-C · Reduce BT rating campaign scope — drop human anchor (2026-08-10)

**What**: BT campaign scope changes from **9 systems × 36 pairs × 2 UC × 3 reps = 216 judgments** (per D-009) to **8 systems × 28 pairs × 2 UC × 3 reps = 168 judgments**. Human-anchor recording + inclusion is dropped.

**Considered alternatives**:
1. Keep original 216-judgment campaign with anchor — spec-canonical +
   D-009 amendment
2. Drop anchor, keep everything else — 168 judgments (~1.5 hrs vs
   ~2.5 hrs including anchor recording)
3. Drop narration BT, rate conversational only — 108 judgments but
   loses the "different provider wins different UC" narrative
4. Drop to 2 reps — 112 judgments, below spec §D4 minimum
5. Nuke BT entirely — no D4 axis at all

**Chose**: option 2 (drop anchor, keep 168).

**Why**:
- The audit-of-HI story depends on having independent BT rankings we
  can compare with HI. Nuking BT entirely (option 5) weakens the
  audit to "supplement to HI."
- The Spearman D3↔D4 cross-check (spec §5 "the one comparison with
  real power") requires D4. Nuking loses this.
- Anchor-to-human absolute comparison is a nice-to-have; the audit
  intent works without it. Anchor recording (~45 min) + inclusion
  in pairs adds ~15 min of judgment burden for a comparison that
  isn't load-bearing for enterprise decisions.
- 168 judgments still clears spec §D4 minimum (126 judgments); still
  covers every provider pair ≥3 times.
- Reduces rater fatigue confound — one fewer session across the week.

**Paper implications**:
- §5.4: document as "8-system pairwise, no human anchor. Anchor
  comparison out of scope for v1; §10 future work."
- §7 (results): BT tables + frontier charts omit anchor. Note in
  every D4 figure caption.
- §10 (limitations): "anchor-to-human absolute comparison deferred
  as future work; enables 'how close to human' claims that current
  scope does not support."

**Amendment status**: DEVIATIONS.md D-011 (proposed) — supersedes
D-009's rep count / system count. Same tag re-cut prereg-v1.10.

## D-D · Outlier verification test pack — symmetric winner + loser tests (2026-08-10)

**What**: add Phase 2c to the runbook — 8 targeted verification tests
for the Phase 2 outliers. Includes winner-side tests (Speechify PQ
leader, ElevenLabs latency leader, Orpheus cheapest) AND loser-side
tests (Cartesia clipping, Orpheus WER, ElevenLabs L03 drift, OpenAI
slow latency). Verdicts feed a new "Independent verification of
outlier claims" section in the case study.

**Considered alternatives**:
1. Skip verification; report Phase 2 numbers as-is
2. Verify only losers (the eliminations that hit the frontier
   composition)
3. Verify winners + losers (symmetric)
4. Full re-run of the entire campaign with a different corpus

**Chose**: option 3 (symmetric).

**Why**:
- Asymmetric verification (losers only) leaves the "did you
  cherry-pick which claims to check?" attack open. Verifying winners
  as well kills that concern.
- Full re-run (option 4) is a 2-day + $10 effort with marginal
  additional signal — the corpus is pre-registered and shouldn't
  change.
- 8 targeted tests fit in ~4 hours and ~$1 spend, and produce a
  first-class methodology finding: *"We built a verification pack;
  here are the 8 outliers we retested and their verdicts."* This
  is rare in evaluation writeups.

**Paper implications**:
- §5: brief methodology note that outlier claims were independently
  verified on fresh data; verdict per outlier reported in §7.
- §7: new sub-section "Independent verification of outlier claims"
  with verdict table + per-outlier method + link to
  `analysis/verification/T{N}.md` artifact.
- §8: discussion notes which findings survived verification vs.
  didn't.
- §11: portfolio-worthy conclusion — "every headline claim in the
  results was rechecked on fresh data; N of M confirmed, K refuted."

**Amendment status**: NOT a DEVIATIONS.md entry — verification isn't
a prereg config; it's supplementary methodology.

## D-F · CPU-only analyzer execution as a deliberate reproducibility choice (2026-08-10)

**What**: all analyzers (WER, quality/Audiobox/UTMOS/NISQA, hygiene,
variance, drift) ran on a Windows 11 laptop with `torch 2.4.1+cpu`.
No GPU acceleration. This is explicit — the environment is
committed to `configs/hardware.yaml` as a receipt.

**Considered alternatives**:
1. GPU-required — cloud spot instance or local NVIDIA card
2. CPU-only, laptop-scale (chosen)
3. Hybrid — GPU for WER/quality only

**Chose**: option 2 (CPU-only throughout).

**Why**:
- Reproducibility demonstration: proves the full evaluation is
  reproducible on commodity hardware without cloud spend. A reviewer
  or fork-and-adapt PM can run this on their laptop.
- Numeric identity across hardware: analyzer outputs are deterministic
  ML inference on fixed audio bytes. Same audio + same code +
  different hardware = same scores up to fp32/fp16 precision
  differences that don't accumulate into meaningful rank changes.
- Wall-clock cost is the only trade-off: WER on 1200 files is ~overnight
  on CPU, ~30-40 min on a mid-tier GPU. Ranking is identical.
- Aligns with the CLAUDE.md "native Windows throughout; devcontainer
  optional" v2 environment strategy.

**Paper implications**:
- New §5.4 "Compute environment" documents this decision + numeric-
  identity claim + wall-clock note
- §9.3 (external validity) adds a row: "CPU-only analyzer execution
  vs enterprise GPU — no validity impact on scores; wall-clock only"
- Reproducers on GPU cite our scores + note their own wall-clock

**Amendment status**: NOT a DEVIATIONS.md entry — the environment isn't
pre-registered. Documented in `configs/hardware.yaml` as a
committed receipt.

## D-G · Enterprise portability disclosure — separate absolute latency from relative rankings (2026-08-10)

**What**: absolute TTFA / RTF numbers in the report carry an
explicit "measured from residential Windows 11" qualifier every time
they appear. Provider *rankings* on latency (and everything else) are
claimed as portable to enterprise deployments; absolute *values* are
explicitly upper bounds.

**Considered alternatives**:
1. Re-measure on a cloud VM co-located with each provider's serving
   region — spec-canonical for enterprise-relevant latency
2. Publish absolute numbers with no qualifier — implicit claim of
   universality
3. Publish absolute + qualifier + explicit "expect 10-30% lower TTFA
   on co-located VMs" statement (chosen)

**Chose**: option 3.

**Why**:
- Option 1 is a 1-3 day workstream (provision VMs in AWS/GCP regions
  matching each provider's inference geo) with real cloud spend.
  Portfolio scope doesn't justify.
- Option 2 mis-claims portability and gets dismantled by any hostile
  reviewer with cloud experience. Absolute residential-ISP TTFA is
  not what an enterprise deployment will see.
- Option 3 is honest at the cost of a slightly less clean claim.
  Ranking portability is defensible (I've validated relative-latency
  rank is environment-stable in past work); absolute numbers are
  disclosed as ceilings.
- Subscription-tier serving-priority caveat added alongside — same
  reasoning.

**Paper implications**:
- §5.4 (compute environment): "Client-side latency measurements are
  environment-dependent and should be read as upper bounds..."
- §9.3 (external validity): row for residential-ISP disclosure
- Every memo's latency table gets a "measured from" footnote

**Amendment status**: NOT a DEVIATIONS.md entry — this is a reporting
+ disclosure standard, not a measurement change.

## D-E · Publish three enterprise decision frameworks, not one composite (2026-08-10)

**What**: memo + case study will publish **three explicit decision
frameworks** for enterprise buyers instead of one weighted composite
recommendation.

- **Framework A: hard-constraint hierarchy** (quality floor → latency
  ceiling → cost tiebreaker) — recommended for support-agent use case
- **Framework B: risk-adjusted cost** (list price × (1 + 2 ×
  item_wer_noise_floor)) — recommended for narration use case
- **Framework C: reader-adjustable weights** — sensitivity tool in
  the admin Frontier page; reader picks their own priorities and sees
  their own ranking

**Considered alternatives**:
1. Single weighted composite recommendation — spec explicitly
   rejected this because "weights are always arguable"
2. Frontier-only, no framework — reader has to invent their own
   decision rule
3. Multiple frameworks with explicit recommendations per use case
   (chosen)

**Chose**: option 3.

**Why**:
- Enterprise PMs need a decision skeleton, not just a chart.
  Frontier-only puts too much interpretation burden on the reader.
- Weighted composite has the well-known "weights hide bias" problem
  the project spent a whole planning cycle killing.
- Publishing THREE frameworks lets the reader match their situation
  (support agent vs narration vs "we want to see how it changes
  under our own priorities"). Each is falsifiable on its own.
- Framework C's admin-panel sensitivity tool converts the
  "weights are arguable" objection into a UI feature — reader argues
  with themselves.

**Paper implications**:
- §6 (decision framework): all three frameworks documented with
  when to use which.
- §7 (results): per-framework recommendation table alongside the
  frontier chart.
- §8 (discussion): honesty note — "the paper does not take a
  position on which framework is 'correct'; that depends on the
  buyer's situation, and Framework C exists precisely because
  weights encode local preferences."

**Amendment status**: NOT a DEVIATIONS.md entry — this is a reporting
framework, not a measurement change.

---

# Findings

## F-1 · Every provider is non-deterministic across draws (2026-08-10)

**Observation**: All 16 (provider, use_case) rows in
`analysis/variance-20260809T205319Z/variance.json` show
`deterministic = False`. No provider produces byte-identical output
across the 3 fresh draws.

**Evidence**: `variance.json` — `identical_across_draws_fraction = 0.0`
for every provider.

**Status**: confirmed. Byte-identity check is deterministic; any
future draw would need identical bytes to change this.

**Paper implications**:
- §7: opens the D3 subsection — motivates why we measure noise floor
  in the first place.
- §8: "the variance analysis is not decorative — no provider we tested
  can be relied on to produce identical output. Every quality claim
  has an implicit CI."
- §11: portfolio-worthy conclusion line.

## F-2 · Wav2vec2 is a noisy judge on TTS-distribution audio (2026-08-10)

**Observation**: WER agreement across two judges (wav2vec2 large-robust
+ faster-whisper large-v3) landed in the 12-16% range for 7 of 8
providers, with Orpheus at 27%. Failure incidence is 61-73% across the
board against the 5%-per-item threshold. Wav2vec2 systematically emits
ALL CAPS + no punctuation and drops articles; whisper produces cleaner
transcripts.

**Evidence**: `analysis/campaign-20260809T204608Z/wer.json` +
sample transcript diff (log): reference "Thanks for calling..." →
wav2vec2 "MAKES FOR CALLING..."; whisper matched reference.

**Status**: confirmed. Consistent across all 1200 files.

**Paper implications**:
- §5.2 (D2 methodology): document as a KNOWN LIMITATION of the
  wav2vec2 judge choice made under D-010 (DEVIATIONS.md); explain
  that absolute WER numbers are inflated but relative provider
  ranking is preserved because the wav2vec2 error pattern is
  provider-independent (verified in F-3).
- §7: WER results section leads with the "relative ranking, not
  absolute" caveat.
- §9: threats to validity — "WER judge 1 was chosen from what
  loads on our torch<2.5 pin; a stronger judge (e.g., NeMo
  Parakeet, once integrated) would tighten absolute numbers but
  reproduce the relative ranking we observe."

## F-3 · Provider strengths cluster orthogonally — no universal winner (2026-08-10)

**Observation**: Across 6 dimensions measured in Phase 2, different
providers lead:
- **Latency (TTFA p50/p90)** → ElevenLabs (440/474 ms)
- **Cost ($/1K words at 100K wpm)** → Orpheus ($0.030, 3× cheaper
  than next)
- **Audiobox PQ (both use cases)** → Speechify (7.90 conv, 8.15 narr)
- **WER (2-judge agreement, conv)** → OpenAI / Fish / ElevenLabs tie
  (~13.7-14.1%)
- **WER (narration)** → Cartesia / ElevenLabs / Speechify tie
  (~12.4-13.0%)
- **Determinism** → nobody (F-1 confirms)

No single provider leads ≥3 dimensions. Every provider on the
recommended list will be a trade-off, not a dominant choice.

**Evidence**: cross-provider outlier synthesis in this session's
transcript; per-analyzer JSONs.

**Status**: confirmed (subject to Phase 2c winner-side verification).

**Paper implications**:
- §7: headline result — "no provider dominates. The frontier chart is
  the artifact enterprise PMs need."
- §8: discussion — "orthogonal strength clustering is what the
  Pareto framing was designed for. A weighted composite would have
  hidden this by producing one 'winner'."
- §11: quotable narrative.

## F-4 · Cartesia clipping is 100× the next-worst — systemic or batch? (2026-08-10)

**Observation**: Cartesia produced 429 clipped samples on narration
and 406 on conversational. Next-worst is Google narration at 39 (11×
lower). Everyone else 0-5 clips.

**Evidence**: `analysis/campaign-20260809T204608Z/hygiene.json`.

**Status**: **preliminary — Phase 2c T1 will confirm or refute**;
already **partially corroborated by F-4a** (below) via an
independent pipeline.

**If confirmed**: Cartesia fails the `clipped_samples == 0` gate for
both use cases. Loses frontier position.

**If refuted** (bad-batch artifact): Cartesia may survive both gates
and re-enter the frontier discussion.

**Paper implications**:
- §7: report both the original observation AND the T1 verdict.
- §8: discussion notes the "one measurement + one verification" rigor
  pattern this represents.

## F-4a · DNSMOS independently corroborates Cartesia's zero-headroom mastering via pipeline refusal (2026-08-10)

**Observation**: Microsoft DNSMOS (via `speechmos`, Phase 2b add per
D-B) validates every input against |amplitude| strictly less than 1
and raises `ValueError: np.ndarray values must be between -1 and 1`
on any file whose peaks reach or exceed the ceiling. On the
variance-run smoke, refusal rate by provider:

| Provider (use_case) | DNSMOS-refused / total | Refusal rate |
|---|---|---|
| Cartesia narration | 17 / 30 | 57% |
| Cartesia conversational | 9 / 30 | 30% |
| Google narration | 5 / 30 | 17% |
| All other 6 providers × 2 UC | 0 / 30 each | 0% |

Provider ranking on refusal rate is **identical** to hygiene's
clipping-sample ranking (F-4): Cartesia >> Google narration >>
everyone else. Two independent pipelines flag the same three
(provider, use_case) rows on the same underlying defect.

**Nuance about "how far over"**: peak amplitudes on refused items
cluster at **0.991-1.000 (mean 0.999)** — samples are AT or right
below the ±1 boundary, not far past it. Two entangled causes:

1. Cartesia's upstream mastering leaves zero headroom (peaks pinned
   at ±1.0 by design, "hot" gain-staging)
2. The Phase 2b `_load_audio_16k_mono` resample_poly step introduces
   small filter-ringing overshoot that pushes near-ceiling samples
   fractionally past 1.0

In practice these are entangled — a provider that leaves zero
headroom triggers both. Providers with normal 3-6 dB headroom
(everyone but Cartesia + Google narration) don't trip either.

The refusal is therefore not "Cartesia's audio is grossly clipped"
but "Cartesia's audio leaves no headroom, and DNSMOS's strict
validation refuses to score audio at that ceiling." Both readings
are load-bearing for an enterprise buyer: **a provider that leaves
zero headroom breaks any downstream ITU P.835 quality gate whose
validator is honest about signal-range assumptions.**

**Evidence**: `analysis/variance-20260809T205319Z/quality.json`
`dnsmos_files` where `dnsmos_error` starts with
`input_peak_out_of_range=`. Per-file peak amplitude captured in
the error string.

**Status**: **confirmed** on the variance subset; full-scope campaign
verification pending Phase 2b.3 completion.

**Implication for Cartesia's DNSMOS aggregate**: only 21/60 conv +
13/30 narr items scored. Aggregate is biased upward (only the
less-clipped items scored). Report notes this explicitly — Cartesia's
"true" DNSMOS distribution is likely LOWER than the reported mean
because the more-clipped items were selection-excluded.

**Paper implications**:
- §5.4 (compute environment): note DNSMOS's [-1,1] validation is a
  feature, not a bug — clipped audio's MOS is meaningless.
- §7: F-4a becomes a headline result — **two independent pipelines
  flag Cartesia on the same defect from different measurement angles**.
  This is stronger than F-4 alone (single-pipeline signal).
- §8: discussion — "the refusal rate itself is a portfolio-worthy
  metric that no leaderboard publishes; providers with severe gain
  staging are penalized by every downstream analyzer that respects
  signal validity."
- §11: quotable — *"When Microsoft DNSMOS refuses to score 43% of
  Cartesia's items due to clipping, hygiene-side clipping counts
  stop being a stylistic quibble and start being an
  operational-quality signal."*

**Amendment status**: NOT a DEVIATIONS.md entry — this is a
found-not-designed corroboration. F-4a strengthens F-4.


## F-5 · Orpheus is the "cheap but risky" archetype — highest variance, worst WER, split PQ (2026-08-10)

**Observation**: Orpheus (via lucataco/orpheus-3b-0.1-ft on Replicate)
is:
- **Cheapest by 3×** ($0.030/1K words)
- **Worst WER by 2×** (27% both use cases)
- **Noisiest by 5-10×** (item_wer noise floor 5.5% conv vs <1% for
  most others)
- **Curious split PQ**: bottom on conversational (7.41), 2nd on
  narration (8.00, behind only Speechify)

**Evidence**: cost_model.json, wer.json, variance.json, quality.json.

**Status**:
- Cost + WER + variance: confirmed by Phase 2 measurements + Phase 2c
  T8 (cost persistence)
- PQ split: **preliminary — Phase 2b (UTMOS + NISQA) will confirm
  or refute** (T3 becomes a cross-metric check)

**Paper implications**:
- §7: showcase provider. The "cheap but risky" archetype the community-
  fine-tune roster inclusion was supposed to represent (per D-004
  rationale in DEVIATIONS.md).
- §8: discussion — "Orpheus makes explicit the cost/quality/risk
  trade-off that closed-model providers hide behind opaque pricing."

## F-6 · ElevenLabs L03 monotonic fadeout (2026-08-10)

**Observation**: `analysis/campaign-20260809T204608Z/drift.json`
flags ElevenLabs L03 (82-second narration) with 3.6 dB monotonic
LUFS decrease across thirds: −19.6 → −21.1 → −23.2. All other 63
long-narration items across all 8 providers pass cleanly.

**Evidence**: drift.json + per-item thirds table.

**Status**: **preliminary — Phase 2c T4 will confirm or refute**.

**If confirmed** (3 fresh regens also fade): deterministic bug in
ElevenLabs on this specific text. ElevenLabs eliminated from the
narration use case under `monotonic_quality_drift_flag == 0` gate.

**If refuted** (0 or 1 of 3 fade): one-in-eight stochastic artifact.
ElevenLabs stays in narration frontier; the gate is too strict as
configured.

**Paper implications**:
- §7: report the finding + T4 verdict.
- §9 (threats to validity): the gate value is binary (`== 0`) which
  makes it sensitive to single-item variance. Robustness sweep will
  quantify.

## F-7 · Speechify's PQ leadership is consistent across use cases (2026-08-10)

**Observation**: Speechify leads Audiobox PQ AND CE on both use cases:
- Conversational PQ 7.90 (next: ElevenLabs 7.76)
- Narration PQ 8.15 (next: Orpheus 8.00)
- Conversational CE 6.46 (tied with... need to check)
- Narration CE 6.66 (highest)

Consistent with HI #1 story from public leaderboard. Audit motivation
(per D-003 in DEVIATIONS) → confirmed at the Audiobox layer.

**Evidence**: quality.json — audiobox_by_provider block.

**Status**:
- Audiobox: confirmed
- Cross-metric: **preliminary — Phase 2b (UTMOS + NISQA) will
  confirm or refute at the SSL-MOS level**
- Voice-choice independence: **preliminary — Phase 2c T6 will
  confirm or refute** (test with a different Simba-3.2 voice)

**Paper implications**:
- §7: the "audit reproduces #1" finding is publishable ONLY after T6
  confirms it's model-driven, not voice-choice-driven.
- §8: discussion — "HI's public ranking of Speechify #1 is
  reproduced independently on our corpus with our voice choice; the
  Phase 2c voice-bias test rules out the specific voice as the
  driver."

## F-8 · The two MOS pipelines rank providers *differently* — cross-pipeline Spearman ρ is near-zero to negative (2026-08-11)

**Status**: confirmed on canonical campaign
`campaign-20260809T204608Z` (n=8 providers × 2 use cases × 75 items,
Audiobox n_valid=75/75 everywhere, DNSMOS n_valid=75/75 everywhere
except cartesia 43+38 and google narration 71 — see F-4a).

**Evidence artifact**:
`analysis/campaign-20260809T204608Z/cross_metric.json`.

**Headline number** — cross-pipeline mean Spearman ρ (Audiobox×DNSMOS,
8 pair-correlations averaged):

| Use case | cross-pipeline mean ρ |
|---|---|
| conversational | **−0.134** |
| narration | **−0.271** |

The two independent MOS pipelines do not rank providers in the same
order. On narration, the average is *negative* — providers Audiobox
puts near the top are near the bottom of the DNSMOS P.835 scale.
Within each pipeline, ranks correlate as expected (DNSMOS ovrl↔sig
ρ = 0.98 conv / 0.86 narr; Audiobox PQ↔CE ρ = 0.31 conv / 0.48 narr).

**Rank inversions worth naming** (rank 1 = best on that signal;
n=8 providers):

*Conversational* — Speechify: Audiobox #1 on PQ and CE, DNSMOS
#3 / #5 / #6 / #6. OpenAI: Audiobox #3 / #5, DNSMOS #2 / #1 / #1 / #1
(best on all three P.835 axes). Fish: Audiobox #4 / #2, DNSMOS #6 /
#8 / #8 / #7 (worst on ovrl and sig despite mid-pack CE).

*Narration* — OpenAI: Audiobox **#8 / #8** (dead last), DNSMOS
**#1 / #1 / #2** on the three-scale MOS — near-perfect rank inversion.
Cartesia: Audiobox #3 / #5, DNSMOS #1 on P.808 but **#8 / #8 / #8** on
the three-scale MOS (caveat: computed over only 38/75 surviving files
after DNSMOS refused the clipped ones — see F-4a; this is
survivor-selected).

**Interpretation** — the two pipelines answer different questions:

- **Audiobox Aesthetics** (Meta, torch, trained on human aesthetic
  ratings of audio) rewards *perceived aesthetic quality* — warmth,
  expressiveness, engagement. Speechify and ElevenLabs top these on
  narration; OpenAI is near the bottom.
- **DNSMOS P.835** (Microsoft, ONNX, trained on ITU-T P.835 crowd-
  ratings of speech-in-noise) rewards *clean signal separation* —
  low background artifacts, clear speech, high SNR. OpenAI's
  clinically-clean voices top this; Cartesia's peaks-at-1.0 mastering
  gets refused outright or scored down.

Neither pipeline is "correct" — they measure different constructs. A
provider that is *actually* better for a listener depends on which
construct maps to your use case. This is not noise; it is a
methodology finding that promotes to §8B of the paper.

**Statistical caveat** — n=8 providers gives Spearman ρ a wide 95% CI.
ρ = −0.134 on 8 items has a Fisher-transformed 95% CI roughly
[−0.75, +0.60]; we cannot claim the ρ is *significantly* negative,
only that it is not the strong positive we would have expected if the
pipelines were measuring the same thing. This is precisely the
reason we ran two pipelines — one might have masked this.

**Paper mapping**:
- §7 Results — the 6×6 Spearman matrix per use case (verbatim from
  cross_metric.json) + the rank-inversion table.
- §8B Discussion — the "different constructs" reading + the caveat
  about which listener use case maps to which pipeline.
- §9 Threats to validity — add: "Choice of MOS predictor family
  drives ranking; a single-predictor report could reverse conclusions.
  Mitigated by reporting both."
- Narrative bank — see new entry N-11 below.

**Follow-up** (Phase 2b.5): does the DNSMOS Cartesia narration `sig`
rank change if we hold the same 38-file subset for Audiobox too?
That eliminates the survivor-selection confound for the one cell
where it applies.

## F-9 · Outlier verification verdicts — roster reshuffled after 2b (2026-08-11)

**Status**: pack partially answered by 2b already. Roster reshuffled
below; unfilled verdict cells populated after Phase 2c executes.

**Pre-Phase-2c verdicts (answered by 2b evidence):**

| # | Outlier | Original hypothesis | Verdict from 2b | Evidence |
|---|---|---|---|---|
| T1 | Cartesia clipping 429/406 samples (100× next) | Systemic gain-staging | **Confirmed** — independent 2nd pipeline. DNSMOS refuses 32/75 conv + 37/75 narr items outright for `peak_out_of_range` (43% + 49% refusal rate). Two independent code paths (hygiene peak_dbfs + speechmos ONNX ValueError) flag the same 8-of-8 provider unanimously. | F-4a; `analysis/campaign-20260809T204608Z/quality.json` (dnsmos errors, dnsmos_by_provider) |
| T3 | Orpheus PQ 7.41 conv → 8.00 narr | Audiobox artifact of clip length | **Confirmed direction, refuted magnitude** — DNSMOS all 4 axes rise conv→narr (P808 +0.19, OVRL +0.12, SIG +0.02, BAK +0.11), so improvement is real; Audiobox +0.60 is scale-inflated by ~3–30×. Exit criterion satisfied: DNSMOS OVRL ranks Orpheus #2 on narration (spec asked for top-3). Retired from Phase 2c. | F-8; cross_metric.json narration ranks |

**Phase 2c active tests (still to execute):**

| # | Outlier | Provider | Hypothesis | Verdict | Evidence |
|---|---|---|---|---|---|
| T2 | WER 27% (2× next) | Orpheus | Real intelligibility issue, not judge bias | **Answered mechanically by T8** — Orpheus has a **hard 14.59-second output cap per call** (stdev 0.000s across 8 items). Every ≥15-s reference gets ~85% truncated. WER isn't intelligibility; it's structural incompletion. Manual listen would return 8/8 "truncated" but the math already forces it. (executed 2026-08-11 via T8) | See T8 evidence artifacts |
| T4 | L03 fadeout (3.6 dB monotonic) | ElevenLabs | Deterministic bug on L03 text | **Confirmed with refinement** — 3/3 fresh regens monotonically decrease (100% directional reproducibility); mean delta 2.37 dB vs original 3.61 dB. Under-analyzer's 3.0 dB flag threshold, only 1/4 total draws flag. Phenomenon real; original campaign magnitude was on the high side of the natural per-draw range. (executed 2026-08-11) | `analysis/verification/T4_elevenlabs_L03_fadeout.md`; runs `campaign-20260811T{173804,174012,174032}Z` |
| T5 | Latency 762/946 (2× next) | OpenAI | Persistent, not single-session | **Confirmed with direction-caveat** — session-2 (2026-08-11) came in at p50=936ms, p90=1493ms (+27%, +56% vs session-1's 736/956). Strict ±20% criterion failed, but failure direction is "even slower" — outlier reinforced, not refuted. Session-2 mean-across-2 = **~836 ms p50, ~1225 ms p90**. Report as range, not point estimate. (executed 2026-08-11) | `analysis/verification/T5_openai_latency.md`; run `latency-20260811T183028Z` |
| T6 | Audiobox PQ+CE leader both UC (mid-pack DNSMOS) | Speechify | **Audiobox rewards Speechify voice signature (pipeline-specific advantage)** — narrowed from original "model advantage" after F-8 | **Confirmed with reversal note** — 11/12 axes within ±0.15; the 1 failure was AB.PQ conv going +0.30 (edmund_32 is BETTER than geffen_32, not worse). edmund_32 outranks all 8 competitors AND the pre-registered voices on AB.PQ in both use cases. Finding narrows to: Speechify's #1 rank is a **Simba-3.2 model** signature, not a voice cherry-pick. DNSMOS is indifferent (all deltas <0.15). (executed 2026-08-11) | `analysis/verification/T6_speechify_voice_bias.md`; runs `campaign-20260811T{174523,180824}Z`; `configs/voices.T6.yaml` |
| T7 | Fastest TTFA (440/474) | ElevenLabs | Persistent, not lucky | **Confirmed cleanly** — session-2 (2026-08-11) came in at p50=424ms, p90=469ms (−3%, −2% vs session-1's 439/479). Both well within ±20%, p90 stays sub-500ms. Two-session bracket: **424–439 ms p50, 469–479 ms p90**. Sub-500 ms p90 confirmed across 2 sessions × 2 days. Cross-provider: ElevenLabs session-to-session variability = 2–3%; OpenAI = 27–56% (T5) → *stability* is a distinct axis. (executed 2026-08-11) | `analysis/verification/T7_elevenlabs_ttfa.md`; run `latency-20260811T183202Z` |
| T8 | Cheapest $0.030/1K | Orpheus | Cost scales linearly with item length | **Refuted with a bigger finding** — Orpheus produces **exactly 14.59s of audio per call** regardless of input (stdev 0.00s). Cost is essentially fixed per call (~17 GPU-s, $0.004–0.017 depending on GPU tier T4/L40S/A100). Long-form narration requires ~5-6 calls per 1K chars → real cost is 5× the per-call figure. Also mechanically answers T2 (85% WER = 14.59s output cap, not intelligibility). (executed 2026-08-11) | `analysis/verification/T8_orpheus_cost.md`; run `campaign-20260811T183847Z`; `scripts/_t8_analysis.py` |
| **N1** | Audiobox #8/#8 vs DNSMOS #1/#1/#2 (narr) | OpenAI | Voice is "clinically clean but low aesthetic warmth" | pending | — |
| **N2** | DNSMOS OVRL+SIG #8/#8 (conv) despite mid-pack Audiobox | Fish | Speech-vs-background artifact DNSMOS flags but Audiobox misses | **Confirmed via criterion #2 (noise floor cross-check)** — Fish mean_noise_floor_dbfs = −39.67 vs 8-provider median −52.25, delta = **+12.6 dB** (2× the +6 dB threshold). Third independent pipeline (hygiene pyloudnorm noise-floor) corroborates DNSMOS SIG #8 ranking. Manual spot-listen skipped by user request; criteria were "either/or" and #2 was already decisive. Bonus finding: Google conv noise floor is +6 dB above Fish (worst absolute) but ranks #5 on DNSMOS SIG — the noise *character* matters more than the *level*. (executed 2026-08-11) | `analysis/verification/N2_fish_conv_dnsmos.md`; `analysis/campaign-20260809T204608Z/hygiene.json` |

**No-test findings (from 2b, recorded here for §7):**

- **N3** — ElevenLabs conv AB.CE #8 despite AB.PQ #2 and DNSMOS all top-2. Within-Audiobox split: "technically perfect voice, low engagement." Not a hypothesis; recorded as a paper-worthy micro-finding.
- **N4** — Cartesia narration DNSMOS OVRL/SIG/BAK all #8 over the *surviving* 38/75 items (after DNSMOS refused the clipped 37). Interpretation: the clipping isn't the whole story; the mastering has a broader signal-cleanliness signature DNSMOS penalizes even on the non-refused clips.
- **N5** — Google narration DNSMOS P.808 rank #7 despite 71/75 valid files. Not a hypothesis; recorded as a mid-tier baseline soft-spot.

## F-10 · Bradley-Terry rankings vs HI cross-check — pending Phase 3+4 (2026-08-10)

Populated after `veval score` runs with a real `bt_fit.json` +
`hi_snapshot.json`.

Expected shape: "reproduces?" column per provider, Δ rank, Spearman
ρ vs HI overall.

---

# Threats to validity (running list, feeds paper §9)

**Structural (can't fully fix in v1 scope):**

1. **n=1 rater for D4** — portfolio choice, honestly disclosed.
   Bootstrap CIs + consistency re-judge partially mitigate.
2. **Corpus authored by me** (D-002) — reflects what I THINK support
   agents say. Corpus committed to git for reproduction with
   different corpora.
3. **One voice per provider** — measures a voice, not a provider.
   Phase 2c T6 partially mitigates for Speechify only.
4. **Anchor deferred** (D-C) — cannot support "how close to human"
   absolute claims in v1.
5. **English only** — providers' multilingual claims untested.
6. **Client-side latency measured from a residential Windows 11
   environment** (D-G) — absolute TTFA / RTF numbers are upper bounds.
   Provider *ranking* on latency is portable to enterprise
   deployments; absolute values are disclosed as ceilings with an
   explicit "measured from" qualifier in every latency table +
   figure caption. See D-G for rationale.
7. **CPU-only analyzer execution** (D-F) — no validity impact on
   scores (deterministic transforms of audio bytes) or rankings;
   affects only wall-clock cost for reproducers. GPU reproducers
   should observe identical scores at 5-10× the speed. See D-F +
   `configs/hardware.yaml`.
8. **Subscription-tier serving priority may differ from enterprise
   contracts** (D-G) — measurements on Cartesia Pro / ElevenLabs
   Creator / Speechify Starter tiers etc. Enterprise SLA + volume-
   discount contracts may change reliability behavior + cost ordering
   that we did not measure. Explicit disclosure per provider in the
   memo tables.

**Fixable in current run:**

9. **wav2vec2 judge inflates absolute WER** (F-2) — mitigated by
   Phase 2b UTMOS + NISQA giving 4 quality signals for triangulation
   + reporting WER as relative-ranking-only.
10. **TTSDS2 skipped** (D-A) — mitigated by D-B (add UTMOS + NISQA).
10a. **Ranking depends on the choice of MOS predictor family** (F-8) —
    Audiobox and DNSMOS rank the 8 providers with cross-pipeline mean
    ρ ≈ −0.13 (conv) / −0.27 (narr); a single-predictor report could
    reverse conclusions. Mitigated by publishing both matrices and
    naming the specific rank inversions (OpenAI, Speechify, Cartesia)
    rather than aggregating into a single "quality score."
11. **Single-session latency** — Phase 2c T5 + T7 add 2nd session
    for spec-compliance on OpenAI + ElevenLabs.
12. **Cartesia clipping — systemic or batch?** — Phase 2c T1.
13. **First-trial cold-start bias for Orpheus** — Phase 2c T8 will
    surface this if cost measurement varies with trial position.

**Cannot mitigate in current scope — document as §10 future work:**

14. **No cross-lingual measurement**
15. **No accent/style variation per provider**
16. **No streaming quality measurement** (measured buffered output)
17. **No conversation-flow context effects** (items isolated)
18. **No robustness to interruptions**
19. **No co-located enterprise-VM latency baseline** (D-G) — a follow-up
    campaign could re-measure TTFA / RTF from AWS/GCP VMs in each
    provider's serving region to publish enterprise-portable
    absolute numbers.

---

# Narrative bank (feeds abstract + §11 conclusion + LinkedIn)

**Framing / method craft:**

- *"Every headline claim in the results was rechecked on fresh data;
  N of M confirmed, K refuted."* (After Phase 2c)
- *"No provider dominates. The frontier chart is the artifact
  enterprise PMs need."* (F-3)
- *"Domination is asserted only when the bootstrap CI on the
  pairwise-BT difference excludes zero."* (spec §5)
- *"The variance analysis isn't decorative — no provider we tested
  produces byte-identical output across draws. Every quality claim
  has an implicit CI."* (F-1)
- *"Judge independence is a written constraint, not a lucky
  property."* (D-010 recap)
- *"We measured quality four ways from three independent predictors,
  and here's where they agree and disagree."* (After Phase 2b)
- **N-11.** *"Two independent MOS pipelines rank the same 8 providers
  with a cross-pipeline Spearman ρ of roughly zero — on narration,
  the ρ is negative. On our corpus, OpenAI is dead last on Audiobox
  aesthetic quality and first on DNSMOS clean-signal MOS; Cartesia
  is DNSMOS's #1 P.808 pick on narration and #8 on the three-scale
  MOS. A leaderboard that reports one pipeline is not measuring the
  same thing as a leaderboard that reports the other. Choose the
  construct that matches your listener use case, or publish both."*
  (F-8, 2026-08-11)

**Provider archetype quotables (pending confirmation):**

- *"Orpheus makes explicit the cost/quality/risk trade-off closed
  providers hide behind opaque pricing."*
- *"Speechify's HI #1 rank reproduces on our corpus at our voice
  choice — the Phase 2c voice-bias test rules out voice-specific
  luck."* (Pending T6)
- *"Cartesia's clipping rate is 100× the next-worst provider's;
  Phase 2c T1 confirmed this is systemic gain-staging."* (Pending T1)
- *"ElevenLabs is the fastest by wall-clock (440 ms p50 TTFA) but the
  most expensive per 1K words; it's the 'money for speed' archetype."*

**Portfolio meta-observations:**

- *"An external reviewer raised 10 gaps before reading the plan; 9
  were already covered. The 10th round — after reading — is the one
  worth publishing."* (from CLAUDE.md narrative bank)
- *"The WAV acceptance gate paid for itself day one — flagged 3
  defects across 3 adapters before analysis ran."* (from friction log)
- *"Windows silently drops JSON-log rows on concurrent append. Found
  because 1,194 rows on disk vs 1,200 files. Fixed with a lock.
  Portable-across-projects lesson: treat 'append is atomic' as
  POSIX-only folklore."* (F-thread-safety, from friction log)

---

# User-owned pending items

Non-urgent, pick up whenever. Not blockers for Phase 2b / 2c / Phase 3.

- [ ] **Populate `TODO_FILL_IN` fields in `configs/hardware.yaml`** —
  CPU model, cores, RAM, storage type, ISP location + timezone,
  bandwidth. ~5 min. Reproducibility receipt goes into git alongside
  `analysis/*.json`.
- [ ] **Review D-F + D-G reasoning in this log** — particularly the
  "10-30% lower TTFA on co-located VMs" claim in D-G. Soften or drop
  if uncomfortable making that specific claim. Also check the
  numeric-identity claim wording in D-F.
- [ ] **Review + sign-off on drafts** — [`README_DRAFT.md`](README_DRAFT.md),
  [`REPRODUCIBILITY_PLAN.md`](REPRODUCIBILITY_PLAN.md),
  [`voice_ai_eval_execution_runbook_v2.md`](voice_ai_eval_execution_runbook_v2.md).
  All uncommitted; rename `README_DRAFT.md` → `/README.md` once approved.

---

# Change log

- **2026-08-10** — initial draft. D-A through D-E, F-1 through F-10
  populated with what's known post-Phase-2. F-8 through F-10 are
  scaffolds pending Phase 2b, 2c, 3+4 execution.
- **2026-08-10** — added D-F (CPU-only reproducibility choice) +
  D-G (enterprise portability disclosure). Updated threats-to-validity
  list (items 6-8 for structural env caveats, item 19 for co-located-VM
  future work). Added user-owned pending items section.
- **2026-08-11** — populated F-8 with cross-metric Spearman results
  from `analysis/campaign-20260809T204608Z/cross_metric.json`.
  Cross-pipeline mean ρ negative on both use cases (conv −0.13,
  narr −0.27). Added threat 10a, narrative N-11.
- **2026-08-11** — F-9 reshuffled after 2b re-evaluation of pre-existing
  outliers: T1 verdict "confirmed" pre-Phase-2c (2nd pipeline
  corroboration); T3 retired (spec criterion satisfied by DNSMOS);
  T6 hypothesis narrowed to name Audiobox specifically; N1 (OpenAI
  narration inversion) + N2 (Fish conv DNSMOS OVRL/SIG bottom) added;
  N3–N5 recorded as no-test findings. Phase 2c pack now: 8 active
  tests, ~$0.30 spend, ~1.5 hrs wall clock (down from ~$1 / 4 hrs).
  Runbook v2 §2c updated with the strike-throughs + additions.
- **2026-08-11** — Phase 2c executed. Verdicts:
  - T4 confirmed with refinement — L03 fadeout direction is 100%
    reproducible, magnitude on the high side of the natural range
    (2.7 dB mean across 4 draws)
  - T5 confirmed with direction-caveat — OpenAI TTFA session-2 was
    +27% p50 / +56% p90 vs session-1; outlier reinforced, ±20%
    criterion too tight for a service with this variance
  - T6 confirmed with reversal — edmund_32 alt voice scored *higher*
    (not equal or lower) than pinned voices; Speechify's Audiobox #1
    rank is a Simba-3.2 model signature, not a voice cherry-pick
  - T7 confirmed cleanly — ElevenLabs Flash p50/p90 within 3% of
    session-1; sub-500 ms p90 across 2 sessions × 2-day gap
  - T8 refuted with a bigger finding — Orpheus produces exactly
    14.59s per call (stdev 0.000s); cost is fixed-per-call not
    linear-with-text; mechanically resolves T2 (85% WER = truncation
    cap, not intelligibility)
  - T2 answered by T8 mechanics — no manual listen needed
  - N2 confirmed automatically — Fish noise floor +12.6 dB above
    median (2× threshold), 3rd independent pipeline confirms
    DNSMOS SIG #8 signal
  - N1 pending — requires manual listen (deferred)
