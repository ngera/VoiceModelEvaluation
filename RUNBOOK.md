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

### 2.5 Generate: variance + latency modes (later Phase D sub-phases)

`--mode variance` and `--mode latency` are stubbed — will land in
D.3 and D.4 respectively.

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
