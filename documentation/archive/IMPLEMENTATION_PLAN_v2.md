# Implementation plan v2

> **Provenance.** v1 of this file was reconstructed 2026-08-04 from code comments after
> the original planning session's transcript was lost. v2 (2026-08-06) supersedes it,
> folding in the ten findings of `EXTERNAL_REVIEW_2026-08-06.md` and the analyzer-backbone
> decision. Phase letters A–G are carried forward unchanged — they survive in code
> comments and renaming them would break the citation trail. v1 is retained in
> `documentation/archive/`.
>
> This file exists so the plan lives in the repo, not in a chat transcript.

## Reference documents

- **Spec (WHAT + HOW):** [voice_ai_eval_spec_v2.md](voice_ai_eval_spec_v2.md) — the single source of truth
- **Architecture:** [eval_harness_architecture.mermaid](eval_harness_architecture.mermaid)
- **Review register:** [EXTERNAL_REVIEW_2026-08-06.md](EXTERNAL_REVIEW_2026-08-06.md)
- **Post-build campaign:** [voice_ai_eval_execution_runbook.md](voice_ai_eval_execution_runbook.md)
- **Locked decisions + conventions:** [../CLAUDE.md](../CLAUDE.md)
- **Archived:** `archive/voice_ai_eval_portfolio_edition.md`, `archive/voice_ai_eval_plan_v1_descoped.md`, `archive/IMPLEMENTATION_PLAN_v1.md`

## Scope

Build the ten boxes in the architecture diagram — FRONT, CONFIG, ADAPTERS, RUNNER, STORE,
ANALYZE, HUMAN, DESK, SCORE, REPORT — at portfolio-edition scope: 6 providers, 2 use
cases, 75 corpus items per use case, n=1 rating baseline with quantified uncertainty,
private results.

Six providers (locked): ElevenLabs · Cartesia · Fish Audio · Google Cloud TTS ·
Deepgram (off-index control) · Canopy Orpheus (Replicate-hosted).

**The schedule's hard constraint is Fish Audio's free window, which closes 2026-08-31.**
Everything upstream of the Fish campaign run is date-critical; everything downstream is
compute and writing.

## What changed from v1 of this plan

| Area | v1 | v2 | Driver |
|---|---|---|---|
| Analyzer backbone | VERSA, with the decision left open | **Dropped** — direct library calls, one module per dimension | Spec B.1 |
| ASR judge 1 | Parakeet TDT via NeMo | **Parakeet RNNT 0.6B via HuggingFace `transformers`** — TDT exists only on `transformers` `main`, so it cannot be pinned by version; RNNT shipped in a release. Same encoder family, so §4.2's independence argument is unchanged. Phase B re-checks whether TDT has landed in a release | Spec B.3, fact-check 2026-08-06 |
| ASR judge 2 | faster-whisper, with a Canary swap under consideration | **faster-whisper, locked.** Canary rejected as judge 2 | R1 / Spec §4.2 |
| Environment | Devcontainer mandatory from Phase E | **Native Windows works throughout.** Devcontainer optional, kept as a reproducibility artifact | Follows from the two rows above |
| Phase D runner | Campaign + latency modes | **+ variance mode** (10 items × 2 use cases × 3 draws × 6 providers = **360 generations**, all six at full subset) | R4 |
| Phase E analyzers | 4 modules | **7 modules** — adds `variance.py`, `drift.py`, `cost.py`; `wer.py` gains failure incidence; `quality.py` gains split-half | R3–R6 |
| Phase F human layer | Bradley–Terry fit | **+ bootstrap CIs, randomised session ordering, session-gap reporting** | R2, R8 |
| Phase G scoring | Gates → Pareto → robustness | **+ CI-gated domination rule, Spearman cross-checks** | R2, R7 |
| Config files | `versa.yaml` | **`analyzers.yaml`** — pins the TTSDS2 reference set and both judge revisions | R3 |
| Corpus size | Ambiguous (75 vs 84 across docs) | **75 per use case**, reconciled everywhere | R10 |

## Repo layout

```
voiceAgentEvals/
├── CLAUDE.md                          # locked decisions, conventions, narrative bank
├── documentation/
│   ├── IMPLEMENTATION_PLAN.md         # this file
│   ├── voice_ai_eval_spec_v2.md       # THE spec
│   ├── EXTERNAL_REVIEW_2026-08-06.md  # second red-team pass
│   ├── voice_ai_eval_execution_runbook.md
│   ├── voice_ai_eval_tester_guide.md
│   ├── voice_ai_test_suite_spec.md    # parent spec (reference only)
│   ├── eval_harness_architecture.mermaid
│   ├── archive/                       # superseded v1 docs, kept as provenance
│   └── *.docx                         # corpus source
├── DEVIATIONS.md
├── .devcontainer/                     # OPTIONAL — reproducibility artifact, no longer required
├── .env / .env.example
├── pyproject.toml                     # uv-managed; base + analyze/admin/dev extras
├── uv.lock                            # pins the measuring instrument — committed
├── configs/                           # pre-registered YAMLs (git-tag `prereg-v1`)
│   ├── providers.yaml
│   ├── voices.yaml
│   ├── gates.yaml                     # gates + na_policy + robustness_points + significance rule
│   │                                  #   + WER threshold + band cut-points + dBFS + event detectors
│   ├── analyzers.yaml                 # TTSDS2 speech + noise references; min sample size; split-half
│   │                                  #   threshold; normaliser hash; Audiobox axes; MDD; judge revisions
│   └── pricing.yaml                   # published rates per provider, date-stamped (D6)
├── corpus/
│   ├── conversational.yaml            # 60 novel + 15 probe = 75
│   ├── narration.yaml                 # 60 novel + 15 probe = 75
│   └── variance_subset.yaml           # 10 items per use case, frozen in prereg
├── src/veval/
│   ├── cli.py                         # Typer: doctor|generate|analyze|score|report
│   ├── config.py                      # Pydantic models + loaders
│   ├── doctor.py                      # shared by CLI + Streamlit
│   ├── adapters/                      # one file per provider, common interface
│   ├── runner/                        # orchestrator + latency mode + variance mode
│   ├── store/                         # immutable runs/<run_id>/ writer
│   ├── analyze/
│   │   ├── wer.py                     # two-judge + failure incidence
│   │   ├── quality.py                 # TTSDS2 + Audiobox + split-half
│   │   ├── hygiene.py                 # silero-VAD + pyloudnorm + clipping
│   │   ├── latency.py                 # TTFA p50/p90 + RTF
│   │   ├── variance.py                # noise floor + determinism
│   │   ├── drift.py                   # per-third quality drift
│   │   └── cost.py                    # pricing.yaml × logged char counts → cost_model.json
│   ├── human/                         # normalize, pair builder, BT fit, bootstrap CI
│   ├── score/                         # gates, Pareto, CI domination rule, robustness, Spearman
│   ├── report/                        # tables, charts (with error bars), memo templates
│   └── admin/                         # Streamlit — thin wrapper over CLI functions
│       ├── app.py
│       └── pages/{1_Doctor,2_Run,3_Results,4_Frontier}.py
├── scripts/extract_corpus.py          # python-docx → YAML
├── dx/friction_log.md                 # D7 — written live during Phase C, not reconstructable
├── rating/                            # LOCAL static A/B page + local audio dir (Phase F)
├── tests/                             # pytest — regression net for silent-corruption bugs
├── runs/<run_id>/                     # immutable: manifest.json, audio/, api_log.jsonl
├── analysis/<run_id>/                 # pure functions of runs/
├── judgments/                         # votes exported from the form backend
├── decisions/                         # gate survivors, frontiers, robustness, correlations
└── site/                              # local case study, memos, charts (private)
```

`runs/audio/` and `judgments/` raw exports are gitignored. **`analysis/` and `decisions/`
are committed** — they are small JSON, and the pre-registration receipt is worthless
without them: if no result artifact ever enters git, "the `prereg-v1` tag predates all
result files" is vacuously true and proves nothing. Each run also commits a
`runs/<run_id>/MANIFEST.sha256` so the audio stays out of git while its provenance stays
in. `veval report` asserts the tag ordering rather than leaving it to be eyeballed.

## Two front doors, one implementation

| Front door | Command | Audience |
|---|---|---|
| **CLI** | `veval <subcommand>` | Scripting, CI, terminal work |
| **Admin panel** | `streamlit run src/veval/admin/app.py` | Interactive ops, demos |

**Convention (CLAUDE.md):** the admin panel is a *thin wrapper* over the same functions
the CLI calls. Never duplicate logic. First embodiment: both `veval doctor` and the
Streamlit Doctor page call `run_doctor()` in `src/veval/doctor.py`.

| Command | Purpose | Phase |
|---|---|---|
| `veval doctor` | Health-check all/one adapter end-to-end → `runs/doctor-<ts>/` | A ✅ |
| `veval generate` | Corpus × providers campaign; `--mode campaign\|latency\|variance` | D |
| `veval analyze` | WER + failure incidence / quality + split-half / hygiene / latency / variance / drift / cost | E |

| `veval score` | Gates → survivors → Pareto with CIs → ±20% robustness → Spearman → HI cross-check | G |
| `veval report` | Results tables, frontier charts with error bars, memo and case-study templates | G |

## Phase map

| Phase | Scope | Status |
|---|---|---|
| **A** | Skeleton: package, `veval doctor`, run store, base adapter, first adapter (Deepgram), admin panel + Doctor page, tests | ✅ **closed 2026-08-05** (`990e4ca`, `51e4f6b`) |
| **B** | Configs + corpus + pre-registration | ⬜ **next** |
| **C** | Remaining 5 adapters | ⬜ |
| **D** | `veval generate` — campaign, latency and variance modes | ⬜ |
| **E** | `veval analyze` — seven analyzer modules | ⬜ |
| **F** | Voting UI + human judgment layer | ⬜ |
| **G** | `veval score` + `veval report` | ⬜ |

Week 1 ≈ B–D (through the $1 pilot and the Fish run), Week 2 ≈ D–E plus the start of F,
Week 3 ≈ F–G plus writing. See spec §7.

---

## Build sequence

### Phase B — configs, corpus, pre-registration

The gate for everything else. Nothing here needs an API key, so it can run in parallel
with account setup.

0. **Land and verify the interpreter fix (`11ff01d`) on the machine that will actually run
   the campaign.** `test_manifest_records_a_stable_interpreter` is red until it does, and
   every run's manifest — the reproducibility receipt — records the interpreter. A campaign
   stamped `3.11.0rc1` undermines the provenance claim the project is built on.
1. `scripts/extract_corpus.py` — python-docx over `documentation/*.docx` → draft YAMLs.
2. Curate and trim to **60 novel items per use case**: fix AI-generation artifacts, verify
   the jargon items are actually hard, confirm the edge battery covers numbers, dates,
   currency, acronyms, URLs and proper nouns. Confirm all names and amounts are synthetic.
3. Add **15 famous public-domain items per use case** (Harvard sentences, pre-1930
   literary openings) as the contamination probe.
4. Select the **10-item variance subset per use case** — drawn across the length and
   difficulty strata — into `corpus/variance_subset.yaml`.
5. Write `configs/providers.yaml` (all 6), `voices.yaml` (recommended voice per provider
   per use case, with selection reasoning per entry).
6. Write `configs/gates.yaml` — the gates from spec §5, **plus the pre-committed
   numeric rules**: the per-item WER threshold that defines failure incidence; the
   noise-floor reporting rule (no difference below the §3.4 significance rule
   reported as a difference); and the hygiene thresholds (noise floor ≤ −40 dBFS, zero
   clipped samples). Each entry carries a one-line rationale. No gate ships as prose —
   "no audible artifacts" is not pre-registrable, a number is.
7. Write `configs/analyzers.yaml` — **the TTSDS2 reference set with its domain-match
   rationale**, **the benchmark's documented minimum sample size**, **the absolute
   split-half divergence threshold**, plus pinned revisions for both ASR judges, TTSDS2
   and Audiobox.
8. Write `configs/pricing.yaml` — published rates per provider with a per-cell source and
   date. Re-pulled on analysis day (D6 rule); the Week 1 version exists so the pilot can
   produce a toy frontier with a real x-axis.
9. **Apply the CLAUDE.md amendments** proposed at the foot of this document. Until they
   land, the locked-decisions file still mandates VERSA and a required devcontainer, and
   its meta-rule 2 points future sessions at archived documents — so Phase E could be built
   against superseded instructions.
10. **Git tag `prereg-v1`.** The receipt that gates, voices, corpus and analyzer parameters
   all predate any result.

> **Ordering note.** Two Phase B artifacts cannot be fully validated until audio exists:
> the TTSDS2 split-half check (spec §4.3) and any gate threshold that turns out to
> discriminate nothing. Both are validated against the **$1 pilot in Phase D**. If either
> fails, amend the config and re-tag as `prereg-v1.1` with the reason recorded in
> `DEVIATIONS.md`. Amending pre-registration *with a logged reason before the campaign* is
> honest; amending it after results exist is not. The split-half check compares against an
> absolute threshold from `analyzers.yaml`, **not** against the noise floor — the noise
> floor does not exist until Phase E, and using it here would be circular.

### Phase C — five more adapters

Order by onboarding ease: **Fish → Google → Cartesia → ElevenLabs → Orpheus (Replicate)**.
Fish first because the free window closes Aug 31. Each must pass
`veval doctor --provider X` before the next is started.

Per-adapter checklist: streaming TTFA measurement wired into the common return shape;
`finalize_wav_header()` applied to any streamed WAV (the Phase A defect class); character
count captured for D6; model string and voice ID written into the manifest.

**Per-provider constraints to implement, not discover** (spec §3.1). **Google first, and
test before assuming:** Chirp 3 HD went GA in April 2025 and its documentation shows
streaming synthesis, so the "Preview" justification for falling back to buffered REST is
stale. Spend fifteen minutes calling `streaming_synthesize` before committing to the
fallback — if it works, a non-comparability footnote disappears from the latency table,
both results tables and a threat-to-validity row. If it does not, buffered REST with the
footnote stands. Remaining constraints: Deepgram REST caps at ~2K chars per request, so long-stratum
items chunk and reassemble with boundaries recorded; Cartesia concurrency is capped at 2–3;
Orpheus is `N/A-hosted` for D1 and takes a 5-item variance subset.

**D7 is a separate session per provider, not a by-product of adapter work.** The spec
measures "open docs → first audio in a fresh venv"; building a production adapter with
streaming capture, WAV finalisation and manifest wiring is a different task with a
different duration. Each provider therefore gets a ~30–45 minute throwaway hello-world
session, clocked, *before* its production adapter is written. **Deepgram's must be re-run**
— its adapter was built in Phase A, before D7 was defined, so its datapoint is otherwise
missing from a published column. Report times with the direction of the learning bias
stated (later providers benefit from earlier ones), and publish friction-event counts
alongside minutes since counts are less order-sensitive.

**R9 task:** while onboarding Fish, determine whether `s2.1-pro-free` and the paid string
share weights. Record the finding in the capability matrix; it becomes a footnote or a
caveat on every Fish quality row.

### Phase D — runner

- **Orchestrator:** async `httpx`, retry with backoff, rate-limit aware, content-hash
  cache (re-runs cost only changed items), spend cap, errors logged as data.
- **`--mode campaign`** — 75 items × 2 use cases × 6 providers = 900 files.
- **`--mode latency`** — 50 serial trials per provider (one request in flight),
  scheduled across ≥2 days and ≥2 times of day, from the pinned VM only; RTF on long
  items; serving region recorded. Orpheus skipped (N/A-hosted).
- **`--mode variance`** — 10 items × 2 use cases × 3 draws × 6 providers = **360
  generations**. All six run the full subset: Replicate's per-generation cost is ~$0.003,
  not the ~$0.08 an earlier draft assumed, so Orpheus's share is about $0.20 and the
  earlier 5-item reduction was unnecessary.
- **Admin:** `pages/2_Run.py` — pick corpus subset and providers, run, live progress.
- **Two pilots, because one cannot exist yet.** An end-to-end "toy frontier" needs D4
  (Phase F) on its y-axis, `cost.py` (Phase E) on its x-axis and `veval score`/`report`
  (Phase G) to render — none of which exist in week 1.
  - **Pilot-1 (week 1, ~$1):** 5 items × 6 providers → generation + `quality.py` +
    `hygiene.py`. Purpose: prove the pipeline runs end to end and check that gate
    thresholds discriminate at all. Any threshold that passes or fails everyone is amended
    and re-tagged `prereg-v1.1` before the campaign.
  - **Pilot-2 (end of week 2):** the toy frontier, once F and G stubs exist.
  - **The TTSDS2 split-half check moves off the pilot entirely.** The benchmark documents
    50–100 samples as sufficient; a 5-item pilot is far below that and each half further
    still, so a split-half result there would be noise. It runs on the first full
    per-provider campaign slice instead, averaged over ≥100 random splits rather than one
    arbitrary split.

### Phase E — analyzers

**Now native on Windows.** VERSA and NeMo are both gone; every remaining dependency has
Windows wheels. The devcontainer stays in the repo as an optional reproducibility
artifact for anyone who wants a pinned Linux environment, and is no longer on the
critical path. A GPU is still wanted — TTSDS2 plus two ASR judges over **~1,300 files**
(900 primary + 360 variance + pilot) is slow on CPU. Hardware is recorded in
`manifest.json`.

**Acceptance gate before any analyzer runs.** Every campaign WAV is decoded and checked:
header duration matches decoded duration within 1%, LUFS falls in a plausible range, VAD
finds speech, character counts are logged. Phase A shipped a defect where a streamed header
declared 44,737 seconds for a 2.8-second clip — which would have silently corrupted RTF,
VAD, loudness and the distributional score alike. That class of bug fails loudly here or
not at all. **For Fish this gate must be green before 2026-08-24**, since its audio cannot
be regenerated at $0 after the free window closes.

All analyzers are pure functions over the run store, re-runnable without regenerating
audio.

| Module | Produces |
|---|---|
| `wer.py` | Two-judge agreement WER per item and per provider (Parakeet-HF + faster-whisper, `jiwer`); **failure incidence** — % of items above the pre-committed threshold; **typed catastrophic-event counts** — drops, repetition loops, truncation, hallucinated content; flagged-file queue for manual listen |
| `quality.py` | TTSDS2 against the pre-registered reference set + Audiobox Aesthetics, per file and aggregated; **split-half stability value** per provider per use case |
| `hygiene.py` | Clipping, clicks, noise floor, VAD-based unnatural pauses, LUFS per file |
| `latency.py` | TTFA p50/p90 with trial count and spread; RTF on long items; serving region |
| `variance.py` | **Pooled within-provider SD on TTSDS2 and item WER across the 3 draws → the noise floor**; byte-identity check → determinism flag for D8 |
| `drift.py` | **Per-third TTSDS2 and hygiene on the 8 long narration items** → monotonic-degradation flag feeding the narration gate |
| `cost.py` | `pricing.yaml` × logged character counts → `cost_model.json`: $/1K words at 10K / 100K / 1M words per month, plus $/session. Code rather than a spreadsheet, because cost is a frontier axis and must regenerate on the drift re-run |

- **Admin:** `pages/3_Results.py` — browse runs, view metric tables.
- **Manual-listen queue is hard-timeboxed at 2 hours.** It is the item that historically
  eats Week 3.

### Phase F — human judgment layer

The only phase with an online component; everything else stays local.

- `human/loudness_normalize.py` → **−18 LUFS via pyloudnorm, mandatory before upload.**
- **Anchor recordings** — quiet room, decent mic, normalised like everything else; pilot
  A/B against the best TTS before locking (E8). Own voice by default; a friend's voice
  requires written consent, since anchor recordings would leave the machine.
- **Pair builder** — 7 systems (6 providers + anchor) → 21 pairs × 2 use cases × 5
  repetitions = **210 judgments target, 126 minimum**. Roughly two hours across 5–6
  sessions. Pairs are **randomised across sessions rather than blocked by provider** (R8),
  and written to a per-rater manifest.

- **The rating page runs locally in v1** — a static HTML page against a local audio
  directory. This serves an n=1 design fully, and it removes the hosting decision, the form
  backend, the token model and, critically, the audio-redistribution exposure: a public
  `/public` directory is world-readable regardless of any `?rater=` token, and publishing
  six providers' generated audio plus a human recording contradicts the "private results,
  no redistribution question" position in the spec's Appendix E. Remote raters are §10
  future work; when added, audio goes behind signed expiring URLs and a provider ToS review
  re-enters scope.
- **Bradley–Terry fit + bootstrap 95% CIs** (2,000 resamples) — the numbers the frontier
  charts depend on.
- **10% consistency re-judge** at least a week later; publish the consistency figure
  **with its session gap**.

### Phase G — decision layer and reporting

- Gate application → survivor list per use case.
- **Pareto frontiers with y-error bars.** Domination asserted only where D4 intervals do
  not overlap; overlapping pairs labelled **"no difference detected at this n"** — a
  first-class status alongside "on frontier", "dominated" and "gated".
- **Noise-floor rule applied** to every reported difference.
- **Cost axis** from `cost_model.json` (D6) — re-pull `pricing.yaml` and re-date-stamp it
  on analysis day before the frontier is rendered.
- Gate-robustness sweep at ±20%, reporting where the frontier changes.
- **Spearman ρ** for D3↔D4, D3↔HI, D4↔HI.
- HI snapshot loader (hand-scraped JSON) → Δ and "Reproduces?" columns.
- Report generator: markdown tables, matplotlib frontier charts, memo and case-study
  templates with data slots.
- **Admin:** `pages/4_Frontier.py` — interactive frontier plots.

---

## Phase A closeout — what was actually wrong (2026-08-05)

Preserved from v1 because it is evidence, not narrative. Four defects, two of them
silent; the last two would have corrupted Phase E metrics without ever failing visibly.

1. **CLI dead at import** — `cli.py` imported `DoctorResult`; `doctor.py` defines
   `DoctorReport`. `veval` had never successfully run.
2. **Devcontainer shadowed its own source** — `PYTHONPATH=/workspace/src` pointed at the
   stale copy the Dockerfile `COPY`s in for layer caching, overriding the editable
   install. *No source edit took effect without an image rebuild.*
3. **`postCreateCommand` uninstalled the analyzer stack** — synced `--extra admin --extra
   dev` without `--extra analyze`, and `uv sync` prunes extras it isn't given. It removed
   the torch/CUDA stack the Dockerfile had just spent 10+ minutes installing, then failed
   its own `import torch` check.
4. **Streamed WAVs declared a false duration** — Deepgram can't know the length when it
   emits the header, so it ships a placeholder `0x7FFFAC00`: **44,737 seconds declared for
   a 2.80-second clip.** RTF, silero-VAD, pyloudnorm and TTSDS2 all read duration from
   that header. Fixed via `finalize_wav_header()` in `adapters/base.py` — placed in the
   base class because every streaming adapter added in Phase C will hit it.

Also: `veval --version` unreachable without `invoke_without_command=True`; dead
`_guess_env_key` placeholder removed; ruff (12 errors) and mypy strict (5 errors) now
pass clean.

**Verified end-to-end:** `veval doctor` synthesises against Deepgram and writes
`manifest.json` + `api_log.jsonl` + a WAV that decodes to its true 2.76s. TTFA
~600–700ms, total ~1.8–2.0s across three runs.

**Outstanding:** one test red by design —
`test_manifest_records_a_stable_interpreter` fails until the interpreter fix
(`11ff01d`) lands. Note that with the devcontainer no longer mandatory (Phase E),
the fix should be verified on the **native** Windows environment as well; the
interpreter recorded in `manifest.json` must be a stable 3.11, not Ubuntu's
`3.11.0rc1`, wherever the campaign actually runs.

## Environment strategy

| Phase | Where to run |
|---|---|
| A – D | **Native OS** (Windows primary) with `uv sync --extra admin --extra dev` |
| E – G | **Native OS also works now.** `uv sync --extra analyze --extra admin --extra dev` pulls torch, TTSDS2, Audiobox, faster-whisper and HF-Parakeet — all Windows-compatible. GPU strongly recommended |
| Optional | **Devcontainer** retained as a pinned-Linux reproducibility artifact and fallback, not a requirement |

Same commands work in both. The switch is invisible to the code.

## Voting UI stack (Phase F)

| Piece | Choice (v1) |
|---|---|
| Hosting | **None — local static page**, opened from the filesystem |
| Audio storage | Local directory; nothing leaves the machine |
| Vote collection | Local CSV written by the page |
| Rater model | n=1. Multi-rater is §10 future work and would need its own fit, not pooled judgments |
| Consent | Anchor voice recorded with written consent (a third party, not the rater — see spec A.4) |

*Rationale for dropping the hosted stack: it existed to reach remote raters, who are future
work; it cost several hours the schedule does not have; and it published provider audio to
an open URL, contradicting the spec's own legal position.*

## Open decisions

**Resolved in v2:** analyzer backbone (VERSA dropped), ASR judge 2 (faster-whisper
locked, Canary rejected), environment strategy (native throughout), corpus size (75).

Still open:

- **Orpheus host:** Replicate (default, easier onboarding) vs Baseten — decide in Phase C
- **Formspree vs Basin:** free-tier and DX comparison — decide in Phase F
- **Anchor voice source:** own (no consent needed) vs friend (written consent) — decide in Phase F
- **TTSDS2 reference set:** chosen in Phase B, *validated* against the pilot in Phase D — may force a `prereg-v1.1` re-tag
- **Empty env keys:** `FISH_API_KEY`, `CARTESIA_API_KEY`, `ELEVENLABS_API_KEY`, `GOOGLE_API_KEY`. **Fish is the time-boxed one — the free window closes Aug 31.**

## Definition of done

- [ ] A stranger skimming the repo for 10 minutes can state the problem, the method's two cleverest ideas, and both recommendations
- [ ] Case study readable in 5 minutes; every claim traceable to a dated artifact
- [ ] `prereg-v1` tag predates **the first committed `analysis/` artifact and every `runs/*/MANIFEST.sha256`**, verified by `git log --diff-filter=A` and asserted in `veval report`
- [ ] **All four frontier charts** render **with error bars**; memos complete
- [ ] Consistency re-judge number **and its session gap** disclosed next to every D4 figure
- [ ] Noise floor published; no difference below the §3.4 significance rule reported as a difference
- [ ] TTSDS2 reference set named; split-half stability published
- [ ] Failure incidence published per provider
- [ ] Every "dominated" claim backed by a bootstrap CI on the pairwise D4 difference excluding zero
- [ ] Per-third drift analysis run, or the listener-fatigue column removed
- [ ] Spearman ρ published for D3↔D4, D3↔HI, D4↔HI
- [ ] Total spend ≤ $50, logged — or the overrun logged in `DEVIATIONS.md` with its cause
- [ ] Subscriptions cancelled
- [ ] Drift re-run scheduled (+4 weeks)

---

## Proposed CLAUDE.md amendments

Per meta-rule 1, these are **proposed, not written**. CLAUDE.md is never edited silently.

**Locked technical decisions — replace three rows, add two:**

| Piece | Current | Proposed |
|---|---|---|
| Analyzer backbone | VERSA (jiwer, TTSDS2, silero-VAD surfaced through it) | **Direct library calls** — jiwer · TTSDS2 · Audiobox · silero-VAD · pyloudnorm; Parakeet via HuggingFace |
| **Dev env** | WSL2 + Docker Desktop, CUDA base image | **Native Windows throughout; devcontainer optional** — this is one of the headline v2 changes and the current row now contradicts it |
| **CLI** | doctor / generate / analyze / score / report | unchanged — `invites` and the tokened voting model are cut from v1 with the hosted rating page |
| ASR judges | *(not recorded)* | **Parakeet RNNT 0.6B (HF, released version) + faster-whisper large-v3, locked.** Judges must differ in org, architecture family and training pipeline — Canary is not admissible as judge 2 |
| Statistics | *(not recorded)* | Bootstrap CIs on all D4 scores; noise-floor rule from the variance subset; Spearman for cross-metric agreement |

**Meta-rule 2 needs rewriting.** It currently hard-codes the three source-of-truth docs as
`voice_ai_eval_portfolio_edition.md` (WHAT), `voice_ai_eval_plan_v1_descoped.md` (HOW) and
the mermaid. Two of those are now archived — left as-is, the rule instructs every future
session to treat superseded documents as authoritative. Proposed replacement: **`voice_ai_eval_spec_v2.md` (WHAT + HOW), `IMPLEMENTATION_PLAN.md` (BUILD), `eval_harness_architecture.mermaid` (STRUCTURE).**

**Project overview — two stale lines:** status reads *"Planning complete; Phase A not yet
started"* (Phase A closed 2026-08-05) and budget reads *"~$30–45"* (now ~$36–47 plus
contingencies, spec §8).

**Reference documents — replace the superseded entries** with `voice_ai_eval_spec_v2.md`
and `EXTERNAL_REVIEW_2026-08-06.md`; move the old three to `archive/`. Also add a
four-line D1–D8 dimension summary: CLAUDE.md currently records the locked decisions and
the narrative bank but not the measurement scope, which makes the project read as thinner
than it is to anyone — or any session — starting from that file. That gap is not
hypothetical: an external reviewer working from CLAUDE.md alone concluded latency was
unmeasured, when D1 is the most rigorous dimension in the plan.

**Narrative bank — proposed additions:**

- Removed VERSA after choosing it. The tool picked to reduce dependency friction became
  the one forcing a Linux container — for five of its ninety-odd metrics. The lockfile was
  already doing the job VERSA was hired for. *(Second killed-my-own-decision moment,
  pairs with the weighted composite.)*
- Caught a swap that would have broken the two-judge design. Replacing faster-whisper
  with Canary would have escaped the Windows problem and quietly gutted the agreement
  rule — Canary and Parakeet share NVIDIA's encoder family and data pipeline. Judge
  independence is now a written constraint, not a lucky property.
- Measured our own noise floor. Ten items, three draws, six providers: the project can
  now state which differences it is not entitled to report. No competing eval publishes
  this.
- Put error bars on the money chart. An n=1 perceptual study that declares "dominated"
  without confidence intervals is exactly the thing a hostile reader dismantles first —
  so domination now requires the difference interval to exclude zero, and "no difference detected at this n"
  is a result we are willing to print.
- An external reviewer raised ten gaps before reading the plan; nine were already
  covered, several more rigorously than the reviewer's own recommendation. The tenth
  round — the one that came *after* reading — is the one worth publishing.
