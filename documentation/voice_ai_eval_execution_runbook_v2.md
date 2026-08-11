---
title: Execution Runbook v2 — post-Phase-2 measurement plan
project: Voice AI Provider Evaluation (portfolio edition)
assumes: Phase 0, 1, 2 from runbook v1 complete; git tag `prereg-v1.9`; `analysis/*` populated for 3 runs
supersedes: `voice_ai_eval_execution_runbook.md` phases 3-5 only (0-2 stand as historical)
authored: 2026-08-10
---

# Execution Runbook v2 — from "8 analyzers ran" to "paper is defensible"

This document supersedes phases 3-5 of the v1 runbook and inserts two new
phases (2b and 2c) that materially strengthen the report's rigor story.
Phases 0-2 of v1 stand as executed history — do not re-run them.

**Motivation for v2** — after Phase 2 completed, two review-level
concerns surfaced:

1. **Single-quality-signal dependence.** We ran Audiobox alone (TTSDS2
   deferred per plan v2 line 267). Rankings float without a
   cross-signal check. Adding DNSMOS (via speechmos; UTMOS attempted, blocked on Windows) gives us four quality
   signals from three independent training pipelines — triangulation
   becomes possible.
2. **No robustness on the outliers.** Every headline claim
   (Cartesia clipping, Orpheus WER, Speechify PQ leadership,
   ElevenLabs latency lead, etc.) rests on one measurement pass. A
   symmetric verification pack turns "we measured once" into "we
   measured once + independently re-checked every extreme claim." Rare
   in commercial-eval writeups. Publishable methodology by itself.

Also: the BT rating campaign scope is reduced (D-011 in DEVIATIONS —
drop human anchor, keep 168 judgments; see §3 below for rationale).

**Total incremental effort**: ~2 days part-time, ~$1 spend.

---

## Recap: what v1's Phase 0-2 delivered

| Artifact | Status |
|---|---|
| Canonical rollup campaign `campaign-20260809T204608Z` | 1200/1200 acceptance-clean, `manifest.extras.provenance.cache_hits=1200` |
| Variance run `variance-20260809T205319Z` | 480/480 acceptance-clean, fresh (non-cached) |
| Latency run `latency-20260809T222356Z` | 200/200 acceptance-clean, single-session (2nd session pending in T5) |
| Cheap analyzers on all 3 runs | acceptance / hygiene / latency / cost — all green |
| WER on campaign + variance | wav2vec2-large-robust + faster-whisper large-v3, 1200 + 480 items transcribed |
| Quality on campaign + variance | Audiobox (TTSDS2 skipped) |
| Variance rollup | 16 rows, all providers non-deterministic, Orpheus 5-10× noisiest |
| Drift analysis | 1 flag: ElevenLabs L03 fadeout |
| First cross-provider outlier picture | see the "cross-provider outlier synthesis" section in this session's transcript |
| prereg tag v1.9 | pushed to origin |

Cumulative spend to end of Phase 2: **~$14** (of $30 budget).

---

## Phase 2b — Analyzer expansion (DNSMOS (via speechmos; UTMOS attempted, blocked on Windows)) · ~half day

**Goal:** bring the quality-signal count from 2 to 4. Enables:
- Triangulation on Orpheus's split ranking (Audiobox-only conv bottom / narr 2nd) — see if DNSMOS (via speechmos; UTMOS attempted, blocked on Windows) agree
- NISQA's discontinuity axis independently corroborates (or refutes)
  Cartesia's hygiene-side clipping finding
- Stronger D3↔D4 Spearman correlation once BT lands

### 2b.1 Dependency picks (~10 min — done 2026-08-10)

**PyPI dep check** (done 2026-08-10):

```powershell
curl -s -o NUL -w "nisqa: %{http_code}`n"     https://pypi.org/pypi/nisqa/json
curl -s -o NUL -w "utmos: %{http_code}`n"     https://pypi.org/pypi/utmos/json
curl -s -o NUL -w "speechmos: %{http_code}`n" https://pypi.org/pypi/speechmos/json
```

Result → all three published on PyPI, but NISQA 2.0.post2 hard-pins
`torch==2.2.1` (breaks our `torch 2.4.1+cpu` envelope + cascade-breaks
ttsds/s3prl). Revised plan per RESEARCH_LOG D-B: **use utmos +
speechmos instead**. Six quality signals from three independent
pipelines (Audiobox / UTMOS / Microsoft DNSMOS P.835 via ONNX). See
RESEARCH_LOG D-B for the trade-off rationale.

Add to `pyproject.toml` `analyze` extra:

```toml
"utmos>=1.1,<2.0",       # SSL-based overall MOS, from sarulab-speech
"speechmos>=0.0.1,<0.1", # Microsoft DNSMOS P.835 (SIG/BAK/OVRL) + PLCMOS/AECMOS, ONNX-based
```

Then:

```powershell
uv sync --extra analyze --extra admin --extra dev
```

If the resolution breaks the torch pin (unexpected — utmos declares
no version pin, speechmos is ONNX-only), diagnose per the ttsds
cliff pattern; fallback is to skip whichever fails and document as
D-011 rationale.

### 2b.2 Extend `quality.py` (~2 hrs coding + tests)

- Add `_load_utmos()` + `_load_nisqa()` lazy loaders (same pattern as
  Audiobox loader)
- Add `_utmos_score_for(record, predictor) -> float` + `_nisqa_axes_for(record, predictor) -> dict[str, float]`
  (NISQA has 4 axes: MOS overall, noise, coloration, discontinuity, loudness)
- Extend `FileQuality` dataclass with `utmos: float | None` and
  `nisqa: dict[str, float]` fields
- Extend `_aggregate_audiobox` to `_aggregate_quality` producing means
  per (provider, use_case) for all quality signals
- Update `run()` to invoke DNSMOS (via speechmos; UTMOS attempted, blocked on Windows) per file, aggregate, write
  extended JSON
- Update tests (`tests/test_quality.py`) with monkeypatches for the
  new loaders; assert schema-shape

Pattern: mirror the Audiobox integration exactly. Keep the additions
opt-in via `--skip-utmos` / `--skip-nisqa` CLI flags for iterative dev.

### 2b.3 Re-run quality stage against existing runs (~1-2 hrs compute)

Models pre-download on first run; ~200 MB + ~300 MB respectively.

```powershell
uv run veval analyze campaign-20260809T204608Z --stages quality --skip-ttsds
uv run veval analyze variance-20260809T205319Z --stages quality --skip-ttsds
```

Expected outputs: extended `quality.json` per run with DNSMOS (via speechmos; UTMOS attempted, blocked on Windows)
per-file scores and per-provider means.

### 2b.4 Cross-metric agreement analysis (~1 hr)

Produce a table + Spearman-ρ matrix per use case:

- **Table**: for each provider, rank on {Audiobox PQ, Audiobox CE, UTMOS, NISQA-MOS}
- **Matrix**: pairwise Spearman ρ across the 4 quality signals across 8 providers
- **Divergences**: any provider where the 4 signals disagree on rank
  by ≥3 positions → flag as a "signal-dependent" ranking (weaker
  confidence)

Write findings to `RESEARCH_LOG.md` finding-F-8 (see companion doc).

### 2b.5 New-outlier scan (~30 min)

NISQA's discontinuity axis likely surfaces Cartesia clipping as a
quality-side finding. Any new outliers (e.g., providers with high
NISQA-noise or low UTMOS-naturalness that weren't visible in
Audiobox alone) get added to the Phase 2c verification pack.

### Exit criteria (Phase 2b)

- [ ] `quality.json` on campaign run has 4 quality signals populated
      per (provider, use_case)
- [ ] Cross-metric agreement table + Spearman ρ matrix in RESEARCH_LOG
- [ ] Any new outliers appended to §2c test pack
- [ ] DEVIATION D-011 logged if `audiobox_axes_reported`
      pre-registration is amended to include DNSMOS (via speechmos; UTMOS attempted, blocked on Windows)
- [ ] prereg tag re-cut to v1.10 if D-011 lands

---

## Phase 2c — Outlier verification test pack · ~4 hrs, ~$1 spend

**Goal:** for every outlier claim from Phase 2 (winners AND losers),
run one targeted test that can *confirm* or *refute* the finding on
fresh data. Symmetric treatment. Verdicts feed the case study's
"Independent verification" section (spec §7 "results" analog).

**Design principles:**

1. **Hypothesis + falsifiable success criterion stated BEFORE regeneration** — prevents "we saw what we wanted to see"
2. **Fresh calls, no cache** — different day/time where relevant
3. **Winner-side tests get the same scrutiny as loser-side** — kills the "cherry-picked eliminations" critique
4. **Verdict column: Confirmed / Refuted / Inconclusive** — three outcomes, not two
5. **Per-test JSON artifact in `analysis/verification/T{N}.json`** so the paper's supplementary materials link straight to raw evidence

### Test roster (updated post-2b — reshuffled after F-8 cross-metric findings)

**Roster changes vs pre-2b draft** (dated 2026-08-11):

- **T1 downgraded** — 2b's DNSMOS refusal rate (43%/49% Cartesia) is an independent-pipeline corroboration of the hygiene clipping finding on non-overlapping code paths (F-4a). Regenerating 20 more Cartesia items to re-count clipped samples adds no new information. Downgraded from regen to "cite the 2b evidence in the memo."
- **T3 retired** — spec exit criterion satisfied by 2b: DNSMOS OVRL ranks Orpheus #2 on narration (criterion was "top-3"). Direction of Audiobox's conv→narr improvement confirmed by all 4 DNSMOS axes; magnitude gap (Audiobox +0.60 vs DNSMOS +0.02–0.19) is now a pipeline-scale observation for §8B, not a test to run.
- **T6 reframed** — F-8 showed Speechify is Audiobox #1/#1 but DNSMOS mid-pack. Hypothesis narrowed from "model advantage" to "Audiobox rewards Speechify voice signature (DNSMOS is neutral)"; test design unchanged.
- **N1 + N2 added** — two new outliers surfaced by DNSMOS (see 2b.5 finding block below).

| # | Outlier | Provider | Hypothesis | Test design | Confirms if | Cost | Time |
|---|---|---|---|---|---|---|---|
| T1 | Clipping 429/406 (100× next) | Cartesia | Systemic gain-staging | **Downgraded** — cite F-4a DNSMOS refusal rate (43% conv / 49% narr) as second-pipeline corroboration; no regen | Memo lists both pipelines' evidence | $0 | 5 min (write-up) |
| T2 | WER 27% (2× next) | Orpheus | Real intelligibility issue, not judge bias | Manual-listen 10 flagged Orpheus items; self-mark unclear/clear | ≥5/10 self-marked unclear | $0 | 20 min |
| ~~T3~~ | ~~Narration PQ 7.41 conv → 8.00 narr~~ | ~~Orpheus~~ | ~~Audiobox artifact of clip length~~ | **Retired** — DNSMOS OVRL confirmed Orpheus #2 on narration (criterion satisfied). Magnitude gap goes to §8B | — | — | — |
| T4 | L03 fadeout (3.6 dB monotonic) | ElevenLabs | Deterministic bug on L03 text | Regen L03 × ElevenLabs × 3 fresh; drift | ≥2/3 fresh regens also flag monotonic degradation | $0.02 | 2 min |
| T5 | Latency 762/946 (2× next) | OpenAI | Persistent, not single-session artifact | 2nd 50-trial session next morning; compare p50/p90 | Within ±20% of first session | $0.02 | 10 min |
| T6 | Audiobox PQ+CE leader both UC | Speechify | **Audiobox rewards Speechify voice signature (DNSMOS is neutral, so this is a pipeline-specific advantage — not universally best)** | Regen 20 items × Speechify with a DIFFERENT Simba-3.2 voice; quality with all 6 signals | Both new-voice Audiobox axes AND all 4 new-voice DNSMOS axes within ±0.15 of geffen_32/wyatt_32 | $0.20 | 15 min |
| T7 | Fastest TTFA (440/474) | ElevenLabs | Persistent, not lucky | 2nd 50-trial session on different day; p90 under 500 ms | Confirms sub-500ms p90 both sessions | $0.02 | 10 min |
| T8 | Cheapest $0.030/1K | Orpheus | Cost scales linearly with item length | 10 long-item Orpheus calls; measure actual GPU-seconds per Replicate dashboard | Mean per-call within ±30% of $0.003 | $0.05 | 15 min |
| **N1** | **Audiobox PQ+CE #8/#8 narr, DNSMOS #1/#1/#2 narr — perfect rank inversion** | **OpenAI** | **The voice is "clinically clean but low aesthetic warmth" — Audiobox and DNSMOS measure different constructs, and OpenAI sits at opposite ends** | Manual-listen 5 narration items (self-mark warmth 1–5, cleanliness 1–5); look for pattern "clean but flat" | Self-marked cleanliness ≥4 AND warmth ≤3 on ≥3/5 items | $0 | 10 min |
| **N2** | **DNSMOS OVRL+SIG #8/#8 conv despite mid-pack Audiobox** | **Fish** | **Speech-vs-background artifact DNSMOS flags but Audiobox misses** | Spot-listen 3 conversational items; check for hiss, breath, low-frequency rumble; grep hygiene.json noise_floor_dbfs | ≥2/3 clips have audible non-speech artifact OR Fish noise_floor > median +6 dB | $0 | 10 min |

**Total: ~$0.30 spend, ~1.5 hrs wall clock** (down from ~$1/~4 hrs — regens retired/downgraded, replaced by cheaper manual-listen tests).

**Not-a-test observations from 2b** (recorded in F-9, no verification needed — they're findings, not hypotheses):

- **N3** — ElevenLabs conv AB.CE #8 despite AB.PQ #2, DNSMOS all top-2: within-Audiobox split ("technically perfect, low enjoyment")
- **N4** — Cartesia narration DNSMOS three-scale sweep #8/#8/#8 over the *surviving* 38/75 items: not just peaks, deeper mastering signature
- **N5** — Google narration DNSMOS P.808 #7 despite full validity: mid-tier baseline provider does have a soft spot on the P.808 model

### Execution (post-Phase 2b)

For each test, write the hypothesis + criterion to
`analysis/verification/T{N}.md` FIRST, then execute, then write the
verdict. Example scaffold:

```powershell
# Create verification dir
mkdir -Force analysis/verification

# T1: Cartesia clipping
# (see analysis/verification/T1_cartesia_clipping.md for hypothesis)
uv run veval generate --mode campaign --provider cartesia --items S02 --items S03 [...] --no-cache --spend-cap 1.00
uv run veval analyze <new-run-id> --stages acceptance,hygiene
# Read hygiene.json total_clipped_samples for cartesia; write to
# analysis/verification/T1_cartesia_clipping.md verdict section

# T2: Orpheus WER manual listen
# Play 10 flagged items, self-mark, write to
# analysis/verification/T2_orpheus_wer.md

# ... etc for T4-T8
```

Consider batching test commands into a `scripts/run_verification_pack.py`
helper if it's convenient.

### Exit criteria (Phase 2c)

- [ ] All 9 active verification tests executed (T1 write-up + T2 + T4-T8 + N1 + N2; T3 retired)
- [ ] Per-test artifact in `analysis/verification/T{N}.md` or `N{N}.md`
      with hypothesis, method, result, verdict
- [ ] Verdicts summarized in RESEARCH_LOG.md finding F-9
- [ ] Any flipped verdicts (outlier refuted) → memos updated to
      remove the corresponding elimination/recommendation
- [ ] N3, N4, N5 recorded as findings in F-9 (no separate test)

---

## Phase 3 (revised) — Reduced-scope BT rating campaign · ~1.5 hrs, $0 spend

**D-011 amendment (proposed)**: drop anchor from the BT campaign.
Rationale in RESEARCH_LOG D-C. Reduces rating burden to 168
judgments (from 216) while preserving:

- Full 8-provider pairwise ranking with bootstrap CIs
- D3↔D4 Spearman cross-check
- Audit-of-HI story (independent BT ranking to compare with HI)

Loses: absolute "how close to human" comparison (published as §10
future work).

Judgment math: **8 providers × C(8,2)=28 pairs × 2 use cases × 3 reps
= 168 judgments** + ~17 consistency repeats (10%) = ~185 total. About
1.5 hours across 3 sessions of ~40 min each.

### 3.1 Normalize campaign audio (no anchor) — ~5 min

```powershell
uv run veval rate normalize --source-run campaign-20260809T204608Z
```

No `--anchor-dir` flag. Only the 8-provider audio gets normalized to
−18 LUFS into `rating/audio/`.

### 3.2 Build 168-judgment manifest — <1 min

```powershell
uv run veval rate build --rater njg --exclude-system anchor --exclude-system orpheus-if-still-flagged
```

`--exclude-system anchor` is the D-011 payload. If Phase 2c T2
confirms Orpheus's WER problem AND we want to reduce burden further,
excluding orpheus drops us to 7-system pairs = 21 pairs × 2 × 3 =
126 judgments (~1 hr). Default: keep orpheus in.

### 3.3 Serve + rate across 2-3 sessions — ~1-1.5 hrs

```powershell
uv run veval rate serve
```

Session discipline: 20-40 min max per sitting, spread across days,
consistency re-judge in the last session ≥1 week after original
(runner already assigns consistency repeats to the last session).

### 3.4 Fit Bradley-Terry — <1 min

```powershell
uv run veval rate fit judgments-njg-<timestamp>.csv --n-resamples 2000
```

Writes `analysis/bt_fit.json` with per-use-case fits + pairwise-diff
CIs + consistency rate.

### Exit criteria (Phase 3)

- [ ] 168+ judgments in the CSV
- [ ] Consistency rate ≥ 80% (published alongside every D4 figure)
- [ ] Every provider pair covered ≥ 3× → `n_judgments` per fit
- [ ] `analysis/bt_fit.json` written; per-use-case fits with
      pairwise_diff and non-null CIs
- [ ] D-011 logged in DEVIATIONS.md and re-tagged prereg-v1.10 (or
      v1.11 if 2b landed a UTMOS+NISQA amendment)

---

## Phase 4 — HI snapshot + score + report · ~1 hr, $0 spend

Same as v1 Phase 4, but now:

- `veval score` consumes **4 quality signals** (D3 richer than v1)
- Frontier axis choice: still Audiobox PQ (spec-locked); UTMOS +
  NISQA appear as supplementary columns in the memo tables
- New **"Independent verification of outlier claims"** section in
  the case study pulling from `analysis/verification/T{N}.md`
- No anchor point on the frontier (D-011); anchor labeled as
  "future work" in the memo

### 4.1 Hand-scrape HI snapshot — ~15 min

Same as v1. Create `configs/hi_snapshot.json` with today's date.

### 4.2 Re-pull pricing — ~10 min

Same as v1. D6 rule — re-verify each cell against provider's current
pricing page, update `date_verified`.

### 4.3 Score — <1 min

```powershell
uv run veval score campaign-20260809T204608Z --bt-fit analysis/bt_fit.json --hi-snapshot configs/hi_snapshot.json --out analysis/score.json
```

### 4.4 Report — <1 min

```powershell
uv run veval report analysis/score.json --out site/
```

### 4.5 Case study manual sections — ~1-2 hrs writing

Write the following into `site/case_study.md` (or as a companion md
that `veval report` appends):

- **Framework guidance for enterprise PMs**: publish all three
  decision frameworks (Framework A hard-constraint hierarchy for
  support agents; Framework B risk-adjusted cost for narration;
  Framework C reader-adjustable weights as sensitivity tool). See
  RESEARCH_LOG D-E.
- **Threats to validity section** — first-class, before Recommendations
  — enumerate biases per RESEARCH_LOG threats-list.
- **Independent verification section** — verdict table from Phase 2c
  + per-outlier writeup with the T-artifact link.

### 4.6 Commit receipts + push — ~5 min

```powershell
git add analysis/ configs/hi_snapshot.json configs/pricing.yaml site/ documentation/RESEARCH_LOG.md
git commit -m "campaign results + verification + score.json + HI snapshot <date>"
git push origin main --follow-tags
```

### Exit criteria (Phase 4)

- [ ] `site/case_study.md` renders with real numbers, verification
      verdicts, and threats-to-validity section
- [ ] Every "dominated" claim backed by non-overlapping pairwise-BT
      CI (score.json's `dominates` fields)
- [ ] HI snapshot captured today; "reproduces?" column populated
- [ ] All 4 quality signals reported in memo tables (Audiobox PQ + CE,
      UTMOS, NISQA-MOS)
- [ ] Result artifacts committed to git

---

## Phase 5 — Drift re-run · +4 weeks, ~30 min, $0.50-2 spend

**Unchanged from v1.** See `voice_ai_eval_execution_runbook.md`
Phase 5 for the drift procedure. The `.cache/synthesis/` and Whisper
model caches will make this cheap (~$1 in fresh API calls).

Stop condition (from CLAUDE.md) still applies: after 3-4 monthly
drift cycles, either wind down gracefully or explicitly commit to
another cycle. Do not let this become the untended stale leaderboard
the project critiques.

---

## Standing rules (all phases, unchanged from v1)

- **Immutability**: nothing in `runs/` is ever edited.
- **Deviations over silent fixes**: DEVIATIONS.md D-XXX + re-tag.
- **Errors are data**: provider failures feed D7 friction findings.
- **Timeboxes beat completeness**: sample-and-disclose beats
  exhaustive-and-never-shipped.
- **RESEARCH_LOG is the paper's raw feedstock**: every decision +
  finding worth citing in the paper gets logged there, not just in
  git commit messages.

---

## Cross-references

- `voice_ai_eval_spec_v2.md` — the WHAT + HOW spec
- `voice_ai_eval_execution_runbook.md` — v1 runbook (Phases 0-2
  history)
- `RESEARCH_LOG.md` (this session) — running decision + finding log
  that feeds the paper's Results / Discussion / Threats sections
- `RESEARCH_REPORT.md` — paper template; populated at end of Phase 4
- `../DEVIATIONS.md` — amendments (v1 → v1.9 at time of writing;
  D-011 pending in Phase 2b/3)
- `../dx/friction_log.md` — DX findings per provider
