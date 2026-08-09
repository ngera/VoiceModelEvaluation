---
title: Execution Runbook — Post-Build Measurement Campaign
project: Voice AI Provider Evaluation (portfolio edition)
assumes: All 7 build phases (A–G) closed; tag prereg-v1.8 pushed to origin/main
companion: voice_ai_eval_spec_v2.md · IMPLEMENTATION_PLAN.md
---

# Execution Runbook — from "the code works" to "the results ship"

**Scope of this document:** the actions that follow once the build is
complete. Everything up to and including `prereg-v1.8` is code + tests +
receipts. This runbook covers the five measurement tasks that turn that
harness into a published finding:

1. Full 5-item → 75-item corpus campaign (topped-up provider credits)
2. Full analyzer sweep including WER + TTSDS2 (model downloads)
3. 216-judgment BT campaign (~2 hours over 5-6 sessions)
4. HI snapshot pull on analysis day
5. Drift re-run in 4 weeks

Wall-clock estimate: **~3-5 days of scattered attention** across ~10 days
calendar, then ~30 min every four weeks for the drift re-run.

---

## Phase 0 — Pre-flight (30 minutes)

Everything downstream trusts that this phase is clean. If it isn't, stop.

### 0.1 Credit + subscription state

Every provider that gates the campaign needs enough credit for the full
run. Actual per-provider draw at 75 items × 2 use cases (5 char/word ×
mean ~90 words = ~450 chars/item × 150 items ≈ **67.5K chars per
provider**):

| Provider | Plan needed | Cost/month | 67.5K-char cost | Action |
|---|---|---|---|---|
| Deepgram | Signup credit ($200) | $0 | ~$2 | verify credit balance in console |
| Fish | `s2.1-pro-free` (until 2026-08-31) + `s2.1-pro` paid | $0 (free window) | ~$1 (paid tier for latency mode) | verify free window still open |
| Google Cloud TTS | Chirp3-HD free tier (1M chars/mo) | $0 | $0 (well inside allowance) | verify billing project active |
| Cartesia | Pro ($5/mo, 100K credits) OR enable overages | $5 | needs 67.5K credits fits Pro | **top up** — hit HTTP 402 during Phase F smoke |
| ElevenLabs | Creator ($22/mo, 121K credits) | $22 | ~$14 (both use cases × 2 model tiers) | verify Creator active |
| Canopy Orpheus | Replicate pay-per-use | $0 | ~$0.45 (150 gens × $0.003) | **top up Replicate credits** — 0/10 in every prior pilot |
| OpenAI | Prepaid API credit | $0 | ~$1 | verify prepaid balance ≥ $5 |
| Speechify | Starter ($10/mo, 1M chars) | $10 | ~$0.70 (well inside allowance) | verify Starter active |

**Total campaign cost estimate: ~$20 in prepaid subscriptions + ~$3-5
in per-use spend.** Cancel monthly subscriptions after the drift re-run
in Phase 5.

**Command to verify:**

```powershell
uv run veval doctor
```

Expected: 8/8 adapters green. Any red row = fix credit/keys before Phase 1.

### 0.2 Environment sanity

```powershell
# Confirm the analyzer stack is installed (model downloads happen later)
uv sync --extra analyze --extra admin --extra dev

# Confirm the pre-registration tag is where we expect
git tag --list "prereg-*" | Select-Object -Last 1
# Should print: prereg-v1.8

# Confirm remote is in sync (no uncommitted changes to configs)
git status -s configs/
# Should be empty
```

### 0.3 Cache hygiene

The synthesis cache from Phase F debugging was nuked (D-008 poisoning).
It'll rebuild during Phase 1. Confirm it's empty:

```powershell
ls .cache/synthesis 2>$null
# Empty or "not found" is the correct state
```

**Go/no-go gate:** all 8 providers green on `veval doctor`, all
subscriptions verified active, cache empty. If any fails: fix before
Phase 1. Do not carry a broken adapter into the campaign.

---

## Phase 1 — Full generation campaign (1-2 days elapsed, mostly waiting)

Goal: **8 providers × 2 use cases × 75 corpus items = 1,200 audio
files** in one clean run.

### 1.1 The campaign run

One command. No `--items` filter — full corpus. Cache is empty so
everything makes a fresh call.

```powershell
uv run veval generate --mode campaign --spend-cap 30.00
```

**What happens:**
- 8 providers scheduled in parallel per `DEFAULT_PROVIDER_CONCURRENCY`
  (Speechify=1, Orpheus=1, others 3-5)
- Content-hash cache populates as each call completes (fixed in
  prereg-v1.7; will actually hit on subsequent re-runs)
- Errors logged as data to `api_log.jsonl`; NOT retried indefinitely
  (`ProviderError.retryable` decides)
- Spend cap $30 is generous — the real total should be ~$5

**Expected wall clock:** ~30-45 min with cache empty. Second call would
be ~2 min.

**Expected pass count:** 1,200/1,200 if all subscriptions are alive. Any
provider hitting < 100% needs immediate diagnosis before Phase 2 runs
against partial data.

### 1.2 WAV acceptance gate (mandatory before analysis)

Phase A defect class (0xFFFFFFFF headers, LIST chunks, JSON envelopes)
must NOT re-emerge silently. Verify:

```powershell
uv run python scripts/check_acceptance.py
```

Expected: `gate_ok: True | passed 1200 / 1200 (failed 0)`.

**If any file fails:** re-generate ONLY the failed items with `--items
<id> --provider <name>` (cache-hits skip). Do not proceed with a
poisoned run.

### 1.3 Variance mode (10 items × 3 draws × 8 providers = 480 fresh calls)

Skips cache by design — the noise floor needs FRESH calls.

```powershell
uv run veval generate --mode variance --n-draws 3
```

**Expected wall clock:** ~15-20 min. **Expected pass count:** 480/480.
Additional spend: ~$2.

### 1.4 Latency mode (50 serial trials × 6 latency-capable providers)

**Only providers with streaming TTFA:** deepgram, fish, cartesia,
elevenlabs, openai. Google + Speechify are buffered (annotated per
D-008 pattern); Orpheus is N/A-hosted.

Ideally run this from a **pinned VM** with a stable region, split
across ≥2 days and ≥2 times of day (spec §D1). For a portfolio
project the laptop is acceptable — record hostname + local time.

```powershell
# Session 1 (morning)
uv run veval generate --mode latency --provider deepgram --provider fish --provider cartesia --provider elevenlabs --provider openai --trials 50

# Session 2 (afternoon, ≥6 hours later, ideally next day)
uv run veval generate --mode latency --provider deepgram --provider fish --provider cartesia --provider elevenlabs --provider openai --trials 50
```

**Expected wall clock:** ~5-8 min per session (serial, one request in
flight). Additional spend: rounding-error.

### 1.5 Budget checkpoint

After Phase 1.1-1.4 complete, sum the observed spend:

```powershell
uv run python -c "
import json
from pathlib import Path
for run in sorted(Path('runs').glob('*'), reverse=True)[:4]:
    m = json.loads((run / 'manifest.json').read_text())
    print(f\"{run.name}: {m.get('kind')} audio={m.get('audio_count')} err={m.get('error_count')}\")
"
```

Total spend should land under **$10**. If it's 2× that, stop and diagnose
before proceeding (usually a retry loop or a wrong-tier fallback).

**Exit criteria (Phase 1):**
- 1,200/1,200 acceptance gate green on the campaign run
- 480/480 fresh audio in the variance run
- Latency data spans ≥2 sessions
- Total observed spend ≤ $10

---

## Phase 2 — Full analyzer sweep (2-4 hours mostly wall clock)

**First run of `wer` + `quality` downloads models: ~6 GB total** across
Parakeet-RNNT-0.6B, faster-whisper-large-v3, TTSDS2 references, and
Audiobox weights. All cached after the first pull; subsequent runs are
compute-only.

### 2.1 Cheap analyzers first (5-10 min)

Fast rollups run without any model download.

```powershell
# Point at the campaign run — analyze runs against one run_id at a time
uv run veval analyze <campaign_run_id> --stages acceptance,hygiene,latency,cost
```

**Expected wall clock:** ~5 min for 1,200 files.

### 2.2 WER (~30-60 min per run, first time longer for model download)

Two-judge WER downloads Parakeet + faster-whisper on first run.

```powershell
uv run veval analyze <campaign_run_id> --stages wer
```

**Expected wall clock:** ~60 min first time (model download + 1,200
files × 2 judges); ~40 min subsequent runs. GPU strongly recommended;
CPU works but is 4-6× slower.

### 2.3 Quality (~30-60 min per run)

TTSDS2 downloads reference sets (DAPS ~30 GB after decompression!).
Audiobox weights are smaller. First run pulls all of these.

```powershell
# --n-split-half 100 is the pre-registered default (analyzers.yaml)
uv run veval analyze <campaign_run_id> --stages quality --n-split-half 100
```

**Expected wall clock:** ~90 min first time (heavy reference download);
~30 min subsequent. If DAPS pull is a problem, `--skip-ttsds` produces
Audiobox-only output and the split-half check runs on Audiobox PQ
instead — noted as a limitation in the report.

### 2.4 Variance + drift (5-10 min)

Reads WER + quality outputs, needs no additional models.

```powershell
uv run veval analyze <variance_run_id> --stages variance
uv run veval analyze <campaign_run_id> --stages drift
```

### 2.5 Analyzer output verification

Every run under `analysis/<run_id>/` should have all 8 JSON files:

```powershell
ls analysis/<campaign_run_id>/
# Expected: acceptance.json cost_model.json drift.json hygiene.json
#           latency.json quality.json variance.json wer.json
```

**Exit criteria (Phase 2):**
- All 8 analyzer JSONs present per run
- WER `by_provider.n_valid` = 150 (75 items × 2 use cases) per provider
- Quality `ttsds_by_provider` populated (or explicitly annotated as
  Audiobox-only in the report)
- Manual-listen queue timeboxed to 2 hours (spec §E) — sample beyond that

---

## Phase 3 — Bradley-Terry rating campaign (~2-3 hours across 5-6 sessions)

216 judgments total (D-009: 3 reps × C(9,2) pairs × 2 use cases).

### 3.1 Record the anchor set (~1 hour one-time)

**Full corpus this time**, not just the 5 pilot items. All 75 items ×
both use cases = 150 recordings.

For each item:
1. Read the corpus text into a quiet-room USB mic
2. Save as `rating/anchor/<use_case>_<item_id>.wav`
3. Any format soundfile can decode (loudness normalization handles the rest)

The corpus is under `corpus/conversational.yaml` and
`corpus/narration.yaml`. Print the texts:

```powershell
uv run python -c "
from pathlib import Path
from veval.config import load_corpus
for uc in ('conversational', 'narration'):
    c = load_corpus(Path(f'corpus/{uc}.yaml'))
    print(f'=== {uc} — {len(c.items)} items ===')
    for i in c.items:
        print(f'--- {i.id} ({i.word_count} words) ---')
        print(i.text)
        print()
" > anchor_script.txt
```

**Time budget:** ~1 hour for both use cases at a reading pace of ~150 wpm
plus retakes. Break into two ~30 min sessions if voice fatigue sets in.

### 3.2 Normalize + build manifest

```powershell
# Normalize the campaign run + anchor to -18 LUFS
uv run veval rate normalize --source-run <campaign_run_id> --anchor-dir rating/anchor

# Build the 216-judgment manifest (D-009 defaults: reps=3, 10% consistency)
uv run veval rate build --rater <your-id> --exclude-system orpheus
```

Expected: **9 systems (8 providers + anchor) × 36 pairs × 2 use cases ×
3 reps = 216 judgments + 22 consistency repeats = 238 total judgments**
across ~6 sessions of 40 judgments each.

If Orpheus is fully unblocked (Replicate credits, all 10/10 in variance),
drop `--exclude-system orpheus`.

### 3.3 Serve + rate

```powershell
uv run veval rate serve
```

Opens `http://localhost:8080`. Keyboard: **1**=A wins, **2**=B wins,
**R**=replay both, **Space**=replay.

**Session discipline (spec §A.4):**
- 20-40 min per sitting max (ear fatigue is real and shows up in the
  data — Bradley-Terry doesn't magically correct for it)
- Spread across days, ideally 5-6 sessions
- Progress persists in localStorage per `rater_id`; refresh the tab or
  restart `rate serve` and pick up where you left off
- **"Download progress CSV"** at any time; the file is safe to keep
  overwriting mid-session

**Consistency re-judge:** the 22 consistency-marked judgments land in
the LAST session automatically. Do them ≥1 week after the first showing
of that item — that gap becomes a published number.

### 3.4 Fit Bradley-Terry

```powershell
# 2000 resamples (spec default). Takes ~15 sec for 216 judgments
uv run veval rate fit judgments-<rater>-<timestamp>.csv --n-resamples 2000
```

Writes `analysis/bt_fit.json` with per-use-case fits + pairwise-diff
CIs + consistency rate.

**Exit criteria (Phase 3):**
- 216+ judgments captured (238 with consistency repeats)
- Consistency rate ≥ 80% (spec: publish alongside every D4 figure — if
  <70%, the fit's CIs need explicit annotation)
- Every (provider, provider) pair covered ≥ 3× → check `n_judgments`
  per fit in `bt_fit.json`
- `bt_fit.json` written; every use-case fit has non-null `strengths`
  and `pairwise_diff` blocks

---

## Phase 4 — HI snapshot + score + report (~1 hour)

Everything downstream is pure computation. Run these back-to-back on
"analysis day" so all timestamps line up.

### 4.1 Hand-scrape the HI snapshot

The Humanness Index moves; the receipt is that ours predates the
comparison. Create `configs/hi_snapshot.json` today:

```json
{
  "captured_at": "YYYY-MM-DD",
  "source": "https://humannessindex.vapi.ai/  (or wherever HI publishes)",
  "scores": {
    "elevenlabs": {"rank": 1, "score": 99.0},
    "cartesia":   {"rank": 2, "score": 95.5},
    "openai":     {"rank": 3, "score": 92.0},
    "fish":       {"rank": 4, "score": 88.5},
    "google":     {"rank": 5, "score": 85.0},
    "deepgram":   {"rank": 6, "score": 82.0},
    "speechify":  {"rank": 7, "score": 99.0},
    "orpheus":    {"rank": null, "score": null}
  },
  "notes": "Copied by hand from the leaderboard on <date>. Speechify at #1 per prereg-v1.1 D-003 audit rationale."
}
```

**Only fill in what HI actually shows.** Missing providers get `null` +
a note; a mis-transcription here silently biases the "reproduces?"
column.

### 4.2 Re-pull pricing (D6 rule)

The cost frontier trusts `configs/pricing.yaml`. Re-verify each cell's
`rate_usd` against the provider's current pricing page and update
`date_verified` to today. Log any material change (>20%) in
`DEVIATIONS.md`.

### 4.3 Score

```powershell
uv run veval score <campaign_run_id> \
  --bt-fit analysis/bt_fit.json \
  --hi-snapshot configs/hi_snapshot.json \
  --out analysis/score.json
```

Console output shows:
- **Gates**: per-use-case survivor lists + first-blocker per non-survivor
- **Robustness**: which gates flip survivor sets across their sweep points
- **Frontiers**: which providers land on cost + latency frontiers
- **HI reproduces**: yes / mostly / no across top-3
- **Spearman ρ**: D3↔D4, D3↔HI, D4↔HI with interpretation buckets

### 4.4 Report

```powershell
uv run veval report analysis/score.json --out site/
```

Produces:
- `site/case_study.md` — composite writeup
- `site/memo_conversational.md`, `site/memo_narration.md` — 1-page
  decision memos
- `site/*.png` — Altair static frontiers for the memo images
- `site/interactive/*.html` — Plotly interactive frontiers

### 4.5 Commit the receipts

`analysis/*.json` and the `score.json` output ARE committed (small,
JSON, and the pre-registration receipt is worthless without them).

```powershell
git add analysis/ configs/hi_snapshot.json configs/pricing.yaml
git commit -m "campaign results: analysis/<run_id> + score.json + HI snapshot <date>"
git push origin main
```

### 4.6 Case-study writeup + publish

`site/case_study.md` is the skeleton. Fill in:
- The "quotable data points" section of CLAUDE.md's narrative bank with
  real numbers (Δ vs HI per provider; $ spread across providers at 1M
  wpm; DX friction times)
- Narrative around any surprises the smoke didn't preview
- The Spec §7 red-team appendix (Appendix E findings — own them)

**Publish surface** (spec §7 line 649-660):
- Repo on GitHub — already pushed
- Static case study — copy `site/case_study.md` + PNGs into a Vercel/
  GitHub Pages project OR paste into a LinkedIn article + repo link
- Curated audio sample set only (spec §Appendix E — not the full 1,200)
- Date-stamp every score and price cell

**Exit criteria (Phase 4):**
- `site/case_study.md` renders with real numbers
- Every "dominated" claim in the memos backed by a non-overlapping
  pairwise-difference CI (score.json's `dominates` fields)
- HI snapshot captured today; "reproduces?" column populated
- Result artifacts committed to git

---

## Phase 5 — Drift re-run (+4 weeks, ~30 min after credit check)

The single artifact no competing leaderboard produces.

### 5.1 Calendar reminder

Set a calendar entry for **+4 weeks from analysis day** titled
"veval drift re-run — recompute campaign, publish diff".

### 5.2 Credit check + subscription refresh (10 min)

Same as Phase 0.1. Speechify/Cartesia/ElevenLabs subscriptions renew
automatically; verify balances. Fish's free window may have closed
(2026-08-31) — if so, switch to paid `s2.1-pro` and log in DEVIATIONS.

### 5.3 Re-run generation

```powershell
uv run veval generate --mode campaign --spend-cap 15.00
```

**Expected wall clock:** ~10 min. **Expected spend:** $0.50-2.00.
The content-hash cache makes this cheap — only providers who changed
their models make real API calls. `cache: hit` in the api_log means
"identical bytes as before".

### 5.4 Re-run analyzers (~15 min, models cached)

```powershell
uv run veval analyze <new_campaign_run_id>
```

All 8 stages. Model weights already on disk from Phase 2, so first-run
overhead is gone.

### 5.5 New HI snapshot (5 min)

Fresh `configs/hi_snapshot.json` (or timestamped `hi_snapshot_YYYYMMDD.json`)
capturing today's leaderboard. Do NOT overwrite the previous snapshot
without keeping the old file — the diff is the story.

### 5.6 Re-score + re-report

```powershell
uv run veval score <new_campaign_run_id> \
  --bt-fit analysis/bt_fit.json \
  --hi-snapshot configs/hi_snapshot.json \
  --out analysis/score_month2.json

uv run veval report analysis/score_month2.json --out site_month2/
```

**Note:** Bradley-Terry does NOT need to re-fit — the human judgments
don't change unless you re-rate. Only the analyzer + cost + HI axes
move. If a provider drops out of the frontier due to a model swap
between months, THAT IS THE STORY.

### 5.7 Drift changelog entry

One paragraph in `site/drift_log.md`:
- Which providers changed measurable output (byte-identity check via
  variance.py's determinism flag would catch this at Phase 2, but
  even a change WITHIN the deterministic-flag envelope is worth noting)
- Which providers moved on the cost frontier (pricing.yaml)
- HI leaderboard shifts (any rank changes since last snapshot)
- Any newly-dead providers (PlayHT-style — the next one gets a
  changelog entry, not silence)

### 5.8 Publish

Same publish surface as Phase 4.6, with a "Month 2 drift update" banner.

**Exit criteria (Phase 5):**
- Fresh `analysis/<new_run_id>/` committed
- `site/drift_log.md` has the paragraph
- Old HI snapshot preserved as a separate file so future re-runs can
  reference the full trajectory

### 5.9 Stop condition

This is a portfolio project, not a company. After **3-4 monthly cycles**
the drift story is told. Either:
- **Wind down gracefully** — final changelog, "archived as of <date>"
  banner, cancel subscriptions
- **Consciously decide it's worth continuing** for a specific reason
  (a provider announced something, a new HI competitor emerged, etc.)

**Do NOT let it become an untended stale leaderboard.** That's the exact
failure mode this project critiques.

---

## Standing rules (all phases)

- **Immutability**: nothing in `runs/` is ever edited; every number is
  recomputable from raw audio.
- **Deviations over silent fixes**: any departure from the pre-registered
  setup lands in `DEVIATIONS.md` with a `D-XXX` entry + a re-tag
  (currently prereg-v1.8 → v1.9 as the next slot).
- **Errors are data**: provider failures feed D7 friction findings; they
  are findings, not embarrassments to be hidden.
- **Timeboxes beat completeness**: sampled-and-disclosed beats
  exhaustive-and-never-shipped. The manual-listen queue timebox
  (2 hrs, spec §E) is the canonical example.
- **Cache is disposable**: `.cache/synthesis/` can be nuked at any time.
  Nothing there is a receipt; the run store IS the receipt.

---

## Troubleshooting quick-reference

| Symptom | Most-likely cause | First check |
|---|---|---|
| Provider returns HTTP 402 | Credit exhausted (Cartesia Pro, Replicate) | Provider console + billing dashboard |
| Provider returns HTTP 429 | Concurrency limit exceeded | `DEFAULT_PROVIDER_CONCURRENCY` in runner.py |
| Provider returns HTTP 401 | Key rotated / .env stale | `veval doctor --provider <name>` |
| Streamlit page won't load | Port collision — bound to 8502 not 8501 | Read the streamlit startup banner |
| Cache showing 0 hits on re-run | (pre-v1.7 bug, now fixed) — verify prereg-v1.7 tag reachable | `git describe` |
| WAV files fail decode in acceptance | New adapter defect class (like Speechify D-008) | `scripts/check_acceptance.py` output |
| BT fit shows tiny CIs on all providers | Not enough judgments captured | Check `n_judgments` per fit; need ≥ 126 |
| Kaleido / Chrome errors on `veval report` | Kaleido shouldn't be installed (hybrid design uses Altair for static) | `uv pip list \| grep kaleido` |

## Reference documents

- **Spec (WHAT + HOW):** [`voice_ai_eval_spec_v2.md`](voice_ai_eval_spec_v2.md)
- **Build plan (already closed):** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
- **Amendments:** [`../DEVIATIONS.md`](../DEVIATIONS.md) (D-001 through D-009)
- **DX findings for the report:** [`../dx/friction_log.md`](../dx/friction_log.md)
- **Locked decisions + narrative bank:** [`../CLAUDE.md`](../CLAUDE.md)
- **Full-body corpus:** [`../corpus/conversational.yaml`](../corpus/conversational.yaml) · [`../corpus/narration.yaml`](../corpus/narration.yaml)
