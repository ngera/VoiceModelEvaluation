# voice AI provider evaluation

**An independent evaluation of 8 commercial voice AI vendors across
two production-realistic use cases, using two independent quality
pipelines, with every decision and deviation traceable to a git
commit that predates the results.**

> **The one thing to know before you keep reading:**
> Two peer-reviewed machine-quality raters, applied to the same 8
> vendors, **rank them differently**. Meta's Audiobox and Microsoft's
> DNSMOS have a cross-pipeline Spearman ρ of **−0.13 on conversational
> and −0.27 on narration**. Before quoting a single vendor "quality
> score", ask: *quality on which axis?*

**Which axis matches human perception?** *This study cannot say*
— and that is a deliberate scoping decision, not a hole in the
work. The correlation structure decomposes on **conversational**
(Audiobox's PQ axis agrees with DNSMOS at mean ρ = **+0.24**,
F-8's "clean" side; CE anti-correlates at mean ρ = **−0.51**,
F-8's "warm" side), so the two pipelines are measuring genuinely
different constructs on that use case. **On narration the story
does not hold**: PQ is mixed-sign at ρ = **−0.17** and CE is
also negative at −0.38 — the clean/warm decomposition is a
**conversational-only** result (see [F-8](documentation/06_KEY_FINDINGS.md#f-8)
for the per-pair × use-case table, which 06 states plainly).
But which construct aligns with real listener preference is a
**human-perceptual D4** question, and the only honest way to
answer it is a multi-rater blinded panel. n=1 self-rating can't license
population-level preference claims (see
[D-H](documentation/06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2)
for the deferral rationale — refusing an under-powered ceremony
is a stronger position than executing it and disclaiming the
result). What would settle it: a 15-30 rater blinded panel
comparing the two pipelines' rankings against human preference
per use case, spec-designed and budgeted in
[07 § What a v2 pass would look like item 1](documentation/07_GAPS_AND_FUTURE_WORK.md#what-a-v2-pass-would-look-like).
Until then: pick the pipeline that matches the construct your
listener use case rewards (F-8 § construct decomposition names
which is which), or **read both**.

> **⚠ Scope disclaimer** · Findings are as of 2026-09-01, on specific
> vendor accounts (paid public tiers), specific voice_ids, and a
> residential Windows 11 measurement environment. No financial
> relationship with any vendor. This is a scoped vendor advisory,
> not legal / contractual / financial advice — see
> [DISCLAIMER.md § Not legal or contractual advice](DISCLAIMER.md#not-legal-or-contractual-advice).
> Full scope + corrections process in [DISCLAIMER.md](DISCLAIMER.md).

---

## Have 10 minutes? Start here

**[▶ docs/index.html — one-page decision brief](docs/index.html)**
— the three-question vendor-selection framework, the cross-pipeline
axis-split chart, the cost table (with Orpheus + Speechify pricing
caveats inline), and a "what I got wrong" box linking to
[CORRECTIONS.md](CORRECTIONS.md). Self-contained HTML, no build
step. Everything else on this page is appendix.

**Have longer than 10 minutes?** The 8 numbered documents (plus EXPERIMENTS_2026-09-01.md) in
[`documentation/`](documentation/) are the full narrative — jump to
the [Where to read](#where-to-read) section below.

---

## What did we find?

Three headline findings and one meta-observation, each backed by an
artefact in this repo:

| # | Finding | Evidence |
|---|---|---|
| 1 | **The two independent quality raters rank vendors differently.** Meta's Audiobox measures two axes (technical cleanliness PQ + warm/enjoyment CE); Microsoft's DNSMOS is a second family of scorers (P.808 single-model + P.835 three-scale). **On conversational, PQ agrees with DNSMOS at mean ρ = +0.24 and CE anti-correlates at mean ρ = −0.51** — a real construct split (PQ-side vs CE-side). **On narration the clean/warm split does not hold**: PQ is mixed-sign at ρ = −0.17 and CE is also negative at −0.38, so both axes anti-correlate weakly with DNSMOS on that use case. The decomposition is a conversational-only result — see [F-8 in 06_KEY_FINDINGS](documentation/06_KEY_FINDINGS.md#f-8) for the full per-pair × use-case table. | [Figure 1](documentation/figures/f1_rank_inversion.png) · [F-8 in 06_KEY_FINDINGS](documentation/06_KEY_FINDINGS.md#f-8) |
| 2 | **Orpheus's hosted Replicate endpoint caps output at 14.59 seconds per call.** On the 8-item T8 long-narration probe, every call hit the cap (std dev 0.000 s); on the full 75-item narration corpus, 27 items (36%) were truncated and 48 came back complete because they fit under the cap. Honest per-1K-word cost under T8's measured per-call output (~35 words/call) is ~$0.067–0.088 (2.2–2.9× the nominal $0.030 in the pricing.yaml table, not 5-6×); WER on long items is ~27% (85% is *content loss* on the truncated tail, not word-error rate). **T10 settled it (2026-09-07, one Replicate call)**: cap is Replicate's `max_new_tokens` default; passing `max_new_tokens = 2000` (the Replicate wrapper's own hard ceiling) produces **24.32 s** of audio (1.67× the 14.59 s default) on a single call against one long item (L01 narration, pinned `dan` voice). Bounded fix, not unbounded — the practical Orpheus-on-Replicate ceiling is ~24 s per call, so long-form narration still needs chunking (~1.67× fewer chunks than the default cap requires). Per-1K-words cost at the raised cap: **~$0.040–0.053** (down from $0.067–0.088 under the default cap, still peer-priced to OpenAI's $0.075 rather than the nominal $0.030). See [T10 verdict](analysis/verification/T10_orpheus_max_new_tokens.md) for the recompute + cost math. | [T8 verdict](analysis/verification/T8_orpheus_cost.md) |
| 3 | **ElevenLabs shifted downward on both Audiobox axes + DNSMOS P.808 between R2 and R3 (paired-z 2.26–7.32σ, 5 cells surviving Bonferroni-12).** The P.835 triad's 6 cells (3 conv + 3 narr) all stayed at \|z\| < 1.6. Two of three scoring models detected the drift; the third didn't. Both ElevenLabs models (Flash v2.5 conv, Multilingual v2 narr) drift together — a single-model update does not explain the pattern. This is the finding the "measurement date on every finding" discipline exists to catch — invisible without R3. | [F-12 in 06_KEY_FINDINGS](documentation/06_KEY_FINDINGS.md#f-12) · [analysis/round3-vs-round2-comparison.md](analysis/round3-vs-round2-comparison.md) |
| ★ | **The verification pack changed the framing of multiple headline findings** (T4/T5/T6/T7/T8/F-11 all named individually — see [verification README](analysis/verification/)), and a targeted Phase 2 experiment pack (2026-09-01) further generalised F-6 (loudness fade) from an item-specific quirk to a cross-vendor phenomenon and extended F-7's voice-swap check from 1 vendor to 5. Cheap replication is where you learn the difference between a real finding and a lucky draw. | [analysis/verification/](analysis/verification/) · [EXPERIMENTS_2026-09-01.md](documentation/EXPERIMENTS_2026-09-01.md) |

---

## Where to read

The 8 numbered documents plus EXPERIMENTS_2026-09-01.md in [`documentation/`](documentation/)
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
   11 findings (F-1..F-9 + F-11 + F-12; F-10 slot reserved for BT panel) + friction-point stories + 8-decision log
   (D-A..D-H)
7. **[07_GAPS_AND_FUTURE_WORK.md](documentation/07_GAPS_AND_FUTURE_WORK.md)** —
   what wasn't done and why; deferred items; a proper v2 outline
8. **[08_KEY_FINDINGS_PLAIN.md](documentation/08_KEY_FINDINGS_PLAIN.md)** —
   the same findings as 06, in plain language for non-technical
   readers
9. **[EXPERIMENTS_2026-09-01.md](documentation/EXPERIMENTS_2026-09-01.md)** —
   Phase 2 experiment pack: five targeted experiments + four
   follow-ups that generalised F-6, extended F-7, and confirmed
   S3's latency spike was transient

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
Google Cloud TTS, Deepgram, Canopy Orpheus / `lucataco`
community-fork on Replicate, OpenAI, Speechify)
evaluated on two use cases (support-agent conversational + long-form
narration) across a 75-item pre-registered corpus per use case. The
spec pre-registered **eight** measurement dimensions; here is what
happened to each:

- **D1 · Latency** — TTFA p50/p90 from 50 serial trials per vendor per
  session, with **six sessions across four dates** for the two
  speed-critical vendors to separate speed from stability
- **D2 · WER** — two ASR judges (Meta `wav2vec2-large-robust` + OpenAI
  `faster-whisper large-v3`), agreement-based failure detection.
  Judges required to differ in *organisation*, *encoder architecture
  family*, AND *training pipeline* (enforced by Pydantic validator)
- **D3 · Quality** — three scoring models: Meta's Audiobox
  Aesthetics (2 axes: PQ = technical cleanliness, CE = warm /
  enjoyment — see F-8 for the construct decomposition) + Microsoft's
  DNSMOS P.808 (1 axis: single-model listening-quality MOS) +
  Microsoft's DNSMOS P.835 (3 axes: ovrl / sig / bak from a shared
  internal representation). Six machine-quality signals total per
  (vendor, use case)
- **D4 · Human perceptual rating** — deferred to a v2 multi-rater
  panel with written rationale in [06_KEY_FINDINGS.md § D-H](documentation/06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2).
  n=1 self-rating cannot license "human preference" claims at
  population level; refusing that ceremony is a stronger position
  than executing and disclaiming it
- **D5 · Audio hygiene** — sample-level clipping scan, VAD-based
  pause detection, and ITU-R BS.1770-4 loudness. Produces three of
  the eight pre-registered gates (`clipped_samples`,
  `long_stratum_clipped_samples`,
  `long_stratum_acoustic_noise_floor_dbfs`) and the whole of F-4
- **D6 · Cost** — full vendor pricing model (`pricing.yaml`) covering
  monthly minimums, included tiers, and per-1K-word rates at 10K /
  100K / 1M words per month
- **D7 · Developer experience** — friction log published, timing
  descoped. The per-vendor friction record is at
  [`dx/friction_log.md`](dx/friction_log.md); the docs-to-first-audio
  stopwatch was never run under controlled conditions and cannot be
  reconstructed, so it is cut on the record rather than estimated —
  see [D-I in 06](documentation/06_KEY_FINDINGS.md#d-i)
- **D8 · Capability audit** — factual feature matrix per vendor
  ([`configs/capabilities.yaml`](configs/capabilities.yaml)): voice
  count, languages, cloning, SSML controls, streaming protocol, word
  timestamps, SLA + data residency, pricing shape, determinism,
  commercial use. 65 of 80 cells carry a value with a source URL and
  a verification date; **15 are unresearched and named as such** in
  [07 gap 10](documentation/07_GAPS_AND_FUTURE_WORK.md)

Corpus, gates, voices, vendor models, and analyzer *parameters*
(dataset ids, axis choices, judge selections, gate thresholds)
frozen in git tag `prereg-v1` before results existed; amendments
logged in [DEVIATIONS.md](DEVIATIONS.md) with rationale and
re-tagged (v1.1 through v1.10). Honest exception: the three
analyzer **neural-model revisions** (Audiobox, wav2vec2,
faster-whisper) were not SHA-pinned in the campaign — placeholders
in `configs/analyzers.yaml` propagated into `wer.json`. Disclosed
in [02 § 1](documentation/02_METHODOLOGY.md#1-pre-registration-with-git-tags)
and tracked as [07 gap 9](documentation/07_GAPS_AND_FUTURE_WORK.md). A separate **Phase 2c verification pack**
(10 tests) confirmed or refuted every headline outlier — verdicts
under [analysis/verification/](analysis/verification/). A **Phase 2
experiment pack** (2026-09-01) then addressed three loose ends
F-6, F-7, F-11 raised, with executive writeup in
[EXPERIMENTS_2026-09-01.md](documentation/EXPERIMENTS_2026-09-01.md).

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

**Full run** (75 items × 8 vendors × 2 use cases = 1,200 audio
outputs) takes ~30 min end-to-end. See
[03_RUNBOOK.md § Reproduce the published evaluation](documentation/03_RUNBOOK.md#reproduce-the-published-evaluation)
for the reproduction-cost bands (campaign + variance + latency
S1–S3 + verification pack + Phase 2 experiment pack), and
[DISCLAIMER § Artefact availability](DISCLAIMER.md) for which
cost models are committed vs regenerable.

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
CORRECTIONS.md                   ← retracted-claim register — every claim traceable to a committed artefact; row count grows with review rounds
CLAUDE.md                        ← project-wide conventions
pyproject.toml                   ← uv-managed Python 3.11 env

configs/
├── providers.yaml               ← 8 vendors, endpoints, env keys
├── voices.yaml                  ← locked voice + model per (vendor, use case)
├── voices.T6.yaml               ← T6-specific overlay (edmund_32)
├── gates.yaml                   ← pass/fail thresholds
├── analyzers.yaml               ← analyzer parameters (dataset ids,
│                                  judge selection, gate thresholds
│                                  pinned; neural-model revisions
│                                  were TODO placeholders — see 07 gap 9)
├── pricing.yaml                 ← cost model per vendor + tier
└── hardware.yaml                ← reproducibility receipt

corpus/                          ← 75 items per use case (top-level, not under configs/)
├── conversational.yaml
└── narration.yaml

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
├── human/                       ← BT rating pipeline pieces (pair_builder,
│                                  bt, loudness) — execution deferred (D-H)
├── report/                      ← report generation helpers
└── score/                       ← gates.py + robustness.py (ran in v1,
                                   receipt at analysis/campaign-20260831T175358Z/
                                   score.json) · correlations.py (module
                                   present, receipt block is [] this pass;
                                   F-8's Spearman ρ comes from
                                   analyze/cross_metric.py) · frontier.py
                                   (D-H-blocked; frontiers block is {})

documentation/
├── 01_ARCHITECTURE.md           ← technical spec + system design (mermaid embedded)
├── 02_METHODOLOGY.md            ← why every methodology choice was made
├── 03_RUNBOOK.md                ← install + reproduce + troubleshooting
├── 04_RESULTS.md                ← full per-vendor data table + cost calculus + decision framework
├── 05_CASE_STUDY.md             ← long-form portfolio narrative
├── 06_KEY_FINDINGS.md           ← F-1..F-9 + F-11 + F-12 + friction stories + D-A..D-H log
├── 07_GAPS_AND_FUTURE_WORK.md   ← threats to validity + deferred items + v2 plan
├── 08_KEY_FINDINGS_PLAIN.md     ← same findings, non-technical framing
├── EXPERIMENTS_2026-09-01.md    ← Phase 2 experiment pack + follow-ups
├── figures/                     ← f1_rank_inversion, f2_cost_vs_quality, f3_latency_stability
└── archive/                     ← superseded v1 docs (kept for git-blame trail)

analysis/
├── verification/                ← Phase 2c per-test verdicts (T1..T8, N1, N2) — committed
├── campaign-20260809T204608Z/   ← R2 primary campaign analyzer JSONs — committed
├── campaign-20260831T175358Z/   ← R3 fresh-generation campaign — committed
├── campaign-20260811T180824Z/   ← T6 Speechify voice-swap — committed
├── variance-*/                  ← 3-draw variance subset — committed
├── latency-*/                   ← S1a/S1b/S2/S3/S4/S5 (6 sessions) — committed
├── experiments-2026-09-01/      ← Phase 2 experiment pack — committed
├── experiments-2026-09-01-E/    ← Follow-up 4 alt-voice analyzer output — committed
└── round3-vs-round2-comparison.md ← R2 vs R3 replication comparison — committed
                                   (audio `runs/` are gitignored; analyzer outputs above are un-ignored explicitly per `.gitignore`)

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
- **Enterprise-colocated latency baseline** — TTFA numbers are
  from a residential Windows 11 environment; enterprise cloud-VM
  measurements would likely see lower absolute numbers, though we
  cannot bound the direction rigorously. Rankings are portable
  across the 6 sessions we ran; absolute values are
  session-to-session observations, not ceilings. See D-G in
  [06_KEY_FINDINGS.md § decisions](documentation/06_KEY_FINDINGS.md#decisions)
  and F-11.

---



*This project is a portfolio piece demonstrating structured
evaluation, self-critical scoping, and pre-registered methodology
in the context of a commercially-relevant vendor-selection
question.*

---

## Licence

Dual-scope, per path — see [`LICENSE`](LICENSE) for the full text.

- **Code** (`src/`, `tests/`, `scripts/`, `configs/`, `dx/`,
  `pyproject.toml`, etc.) — **Apache License 2.0**. The explicit
  patent grant is chosen deliberately for a harness others will
  run against their own vendor accounts.
- **Content** (`documentation/`, `docs/`, `analysis/`, `corpus/`,
  `README.md`, `DISCLAIMER.md`, `DEVIATIONS.md`, `CORRECTIONS.md`,
  and the figures under `documentation/figures/`) —
  **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
  Share and adapt with attribution.

The 15 contamination-probe items per use case (Harvard sentences +
literary openings, IDs P01–P15) are pre-existing public-domain
text; their inclusion does not create additional rights over that
source material. Vendor and analyzer names are trademarks of their
respective owners, used for factual identification only. `LICENSE`
governs re-use rights only; it does not modify [`DISCLAIMER.md`](DISCLAIMER.md)'s
scope, non-affiliation, and not-advice statements.
