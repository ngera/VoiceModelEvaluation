---
title: Execution Runbook — Post-Build
project: Voice AI Provider Evaluation (descoped v1)
assumes: Harness built and tested (adapters, runner, VERSA analyzers, voting page, report generator all working)
companion: voice_ai_eval_plan_v1_descoped.md
---

# Execution Runbook — what happens after the build

High-level operational plan from "the code works" to "results published and maintained." Six phases; calendar time ~2.5 weeks part-time for the campaign itself, then ~2 hrs/month to operate.

---

## Phase 0 — Pre-flight & pre-registration (half a day)

The credibility of everything downstream is established here, before any data exists.

1. **Accounts & keys**: all providers from Appendix B live in `.env`; billing dashboards checked (all at ~$0); spend alerts set where the console supports them.
2. **Smoke test**: `veval doctor` — 1 corpus item through every provider end-to-end (synthesize → store → analyze). Fix adapter breakage now, not mid-campaign.
3. **Lock the pre-registration set** and tag it in git as `prereg-v1`:
   - `corpus/` (hybrid: novel items + contamination probe set)
   - `gates.yaml` (per-use-case gates + one-line rationales)
   - `voices.yaml` (one voice per provider per use case + selection reasoning)
   - `providers.yaml` (exact model strings)
4. **Freeze rule**: after this tag, corpus/gates/voices don't change for the v1 campaign. Any discovered mistake gets logged in `DEVIATIONS.md` with rationale rather than silently fixed — deviations disclosed beat perfection claimed.

**Go/no-go:** every provider passes smoke test, or is formally dropped with a note. Do not start Phase 1 carrying a "mostly working" adapter.

---

## Phase 1 — Generation campaign (3–4 days elapsed, mostly waiting)

1. **Sequence by constraint**: Fish Audio first (free S2.1-Pro window closes Aug 31), then remaining providers in any order; ElevenLabs last (start its paid month as late as possible so the subscription window covers any re-runs).
2. **Quality corpus runs** from the laptop: full corpus × every provider × both use cases → immutable `runs/<run_id>/` with manifests.
3. **Latency campaign** from the pinned cloud VM only: TTFA trials split across ≥2 days and ≥2 times of day (this is why the phase has elapsed days); RTF measured on long passages in the same sessions.
4. **Budget checkpoint** after the first two providers: actual spend vs. Appendix B estimate. If off by >2×, stop and diagnose (usually a retry loop or a wrong quality tier) before burning the rest.

**Failure playbook**: provider errors are logged as data, never hand-patched; a provider that deprecates or swaps a model mid-campaign gets a full clean re-run under a new manifest (partial mixes of model versions are worthless). The content-hash cache makes re-runs cost only the changed items.

**Exit criteria:** every provider has a complete manifest, audio set, and api_log; latency data spans two days.

---

## Phase 2 — Automated analysis (1–2 days, mostly compute)

1. `veval analyze` across all runs: two-judge WER (Parakeet + faster-whisper), TTSDS2 + Audiobox quality, hygiene (VAD silences, clipping, LUFS).
2. **Manual-listen queue**: every WER-flagged and artifact-flagged file gets human ears before the result is attributed to the provider. Timebox: if the queue exceeds ~40 files, sample it and say so.
3. **Contamination probe cut**: compare famous-sentence vs. novel-sentence performance per provider; park the result for the write-up.
4. Freeze analysis outputs as versioned JSON — Phase 3+ reads these, never recomputes silently.

**Exit criteria:** analysis JSONs complete for all providers; manual-listen queue resolved or explicitly sampled.

---

## Phase 3 — Human judgment (spread over ~1 week of short sessions)

1. Loudness-normalize all clips to −18 LUFS; build the blinded A/B pair pool with hidden human anchors.
2. **Self-judging in short sessions**: 20–30 minutes max per sitting (ear fatigue is real and shows up in the data); spread across days.
3. **Consistency re-judge**: 10% of pairs repeated ≥5 days later; compute and record self-agreement — this number gets published.
4. Optional: send the voting page to 5–10 friends for the n≈10 upgrade; keep their judgments segregated by rater ID.
5. Fit Bradley–Terry; anchor to the human recordings; freeze `humanness_ours.json`.

**Exit criteria:** enough pairs for stable fit (every provider pair covered ≥3×), self-consistency computed.

---

## Phase 4 — Decision layer (1–2 days)

Pure computation + thinking; zero new data.

1. Apply pre-registered gates → per-use-case survivor lists (gate failures documented with the measured value that failed).
2. Build Pareto frontiers (quality × cost, quality × latency) per use case.
3. Gate-robustness pass: ±20% on each gate; record any frontier changes.
4. External cross-checks: Δ vs. Humanness Index scores; "Reproduces?" check on their latency figures; capability-matrix facts merged into memos.
5. Draft the two 1-page decision memos while the analysis is fresh.

**Exit criteria:** frontiers + robustness notes done; memos drafted; no result changed after this point except via a logged deviation.

---

## Phase 5 — Ship (3–4 days)

1. **Write-up**: method (lift from Appendix A), findings, frontier charts, HI audit section, contamination probe, honest limitations (n, staleness date, what wasn't measured).
2. **Publish surface**: `veval report` → static results site (GitHub Pages) + repo with README that lets a stranger re-run everything; curated audio sample set only (not the full 1,000+ files).
3. **Date-stamp everything visible** — scores, prices, capability cells.
4. **Distribute** where voice-AI people actually are: a launch post (LinkedIn/X), HN "Show HN", r/LocalLLaMA / r/MachineLearning as fits; send the HI-audit section to Vapi's benchmark contact (humannessindex@vapi.ai) — a correction request from them is engagement, not a threat.
5. Cancel/downgrade paid subscriptions opened for the campaign (ElevenLabs Creator, Speechify Starter, Cartesia Pro).

**Exit criteria:** public URL live; repo reproducible; subscriptions closed.

---

## Phase 6 — Operate (ongoing, ~2 hrs/month)

This is where the project outlives every static leaderboard.

1. **Monthly re-run**: same corpus, same gates; content-hash cache means only changed provider models actually spend money (typical month: $5–15). New `run_id`, new date-stamp on the site.
2. **Drift report**: one short changelog entry per re-run — model swaps, price changes, latency shifts, frontier changes. Over 3–4 months this becomes a unique artifact: *longitudinal provider drift data that nobody else publishes.*
3. **Pricing re-verification** each re-run (D6 rule); capability matrix cells re-checked quarterly or on provider announcements.
4. **Roster review quarterly**: new HI entrants, new models (test them), dead providers (the next PlayHT gets a changelog entry, not silence).
5. **Issue intake**: corrections from providers or readers get a public issue + a logged resolution — visible error-handling is credibility.
6. **Stop condition**: this is a portfolio project, not a company. After 3–4 monthly cycles the drift story is told; either wind down gracefully (final changelog entry, "archived as of [date]" banner) or consciously decide it's worth continuing. Don't let it become an untended, silently-stale leaderboard — that's the exact failure mode this project critiques.

---

## Standing rules (all phases)

- **Immutability**: nothing in `runs/` is ever edited; every number is recomputable from raw.
- **Deviations over silent fixes**: any departure from the pre-registered setup goes in `DEVIATIONS.md`.
- **Errors are data**: provider failures feed D7/reliability notes; they are findings, not embarrassments.
- **Timeboxes beat completeness**: sampled-and-disclosed beats exhaustive-and-never-shipped.
