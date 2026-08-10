# veval — voice AI provider evaluation harness

> _DRAFT — not yet the project's README. Draft for review; when
> approved, rename to `/README.md` and delete this note._

**An independently-audited evaluation of 8 commercial voice AI
providers across two production-realistic use cases, with the
methodology, code, deviations, and every intermediate artifact
in the same repo.**

---

## What this project produces

| Artifact | Where | What it says |
|---|---|---|
| **Case study** | `site/case_study.md` (rendered via `veval report`) | The story: which provider you pick for a support agent + long-form narration, why, and where the ranking is fragile |
| **Two decision memos** | `site/memo_conversational.md` · `site/memo_narration.md` | One-page recommendation per use case with rationale + not-recommended list |
| **Frontier charts** | `site/*.png` (Altair) · `site/interactive/*.html` (Plotly) | Quality-vs-cost + quality-vs-latency Pareto frontiers per use case with 95% bootstrap CIs on every point |
| **Reproducibility receipts** | `analysis/*.json` (committed) · git tags `prereg-v1` → `prereg-v1.9` · `DEVIATIONS.md` | Every result traceable to a git commit that predates it |
| **DX friction log** | `dx/friction_log.md` | Per-provider onboarding notes + cross-provider engineering patterns (0xFFFFFFFF placeholder headers, per-minute throttle backoff, cache put/get symmetry) — publishable observations that survive the specific providers used |

---

## Headline findings

_(populated after Phase 3 — the Bradley-Terry rating campaign — completes)_

- **Support agent recommendation**: `[TBD]` — [BT strength ±CI], on the cost frontier at [$X/1K words]
- **Long-form narration recommendation**: `[TBD]` — [BT strength ±CI], on the cost frontier at [$X/1K words]
- **Reproduces HI's #1?**: `[TBD]` — Δ vs the public leaderboard
- **Portfolio quotables**:
  - Wav2vec2 as the second WER judge is noisier than newer ASRs, so absolute failure incidence is inflated but the RELATIVE ranking is preserved — Orpheus is 5× noisier than any other provider on item-level WER variance, matching its overall bottom-of-the-frontier position
  - Every provider is non-deterministic across draws — no provider produces byte-identical output. **The whole variance analysis exists because of this fact.**
  - `[N]` of 8 providers were on the cost frontier before the CI-domination rule; `[M]` after — the difference is providers whose quality advantage was inside noise

---

## Method in one paragraph

Eight providers evaluated across two use cases (conversational support
agent + long-form narration) on a 75-item pre-registered corpus per
use case. **Four measurement dimensions**: (D1) latency via TTFA
p50/p90 from 50 serial trials per provider; (D2) two-judge WER with
Meta AI wav2vec2 + OpenAI Whisper agreement (judges deliberately
chosen from different orgs, architecture families, and training data
per spec §4.2); (D3) distributional quality via Audiobox Aesthetics
production-quality + content-enjoyment axes; (D4) blind pairwise A/B
with a human anchor fitted via Bradley-Terry with clustered-bootstrap
95% CIs. **Corpus, gates, voices, models, and analyzer parameters
frozen in git tag `prereg-v1` before any results existed**; amendments
logged in `DEVIATIONS.md` with rationale and re-tagged (`v1.1` through
`v1.9` at time of writing). **Domination on the frontier is asserted
only when the bootstrap CI on the pairwise BT difference excludes
zero** — otherwise the pair is reported as _"no difference detected at
this n"_ as a first-class result. Cost from `pricing.yaml` re-pulled
on analysis day. Total campaign spend ~$14 across 8 providers.

Full method: `documentation/voice_ai_eval_spec_v2.md`

---

## Portfolio-worthy engineering craft

The write-up is one thing; the receipts are another. These are the
moments the project itself created (all committed as git artifacts,
none reconstructed after the fact):

- **Killed my own weighted-composite scoring in the planning phase** and
  replaced it with pre-committed gates + Pareto frontiers. Weights are
  always arguable; gates + git tag are falsifiable. (`documentation/DECISION_CHANGELOG.md`)
- **Dropped VERSA as the analyzer backbone** _after_ picking it, when
  I discovered it was forcing a Linux container for 5 of its 80
  metrics that were already covered by direct library calls. Second
  killed-my-own-decision moment.
- **Caught a would-have-been-fatal ASR-judge swap** during config
  review: replacing faster-whisper with Canary would have gutted the
  agreement rule because Canary and Parakeet share NVIDIA's encoder
  family and training data. Judge independence is now a written
  constraint, not a lucky property.
- **Wav2vec2 substitution when Parakeet couldn't load** — spec's
  original judge 1 was Parakeet RNNT via HuggingFace transformers, but
  the released `transformers 4.x` doesn't register that architecture
  class (NVIDIA ships Parakeet through NeMo). Rather than take on the
  NeMo dep cliff, swapped to wav2vec2-large-robust; logged as D-010,
  re-tagged `prereg-v1.9`. See `DEVIATIONS.md`.
- **WAV acceptance gate paid for itself day one of Phase E.** First
  live run flagged 3 defects — Cartesia's `LIST` metadata chunk,
  OpenAI's missing `finalize_wav_header()`, Speechify writing a JSON
  envelope to `.wav` files. All fixed before any analyzer saw poisoned
  audio. (`dx/friction_log.md`)
- **Measured the runner's own thread-safety bug.** First Path B
  canonical rollup showed 1,200 files on disk but only 1,194 rows in
  `api_log.jsonl` — `Run.log_api` was racing on concurrent appends
  (POSIX-atomic-append assumption doesn't hold on Windows). Fixed with
  a `threading.Lock`; verified 1200/1200. Logged as a cross-platform
  pattern in the friction log.
- **Fixed Replicate's per-minute throttle right.** Runner's default 1s→2s→4s
  exponential backoff never reached Replicate's 60-second reset
  window, so 10 items stayed permanent-failed across a re-run. Added
  `retry_after_s` to `ProviderError`; adapter defaults to 60s on 429.
  Portable-across-providers lesson: exponential backoff is the wrong
  knob for fixed-window throttles.

---

## Quick tour of the repo

```
├── configs/                 # Pre-registered YAMLs (git-tagged prereg-v1.x)
│   ├── providers.yaml       # 8 providers × endpoints × env keys
│   ├── voices.yaml          # Locked voice + model per (provider, use_case)
│   ├── gates.yaml           # Per-use-case gates + robustness sweep points
│   ├── analyzers.yaml       # TTSDS2/Audiobox pins + WER judge revisions
│   └── pricing.yaml         # Published rates per provider, date-stamped
├── corpus/                  # 75 items per use case + 10-item variance subset
├── src/veval/
│   ├── adapters/            # One file per provider, uniform httpx transport
│   ├── runner/              # Async runner + spend cap + content-hash cache
│   ├── analyze/             # 8 analyzers (acceptance / hygiene / latency /
│   │                        #   cost / wer / quality / variance / drift)
│   ├── human/               # Loudness norm + pair builder + Bradley-Terry
│   ├── score/               # Gates → survivors → Pareto with CI domination
│   ├── report/              # Markdown tables + Plotly / Altair charts + memos
│   └── admin/               # Streamlit — 5 pages, thin wrapper over CLI
├── analysis/                # Per-run analyzer outputs (JSON, committed)
├── DEVIATIONS.md            # Every amendment with reason + prereg re-tag
├── dx/friction_log.md       # D7 developer-experience log
└── documentation/
    ├── voice_ai_eval_spec_v2.md
    ├── IMPLEMENTATION_PLAN.md
    └── voice_ai_eval_execution_runbook.md
```

Two front doors, one implementation: `veval <cmd>` in the terminal or
`streamlit run src/veval/admin/app.py` in a browser tab.

---

## Three ways to use this repo

### 1. Just look at the results (~5 min, no setup)

- Read `site/case_study.md` for the story
- Read `site/memo_conversational.md` + `site/memo_narration.md` for the
  recommendations
- Look at `analysis/campaign-<latest>/*.json` for the raw analyzer
  outputs — every number in the case study traces to one of these
- `DEVIATIONS.md` for what changed pre-campaign and why

### 2. Rerun the analysis on the committed audio (~15 min + model downloads)

Everyone with a copy of this repo can regenerate `analysis/` and
`site/` from `runs/` without spending a cent, once model downloads are
cached:

```
uv sync --extra analyze --extra admin --extra dev
uv run veval analyze <campaign_run_id>  # produces analysis/*.json
uv run veval rate fit <judgments.csv>   # produces analysis/bt_fit.json
uv run veval score <campaign_run_id>    # produces analysis/score.json
uv run veval report                     # produces site/*
```

_Note: `runs/*/audio/` is gitignored (regenerable + large). To
truly regenerate scores from raw audio, run a fresh campaign per
step 3 below._

### 3. Run a fresh campaign (~$14 + ~2 days part-time)

See `documentation/voice_ai_eval_execution_runbook.md` for the
step-by-step. Setup requires accounts + credits at all 8 providers
(~$20 up front) and ~45 minutes of anchor voice recording. Not
recommended unless you're forking the eval to test a different corpus
or provider set.

---

## Reference documents

**Read in this order for a full picture:**

1. `documentation/voice_ai_eval_spec_v2.md` — the WHAT + HOW spec
2. `documentation/IMPLEMENTATION_PLAN.md` — phase-by-phase build history
3. `DEVIATIONS.md` — every amendment (v1 → v1.9), with reasons
4. `dx/friction_log.md` — per-provider onboarding + cross-provider patterns
5. `documentation/voice_ai_eval_execution_runbook.md` — post-build campaign steps

**Skip to these if you only want to reproduce or extend:**

- `.env.example` — required environment variables
- `configs/` — pre-registered decisions in YAML
- `documentation/voice_ai_eval_tester_guide.md` — invite copy for
  remote raters (§10 future work)

---

## Status + stop condition

**Current status**: campaign complete for 7 of 7 analyzer stages;
Bradley-Terry rating in progress; case study renders. `prereg-v1.9`
tagged.

**Stop condition** (from `CLAUDE.md`): this is a portfolio project,
not a company. After 3-4 monthly drift re-runs the story is told;
either wind down with a final changelog + "archived as of [date]"
banner, or consciously continue with a specific reason. **Do not let
this become the untended stale leaderboard the project critiques.**

---

## Author

Neeraj Gera · [LinkedIn](TBD) · Built native on Windows 11 with
[Claude Code](https://claude.com/claude-code) as pair-programming
copilot.
