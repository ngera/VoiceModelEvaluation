# RUNBOOK.md — operational commands for this project

Lives at repo root next to [CLAUDE.md](CLAUDE.md) and [DEVIATIONS.md](DEVIATIONS.md).
Kept up to date as new commands are added. Different from
[documentation/voice_ai_eval_execution_runbook.md](documentation/voice_ai_eval_execution_runbook.md),
which is the post-build **campaign** runbook — this file is the **build/dev**
runbook you use while shipping the code.

Convention: every command in this file has (1) what it does, (2) when
to use it, (3) the exact invocation, (4) what you should see. If a
command isn't in here, it hasn't been introduced yet.

---

## 0. Prerequisites (once per machine)

### 0.1 Python + uv installed

Native Windows workflow (spec §Environment strategy — devcontainer is optional):

```powershell
# Python 3.11 from python.org or Microsoft Store
# uv from https://astral.sh/uv
python --version   # should be 3.11.x (any stable 3.11 works)
uv --version       # should be recent (0.5+)
```

### 0.2 Repo checked out with real `.env`

```powershell
git clone https://github.com/ngera/VoiceModelEvaluation.git
cd VoiceModelEvaluation
Copy-Item .env.example .env
notepad .env       # paste real API keys per provider
```

The `.env` and `.secrets/` folder are both gitignored. Google
service-account JSON goes in `.secrets/`; the path is set via
`GOOGLE_APPLICATION_CREDENTIALS` in `.env` (currently unused because
we chose API-key auth for Google — see [DEVIATIONS.md D-003](DEVIATIONS.md)).

### 0.3 Install project + dependencies

```powershell
uv sync --extra admin --extra dev
```

**What it does:** creates `.venv/`, installs pinned Python dependencies
from `uv.lock`, plus the `admin` extra (Streamlit) and `dev` extra
(pytest, ruff, mypy). Skips the `analyze` extra — those Linux/CUDA-first
libs land in Phase E via the devcontainer.

**When to use:** first time on a machine, or after pulling `pyproject.toml`
or `uv.lock` changes.

### 0.4 Nuke `.venv` if switching from devcontainer to native Windows

```powershell
Remove-Item -Recurse -Force .venv
uv sync --extra admin --extra dev
```

**Why:** Linux venvs create a `lib64` symlink that Windows can't touch.
`uv sync` fails on `lib64` with "Access is denied" until the whole
folder is removed. Only needed if you originally built the venv inside
the devcontainer. See [dx/friction_log.md](dx/friction_log.md)
Environment gotchas.

---

## 1. Doctor — end-to-end adapter health check

Same spirit as `brew doctor` / `flutter doctor`. Loads configs, checks
env vars, calls `adapter.synthesize()` once per provider, writes to
`runs/doctor-<timestamp>/`.

### 1.1 Doctor: single provider

```powershell
uv run veval doctor --provider <name>
```

Provider name is one of: `deepgram`, `fish`, `google`, `cartesia`,
`elevenlabs`, `openai`, `speechify`, `orpheus`.

**When to use:**
- After adding or fixing an adapter (Phase C)
- After a `voices.yaml` edit (to verify new voice_id works)
- After a `providers.yaml` edit (to verify new endpoint/model/version)
- Before spending money on a campaign — this is the low-cost gate

**What you should see:**

```
configs                ✓ configs\providers.yaml — 8 providers · voices.yaml (16 locks)
env keys               8/8 present
adapters registered    8

                              Adapters
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┓
┃ Provider ┃ Status ┃ TTFA (ms) ┃ Total (ms) ┃ Audio bytes ┃ Notes ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━┩
│ deepgram │ ✓      │       600 │       1800 │       50000 │       │
└──────────┴────────┴───────────┴────────────┴─────────────┴───────┘

All 1 adapters passed.
Run written to: runs\doctor-<timestamp>\
```

Non-zero exit code if any adapter fails — useful in CI.

### 1.2 Doctor: all providers

```powershell
uv run veval doctor
```

Runs every registered provider. **This is the Phase C exit criterion** —
every green means adapters are ready for Phase D.

### 1.3 Doctor: narration use case (defaults to conversational)

```powershell
uv run veval doctor --use-case narration
```

Doctor uses `voices.yaml` to resolve `(voice_id, model)` per
`(provider, use_case)`. Default is `conversational`; add `--use-case
narration` to smoke-test the narration voice+model pair.

### 1.4 Doctor cost per invocation

Rounding-error small. Sends one short probe text
("The quick brown fox jumps over the lazy dog.") per provider. For
split-model providers (Fish), doctor uses the free-tier `quality_model`
to avoid burning paid credits on a smoke test.

---

## 2. Generate — campaign runner (Phase D)

Same run store shape as doctor; writes to `runs/<mode>-<timestamp>/`.

### 2.1 Generate: single-item smoke test

```powershell
uv run veval generate --mode campaign --provider deepgram --use-case conversational --items S01
```

**When to use:** validate the runner + adapter pipeline before spending
on a bigger run. `--items` accepts a space-separated (or repeated flag)
list of corpus item IDs.

**What you should see:**
- 1 audio file written to `runs/campaign-<ts>/audio/deepgram/conversational/S01.wav`
- Summary table showing 1 ok · 0 failed
- Runtime ~2 seconds

### 2.2 Generate: $1 pilot (Phase D.7 exit criterion)

```powershell
uv run veval generate --mode campaign --items S01 --items M01 --items L01 --items J01 --items E01
```

Runs 5 items × 8 providers = 40 files across both use cases (unless
`--use-case` restricts). Total cost <$1 given current pricing. This is
the pilot that gates the real campaign run.

### 2.3 Generate: full campaign

```powershell
uv run veval generate --mode campaign
```

Runs 75 × 2 × 8 = **1200 files**. Only run after the $1 pilot returns
green. Full-campaign cost estimate ~$46–57 per spec §8.

### 2.4 Generate: filters

```powershell
# One provider, both use cases, full corpus
uv run veval generate --mode campaign --provider fish

# Both providers, one use case
uv run veval generate --mode campaign --provider deepgram --provider openai --use-case conversational

# Restricted item subset (repeat --items per item)
uv run veval generate --mode campaign --items S01 --items S02 --items S03
```

### 2.4b Generate: spend cap (D.5)

Every generate run is gated by a USD spend cap. The tracker estimates
per-call cost from `configs/pricing.yaml` (conservatively — highest
rate row wins when a provider has multiple pricing tiers, so estimate
overshoots rather than undershoots).

**Default cap: $100** (from `VEVAL_SPEND_CAP_USD` in `.env`).

**Override per-run:**

```powershell
# Tight cap for a smoke test
uv run veval generate --mode campaign --provider deepgram --items S01 --spend-cap 0.10

# Disable entirely (careful!)
uv run veval generate --mode campaign --no-spend-cap
```

**Behaviour when cap trips:** the call that would have exceeded the
cap is refused (no API call made). Any calls already in flight
complete normally; all subsequent submissions are skipped and logged
as `"status": "skipped", "reason": "spend_cap_exceeded"`. The run
finalizes normally with a partial result.

**Every generate summary shows an "Estimated spend (USD)" table** at
the end so you can see where the money went.

**Warning at 80%:** printed once when running total crosses 80% of the
cap. Not another chance to gate; just a heads-up.

### 2.5 Generate: bypass cache

By default, campaign mode uses a **content-hash cache** at
`.cache/synthesis/` — re-running the same `(provider, model, voice_id,
text, output_format, sample_rate, version)` returns bytes from disk
instead of hitting the provider API. Cache is disabled automatically
for variance + latency modes (fresh calls are the measurement).

Force fresh calls even in campaign mode:

```powershell
uv run veval generate --mode campaign --provider deepgram --items S01 --no-cache
```

**When to use `--no-cache`:**
- Benchmarking (want fresh TTFA)
- Suspect a cached result is wrong (nuke `.cache/synthesis/` or bypass)
- Re-verifying an adapter change post-fix

**Cache location + safety:** `.cache/synthesis/` is gitignored. Nuking
it loses only compute cost, not measurement data. Cache stats show at
the top of every `generate` invocation.

### 2.5 Generate: variance mode (D.3 — noise-floor measurement)

```powershell
uv run veval generate --mode variance
```

Runs the 10-item variance subset × 3 draws × 8 providers × 2 use cases
= **480 generations**. Feeds into Phase E's `variance.py` analyzer to
compute the per-provider within-provider SD (the measurement noise
floor) — every reported D2/D3 between-provider difference must exceed
`1.96 × SE(difference)` to count (spec §3.4).

**Cache is FORCED OFF for variance mode** — fresh draws are the entire
point. Do not use `--no-cache` (it's already off).

Filters same as campaign:

```powershell
# One provider only (still all 10 items × 3 draws × both use cases = 60 files)
uv run veval generate --mode variance --provider deepgram

# One use case only (10 items × 3 draws × 8 providers = 240 files)
uv run veval generate --mode variance --use-case conversational
```

Adjust `--n-draws` if experimenting (default 3, minimum meaningful):

```powershell
uv run veval generate --mode variance --n-draws 5
```

Cost estimate for the full 480-generation variance run: **~$1–2**
total (mostly Orpheus's ~$0.003/gen × 60; character-billed providers
absorbed in free tiers or trivial paid usage). Spec §8 line item.

### 2.6 Generate: latency mode (D.4 — 50 serial trials per provider)

```powershell
uv run veval generate --mode latency
```

Runs **50 serial trials** per provider on **one short item** (default
S01 conversational). Strictly serial per spec §D1 — concurrent load
contaminates TTFA. Total: 50 × 7 providers = **350 calls** (Orpheus
skipped: D1 is N/A-hosted per spec §3.1).

**Provider-specific behaviour:**
- **Fish** uses the paid `s2.1-pro` model, NOT the free tier. Free
  tier latency is best-effort with no SLA and would not represent a
  deployment.
- **Google** returns buffered REST — TTFA ≈ total_ms; results carry
  `meta.transport = "buffered-rest"` and get a non-comparability
  footnote in the D1 results table (spec §3.1).
- **Orpheus** skipped entirely.
- **Cache is FORCED OFF** — measurement IS the fresh call.

**Filters:**

```powershell
# One provider only, 50 trials
uv run veval generate --mode latency --provider deepgram

# Different corpus item (e.g. a medium item to check TTFA vs input length)
uv run veval generate --mode latency --latency-item M01

# Narration use case
uv run veval generate --mode latency --use-case narration

# Shorter trial run for smoke test
uv run veval generate --mode latency --provider deepgram --trials 5
```

**Scheduling across days / times of day is a manual operator step**,
per spec §D1: "50 trials per provider, split across ≥2 days and ≥2
times of day." Run this command a few times over 48+ hours; Phase E's
`latency.py` analyzer stitches results from all `runs/latency-*/`
directories.

**Cost:** ~$0.10 for a full 350-trial run at defaults. Char-billed
providers absorb this; ElevenLabs pulls ~50 chars × 50 trials × their
per-char rate; Fish uses paid tier so slight paid usage there too.
Rounding-error small.

---

## 3. Admin panel — Streamlit

Local-only interactive front door. Same underlying functions as the CLI
(thin-wrapper convention).

### 3.1 Launch admin panel

```powershell
uv run streamlit run src/veval/admin/app.py
```

**What it does:** starts a Streamlit server on `http://localhost:8501`.
Currently has one page (**Doctor**) that wraps `run_doctor()`. More
pages land per Phase (Run page in D.6, Results in E, Frontier in G).

**When to use:** interactive verification without CLI verbosity, or
demoing the flow to a reviewer.

Stop with `Ctrl+C` in the terminal.

---

## 4. Tests

Pytest suite covers config schema, WAV header handling, run store
invariants.

```powershell
uv run pytest -q
```

Should show 46+ passing. One test
(`test_log_api_serializes_non_json_values`) is red-by-design on
Windows due to path-separator quirks — see [dx/friction_log.md](dx/friction_log.md)
Environment gotchas. Not a functional regression.

---

## 5. Provider-side operational commands (not through veval)

### 5.1 List Speechify voices via API (voice-ID discovery)

Speechify's UI doesn't surface voice_ids in a copyable form.
Alternative: query their voices endpoint directly.

```powershell
uv run python -c "import os, httpx; from dotenv import load_dotenv; load_dotenv(); r = httpx.get('https://api.sws.speechify.com/v1/voices', headers={'Authorization': f'Bearer {os.environ[\"SPEECHIFY_API_KEY\"]}'}, timeout=15); print(r.json())"
```

Returns paginated JSON. Filter to `locale` starting with `en-` and
models containing `simba-3.2`. Only 8 of 956 voices support simba-3.2
(verified 2026-08-07 — see [dx/friction_log.md](dx/friction_log.md)
Speechify section).

### 5.2 Look up Replicate model version SHA (for Orpheus SHA pinning)

```powershell
uv run python -c "import os, httpx; from dotenv import load_dotenv; load_dotenv(); r = httpx.get('https://api.replicate.com/v1/models/lucataco/orpheus-3b-0.1-ft', headers={'Authorization': f'Bearer {os.environ[\"REPLICATE_API_TOKEN\"]}'}, timeout=15); d = r.json(); print(f\"latest version: {d.get('latest_version', {}).get('id')}\")"
```

Use this when bumping Orpheus's pinned SHA in `configs/providers.yaml`
(and log the bump as a new DEVIATION per D-005's amendment rule).

---

## Changelog

- 2026-08-07 — created; populated with Phase A (doctor) + Phase C
  (per-provider doctor probes) + Phase D.1 (`generate --mode campaign`)
  commands, plus env setup, admin panel launch, tests, provider-side
  discovery queries.
