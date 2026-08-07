# CLAUDE.md — Voice AI Evaluation Project

## Meta-rules for Claude

1. **This file self-updates as the project evolves.** When a decision is
   made, a convention is established, a naming rule is chosen, or a pattern
   emerges — propose an addition to this file and wait for explicit
   confirmation before writing. Never edit CLAUDE.md silently.
2. **Reference the three source-of-truth docs before proposing changes:**
   `documentation/voice_ai_eval_spec_v2.md` (WHAT + HOW — the single spec),
   `documentation/IMPLEMENTATION_PLAN.md` (BUILD — phase-by-phase execution),
   `documentation/eval_harness_architecture.mermaid` (STRUCTURE).
   The v1 documents (`voice_ai_eval_portfolio_edition.md`,
   `voice_ai_eval_plan_v1_descoped.md`) are superseded and live under
   `documentation/archive/` as provenance only — do not treat them as
   authoritative.
3. **When a decision here conflicts with a source doc, flag it** rather
   than silently favoring one.
4. **Maintain a "Key points to highlight" section as a portfolio narrative
   bank.** When a notable moment happens — a decision with strong
   reasoning, a killed-my-own-bad-idea moment, an unexpected finding, a
   design tradeoff worth articulating, a quotable data point — propose
   adding it to that section. Always ask before writing. This section
   feeds blog posts, LinkedIn/X posts, case study copy, and interview
   talking points. Prefer specific, quotable phrasings over generic
   claims.

## Project overview

- **What:** Voice AI provider evaluation harness (portfolio edition scope)
- **Scope:** 6 providers × 2 use cases (conversational + narration) × 75 corpus items
- **Timeline / budget:** ~3 weeks part-time, ~$36–47 baseline (worst case ~$69 with contingencies — see spec §8)
- **Status:** Phase A closed 2026-08-05; Phase B (configs + corpus + prereg) next
- **Hard deadline:** Fish Audio free window closes **2026-08-31** — sets the schedule

## Locked technical decisions

| Piece | Choice |
|---|---|
| Language | Python 3.11 |
| Package manager | uv |
| Config | Pydantic v2 loading YAML |
| Async | httpx.AsyncClient in runner; adapters sync |
| Dev env | **Native Windows throughout** (macOS/Linux also work); devcontainer retained as optional pinned-Linux reproducibility artifact |
| GPU | Local NVIDIA recommended for Phase E; spot instance ($5–10) as contingency |
| Analyzer backbone | **Direct library calls** — jiwer · TTSDS2 · Audiobox Aesthetics · silero-VAD · pyloudnorm; Parakeet TDT loaded via HuggingFace `transformers` |
| ASR judges | **Parakeet TDT (HF) + faster-whisper large-v3, locked.** Judges must differ in **all three** of: originating organisation, encoder architecture family, and training-data pipeline. Canary-1B is **not admissible as judge 2** (shares NVIDIA's FastConformer encoder + data pipeline with Parakeet) — admissible only as an optional third judge |
| Statistics | Bootstrap 95% CIs (2,000 resamples) on all D4 Bradley–Terry scores; noise-floor rule from the variance subset (any between-provider difference smaller than 2× pooled within-provider SD is *within noise floor*, not a difference); Spearman ρ for D3↔D4, D3↔HI, D4↔HI |
| CLI | `veval <subcommand>` — doctor / generate / analyze / **invites** / score / report |
| Admin panel | Streamlit, local-only, wraps CLI functions |
| Voting UI | Vercel Hobby, static, audio in /public |
| Vote backend | Formspree/Basin, batched POST per rater at session end |
| Rater model | Tokened invite URLs (?rater=abc), remote friends |
| Results / memos / case study | Local only (private) |
| Corpus source | python-docx extractor over documentation/archive/*.docx |

## Providers (locked roster of 6)

ElevenLabs · Cartesia · Fish Audio · Google Cloud TTS · Deepgram (off-index
control) · Canopy Orpheus (Replicate-hosted)

## Conventions

- **Run store:** `runs/<run_id>/` is immutable — manifest.json, audio/,
  api_log.jsonl. Never mutate in place.
- **Analysis outputs:** `analysis/<run_id>/` are pure functions of run
  store — re-runnable without regenerating audio.
- **Pre-registration:** configs (providers, voices, gates, analyzers,
  pricing, corpus) are git-tagged as `prereg-v1` before any results
  exist. Amendments before the campaign are re-tagged `prereg-v1.1`
  with the reason logged in `DEVIATIONS.md`. Amending pre-registration
  after results exist is not honest and is not done.
- **Deviations:** logged in `DEVIATIONS.md` with rationale, never
  silently fixed.
- **Admin panel is a thin wrapper** — never duplicate CLI logic.
- **CLI subcommand naming:** follows the `<tool> doctor` convention
  (brew, flutter, npm precedent).
- **Streamed WAV headers:** every streaming adapter passes bytes through
  `finalize_wav_header()` in `adapters/base.py`. Providers ship a
  placeholder length in the header (Deepgram: 44,737s declared for a
  2.8s clip); anything trusting the header — RTF, VAD, LUFS, TTSDS2 —
  reads that lie. Not optional.

## Key points to highlight (portfolio narrative bank)

Raw material for the case study, blog posts, marketing, and interview
prep. Grouped by theme. Every point should be traceable to a dated
artifact in the repo. Add liberally as the project progresses.

### Framing & scoping (the PM story)
- Inherited a 400-hour, 12-provider × 10-use-case × 16-dimension spec
  and shipped the decision it was for in ~60 hours — the descoping
  table is the artifact.
- Chose the portfolio edition over the public-benchmark edition
  deliberately: sequencing decision, not a one-way door. The full plan
  is still on the shelf if the day comes.
- Two contrasting use cases (conversational support + long-form
  narration) chosen because they pull in opposite directions — a
  provider that wins one and loses the other is the *expected*, most
  instructive outcome.

### Methodology cleverness (the "why this is defensible" story)
- Killed my own weighted-composite design — replaced with pre-committed
  gates + Pareto frontiers. Weights are always arguable; gates are
  falsifiable and the git tag `prereg-v1` proves they predate the data.
- Two-judge WER (Parakeet TDT + faster-whisper, agreement-based) —
  because one judge can't tell its own errors from the system's.
- Refused commercial ASRs as WER judges — Deepgram and Google are
  providers under test; using their ASR to grade competitors is a
  conflict a hostile reader would find in minutes.
- Loudness-normalized all clips to −18 LUFS before A/B — without this,
  louder clips systematically win, and the test measures gain staging
  not voice quality.
- Chose TTSDS2 over UTMOS/NISQA — the parent spec's defaults saturate
  on frontier TTS (everything scores 4.3–4.6, ranking becomes noise).
- **Removed VERSA after choosing it.** The tool picked to reduce
  dependency friction became the one forcing a Linux container — for
  five of its eighty metrics. The lockfile was already doing the job
  VERSA was hired for. *(Second killed-my-own-decision moment, pairs
  with the weighted composite.)*
- **Caught a swap that would have broken the two-judge design.**
  Replacing faster-whisper with Canary would have escaped the Windows
  problem and quietly gutted the agreement rule — Canary and Parakeet
  share NVIDIA's encoder family and data pipeline. Judge independence
  is now a written constraint, not a lucky property.
- **Measured our own noise floor.** Ten items, three draws, six
  providers: the project can now state which differences it is not
  entitled to report. No competing eval publishes this.
- **Put error bars on the money chart.** An n=1 perceptual study that
  declares "dominated" without confidence intervals is exactly the
  thing a hostile reader dismantles first — so domination now requires
  non-overlapping intervals, and "indistinguishable at this n" is a
  result we are willing to print.

### Engineering choices
- Admin panel and CLI share the same underlying functions — two front
  doors, one implementation. Never duplicate logic.
- Immutable run store: `runs/<run_id>/` never mutated. Analyzers are
  pure functions of the store, re-runnable without regenerating audio.
- Content-hash cache in the runner means re-runs cost only the changed
  items — key to the "monthly cached re-run" story.
- Errors logged as data, never hand-patched. Failed provider runs get
  a clean re-run under a new manifest, never partial mixes.

### Quotable data points (fill in as results arrive)
- (TBD) The public leaderboard we audit still ranks PlayHT — a company
  shut down Dec 31, 2025. Ours re-runs in one command.
- (TBD) Δ vs Humanness Index per provider — where do their published
  numbers reproduce, where don't they.
- (TBD) DX friction log: "Provider X — 11 minutes; Provider Y — 74
  minutes and an undocumented header."
- (TBD) $ spread across providers at 1M words/mo — expected to be
  1–2 orders of magnitude, dwarfing quality differences.

### Meta / self-critical
- Red-team review caught 10 flaws in my own plan (Appendix E). Owning
  the red-team appendix in the write-up is the point.
- **Discovered the source corpus was mostly empty and documented the
  pivot rather than papering over it** (DEVIATIONS.md D-002). The plan
  language "curated from the existing corpus" was inherited from a
  corpus assumption that turned out to be wrong; extraction found 20
  long items where 150 items were assumed. Corrected the spec, logged
  the deviation, and authored the corpus fresh with the parent as
  seed — the honest description of what happened, and a small receipt
  for the "every claim traceable to a dated artifact" DoD line.
- **An external reviewer raised ten more gaps** (`EXTERNAL_REVIEW_2026-08-06.md`).
  Nine were already covered — several more rigorously than the
  reviewer's own recommendation. The tenth round — the one that came
  *after* reading — is the one worth publishing.
- n=1 self-rating disclosed honestly beats false rigor of a 3-rater
  "panel." Blinded, consistency-checked, human-anchored, bootstrap-CI'd
  — the method is the demonstration.

## Deferred / open decisions

- Orpheus host: Replicate (default) vs Baseten — decide in Phase C
- Formspree vs Basin — decide in Phase F
- Anchor voice recording source: yours vs friend (consent needed if
  friend, since audio ships to Vercel) — decide in Phase F
- **TTSDS2 reference set:** chosen in Phase B, validated against the
  $1 pilot in Phase D — may force a `prereg-v1.1` re-tag

## Reference documents in this repo

**Active:**
- `documentation/voice_ai_eval_spec_v2.md` — WHAT + HOW (the spec)
- `documentation/IMPLEMENTATION_PLAN.md` — BUILD (phase-by-phase)
- `documentation/eval_harness_architecture.mermaid` — STRUCTURE (v2)
- `documentation/EXTERNAL_REVIEW_2026-08-06.md` — R1–R10 review register
- `documentation/DECISION_CHANGELOG.md` — v1→v2 change trail with reasoning
- `documentation/IMPLEMENTATION_GAP.md` — current implementation vs plan v2
- `documentation/voice_ai_eval_execution_runbook.md` — post-build campaign runbook
- `documentation/voice_ai_eval_tester_guide.md` — for external reproducers (future)

**Archived (provenance only — not authoritative):**
- `documentation/archive/voice_ai_eval_portfolio_edition.md` (v1 WHAT)
- `documentation/archive/voice_ai_eval_plan_v1_descoped.md` (v1 HOW)
- `documentation/archive/IMPLEMENTATION_PLAN_v1.md` (v1 BUILD)
- `documentation/archive/voice_ai_test_suite_spec.md` (parent spec)
- `documentation/archive/*.docx` — corpus source

## Change log

- 2026-08-04 — initial creation with locked decisions after planning phase
- 2026-08-04 — added meta-rule 4 (maintain narrative bank) and the
  "Key points to highlight" section
- 2026-08-04 — moved five .md docs and the mermaid diagram into
  documentation/; updated reference paths
- 2026-08-05 — **Phase A closed** (commits `990e4ca`, `51e4f6b`): walking
  skeleton verified end-to-end (Deepgram → run store → doctor); 29-test
  regression net added; four defects fixed (see IMPLEMENTATION_PLAN §
  "Phase A closeout"), two of them silent (PYTHONPATH shadow,
  `postCreateCommand` uninstalling analyzer stack)
- 2026-08-06 — **v2 spec adopted.** Ten edits applied to reflect
  DECISION_CHANGELOG entries: meta-rule 2 repointed to v2 docs; status
  and budget refreshed; dev-env row reversed (native throughout,
  devcontainer optional); analyzer-backbone row replaced (VERSA
  dropped, direct library calls); CLI adds `invites`; new rows added
  for ASR judges and statistics; reference-docs section rewritten with
  archive separation; four narrative-bank entries added (VERSA drop,
  Canary catch, noise-floor, error-bars); pre-registration convention
  extended with `prereg-v1.1` amendment rule; streamed WAV convention
  added
- 2026-08-07 — **DEFECT_REGISTER fixes landed in Phase B configs +
  Pydantic models** (79-defect sweep folded in). Judge 1 switched to
  Parakeet **RNNT** (TDT unreleased in `transformers`); WER threshold
  reworked to `5% + numeric/currency/date span` clause; noise-floor
  rule renamed to `measurement_noise_floor` (1.96 × SE of the
  difference, per-provider) with acoustic-vs-statistical disambiguated;
  gates gained `na_policy` + explicit `robustness_points`; Orpheus
  cost corrected 24× and the 5-item variance concession reversed;
  ElevenLabs Creator credits corrected to 121K; model string moved
  from `providers.yaml` to `voices.yaml` per (provider, use_case);
  Audiobox axes pre-committed to PQ + CE; TTSDS2 noise reference,
  speaker-identity handling, and WER normaliser hash added.
- 2026-08-07 — **Corpus authoring pivot logged as D-002.** Source docx
  found to have only 20 long items across all 10 parent use cases and
  empty Short/Medium/Jargon/Edge sections; corpus origin story rewritten
  to "authored fresh, seeded by the parent corpus" — spec §3.3 amended,
  DEVIATIONS.md created, narrative-bank entry added.
