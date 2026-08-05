# CLAUDE.md — Voice AI Evaluation Project

## Meta-rules for Claude

1. **This file self-updates as the project evolves.** When a decision is
   made, a convention is established, a naming rule is chosen, or a pattern
   emerges — propose an addition to this file and wait for explicit
   confirmation before writing. Never edit CLAUDE.md silently.
2. **Reference the three source-of-truth docs before proposing changes:**
   `voice_ai_eval_portfolio_edition.md` (WHAT — current build scope),
   `voice_ai_eval_plan_v1_descoped.md` (HOW — methodology),
   `eval_harness_architecture.mermaid` (structure).
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
- **Scope:** 6 providers × 2 use cases (conversational + narration)
- **Timeline / budget:** ~3 weeks part-time, ~$30–45
- **Status:** Planning complete; Phase A not yet started

## Locked technical decisions

| Piece | Choice |
|---|---|
| Language | Python 3.11 |
| Package manager | uv |
| Config | Pydantic v2 loading YAML |
| Async | httpx.AsyncClient in runner; adapters sync |
| Dev env | WSL2 + Docker Desktop, CUDA base image |
| GPU | Local NVIDIA, --gpus all passthrough |
| Analyzer backbone | VERSA (jiwer, TTSDS2, silero-VAD surfaced through it) |
| CLI | `veval <subcommand>` — doctor / generate / analyze / score / report |
| Admin panel | Streamlit, local-only, wraps CLI functions |
| Voting UI | Vercel Hobby, static, audio in /public |
| Vote backend | Formspree/Basin, batched POST per rater at session end |
| Rater model | Tokened invite URLs (?rater=abc), remote friends |
| Results / memos / case study | Local only (private) |
| Corpus source | python-docx extractor over documentation/*.docx |

## Providers (locked roster of 6)

ElevenLabs · Cartesia · Fish Audio · Google Cloud TTS · Deepgram (off-index
control) · Canopy Orpheus (Replicate-hosted)

## Conventions

- **Run store:** `runs/<run_id>/` is immutable — manifest.json, audio/,
  api_log.jsonl. Never mutate in place.
- **Analysis outputs:** `analysis/<run_id>/` are pure functions of run
  store — re-runnable without regenerating audio.
- **Pre-registration:** configs (providers, voices, gates, corpus) are
  git-tagged as `prereg-v1` before any results exist. Receipt for the
  case study.
- **Deviations:** logged in `DEVIATIONS.md` with rationale, never
  silently fixed.
- **Admin panel is a thin wrapper** — never duplicate CLI logic.
- **CLI subcommand naming:** follows the `<tool> doctor` convention
  (brew, flutter, npm precedent).

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
- n=1 self-rating disclosed honestly beats false rigor of a 3-rater
  "panel." Blinded, consistency-checked, human-anchored — the method
  is the demonstration.

## Deferred / open decisions

- Orpheus host: Replicate (default) vs Baseten — decide in Phase C
- Formspree vs Basin — decide in Phase F
- Anchor voice recording source: yours vs friend (consent needed if
  friend, since audio ships to Vercel) — decide in Phase F

## Reference documents in this repo

- `documentation/voice_ai_eval_portfolio_edition.md` — current build scope
- `documentation/voice_ai_eval_plan_v1_descoped.md` — full methodology
- `documentation/voice_ai_eval_execution_runbook.md` — post-build campaign runbook
- `documentation/voice_ai_eval_tester_guide.md` — for external reproducers (future)
- `documentation/voice_ai_test_suite_spec.md` — parent spec (reference only)
- `documentation/eval_harness_architecture.mermaid` — component diagram
- `documentation/*.docx` — corpus source

## Change log

- 2026-08-04 — initial creation with locked decisions after planning phase
- 2026-08-04 — added meta-rule 4 (maintain narrative bank) and the
  "Key points to highlight" section
- 2026-08-04 — moved five .md docs and the mermaid diagram into
  documentation/; updated reference paths
