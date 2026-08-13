# voice AI provider evaluation

**An independent evaluation of 8 commercial voice AI vendors across
two production-realistic use cases, using two independent quality
pipelines, with every decision and deviation traceable to a git
commit that predates the results.**

> **The one thing to know before you keep reading:**
> Two peer-reviewed machine-quality raters, applied to the same 8
> vendors, **rank them differently**. Meta's Audiobox and Microsoft's
> DNSMOS have a cross-pipeline Spearman ρ of **−0.13 on conversational
> and −0.27 on narration**. Whichever leaderboard you're used to
> looking at, ask: *ranked on what?*

> **⚠ Scope disclaimer** · Findings are as of 2026-08-12, on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. No financial
> relationship with any vendor. Not legal/business/purchasing advice.
> Full scope + corrections process in [DISCLAIMER.md](DISCLAIMER.md).

---

## What did we find?

Three headline findings and one meta-observation, each backed by an
artefact in this repo:

| # | Finding | Evidence |
|---|---|---|
| 1 | **The two independent quality raters rank vendors differently.** Consumer-facing warmth vs enterprise cleanliness are literally *different constructs*, not different weightings of the same one. | [Figure 1](documentation/figures/f1_rank_inversion.png) · [F-8 in 06_KEY_FINDINGS](documentation/06_KEY_FINDINGS.md#f-8) |
| 2 | **A 14.59-second output cap was observed on every Orpheus call at the hosted Replicate endpoint** (std dev 0.000s across 8 items). Long-form narration is 5-6× the nominal per-call cost at this cap, and the 85% word-error-rate on long items is mechanical incompletion. Cap may be model-intrinsic OR a deployment-config parameter (`max_new_tokens`) — untested; recommendations differ. | [T8 verdict](analysis/verification/T8_orpheus_cost.md) |
| 3 | **Latency *speed* and latency *stability* are separate axes.** OpenAI's p90 TTFA shifted 56% between two sessions on the same days as ElevenLabs Flash's shifted 2%. | [Figure 3](documentation/figures/f3_latency_stability.png) · [T5](analysis/verification/T5_openai_latency.md) & [T7](analysis/verification/T7_elevenlabs_ttfa.md) |
| ★ | **~40% of the load-bearing findings came from the verification pack**, not the primary campaign. Cheap replication ($0.61 total spend, 90 min work) is where you learn the difference between a real finding and a lucky draw. | [analysis/verification/](analysis/verification/) |

---

## Where to read

The 7 numbered documents in [`documentation/`](documentation/)
are the full narrative. Read them in order for the end-to-end
story, or pick the one that matches what you're here for:

1. **[01_ARCHITECTURE.md](documentation/01_ARCHITECTURE.md)** — how
   the harness is built (adapters, run store, analyzer chain,
   config discipline)
2. **[02_METHODOLOGY.md](documentation/02_METHODOLOGY.md)** — why
   the methodology choices were made (2 MOS pipelines, 2-judge
   WER, pre-registration, verification pattern, honest limits)
3. **[03_RUNBOOK.md](documentation/03_RUNBOOK.md)** — install +
   run + reproduce the published measurements
4. **[04_RESULTS.md](documentation/04_RESULTS.md)** — full per-vendor
   data table + rankings + cost calculus + decision framework
5. **[05_CASE_STUDY.md](documentation/05_CASE_STUDY.md)** — long-form
   portfolio narrative on how the findings were extracted
6. **[06_KEY_FINDINGS.md](documentation/06_KEY_FINDINGS.md)** — the
   9 findings (F-1..F-9) + friction-point stories + 8-decision log
   (D-A..D-H)
7. **[07_GAPS_AND_FUTURE_WORK.md](documentation/07_GAPS_AND_FUTURE_WORK.md)** —
   what wasn't done and why; deferred items; a proper v2 outline

**Quick paths by reader type**:

- **PM choosing a vendor** → read **04_RESULTS.md** first (headline
  table + decision framework), then **05_CASE_STUDY.md** for the
  story. 15-20 min total.
- **Fork-and-adapt engineer** → read **03_RUNBOOK.md** for install
  + reproduce, then **01_ARCHITECTURE.md** for the code layout.
- **Evaluation-methodology researcher** → read **02_METHODOLOGY.md**
  for the *why*, then **06_KEY_FINDINGS.md** for the specific
  decisions + findings, then **07_GAPS_AND_FUTURE_WORK.md** for
  the honest limits.

---

## Method in one paragraph

Eight commercial voice AI vendors (ElevenLabs, Cartesia, Fish Audio,
Google Cloud TTS, Deepgram, Canopy Orpheus, OpenAI, Speechify)
evaluated on two use cases (support-agent conversational + long-form
narration) across a 75-item pre-registered corpus per use case. Five
measurement dimensions:

- **D1 · Latency** — TTFA p50/p90 from 50 serial trials per vendor per
  session, with **two sessions two days apart** for the two
  speed-critical vendors to separate speed from stability
- **D2 · WER** — two ASR judges (Meta `wav2vec2-large-robust` + OpenAI
  `faster-whisper large-v3`), agreement-based failure detection.
  Judges required to differ in *organisation*, *encoder architecture
  family*, AND *training pipeline* (enforced by Pydantic validator)
- **D3 · Quality** — two independent MOS pipelines: Meta's Audiobox
  Aesthetics (aesthetic warmth axes) + Microsoft's DNSMOS P.835
  (signal cleanliness axes). Six machine-quality signals total per
  (vendor, use case)
- **D4 · Human perceptual rating** — deferred to a v2 multi-rater
  panel with written rationale in [06_KEY_FINDINGS.md § D-H](documentation/06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2).
  n=1 self-rating cannot license "human preference" claims at
  population level; refusing that ceremony is a stronger position
  than executing and disclaiming it
- **D5 · Cost** — full pricing model (`pricing.yaml`) covering
  monthly minimums, included tiers, and per-1K-word rates at 10K /
  100K / 1M words per month

Corpus, gates, voices, models, and analyzer parameters frozen in
git tag `prereg-v1` before results existed; amendments logged in
[DEVIATIONS.md](DEVIATIONS.md) with rationale and re-tagged (v1.1
through v1.10). A separate **Phase 2c verification pack** (9 tests,
~$0.61 spend) confirmed or refuted every headline outlier — verdicts
under [analysis/verification/](analysis/verification/). Total
project spend across 8 vendor accounts: ~$56.

---

## Reproducing the work

**Requires:** Python 3.11, [`uv`](https://docs.astral.sh/uv/) as
package manager, ~5 GB disk for model downloads, and API keys for
whichever vendors you want to include. Native Windows, macOS, or
Linux — all supported.

```bash
# Clone + install
git clone https://github.com/ngera/VoiceModelEvaluation.git
cd VoiceModelEvaluation
uv sync

# Add API keys to .env (copy .env.example first)
cp .env.example .env
# Edit .env with your provider keys

# Verify everything's wired up
uv run veval doctor --all-providers

# Generate audio for a small pilot (10 items × 8 providers × 2 use cases)
uv run veval generate --mode campaign --spend-cap 5.00

# Analyze
uv run veval analyze <run-id> --stages all
# Outputs go to analysis/<run-id>/*.json
```

**Full run** (75 items × 8 vendors × 2 use cases) is ~$50 and takes
~30 min end-to-end. See
[03_RUNBOOK.md](documentation/03_RUNBOOK.md) for the phased
execution guide, install steps, and troubleshooting.

**CPU-only by design** (see D-F in
[06_KEY_FINDINGS.md § decisions](documentation/06_KEY_FINDINGS.md#decisions)):
the whole thing runs on commodity hardware. GPU accelerates
wall-clock but doesn't change any measurement. See
[configs/hardware.yaml](configs/hardware.yaml).

---

## Repo layout

```
README.md                        ← this file
DEVIATIONS.md                    ← 11 pre-registered amendments with rationale
CORRECTIONS.md                   ← 20 retracted claims across 5 review rounds, each traceable to a committed artefact
CLAUDE.md                        ← project-wide conventions
pyproject.toml                   ← uv-managed Python 3.11 env

configs/
├── providers.yaml               ← 8 vendors, endpoints, env keys
├── voices.yaml                  ← locked voice + model per (vendor, use case)
├── voices.T6.yaml               ← T6-specific overlay (edmund_32)
├── corpus/                      ← 75 items per use case
├── gates.yaml                   ← pass/fail thresholds
├── analyzers.yaml               ← pinned analyzer parameters
├── pricing.yaml                 ← cost model per vendor + tier
└── hardware.yaml                ← reproducibility receipt

src/veval/
├── adapters/                    ← one per vendor
├── analyze/                     ← per-dimension analyzers
│   ├── quality.py               ← Audiobox + DNSMOS
│   ├── cross_metric.py          ← Spearman across 6 signals (F-8)
│   ├── wer.py                   ← two-judge agreement
│   ├── latency.py               ← TTFA / RTF
│   ├── hygiene.py               ← clipping, LUFS, noise floor
│   ├── drift.py                 ← per-third analysis
│   ├── variance.py              ← within-provider stability
│   └── cost.py                  ← from pricing.yaml
├── cli.py                       ← veval subcommands
├── config.py                    ← Pydantic v2 config validation
├── doctor.py                    ← per-vendor probe
├── runner/                      ← async request runner with spend cap
├── store/                       ← immutable run store
├── admin/                       ← Streamlit local dashboard
└── rate/                        ← BT judgment ingest (deferred)

documentation/
├── 01_ARCHITECTURE.md           ← technical spec + system design (mermaid embedded)
├── 02_METHODOLOGY.md            ← why every methodology choice was made
├── 03_RUNBOOK.md                ← install + reproduce + troubleshooting
├── 04_RESULTS.md                ← full per-vendor data table + cost calculus + decision framework
├── 05_CASE_STUDY.md             ← long-form portfolio narrative
├── 06_KEY_FINDINGS.md           ← F-1..F-9 + friction stories + D-A..D-H log
├── 07_GAPS_AND_FUTURE_WORK.md   ← threats to validity + deferred items + v2 plan
├── figures/                     ← f1_rank_inversion, f2_cost_vs_quality, f3_latency_stability
└── archive/                     ← superseded v1 docs (kept for git-blame trail)

analysis/
└── verification/                ← Phase 2c per-test verdicts (T1..T8, N1, N2)
                                   ← analysis/*.json outputs are gitignored (regenerable)

runs/                            ← immutable audio + api_log (gitignored — regenerable)

tests/                           ← pytest regression suite (~236 tests)
```

---

## Provenance

- **`prereg-v1`** (`git tag prereg-v1`) — the original 6-vendor
  frozen configs, before any campaign result existed
- **`prereg-v1.1` through `prereg-v1.10`** — 10 amendments, each with
  rationale in [DEVIATIONS.md](DEVIATIONS.md). Every amendment
  predates the results that use it.
- **`prereg-v1.10`** is the tag pointing at the state of the configs
  during the current campaign
- Every claim in [04_RESULTS.md](documentation/04_RESULTS.md),
  [05_CASE_STUDY.md](documentation/05_CASE_STUDY.md), and
  [06_KEY_FINDINGS.md](documentation/06_KEY_FINDINGS.md) is either
  derivable from `analysis/*.json` outputs (regenerable from the
  immutable run store) or from a manual verification artefact in
  [analysis/verification/](analysis/verification/)

---

## What's *not* in v1 (and why)

- **Human perceptual rating panel** — deferred to v2 with a proper
  15-30 rater blinded panel; n=1 self-rating BT can't license
  "human preference" claims. See
  [06_KEY_FINDINGS.md § D-H](documentation/06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2).
- **Cross-lingual, accent-varied, or streaming** measurements —
  English-only, one voice per vendor, buffered playback in v1. See
  [07_GAPS_AND_FUTURE_WORK.md](documentation/07_GAPS_AND_FUTURE_WORK.md).
- **Enterprise-colocated latency baseline** — TTFA numbers are from
  a residential Windows 11 environment; enterprise cloud-VM
  measurements would see 10-30% lower absolute numbers. Rankings
  are portable; absolute values are labeled as upper bounds. See D-G
  in [06_KEY_FINDINGS.md § decisions](documentation/06_KEY_FINDINGS.md#decisions).

---

## Contact

Neeraj Gera · [neeraj.gera@outlook.com](mailto:neeraj.gera@outlook.com)

*This project is a portfolio piece demonstrating structured
evaluation, self-critical scoping, and pre-registered methodology
in the context of a commercially-relevant vendor-selection
question. Everything in this repo is committed under a permissive
open-source license; fork and adapt freely.*
