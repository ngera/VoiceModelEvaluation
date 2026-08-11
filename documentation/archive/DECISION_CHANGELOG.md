# Decision changelog — v1 → v2

Purpose: a single scannable record of every planning decision that changed
between v1 (2026-08-04) and v2 (2026-08-06), the reason it changed, and
what it affects downstream. Complements the "What changed in v2" summary
at the top of [voice_ai_eval_spec_v2.md](voice_ai_eval_spec_v2.md) §0 with
the *reasoning* trail, not just the diff.

Read this to answer "why is the code different from what CLAUDE.md still
says?" without re-reading the entire spec.

## Sources

The v2 decisions came from two overlapping inputs:

- **`EXTERNAL_REVIEW_2026-08-06.md`** — a second red-team pass raising ten
  findings, referenced as **R1–R10** below. *(Referenced by v2 docs but
  not currently present in this folder — see Housekeeping at the end.)*
- **Analyzer-backbone decision (2026-08-06)** — a separate architecture
  call, prompted by re-scoping to Windows-primary support. Drove the
  VERSA drop, the ASR-loader change, and the environment reversal.

## Change register

Each entry names: what changed, why (with source), what it affects, and
what still needs to happen for the change to be fully reflected in the
repo. Statuses:

- **✅ Aligned** — decision reflected in code and configs
- **🟡 Doc-only** — decision recorded in v2 spec/plan, code still on v1 shape
- **🟠 Partially applied** — some artifacts updated, others not
- **⚪ No code impact yet** — will land in later phase

---

### 1. Analyzer backbone: **VERSA dropped**

| Before (v1) | After (v2) |
|---|---|
| VERSA as the analyzer engine, with all metrics surfaced through one YAML config | Direct library calls — jiwer, TTSDS2, Audiobox Aesthetics, silero-VAD, pyloudnorm — one module per dimension in `src/veval/analyze/` |

**Why.** Two reinforcing reasons:

1. **Windows-primary support was clarified as a project goal.** VERSA is
   Linux-first; five of the ~80 metrics it wraps had Linux-only
   dependencies that forced the devcontainer to be mandatory at Phase E.
2. **The value VERSA added was mostly hypothetical for this project.**
   The extra metrics it enables (speaker similarity, PESQ, MCD, classic
   MOS predictors) are either not applicable to a non-cloning,
   non-telephony TTS evaluation or explicitly rejected. What remained
   was one YAML config surface — traded against platform lock-in, a
   longer install, and coarser reproducibility (a VERSA version bump
   can silently change any wrapped metric between drift re-runs).

**What it affects.** Phase E structure (six modules instead of one YAML);
Phase E environment (native everywhere, devcontainer optional); the
`versa.yaml` config becomes `analyzers.yaml`; the "scored with VERSA"
narrative is replaced with "portable-by-design, each measurement library
independently pinned in `uv.lock`."

**Status.** 🟡 Doc-only. `src/veval/analyze/` doesn't exist yet; Phase E
hasn't started. **CLAUDE.md still lists VERSA as the analyzer backbone.**

---

### 2. ASR judge 1 loader: **NeMo → HuggingFace `transformers`**

| Before (v1) | After (v2) |
|---|---|
| Parakeet TDT loaded via NVIDIA NeMo toolkit | Parakeet TDT loaded via HuggingFace `transformers` |

**Why.** The Windows portability problem was NeMo, not Parakeet. The
model choice from the plan (Parakeet TDT — currently #1 on the Open ASR
leaderboard for English) is preserved; only the loader changes.
`transformers` ships Windows-compatible wheels and doesn't require the
NeMo dependency graph.

**What it affects.** Phase E `wer.py` module; the devcontainer becomes
optional (this is the change that makes it truly optional, combined with
the VERSA drop).

**Status.** 🟡 Doc-only. No `wer.py` yet.

---

### 3. ASR judge 2: **faster-whisper locked; Canary rejected**

| Before (v1) | After (v2) |
|---|---|
| faster-whisper as adjudicator, with an active discussion about swapping to NVIDIA Canary-1B | faster-whisper large-v3 **locked**. Canary-1B is not admissible as judge 2 |

**Why (R1).** The mid-planning discussion floated Canary as a replacement
because it's HF-loadable and top-tier. R1 caught the flaw: Canary shares
NVIDIA's FastConformer encoder family *and* data pipeline with Parakeet.
Two correlated judges produce a protocol that looks like two-judge but
behaves like one — the agreement rule stops filtering ASR noise. The
independence constraint (differ in **all three** of organisation,
architecture family, training-data pipeline) is now a stated design
rule in [voice_ai_eval_spec_v2.md §4.2](voice_ai_eval_spec_v2.md).

**What it affects.** Locks the judge pair. Canary is admissible only as
an optional third judge. This is one of the two "would have quietly
broken the methodology" catches worth featuring in the narrative bank.

**Status.** 🟡 Doc-only. No `wer.py` yet, so no risk of the swap
sneaking in.

---

### 4. Environment: **Native Windows works throughout; devcontainer optional**

| Before (v1) | After (v2) |
|---|---|
| Native for Phase A–D; devcontainer mandatory from Phase E | Native works end-to-end (A–G). Devcontainer retained as a pinned-Linux reproducibility artifact and fallback |

**Why.** Direct consequence of changes 1 and 2 — VERSA gone, NeMo gone,
everything remaining (torch, TTSDS2, Audiobox, faster-whisper,
`transformers`-loaded Parakeet, silero-VAD, pyloudnorm) has Windows wheels.

**What it affects.** DX drastically simpler; reviewers can `uv sync` and
run without Docker Desktop. The `.devcontainer/` folder stays as a
reproducibility artifact. Same commands work in both modes.

**Status.** 🟡 Doc-only. **CLAUDE.md still says "WSL2 + Docker Desktop"
under Locked technical decisions → Dev env.** The `.devcontainer/`
files themselves are still present and functional; nothing to remove.

---

### 5. Runner: **variance mode added**

| Before (v1) | After (v2) |
|---|---|
| `veval generate` had campaign and latency modes | `veval generate` adds `--mode variance` — 10 items × 3 draws × 6 providers × 2 use cases = 360 generations |

**Why (R4).** Without a variance measurement, the project cannot state
its own noise floor — and every reported between-provider difference is
therefore unaudited. The variance subset produces the pooled
within-provider SD on TTSDS2 and item-WER; the pre-committed rule (in
`gates.yaml`) is that any between-provider difference smaller than 2× the
pooled within-provider SD is reported as "within noise floor," not as a
difference.

**Orpheus exception:** Replicate bills per generation, so the full 60
draws would cost ~$5 on their own. Orpheus runs a 5-item subset instead
(~$1.20), and its noise floor is correspondingly less precise — noted
wherever it is used.

**What it affects.** Phase D runner gains a mode; Phase E gains a
`variance.py` module; `gates.yaml` gains the noise-floor rule;
budget gains a $3–5 line item; `configs/corpus/variance_subset.yaml`
becomes a Phase B artifact.

**Status.** 🟡 Doc-only. No runner code exists yet.

---

### 6. Analyzers: **6 modules instead of 4**

| Before (v1) | After (v2) |
|---|---|
| Four modules: `wer.py`, `quality.py`, `hygiene.py`, `latency.py` | Six + `cost.py`: adds `variance.py` (R4), `drift.py` (R6), and gains failure-incidence in `wer.py` (R5) and split-half in `quality.py` (R3). `cost.py` moves cost modelling out of a spreadsheet into code |

**Why per module:**

- **`variance.py` (R4):** produces the noise floor — see change 5.
- **`drift.py` (R6):** per-third TTSDS2 + hygiene on the 8 long
  narration items. Monotonic degradation across thirds is the measured
  form of listener fatigue and feeds a narration gate. Without this,
  the "listener fatigue" claim is subjective and comes out of the
  results table entirely.
- **`wer.py` failure incidence (R5):** the % of items exceeding a
  pre-committed per-item WER threshold, plus a typed count of
  catastrophic events (drops, repetition loops, truncation,
  hallucinations). Mean WER hides the tail; one mangled currency
  amount in 200 utterances is the fact a buyer acts on.
- **`quality.py` split-half (R3):** before TTSDS2 may carry a headline,
  split each provider's item set in half; if the two scores diverge by
  more than a pre-committed absolute threshold, TTSDS2 is demoted to a
  supporting signal.
- **`cost.py`:** code not a spreadsheet, because cost is a frontier
  axis and must regenerate on the drift re-run.

**What it affects.** Phase E scope; `analyzers.yaml` gains reference-set
and split-half-threshold parameters; `pricing.yaml` becomes a new config
file (D6).

**Status.** ⚪ No code impact yet — Phase E hasn't started.

---

### 7. Human layer: **bootstrap CIs, randomised ordering, session-gap logging**

| Before (v1) | After (v2) |
|---|---|
| Bradley–Terry fit; 10% consistency re-judge | + bootstrap 2,000-resample 95% CIs on every score; pair order randomised across sessions (not blocked by provider); consistency re-judge publishes its session gap |

**Why (R2, R8).**

- **R2:** D4 is the y-axis of both frontier charts and comes from one
  rater. Without confidence intervals, calling a provider "dominated"
  overstates certainty. CIs must propagate all the way to the
  domination rule.
- **R8:** if pairs are blocked by provider within a session, any
  within-session preference drift loads onto specific providers.
  Randomising across sessions removes this confound. The session gap
  matters for the consistency number — same-day re-judgment is not the
  same as one-week re-judgment.

**What it affects.** `human/` module in Phase F; `judgments/` output
schema; frontier charts gain y-error bars; results tables gain ±CI
columns.

**Status.** ⚪ No code impact yet — Phase F hasn't started.

---

### 8. Scoring: **CI-gated domination + Spearman cross-checks**

| Before (v1) | After (v2) |
|---|---|
| Apply gates → Pareto frontier → ±20% robustness | + a provider is declared dominated only where its D4 CI does not overlap the dominating provider's. Overlapping pairs become "indistinguishable at this n" as a first-class result category. + Spearman ρ published for D3↔D4, D3↔HI, D4↔HI |

**Why (R2, R7).**

- **R2 downstream effect:** CIs from change 7 have to change the
  verdict, or the CIs are decorative. Rule: overlap ⇒ indistinguishable.
- **R7:** cross-metric agreement was previously an assertion ("D3 and
  D4 mostly agree"). Publishing three Spearman numbers converts it into
  data. Agreement earns the right to rely on D3 on the many items D4
  never covered; divergence is a finding to explain.

**What it affects.** Phase G `score/` module gains the CI domination
rule and correlation math; results tables gain "indistinguishable at
this n" as a status.

**Status.** ⚪ No code impact yet — Phase G hasn't started.

---

### 9. Config: **`versa.yaml` → `analyzers.yaml`; new `pricing.yaml`**

| Before (v1) | After (v2) |
|---|---|
| `configs/versa.yaml` selecting metrics | `configs/analyzers.yaml` pinning the TTSDS2 reference set (with domain-match rationale), the benchmark's documented minimum sample size, the absolute split-half divergence threshold, and pinned revisions for both ASR judges + TTSDS2 + Audiobox. + `configs/pricing.yaml` for D6 |

**Why (R3).** The TTSDS2 reference set is part of the measurement, not
an implementation detail — using a mismatched reference (read speech for
a conversational corpus, say) can compress exactly the differences the
chart needs to show. Freezing it in prereg puts it on the same footing
as gates and voices. The minimum sample size and split-half threshold
being written before results exist is what makes the demote-to-supporting
rule enforceable rather than post-hoc.

**What it affects.** Phase B config authoring; Phase E `quality.py`
reads reference-set + split-half threshold from `analyzers.yaml`.

**Status.** 🟡 Doc-only. Neither file exists yet; `config.py` doesn't
have Pydantic models for them.

---

### 10. Corpus: **75 items per use case, reconciled everywhere**

| Before (v1) | After (v2) |
|---|---|
| Ambiguous — 75 in some documents, 84 in others | **75 per use case, reconciled.** 60 novel (12 short / 20 medium / 8 long / 12 jargon / 8 edge) + 15 famous public-domain probe. Long stratum raised from 2 in the parent to 8, because per-third drift analysis (R6) needs sample size ≥8 to be worth reporting |

**Why (R10).** The 84 figure was a stale carry-over from an earlier
descope; three separate mechanisms depend on the strata (variance-subset
selection, RTF measurement, per-third drift), so leaving them ambiguous
would have propagated into all three.

**What it affects.** Phase B corpus curation targets 75 per use case;
architecture mermaid diagram corrected; volume math is 75 × 2 × 6 = 900
primary files.

**Status.** ⚪ No code impact yet — corpus not extracted.

---

### 11. Cost budget: **$30–45 → $36–47 (worst case $69)**

| Before (v1) | After (v2) |
|---|---|
| ~$30–45 | ~$36–47 (baseline) with two named contingencies: +$5–10 for GPU spot instance if no local GPU; +$0–12 for ElevenLabs / Cartesia overage. Worst case both contingencies ~$69. Pre-committed rule: if projected spend crosses $50, cap ElevenLabs and Cartesia to a documented paired corpus subset before paying for a second month |

**Why.** Change 5 (variance subset) added ~$3–5. Explicit accounting for
Orpheus/Replicate per-generation billing. Volume vs. paid-tier
allowances (ElevenLabs Creator and Cartesia Pro are ~100K credits/month;
estimated usage is 90–120K + 35K variance) could exceed a single month.

**What it affects.** Budget bookkeeping; a spend-cap rule in the runner
(D4 already has spend cap in `.env.example`).

**Status.** 🟡 Doc-only. **CLAUDE.md still says "~$30–45."**

---

## Housekeeping items uncovered while reading v2

Not decisions per se — items where the v2 update introduced references or
dependencies that don't yet exist in the repo:

- **`documentation/EXTERNAL_REVIEW_2026-08-06.md` is referenced by
  IMPLEMENTATION_PLAN.md v2 (line 16) and by Change register entries
  R1–R10 above, but the file is not present in `documentation/`.**
  Either the file needs to be added, or the references need to be
  removed / repointed. Flagging per CLAUDE.md meta-rule 3.

- **CLAUDE.md is materially stale.** IMPLEMENTATION_PLAN.md v2 already
  proposes the amendments (its "Proposed CLAUDE.md amendments" section);
  they are proposed, not written, per meta-rule 1. The stale rows
  actively contradict v2 decisions:

  | CLAUDE.md row | Says | v2 says |
  |---|---|---|
  | Locked → Dev env | WSL2 + Docker Desktop, CUDA base | Native Windows throughout; devcontainer optional |
  | Locked → Analyzer backbone | VERSA (surfacing jiwer, TTSDS2, silero-VAD) | Direct library calls; VERSA dropped |
  | Locked → CLI | doctor / generate / analyze / score / report | + `invites` (Phase F) |
  | Meta-rule 2 | References `voice_ai_eval_portfolio_edition.md` and `voice_ai_eval_plan_v1_descoped.md` as source-of-truth | Both archived; should reference `voice_ai_eval_spec_v2.md` and `IMPLEMENTATION_PLAN.md` |
  | Project overview | "Planning complete; Phase A not yet started" | Phase A closed 2026-08-05 |
  | Project overview | Budget ~$30–45 | ~$36–47 (see change 11) |
  | Reference documents | Lists five files that are now under `archive/` | Should list the current three |

  Fixes need explicit confirmation per meta-rule 1 — this changelog is
  the confirmation-worthy artifact; see [IMPLEMENTATION_GAP.md](IMPLEMENTATION_GAP.md)
  for the proposed set of edits.

- **The architecture mermaid v2 adds a `DESK` box** (D8 capability
  audit) to the flow. There is no `desk/` module planned in
  `src/veval/`; the D8 audit is desk research producing a matrix, not
  code — likely lives in `configs/` or `docs/` as a YAML/markdown
  table. Worth stating explicitly somewhere that D8 has no code
  artifact, only a config/data one.

## Cross-reference

| Change | Spec §            | Plan (v2) row              | Review finding |
|--------|-------------------|-----------------------------|----------------|
| 1  | Appendix B.1 (implied) | Analyzer backbone | Analyzer decision, not R# |
| 2  | Appendix B.3 (implied) | ASR judge 1        | Analyzer decision, not R# |
| 3  | §4.2              | ASR judge 2                 | R1             |
| 4  | Risks             | Environment                 | Follows 1 & 2  |
| 5  | §3.4              | Phase D runner              | R4             |
| 6  | §4.3, Appendix A  | Phase E analyzers           | R3, R4, R5, R6 |
| 7  | §4.3, Appendix A.4 | Phase F human layer         | R2, R8         |
| 8  | §5                | Phase G scoring             | R2, R7         |
| 9  | §4.3, §3.4        | Config files                | R3             |
| 10 | §3.3              | Corpus size                 | R10            |
| 11 | §8                | (not in v2 plan diff)       | Follows change 5 |
