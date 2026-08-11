# Implementation gap — current state vs plan v2

Snapshot date: **2026-08-06**. Companion to
[DECISION_CHANGELOG.md](DECISION_CHANGELOG.md) (which explains *why* the
plan changed) — this doc records **what is built vs what plan v2 calls
for**, so nothing is missed at the transition from Phase A → Phase B.

Legend:

- ✅ **Aligned** — exists and matches v2 shape
- 🟢 **Aligned with caveat** — exists but v2 needs an incremental
  extension (not a rework)
- 🟡 **Missing (planned for later phase)** — not built yet, no rework
  needed, will land on schedule
- 🟠 **Stale / contradicts v2** — exists but v1-shaped; will actively
  mislead if left uncorrected
- 🔴 **Blocker for next phase** — must be addressed before Phase B can
  finish or the Fish deadline can be met

---

## Root-level artifacts

| Artifact | Plan v2 says | Current state | Status | Action |
|---|---|---|---|---|
| `pyproject.toml` | uv-managed; base + `analyze`/`admin`/`dev` extras | Exists, matches | ✅ | — |
| `uv.lock` | Committed — pins the measuring instrument | Exists, committed | ✅ | — |
| `.env` / `.env.example` | Standard secrets discipline | Both exist; `.env` gitignored | ✅ | — |
| `.gitignore` | Includes `runs/`, `analysis/`, etc. | Correct | ✅ | — |
| `CLAUDE.md` | Reflects v2 locked decisions | v1 shape — multiple stale rows | 🟠 | See CLAUDE.md section below |
| `DEVIATIONS.md` | Created on first deviation | Not present | 🟡 | Create when needed — no deviation logged yet |
| `.devcontainer/` | Optional reproducibility artifact, not required | Present and functional | 🟢 | Update comment/README language to reflect optional status |

## Documentation folder

| File | Plan v2 says | Current state | Status | Action |
|---|---|---|---|---|
| `voice_ai_eval_spec_v2.md` | Single source of truth (WHAT + HOW) | Exists (1082 lines) | ✅ | — |
| `IMPLEMENTATION_PLAN.md` | v2, references EXTERNAL_REVIEW | Exists (v2) | ✅ | — |
| `eval_harness_architecture.mermaid` | v2 with weights.yaml removed, DESK box added, analyzers.yaml added | Exists, v2 | ✅ | — |
| `DECISION_CHANGELOG.md` | (new — this planning cycle) | Just created | ✅ | — |
| `IMPLEMENTATION_GAP.md` | (this file) | Just created | ✅ | — |
| `EXTERNAL_REVIEW_2026-08-06.md` | Referenced by plan v2 and by R1–R10 findings | **Missing** | 🔴 | Either author it or remove references from plan v2 |
| `voice_ai_eval_execution_runbook.md` | Referenced by plan v2 (line 17) | In `archive/` only | 🟠 | Restore to `documentation/` or update plan reference |
| `voice_ai_eval_tester_guide.md` | Referenced in plan repo layout (line 60) | In `archive/` only | 🟠 | Restore or drop the reference |
| `voice_ai_test_suite_spec.md` | Referenced in plan repo layout (line 61) | In `archive/` only | 🟠 | Restore or drop the reference |
| `archive/` | Superseded v1 docs kept as provenance | Contains 6 .md + 5 .docx files | ✅ | — |
| `documentation/*.docx` | Corpus source (referenced by extract_corpus.py) | Files under `archive/` | 🟠 | Corpus extractor needs to point at `archive/`, or files need to move back |

**Judgment call on archived docs vs plan references:** the runbook and
tester_guide were archived when v1 was superseded, but the plan v2 still
lists them as active references. Either restore them (cheap) or amend
the plan (also cheap). No functional blocker either way; just a doc
inconsistency to close.

## `configs/` folder

Plan v2 calls for five config files. Only one exists.

| File | Plan v2 says | Current state | Status | Action |
|---|---|---|---|---|
| `providers.yaml` | All 6 providers with model strings, env keys | Phase A stub — Deepgram only | 🟡 | Phase B: add remaining 5 |
| `voices.yaml` | Locked voice per provider × use case with reasoning | Not present | 🟡 | Phase B |
| `gates.yaml` | Per-use-case gates + noise-floor rule + WER threshold + dBFS thresholds, one-line rationales | Not present | 🟡 | Phase B — see spec §5 for the draft set |
| `analyzers.yaml` | TTSDS2 reference set + rationale + min sample size + split-half absolute threshold + judge revisions | Not present | 🟡 | Phase B — this is a new file introduced in v2 (change 9 in DECISION_CHANGELOG) |
| `pricing.yaml` | Published rates per provider, date-stamped per cell | Not present | 🟡 | Phase B (Week 1 pass) — re-pulled on analysis day per D6 rule |

**Pydantic loaders in `config.py`:** models exist for `ProvidersFile`,
`VoicesFile`, `GatesFile`. **Models for `AnalyzersFile` and
`PricingFile` do not exist yet** — they're new in v2. Cheap to add
during Phase B when the YAMLs are being authored.

## `corpus/` folder

Plan v2 calls for three files. Directory does not exist.

| File | Plan v2 says | Current state | Status | Action |
|---|---|---|---|---|
| `conversational.yaml` | 60 novel + 15 probe = 75 items | Not present | 🟡 | Phase B step 0 |
| `narration.yaml` | 60 novel + 15 probe = 75 items | Not present | 🟡 | Phase B step 0 |
| `variance_subset.yaml` | 10 items per use case, frozen in prereg | Not present | 🟡 | Phase B step 4 (change 5 in DECISION_CHANGELOG) |

## `scripts/` folder

| File | Plan v2 says | Current state | Status | Action |
|---|---|---|---|---|
| `extract_corpus.py` | python-docx → YAML | Not present | 🟡 | Phase B step 0 |

## `src/veval/` — code

### Core scaffolding ✅

| Module | Plan v2 says | Current state | Status |
|---|---|---|---|
| `__init__.py` | Package init | Exists | ✅ |
| `cli.py` | Typer app with doctor / generate / analyze / invites / score / report | Only `doctor` wired; other commands not yet added but structure ready | 🟢 |
| `config.py` | Pydantic models + loaders for all 5 config files | Has models for providers, voices, gates. **Missing analyzers, pricing** | 🟢 |
| `doctor.py` | Shared by CLI + Streamlit | Exists, working | ✅ |
| `store/run_store.py` | Immutable `runs/<run_id>/` writer | Exists, working | ✅ |
| `adapters/base.py` | ABC + shared types + `finalize_wav_header()` | Exists, includes the Phase A defect fix | ✅ |
| `adapters/deepgram.py` | First adapter | Exists, working | ✅ |

### Adapters — Phase C ⬜

| Adapter | Status | Note |
|---|---|---|
| `deepgram.py` | ✅ built | Off-index control |
| `fish.py` | 🟡 not built | **Priority — Fish free window closes 2026-08-31 (25 days out)** |
| `google.py` | 🟡 not built | D1 must run on buffered REST (§3.1 constraint); needs to be enforced in code |
| `cartesia.py` | 🟡 not built | Serialise latency trials — enforce concurrency=1 in the adapter or runner |
| `elevenlabs.py` | 🟡 not built | Biggest cost line (~$22); run last |
| `orpheus.py` | 🟡 not built | Replicate-hosted; latency scored N/A-hosted |

### Runner — Phase D ⬜

| Module | Plan v2 says | Current state | Status |
|---|---|---|---|
| `runner/` package | Async httpx orchestrator + latency mode + **variance mode** (new in v2) | Directory does not exist | 🟡 |

**Note:** variance mode is new in v2 (change 5 in DECISION_CHANGELOG).
Runner design needs three modes from day one, not two.

### Analyzers — Phase E ⬜ (**structurally different from v1**)

| Module | Plan v2 says | Current state | Status |
|---|---|---|---|
| `analyze/` package | Six modules, direct library calls, no VERSA | Directory does not exist | 🟡 |
| `analyze/wer.py` | Two-judge (Parakeet-HF + faster-whisper) + failure incidence + typed catastrophic-event counts | — | 🟡 |
| `analyze/quality.py` | TTSDS2 vs pinned reference + Audiobox + split-half stability | — | 🟡 |
| `analyze/hygiene.py` | silero-VAD + pyloudnorm + clipping | — | 🟡 |
| `analyze/latency.py` | TTFA p50/p90 + RTF + region | — | 🟡 |
| `analyze/variance.py` | Pooled within-provider SD → noise floor; byte-identity → determinism | — | 🟡 |
| `analyze/drift.py` | Per-third quality drift on long items | — | 🟡 |
| `analyze/cost.py` | `pricing.yaml` × logged chars → `cost_model.json` | — | 🟡 |

**Structural implication:** v1 planned 4 analyzer modules; v2 plans 6 +
`cost.py`. Anyone starting Phase E from memory of v1 would build the
wrong scaffolding. This is the single largest v1→v2 delta in the code
scope.

### Human layer — Phase F ⬜

| Module | Plan v2 says | Current state | Status |
|---|---|---|---|
| `human/` package | Normalize + pair builder + BT fit + **bootstrap CI** (new in v2) + randomised session ordering | Directory does not exist | 🟡 |

### Scoring / reporting — Phase G ⬜

| Module | Plan v2 says | Current state | Status |
|---|---|---|---|
| `score/` package | Gates + Pareto + **CI-gated domination** (new in v2) + robustness + **Spearman** (new in v2) | Directory does not exist | 🟡 |
| `report/` package | Tables (with CI cols and Fail % col — new in v2) + charts (with error bars — new in v2) + memo templates | Directory does not exist | 🟡 |

### Admin panel — Streamlit

| Page | Plan v2 says | Current state | Status |
|---|---|---|---|
| `app.py` | Landing | Exists | ✅ |
| `pages/1_Doctor.py` | Interactive doctor | Exists, working | ✅ |
| `pages/2_Run.py` | Wraps `veval generate` | Not present | 🟡 (Phase D) |
| `pages/3_Results.py` | Wraps `veval analyze` results view | Not present | 🟡 (Phase E) |
| `pages/4_Frontier.py` | Interactive Pareto plots with error bars | Not present | 🟡 (Phase G) |

## `tests/` folder

| Test file | Purpose | Status |
|---|---|---|
| `conftest.py` | Pytest fixtures | ✅ |
| `test_config.py` | Config `extra="forbid"` validation | ✅ |
| `test_run_store.py` | Run-store invariants | ✅ |
| `test_wav_header.py` | `finalize_wav_header()` regression net | ✅ |
| `test_manifest_records_a_stable_interpreter` (in one of the above) | Red by design until interpreter fix lands | 🟢 documented in Phase A closeout |

**No test yet for:** Pydantic models for `AnalyzersFile` / `PricingFile`
(don't exist yet), variance-noise-floor math, split-half divergence,
Bradley-Terry bootstrap CI, CI-domination rule. Each becomes a
regression test as its module lands.

## `voting/` folder (Phase F)

Not present. Vercel project scaffolding is Phase F work — not a gap.

## `dx/` folder

Plan v2 calls for `dx/friction_log.md` (D7, written live during Phase C).
Not present. Create when Phase C starts — the log **cannot be
reconstructed later**, so this is a Phase C day-1 task, not a Phase B
one.

---

## CLAUDE.md — proposed edits (per meta-rule 1)

CLAUDE.md is stale in six places. IMPLEMENTATION_PLAN.md v2 already
enumerates the proposed amendments (its "Proposed CLAUDE.md amendments"
section). Consolidated here as an action list:

| # | Section | Current | Proposed |
|---|---|---|---|
| 1 | Meta-rule 2 | Source-of-truth docs = `voice_ai_eval_portfolio_edition.md`, `voice_ai_eval_plan_v1_descoped.md`, mermaid | = `voice_ai_eval_spec_v2.md` (WHAT + HOW), `IMPLEMENTATION_PLAN.md` (BUILD), mermaid (STRUCTURE) |
| 2 | Project overview → Status | "Planning complete; Phase A not yet started" | "Phase A closed 2026-08-05; Phase B (configs + corpus + prereg) next" |
| 3 | Project overview → Timeline/budget | "~$30–45" | "~$36–47; worst case ~$69 with contingencies" (see change 11 in DECISION_CHANGELOG) |
| 4 | Locked → Dev env | "WSL2 + Docker Desktop, CUDA base image" | "Native Windows throughout; devcontainer optional reproducibility artifact" |
| 5 | Locked → Analyzer backbone | "VERSA (jiwer, TTSDS2, silero-VAD surfaced through it)" | "Direct library calls — jiwer, TTSDS2, Audiobox, silero-VAD, pyloudnorm; Parakeet via HuggingFace" |
| 6 | Locked → CLI | "doctor / generate / analyze / score / report" | "+ `invites` (Phase F)" |
| 7 | Locked (new rows) | *(missing)* | Add: **ASR judges** — Parakeet TDT (HF) + faster-whisper large-v3, locked. Judges must differ in org, architecture family, training pipeline (Canary inadmissible as judge 2). **Statistics** — bootstrap CIs on all D4 scores; noise-floor rule from variance subset; Spearman for cross-metric agreement |
| 8 | Reference documents | Lists 5 files under old paths | Replace with current three + note archive |
| 9 | Narrative bank | Existing entries | Add the four new ones proposed in IMPLEMENTATION_PLAN.md v2 (VERSA drop, Canary catch, noise-floor, error-bars-on-money-chart) |
| 10 | Change log | Ends 2026-08-04 | Add 2026-08-05 (Phase A closed) and 2026-08-06 (v2 adopted) entries |

Per meta-rule 1, these are proposed only. **Recommend accepting all
ten as one batch** — leaving any of them stale risks a future session
citing archived docs as authoritative or building the wrong analyzer
shape from CLAUDE.md's VERSA line.

---

## Priority-ordered action list

Ordered by what unblocks the next milestone. The next milestone is the
$1 pilot (Phase D exit), which is upstream of every Fish-window
constraint.

### Do first (before Phase B starts)

1. 🔴 **Resolve EXTERNAL_REVIEW_2026-08-06.md.** Either author it (the
   R1–R10 findings need a home) or edit v2 plan/spec to remove
   references. Non-negotiable — the plan currently cites a doc that
   does not exist.
2. 🟠 **Reconcile archived-vs-referenced docs.** Runbook and tester
   guide either come out of archive or leave the plan's reference list.
   Cheap either way.
3. 🟠 **Update CLAUDE.md with the ten edits above.** Prevents future
   sessions from wiring the wrong analyzer stack.

### Phase B (blocking Fish window)

4. 🟡 **Author `configs/pricing.yaml`** and its Pydantic model — new
   in v2, needed by cost.py and by the $1 pilot's frontier chart.
5. 🟡 **Author `configs/analyzers.yaml`** and its Pydantic model — new
   in v2, needed by quality.py's split-half validation.
6. 🟡 **Author `configs/voices.yaml`, `gates.yaml`.** Gates must
   include the noise-floor rule and the WER failure threshold.
7. 🟡 **Extract corpus** — 75 per use case per §3.3 strata table.
8. 🟡 **Select `variance_subset.yaml`** — 10 items per use case across
   strata; frozen in prereg.
9. 🟡 **`git tag prereg-v1`.**

### Phase C (Fish first)

10. 🟡 **Build Fish adapter** first (free window).
11. 🟡 **Start `dx/friction_log.md`** on the same day — cannot be
    reconstructed later.
12. 🟡 **Google, Cartesia, ElevenLabs, Orpheus** adapters in that order.

### Phase D–G

13. 🟡 Runner with **three modes** (campaign / latency / variance),
    not two.
14. 🟡 Analyzers as **six modules + cost.py**, not four.
15. 🟡 Human layer with bootstrap CI and randomised session ordering
    from day one.
16. 🟡 Scoring with CI-gated domination and Spearman.

---

## Summary

- **Phase A is aligned with v2.** No rework needed — the shape of what
  was built (adapter base, run store, doctor, CLI, Streamlit skeleton)
  is unchanged v1 → v2. The `finalize_wav_header()` fix is in the right
  place.
- **Every subsequent phase has v2-shape changes that must land at
  build time, not as retrofits.** The runner needs a third mode; the
  analyzer package is 6+1 modules not 4; the human layer needs
  bootstrap CIs from day one; the scoring layer needs CI-domination
  and Spearman. None are big lifts individually; all are easy to miss
  if working from v1 memory.
- **Three doc-level blockers exist before Phase B can cleanly start:**
  EXTERNAL_REVIEW existence, archived-doc references, and the ten
  CLAUDE.md edits. All are cheap.
- **The Fish deadline (2026-08-31) is 25 days out.** Phase B + Phase C
  (Fish adapter + $1 pilot) is the critical path.
