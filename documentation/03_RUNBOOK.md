# 03 · Installation + Runbook

*Install the harness on a fresh machine, reproduce the published
evaluation, and run your own campaign against alternative vendors,
voices, or corpora.*

> **⚠ Scope disclaimer** · Absolute measurement values depend on
> your environment (network, hardware, subscription tier) and on
> when the measurement was taken (see F-11 for our 6-session
> per-vendor TTFA spread across four dates). Vendor *rankings* are
> portable; absolute *values* are one point in a session-to-session
> distribution, not ceilings. See [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Prerequisites

- **Python 3.11** (any 3.11.x — 3.11 is pinned; 3.12+ untested)
- **uv** package manager — install from https://astral.sh/uv
- **Free disk for model downloads on first analyzer run**:
    - ~2 GB for WER judges (wav2vec2 + faster-whisper)
    - ~500 MB for Audiobox
    - ~10 MB for DNSMOS (ships with pip package)
    - **~30 GB additional if you run TTSDS2** (reference datasets;
      the `--skip-ttsds` flag bypasses this download entirely — this
      project's published results use `--skip-ttsds` per D-A)
- **API keys** for whichever vendors you want to include (all 8 for
  the full published evaluation)

**Environment tested:** developed and run end-to-end on **Windows 11**
(residential setup, see [../DISCLAIMER.md](../DISCLAIMER.md)). All
commands below are PowerShell syntax; substitute your shell as
needed. The codebase is Python 3.11 + uv, both cross-platform, but
macOS / Linux have not been exercised in v1 — expect some path-separator
edge cases in tests that pass on Windows. UTMOS is known blocked on
Windows (see D-B); VERSA was dropped as an analyzer backbone partly
because it needed a Linux container. A macOS / Linux reproduction
run would be a v2 workstream — see
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md).

---

## Install

```powershell
# Clone
git clone https://github.com/ngera/VoiceModelEvaluation.git
cd VoiceModelEvaluation

# Copy env template, add your API keys
Copy-Item .env.example .env
notepad .env

# Install project + dependencies (creates .venv/)
uv sync --extra admin --extra dev

# Verify tools available
uv run veval --help
```

### API key configuration

The `.env` file (gitignored) holds one line per vendor:

```
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
CARTESIA_API_KEY=...
FISH_API_KEY=...
OPENAI_API_KEY=...
SPEECHIFY_API_KEY=...
REPLICATE_API_TOKEN=...
GOOGLE_APPLICATION_CREDENTIALS=.secrets/<service-account>.json
```

The Google service-account JSON goes in `.secrets/` (also
gitignored). Everything else is API-key auth via the vendor's own
console.

You do **not** need all 8 vendors to run. If a vendor's key is
missing, `veval doctor` will flag it but subsequent commands can
be scoped to whichever vendors you have configured.

---

## Doctor — end-to-end adapter health check

Same spirit as `brew doctor` / `flutter doctor`. Loads configs,
verifies env vars, calls `adapter.synthesize()` once per vendor,
writes results to `runs/doctor-<timestamp>/`.

```powershell
# All vendors, conversational voice
uv run veval doctor

# One vendor
uv run veval doctor --provider elevenlabs

# Narration voice smoke test
uv run veval doctor --use-case narration
```

**Cost**: rounding-error small (~$0.001/vendor for a probe text).

**What you should see**: a Rich table with 1 row per vendor,
column status ✓/✗, TTFA + total_ms + audio bytes columns populated.
Non-zero exit code if any adapter fails.

**Before spending any real money, doctor should be all green.**

---

## Generate — the campaign runner

Every `generate` invocation writes to `runs/<mode>-<timestamp>/`
with immutable audio + `api_log.jsonl` + `manifest.json`. Nothing
is mutated in place — the run store is designed so an analyzer
can be re-run against the same run any time.

### Campaign mode (Phase D primary)

```powershell
# Full campaign (75 items × 8 vendors × 2 use cases = 1200 files)
uv run veval generate --mode campaign

# $1 pilot before spending real money
uv run veval generate --mode campaign `
  --items S01 --items M01 --items L01 --items J01 --items E01

# One vendor, both use cases
uv run veval generate --mode campaign --provider fish

# One use case, subset
uv run veval generate --mode campaign --use-case conversational `
  --items S01 --items S02 --items S03
```

**Cache**: campaign mode uses a content-hash cache at
`.cache/synthesis/`. Same `(provider, model, voice_id, text, format,
sample_rate, version)` returns cached bytes instead of a fresh call.
Force a fresh call:

```powershell
uv run veval generate --mode campaign --provider elevenlabs `
  --items L03 --no-cache
```

**Spend cap**: every invocation is gated by a USD cap (default
`$100`, override with `--spend-cap 0.10` or disable with
`--no-spend-cap`). Estimator uses the highest per-call rate row in
`pricing.yaml` so it overshoots rather than undershoots. Calls
exceeding the cap are refused; in-flight calls complete; subsequent
submissions logged as `status=skipped`.

### Variance mode (Phase D noise-floor measurement)

```powershell
# 10 items × 3 draws × 8 vendors × 2 use cases = 480 fresh generations
uv run veval generate --mode variance

# One vendor variance
uv run veval generate --mode variance --provider deepgram
```

**Cache is forced OFF** in variance mode — fresh draws *are* the
measurement. Feeds `variance.py` to compute per-vendor within-vendor
SD (the **measurement noise floor**, statistical). Every
between-vendor delta is compared against `1.96 × SE(difference)`
to check whether it exceeds that measurement noise floor. This is
separate from the **acoustic** noise floor — the dBFS hygiene
metric with its own pre-registered gate in `configs/gates.yaml`
(`long_stratum_acoustic_noise_floor_dbfs ≤ −40`); the two share
a name for historical reasons and are otherwise unrelated (per
CORRECTIONS row B2's vocabulary retirement).

### <a name="latency--ping"></a>Latency mode (Phase D speed measurement)

```powershell
# 50 serial TTFA trials per vendor on the S01 corpus item
uv run veval generate --mode latency

# One vendor
uv run veval generate --mode latency --provider elevenlabs --trials 50
```

Cache forced OFF (fresh trials = fresh measurements). Serial, not
parallel — measures per-user tail experience, not aggregate
throughput. Phase 1 called for **≥5 sessions on different days**
for a proper stability characterisation; the project has run
**6 sessions on 4 dates** (S1a, S1b, S2, S3, S4, S5) and F-11
concludes that even at n=6 mechanism attribution remains blocked
on **client-side lag logging** (per-request timestamps for DNS +
TCP handshake + first-byte-arrival) that was not run in v1. F-11
in 06_KEY_FINDINGS.md is the receipt for both the six-session
rank stability and the residual attribution gap; the older
"two-session comparison is not sufficient" framing was the
pre-R14 S3 story.

**S3 setup with concurrent ping baseline** (recommended for any
new session that will be used to make a distributional claim):

```powershell
# Runs the latency campaign AND starts a concurrent ping-to-1.1.1.1
# subprocess. Ping log lands at runs/ping-baseline-<ts>.jsonl.
uv run python scripts/latency_with_ping.py --provider elevenlabs
uv run python scripts/latency_with_ping.py --provider openai
```

The ping log rules out only the "last-mile link dropped packets"
hypothesis for network-side contamination; it does not touch DNS,
TLS, or client-side event-loop stalls. See
[06_KEY_FINDINGS.md § F-11](06_KEY_FINDINGS.md#f-11)
for the full scope-of-ruleout discussion.

**Commit the ping log**: copy `runs/ping-baseline-*.jsonl` into
`analysis/` so it survives `runs/`'s gitignore. `.gitignore` has
`!analysis/ping-baseline-*.jsonl` un-ignored explicitly for this
purpose (small text file, big evidentiary value).

---

## Analyze — the analyzer chain

Pure function of `runs/<run-id>/`. Writes JSON outputs to
`analysis/<run-id>/`. Every analyzer is idempotent and re-runnable.

```powershell
# Latest campaign run, all stages
uv run veval analyze --stages all

# Specific run, specific stages
uv run veval analyze campaign-20260809T204608Z `
  --stages acceptance,hygiene,latency,cost,wer,quality,cross_metric,variance,drift

# Skip TTSDS2 in quality stage (fast iteration)
uv run veval analyze <run-id> --stages quality --skip-ttsds

# Skip DNSMOS (if you don't want the second MOS pipeline)
uv run veval analyze <run-id> --stages quality --skip-dnsmos
```

### Analyzer stages

| Stage | Reads | Writes | Notes |
|---|---|---|---|
| `acceptance` | audio + api_log | `acceptance.json` | WAV header / decode / LUFS / VAD / char sanity |
| `hygiene` | audio | `hygiene.json` | clipping, LUFS, noise floor, long pauses |
| `latency` | api_log | `latency.json` | TTFA percentiles + RTF on long items |
| `cost` | api_log + pricing.yaml | `cost_model.json` | observed vs pricing-modeled cost |
| `wer` | audio | `wer.json` | two-judge agreement WER (first run downloads ~2 GB ASR models) |
| `quality` | audio | `quality.json` | Audiobox + DNSMOS + optional TTSDS2 (first run downloads ~5 GB) |
| `cross_metric` | quality.json | `cross_metric.json` | Spearman ρ across the 6 quality signals |
| `variance` | audio + wer + quality | `variance.json` | within-vendor SD per signal → noise floor |
| `drift` | audio | `drift.json` | per-third loudness/spectral analysis on long items |

**CPU-only by design** — no GPU required. Wall-clock ~30-60 min
for the full 1200-file `quality` stage on a mid-tier CPU. GPU
reproducers see identical scores at 5-10× the speed.

### First-run model downloads

First `wer` invocation downloads Meta wav2vec2 + OpenAI Whisper
(~2 GB combined). First `quality` invocation downloads Audiobox
weights (~500 MB) + optional TTSDS2 references (~30 GB). DNSMOS
weights (~10 MB) ship with the pip package.

Cached under `~/.cache/huggingface/` and Whisper's default cache dir.

---

## Reproduce the published evaluation

To reproduce the numbers in [04_RESULTS.md](04_RESULTS.md), starting
from a fresh clone:

```powershell
# 0. Prerequisites (Python 3.11 + uv + all 8 vendor API keys)

# 1. Install
uv sync --extra admin --extra dev

# 2. Doctor — every vendor must be green
uv run veval doctor

# 3. Run the primary campaign (~$8 measured, ~30 min wall clock;
#    see cost_model.json `total_observed_cost_usd` in the run's
#    analysis/ output)
uv run veval generate --mode campaign

# 4. Run the variance subset for the noise-floor measurement (~$2, ~10 min)
uv run veval generate --mode variance

# 5. Run 3 latency sessions across ≥2 different days for T5, T7, F-11.
#    We ran ours on days 1, 3, and 4; you can compress but do not
#    run them back-to-back on the same day (defeats the point of
#    session-to-session variance measurement).
uv run veval generate --mode latency  # session 1 (S1)
# wait a day
uv run veval generate --mode latency --provider openai      # S2 OpenAI
uv run veval generate --mode latency --provider elevenlabs  # S2 ElevenLabs
# wait another day
# S3 — third session, run with a concurrent ping-baseline log to
# Cloudflare 1.1.1.1 so a reader can rule out ISP jitter
# independently (F-11). `scripts/latency_with_ping.py` starts the
# ping subprocess, runs the latency call, and writes the ping log
# to `runs/ping-baseline-<ts>.jsonl` alongside the latency run.
uv run python scripts/latency_with_ping.py --provider openai
uv run python scripts/latency_with_ping.py --provider elevenlabs

# 6. Analyze — order matters within a single --stages list:
#    quality + wer must land before variance reads them
uv run veval analyze <campaign-run-id> --stages all --skip-ttsds
uv run veval analyze <variance-run-id> --stages quality,wer,variance --skip-ttsds
uv run veval analyze <latency-run-id-s1a> --stages latency
uv run veval analyze <latency-run-id-s1b> --stages latency
uv run veval analyze <latency-run-id-s2-oai> --stages latency
uv run veval analyze <latency-run-id-s2-el>  --stages latency
uv run veval analyze <latency-run-id-s3-oai> --stages latency
uv run veval analyze <latency-run-id-s3-el>  --stages latency
uv run veval analyze <latency-run-id-s4-el>  --stages latency  # Phase 2 Follow-up 3
uv run veval analyze <latency-run-id-s4-oai> --stages latency
uv run veval analyze <latency-run-id-s5-el>  --stages latency
uv run veval analyze <latency-run-id-s5-oai> --stages latency  # T19:10 attempt crashed; use T20:10 rerun

# 7. Recompute the per-comparison SE(diff) tie tests and the paired
#    vs unpaired comparison (Wave 1 statistical honesty pass —
#    reads campaign + variance analysis JSONs, prints to stdout)
uv run python scripts/_noise_floor_recompute.py
uv run python scripts/_paired_test.py

# 8. Generate figures
uv run python scripts/generate_figures.py
```

**S3 evidence commit**: the ping-baseline log from S3
(`ping-baseline-20260812T191138Z.jsonl` in ours) is
committed into `analysis/` under the same name so a reader
can verify the "network was clean during S3" claim without
having to regenerate. See [.gitignore](../.gitignore) —
`!analysis/ping-baseline-*.jsonl` is un-ignored explicitly for
this purpose. The audio latency `runs/` are gitignored
(regenerable + large).

Analyzer outputs land in `analysis/<run-id>/*.json`. Figures land
in `documentation/figures/`. Compare against the published
[04_RESULTS.md](04_RESULTS.md) — findings should reproduce within
per-vendor per-signal SE(diff) bands documented in
[04's Rankings summary](04_RESULTS.md#rankings-summary) and computed
by [`scripts/_noise_floor_recompute.py`](../scripts/_noise_floor_recompute.py).
**One caveat**: the three analyzer neural models
(Audiobox, wav2vec2, faster-whisper) were not SHA-pinned in the
campaign (see [02 § 1 honest exception](02_METHODOLOGY.md#1-pre-registration-with-git-tags)
and [07 gap 9](07_GAPS_AND_FUTURE_WORK.md)); a fresh clone
today re-downloads them at whatever `main` serves, so exact-value
reproduction is only guaranteed inside the R2↔R3 measurement
interval where the resolved stack was stable
(ρ = 0.905-1.000). Rank-level reproduction is the load-bearing
promise.

**Estimated cost of a clean reproduction** (from committed
`analysis/*/cost_model.json` `total_observed_cost_usd` fields —
the receipt is directly reproducible):

**Minimum reproduction** — one fresh campaign is enough to
reproduce every ranking claim in [04_RESULTS.md](04_RESULTS.md)
and adjudicate every pre-registered gate:

- Doctor probes + pilot runs: **~$0.61**
- Primary campaign (1200 fresh files, `--no-cache`): **~$7.84**
- Variance run (10 items × 3 draws × 8 vendors × 2 use cases = 480 files): **$3.16**
- Two S1 latency sessions (50 trials × 4 streaming vendors): **$0.34**
- Verification pack (T4 + T6 + T8 fresh regens + S2 verification
  latency session covering T5 + T7): **~$0.63** (per
  [04's verification-pack cost line](04_RESULTS.md#verification-pack-outcomes-phase-2c);
  DISCLAIMER's breakdown lists S2 as part of the latency-sessions
  aggregate, so summing DISCLAIMER's lines does not double-count S2 — it
  sits inside the $0.63 total here, and inside the latency-sessions
  line there)
- Third latency session with ping baseline: **~$0.02**
- Phase 2 experiment pack (5 experiments + 4 follow-ups): **~$3.55**
- **Minimum total: ~$16** across 8 vendor accounts, plus 8-12 hrs
  wall clock on a mid-tier CPU laptop (~5 hrs of that is the
  campaign analyzer pass; ~5 hrs is Phase 2 Experiment E's
  alt-voice quality pass).

**Full replication (R2 + R3)** — additionally runs a second full
campaign three weeks later to verify measurement stability
(reproduces the R2→R3 ranking comparison, the ElevenLabs cross-axis
regression signal, and the hygiene-gate R2→R3 flip on Orpheus):

- Add a second campaign 2-4 weeks after the first: **+~$7.84**
- **Full total: ~$24**, plus another ~5 hrs analyzer wall clock

The load-bearing per-run cost figures come from
`total_observed_cost_usd` in each committed
`analysis/*/cost_model.json`; the pilot-runs and T4/T8/Wave-4b
lines are reproducible from `runs/<id>/api_log.jsonl` via
`veval analyze <id> --stages cost` but `runs/` is gitignored
(regenerable audio, not versioned) so re-deriving those cost
figures requires either (i) running the corresponding
`veval generate` again from a fresh clone or (ii) having the
original `runs/` tree on disk from the initial run. See
DISCLAIMER's cost breakdown for the committed-vs-reproducible
split per line. **Effective out-of-pocket** for our specific project
was lower because Deepgram's $200 signup credit absorbed ~$1.20
and Speechify Starter's $10/mo subscription and ElevenLabs
Creator's $22/mo Creator plan absorbed within-month re-runs; your
own out-of-pocket depends on your credit balances and subscription
timing.

---

## Reproduce R3 (the fresh-generation replication)

R3 is a second full campaign run 3 weeks after R2, with `--no-cache`,
that adjudicates the pre-registered `rtf ≥ 3.0` narration gate that
R2's cache-only replay could not (no `synthesis_time` on cached
rows). It also stress-tests the R2 rankings under a fresh generation
set and surfaces vendor-side drift signals.

```powershell
# Full campaign, fresh, ~$7.84 metered
uv run veval generate --mode campaign --no-cache

# Analyze — same stages as R2
uv run veval analyze <r3-run-id> --stages all --skip-ttsds

# Recompute the R2-vs-R3 replication comparison
uv run python scripts/_r2_vs_r3.py --r2 campaign-20260809T204608Z `
                                    --r3 <r3-run-id>
# Writes analysis/round3-vs-round2-comparison.md — same table shape
# as our published version. Redirect stderr to /dev/null (or $null on
# PowerShell) to avoid capturing uv's VIRTUAL_ENV warning into the doc
# (see CORRECTIONS row 29).
```

**What R3 adjudicates that R2 does not**:

- Pre-registered `rtf ≥ 3.0` narration gate (5 pass / 3 fail on our
  R3; see [04 § RTF admission](04_RESULTS.md#rtf-admission)).
- Vendor-side model drift over the 3-week interval (our R3 showed
  ElevenLabs shifting significantly downward on 5 of 6 Audiobox +
  DNSMOS P.808 cells under paired-z + Bonferroni-12; the 6 DNSMOS
  P.835 cells showed no significant shift; two of three scoring
  models detected the drift, the third did not — see F-12 in
  [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md#f-12)).
- Long-stratum hygiene gate flip: Orpheus's `worst_noise_floor_dbfs`
  moved from −52.78 dB (R2, pass) to −27.75 dB (R3, fail), most likely
  a truncation-tail artefact on the 14.59-s output cap.

**When to run R3**: if you want to publish a "measurement stable
over N weeks" claim; if you need to adjudicate the RTF gate; if you
want to see whether a specific vendor's model has drifted since your
first run.

---

## Reproduce the Phase 2 experiment pack

The 5-experiment pack (2026-09-01) + 4 follow-ups answered three
loose ends from R2+R3 (F-6 fade generalisation, F-7 voice-swap
consistency, F-11 latency session-count). Full report:
[EXPERIMENTS_2026-09-01.md](EXPERIMENTS_2026-09-01.md). Total
metered spend: **~$3.55**.

Each experiment reproduces from a single script:

```powershell
# A — 20 authored long-form items × ElevenLabs charlotte
uv run python scripts/_experiment_pack.py A

# B — 5 ElevenLabs voices on L03
uv run python scripts/_experiment_pack.py B

# C — L03 halves (chunk-mitigation check)
uv run python scripts/_experiment_pack.py C

# D — S4 + S5 latency sessions (OpenAI + ElevenLabs, 50 trials each)
uv run python scripts/_experiment_pack.py D

# E — alt-voice sweep (OpenAI, Fish, Deepgram, Google — 8 items each)
uv run python scripts/_experiment_pack.py E

# Drift analysis on every generated WAV (Experiments A/B/C/E + the
# R3 primary-campaign narration audio for Follow-up 1's cross-vendor
# fade rate)
uv run python scripts/_experiment_pack.py drift
```

**Follow-up analyses**:

```powershell
# Follow-up 1 — cross-vendor pinned-voice fade rate on R3 primary
uv run python scripts/_item1_primary_narration_drift.py

# Follow-up 2 — cost reconciliation (per-experiment + per-vendor)
uv run python scripts/_item2_cost_reconcile.py

# Follow-up 3 — S4 + S5 latency sanity vs S1-S3 baseline
uv run python scripts/_item3_latency_sanity.py

# Follow-up 4 — alt-voice E audio through the full analyzer chain
#   Step 1: build a synthetic run-store that lets `veval analyze`
#   work on the E audio (copies E WAVs + fabricates a manifest.json)
uv run python scripts/_build_synthetic_e_runstore.py
#   Step 2: analyze quality + WER (~5 hrs CPU wall-clock)
uv run veval analyze experiments-2026-09-01-E `
  --stages acceptance,quality,wer --skip-ttsds
#   Step 3: compute the alt-vs-pinned paired-z table
uv run python scripts/_item4_e_vs_pinned.py
```

**Render the report body**:

```powershell
# Renders EXPERIMENTS_2026-09-01.md body from the committed
# analysis/experiments-2026-09-01/*.json + logs/*.jsonl
uv run python scripts/_experiment_report.py
```

**Inputs**:

- 20 authored items for A: [`analysis/experiments-2026-09-01/inputs/A_items.json`](../analysis/experiments-2026-09-01/inputs/A_items.json)
- L03 halves for C: [`analysis/experiments-2026-09-01/inputs/C_l03_halves.json`](../analysis/experiments-2026-09-01/inputs/C_l03_halves.json)
- Long items (L01..L08) for E: [`analysis/experiments-2026-09-01/inputs/E_long_items.json`](../analysis/experiments-2026-09-01/inputs/E_long_items.json)

**Uncompleted cheap tests** (proposed, not yet run — flagged for
future revision):

- **T10 — Orpheus `max_new_tokens` check.** ~$0.01, one Replicate
  call. Passes a large `max_new_tokens` in the request payload and
  measures whether the 14.59-s output cap extends. Distinguishes
  "model-intrinsic cap" from "deployment-config default", which
  changes the PM recommendation (one API-flag flip vs a
  chunking-engineering workstream). Currently the README and
  05_CASE_STUDY.md footnote both flag this as untested.
- **Sample-rate header sweep.** ~$0.10, one probe per vendor. For
  each vendor, generates a short clip and verifies the WAV header's
  declared sample rate matches the actual data-chunk sample rate.
  Related to the streamed-WAV-header defect class fixed by
  `finalize_wav_header()` (see F-1a and
  [`dx/friction_log.md`](../dx/friction_log.md)) — this test would
  confirm no vendor is *still* shipping a placeholder sample rate.

Both scaffolds sit in the "cheap tests not yet run" list at
[07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md).

---

## Run the Phase 2c verification pack

Each of the 9 verification tests has a scaffold in
[analysis/verification/](../analysis/verification/) with a
pre-registered hypothesis + falsifiable success criterion. To
re-run any of them, follow the test's `## Method` section — e.g.:

```powershell
# T4 — regenerate L03 × 3 fresh
uv run veval generate --mode campaign `
  --provider elevenlabs --items L03 --use-case narration `
  --no-cache --spend-cap 0.50
# (run 3 times to get n=3 draws; each takes ~15 seconds)
uv run veval analyze <new-run-id> --stages drift

# T6 — Speechify alt-voice regen using the T6 overlay
uv run veval generate --mode campaign `
  --provider speechify `
  --items S01 --items S02 ... --items E04 `
  --voices-file configs/voices.T6.yaml `
  --no-cache --spend-cap 1.00
uv run veval analyze <new-run-id> --stages acceptance,quality --skip-ttsds

# T8 — Orpheus cost + output-cap measurement
uv run veval generate --mode campaign `
  --provider orpheus --items L01 --items L02 ... --items L08 `
  --use-case narration --no-cache --spend-cap 1.00
uv run python scripts/_t8_analysis.py
```

Full per-test commands + expected verdicts in the individual
scaffold files under `analysis/verification/T*.md` and `N*.md`.

---

## Alternative-configuration guides

### Add a new vendor

1. Add adapter class in [`src/veval/adapters/<vendor>.py`](../src/veval/adapters/)
2. Register in `src/veval/adapters/__init__.py`
3. Add vendor entry to [`configs/providers.yaml`](../configs/providers.yaml)
4. Add voice+model rows to [`configs/voices.yaml`](../configs/voices.yaml)
   (one per use case)
5. Add pricing to [`configs/pricing.yaml`](../configs/pricing.yaml)
6. Run `veval doctor --provider <new-vendor>` — should be green
7. Amend `DEVIATIONS.md` with the addition + re-tag `prereg-v1.N`
   (see D-003 for the pattern)

### Swap a voice for one vendor

```powershell
# Copy the base voices file, edit the row you want to change
Copy-Item configs/voices.yaml configs/voices.custom.yaml
notepad configs/voices.custom.yaml

# Run with the overlay
uv run veval generate --mode campaign --provider <vendor> `
  --voices-file configs/voices.custom.yaml
```

See [`configs/voices.T6.yaml`](../configs/voices.T6.yaml) for the
overlay pattern used by T6 verification.

### Use a different corpus

Edit or replace [`corpus/conversational.yaml`](../corpus/) +
[`corpus/narration.yaml`](../corpus/). Corpus schema is documented
in [`src/veval/config.py`](../src/veval/config.py) `CorpusFile`.

For a fully-alternative corpus, expect to re-derive the corpus's
per-item character/word statistics + the per-strata split.

---

## Troubleshooting

### `uv sync` fails on `.venv/lib64: Access is denied`

You're on Windows with a `.venv` originally created inside a Linux
devcontainer. Delete the venv and re-create:

```powershell
Remove-Item -Recurse -Force .venv
uv sync --extra admin --extra dev
```

### Doctor: adapter returns 4xx or 5xx

- Verify your `.env` key is valid via the vendor's own console
- Check `configs/providers.yaml` for the endpoint URL — some
  vendors change these (see D-005 for Orpheus, D-006 for OpenAI,
  D-008 for Speechify)
- Check `configs/voices.yaml` for a valid `voice_id` — some voice
  enums differ between models (see D-007)

### `veval analyze --stages quality` fails on first run

Model downloads. First run needs internet + ~5 GB free disk.
Subsequent runs are offline.

### `veval analyze --stages wer` fails with torch/CTranslate2 errors

Faster-whisper needs a specific torch/CTranslate2 pair. If your
platform mismatches the pin in `pyproject.toml`, wipe `.venv` and
`uv sync` from scratch.

### Spend cap tripped mid-campaign

Expected behaviour. In-flight calls completed; subsequent were
skipped. Re-run with either a higher cap (`--spend-cap 5.00`) or
resume from the partial results — cache will skip anything already
completed.

### DNSMOS refuses items with `ValueError: values must be between -1 and 1`

Also expected — this is Cartesia's F-4a behavior (peak amplitude
= 1.0). The analyzer classifies it as `input_peak_out_of_range`
and continues; the file contributes to the error-rate stat but
not to the DNSMOS mean.

---

## Where to go next

- [01_ARCHITECTURE.md](01_ARCHITECTURE.md) — what the harness looks
  like under the hood
- [02_METHODOLOGY.md](02_METHODOLOGY.md) — the *why* behind the
  choices baked into the commands above
- [04_RESULTS.md](04_RESULTS.md) — the numbers this runbook
  reproduces
- [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md) — the interpreted
  findings with a decision log
- [../DEVIATIONS.md](../DEVIATIONS.md) — the 11 pre-registered
  amendments, with rationale for each
