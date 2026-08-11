---
title: External review — third-party red-team pass
date: 2026-08-06
reviewer: External (Claude), reading portfolio-edition + descoped-plan + implementation-plan + architecture diagram
status: Findings for triage — none applied
scope: Methodology and decision-layer validity. Not a code review.
---

# External review — third-party red-team pass

Read in full: `voice_ai_eval_portfolio_edition.md`, `voice_ai_eval_plan_v1_descoped.md`
(incl. Appendices A–G), `IMPLEMENTATION_PLAN.md`, `eval_harness_architecture.mermaid`,
`CLAUDE.md`.

**Verdict.** The measurement design is stronger than most published TTS comparisons
and materially stronger than the enterprise-selection template I would normally
recommend. Nine of the ten "gaps" I raised before reading the source docs turned out
to be covered — several with reasoning better than mine. What follows is what survived
a full read.

The findings below are all in the same class: the *measurements* are sound, but three
of them feed the frontier charts as point estimates whose uncertainty is never
propagated, and one architectural decision currently under review would quietly break
the design's cleverest idea.

---

## Part 1 — Corrections to my pre-read gap list

Recorded because the corrections are themselves evidence about the plan.

| I claimed missing | Reality | Where |
|---|---|---|
| Latency / TTFA / RTF | **Covered, and more rigorous than my recommendation.** 50 serial trials, ≥2 days × ≥2 times of day, pinned region, p50/p90 only (explicitly refusing p99 at n=50), RTF for narration, serving region published per provider, Orpheus scored N/A-hosted because host cold-start would contaminate it | D1 · A.1 · E5 · E6 · B.11 |
| Hard-input robustness | Covered — jargon + edge batteries (numbers, dates, acronyms, currency), plus the famous-sentence contamination probe with an honest E7 caveat about what n=15 can support | §3.3 · A.2 · E7 |
| Metric-vs-human correlation | Covered as a three-way cross-check (D3 predicted ↔ D4 pairwise ↔ HI crowd), with "agreement is evidence, disagreement is a finding" | §4.1 · A.3 |
| Licensing / data residency / commercial terms | Covered — D8 capability audit carries SLA and compliance terms; F.3 adds ToS benchmark clauses, per-tier output licensing, and NC model-license audit | D8 · A.9 · F.3 |
| Speaker similarity | Correctly **absent by design** — locked provider-recommended voices, no cloning, with the HI's clone-one-voice alternative documented as a conscious trade-off | §3.2 · §4.1 |
| Weight sensitivity analysis | Covered, re-expressed as gate-robustness ±20% — the same function, better suited to a gates design | §5.4 · A.8 |

My "add a weighted layer on top of Pareto" suggestion is withdrawn. §5.5's decision
memo already carries the recommendation explicitly, made by a human and defended in
prose. That is more honest than a composite and does the same job. The residual
observation is narrower and appears as R2 below: with 6 providers the frontier may
retain 3–4 of them, so the memo carries nearly the whole decision load — which makes
the memo's quality, and the uncertainty on the axes it reads from, load-bearing.

---

## Part 2 — Findings

Severity is about **validity of the published conclusion**, not effort.

| # | Finding | Severity | Fix |
|---|---|---|---|
| **R1** | **The Canary swap would break the two-judge design.** The open analyzer-stack item proposes replacing faster-whisper with NVIDIA Canary-1B to escape the NeMo/Windows problem. But A.2 and C.3 justify the agreement rule on judges having *unrelated architectures and training pipelines* — "two unrelated ASR architectures rarely make the same mistake." Parakeet and Canary share the FastConformer encoder family, NVIDIA's training data pipeline, and normalization conventions. Correlated judges make the agreement rule filter far less ASR noise than claimed while still *looking* like a two-judge protocol. This would compromise the single idea the write-up leans on hardest. | **High** (validity) | Keep faster-whisper as judge 2. The Windows blocker is NeMo, not faster-whisper — CTranslate2 ships Windows wheels. The correct swap is Parakeet-via-NeMo → Parakeet-via-HuggingFace, leaving judge 2 untouched. If Canary is wanted, add it as a *third* judge, never as judge 2's replacement. |
| **R2** | **D4 uncertainty is never propagated to the frontier charts.** D4 is the y-axis of both money charts. At 6 providers that is 15 pairs × 2 use cases × ~3 reps ≈ 90 judgments from one rater. Table A displays Bradley–Terry scores as two-significant-figure point estimates (88, 82, 85). At that judgment count the BT confidence intervals are wide enough that adjacent providers are likely statistically indistinguishable — yet "dominated by Fish" is asserted as a categorical outcome. The plan owns n=1 honestly in prose (§9), but honesty about n is not the same as propagating n into the conclusion. | **High** (validity) | Bootstrap CIs over the judgment set; plot frontier points with error bars; require non-overlapping intervals before declaring domination, and label the rest "indistinguishable at this n." Add to Definition of Done alongside the consistency-re-judge line. Bonus: this converts a weakness into the most statistically literate moment in the write-up. |
| **R3** | **TTSDS2's reference set is never specified.** TTSDS2 scores a *distribution* against real speech — so the reference corpus is a parameter of the measurement, not a detail. Two risks: (a) if the reference is out-of-domain relative to a corpus derived from enterprise `.docx` content in support/narration registers, distributional distance may be dominated by domain mismatch rather than synthesis quality, compressing the differences the chart needs to show; (b) at ~75 items per provider per use case, per-system distributional stability is unverified. | **Med-High** (validity) | Name the reference dataset in `versa.yaml`/`prereg-v1` with a one-line rationale, per the project's own convention. Check the benchmark's guidance on minimum sample size *before* tagging prereg. Cheap validation: split each provider's items in half and score both halves — if the two scores diverge materially, the sample is too small to carry a headline. |
| **R4** | **No within-provider generation variance.** Every corpus item is synthesized once. Modern TTS is stochastic; two generations of the same text from the same provider differ. So every quality delta between providers is currently confounded with a single-draw variance term of unknown size, and the project cannot state its own noise floor. | **Medium** (validity) | Re-synthesize a 10-item subset 3× per provider and report within-provider spread on D3 and hygiene. Costs a rounding error of budget. Gives the write-up a line no competing eval has: "our noise floor is X; differences below it are not reported as differences." Also answers determinism, which matters for regression testing and is a real enterprise question. |
| **R5** | **Failure incidence is not reported as its own number.** D2 reports comparative WER bands and routes flagged files to a manual listen. But mean-ish WER hides the tail, and the tail is what kills deployments — one mangled currency amount in 200 utterances is a different procurement fact from "band A vs band B," and it is the fact a buyer acts on. | **Medium** (completeness) | Report `% of items with WER above a pre-committed threshold` and a raw count of catastrophic events (word drops, repetition loops, truncation) per provider. The flagged-file queue already generates this data; it just needs to become a published column rather than a QA step. |
| **R6** | **"Listener fatigue" has no defined measurement.** §8.1 Table B lists a listener-fatigue note as a narration column, and A.5 argues artifacts are "corrosive over a 10-minute narration," but no method produces either. It is currently a placeholder in the deliverable that is supposed to differentiate the narration use case. | **Medium** (method undefined) | Cheapest defensible version: chunk long-passage items into thirds and compare per-third D3/hygiene values — within-item quality drift, measured. Anything that degrades monotonically across thirds is the fatigue story, with a chart. If that is out of scope, cut the column rather than shipping a subjective note in a table of measurements. |
| **R7** | D3↔D4 agreement is specified qualitatively ("sanity-checked," "agreement is signal"). | **Low-Med** | Compute and publish Spearman rank correlation between D3 and D4, and between each and the HI ranking. Three numbers instead of three assertions — and it directly earns the right to trust D3 on the items D4 never covered. |
| **R8** | D4 runs as 6–8 sessions by one rater over days. Self-consistency is measured (10% re-judge) but preference drift across sessions is neither randomized against nor reported. | **Low** | Randomize pair order across sessions rather than blocking by provider; report the re-judge sample's *session gap* alongside the consistency number. |
| **R9** | Fish quality/WER runs on `s2.1-pro-free` while latency runs on the paid model string (B.2). The write-up will report one provider's quality from a tier the buyer would not deploy. | **Low** | Either verify the free and paid strings share weights and state it, or footnote the assumption in the results table where the Fish row appears. |
| **R10** | Corpus size is stated as ~75 items/use case (§3.3, IMPLEMENTATION_PLAN) but 84 in `eval_harness_architecture.mermaid`. The same diagram also still lists `xai.py`/`minimax.py` adapters, dropped from the locked 6-provider roster — a second staleness issue beyond the `weights.yaml` one already flagged. | **Doc** | Reconcile before `prereg-v1`. The corpus number is not cosmetic: it is the input to R3's sample-size question. |

Ten findings, which is a coincidence worth enjoying given Appendix E.

---

## Part 3 — Recommendation on the open analyzer-backbone decision

**Drop VERSA. Call jiwer / TTSDS2 / Audiobox / silero-VAD / pyloudnorm directly.**

C.1 justified VERSA on three grounds. Re-tested against where the project now stands:

- *Credibility* — "scored with VERSA's standard implementations." This survives without
  VERSA, because credibility attaches to the underlying metric implementations, which
  are the same libraries either way and are named individually in the write-up. VERSA
  is a wrapper; it does not make a number more true.
- *Reproducibility* — the stated mechanism was the committed YAML config. `uv.lock`
  (`d850ddd`) now pins the measuring instrument directly, which is the stronger receipt
  and was the actual point.
- *Leverage* — collapsing six dependencies into one. This inverts once the Windows-primary
  goal lands: VERSA becomes the dependency that *forces* the devcontainer, and the
  project uses roughly five of its eighty metrics.

So the tool that was chosen to reduce dependency friction is now the main source of it.
Removing it makes Phase E native on Windows, removes the mandatory container, and
removes NeMo alongside it (see R1 — swap Parakeet to HuggingFace, keep faster-whisper).

The portfolio angle is better this way, not worse: *"I chose VERSA on credibility
grounds, then removed it when a Windows-primary requirement landed and I noticed I was
using five of its eighty metrics — the lockfile was already doing the job I had hired
VERSA for."* That is a second killed-my-own-decision moment with a receipt, and it pairs
with the killed weighted composite. Keep the VERSA evaluation in Appendix C as the
reasoning trail; add the reversal underneath it.

One consequence to note: with VERSA gone, C.1's "rejected alternatives" entry for
hand-rolled scripts needs a sentence explaining why direct library calls are not that —
they are standard implementations invoked directly, not reimplementations.

---

## Part 4 — What is not a finding

Stated explicitly so these are not re-litigated later:

The two-judge WER design, the refusal of commercial ASRs as judges, gates + Pareto over
weighted composite, −18 LUFS normalization before A/B, hidden human anchors with a
pilot quality bar (E8), pre-registration by git tag, the immutable run store, errors as
data, the HI Δ/"Reproduces?" columns, the contamination probe with its own honest E7
caveat, serving-region disclosure, Orpheus latency marked N/A-hosted, and the decision
to lock provider-recommended voices rather than clone one voice — all of these are
correct as designed and several are better than standard practice in published TTS
comparisons. R1 exists precisely because the two-judge design is worth protecting.
