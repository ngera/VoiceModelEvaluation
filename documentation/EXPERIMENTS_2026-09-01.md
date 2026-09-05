<!--
Experiment pack — F-6 deep dive and adjacent hypotheses.
Author: Neeraj Gera · Date: 2026-09-01
Scope: This is a self-contained experiment report. It does not edit or
supersede any of the numbered reports (01-08). Findings here may
inform a future v2 amendment to 06/08, but no in-place edits were made.
-->

# Experiment pack — 2026-09-01

*Five targeted experiments probing F-6 (ElevenLabs L03 monotonic
loudness fadeout) and adjacent hypotheses, run as a standalone probe
after the R3 replication campaign (`campaign-20260831T175358Z`)
completed.*

> **Scope + status** — This is a **new-artefact-only** report.
> Every numbered report (01–08) is untouched. New assets live under
> [`analysis/experiments-2026-09-01/`](../analysis/experiments-2026-09-01/):
> `audio/` (73 fresh WAVs across all 5 experiments), `drift.json`
> (per-file loudness-thirds), `logs/` (per-experiment API logs), and
> `inputs/` (the 20 authored items for A + the L03 halves for C).

---

## Executive summary in one paragraph

The L03 fade **is not unique to L03**, **is not unique to ElevenLabs**,
**is not fully deterministic on a given voice × text combination**, and
appears **stochastic across runs of the same voice on the same text**.
Across 64 primary-campaign L01..L08 narration items on 8 vendors'
pinned voices (Item 1 addition), **6.2% fade at threshold** — with
elevated rates on ElevenLabs (25%), Deepgram (12%), and Orpheus (12%),
and 0% on Cartesia, Fish, Google, OpenAI's pinned voices. Two
new-item experiments (A/E) find similar or higher rates on affected
voices. **Chunking L03 into two halves cuts the fade sharply**
(2.79 dB full → 1.89 dB half 1 → 0.81 dB half 2), consistent with
cumulative internal-state decay reset on each fresh call. And
notably: L03 itself **doesn't fade on charlotte in the R3 campaign
audio** (delta = −0.26 dB, non-monotonic), despite fading 2.79 dB
in the same-day Experiment B — direct evidence that the fade on any
given item is stochastic, not deterministic, across runs. **The
generalizable finding**: monotonic loudness fade on long-form TTS
narration is a real, cross-vendor, cross-voice, run-to-run-variable
phenomenon at roughly 5–25% base rate on affected voice/model
combinations. F-6's original framing ("reproducible text-specific
quirk on one ElevenLabs item") **overstates the reproducibility and
understates the generality**.

---

## Experiment A — is the fade unique to L03? *(headline: NO)*

**Design.** 20 fresh narration paragraphs (200–500 chars each) written
for this experiment, mixed across 4 topic categories (5 each):
technical instructions (TECH), warm storytelling (WARM), dry factual
(FACT), emotional (EMOT). All rendered on the ElevenLabs pinned
narration voice (`qSeXEcewz7tA0Q0qk9fH` / `eleven_multilingual_v2` —
the same combination that generated L03 in the primary campaign).
Drift analyzer applied to each WAV: LUFS of first / middle / last
third; **fade** = Δ(t1 − t3) ≥ 2 dB AND monotonically decreasing.

**Results** (from
[`analysis/experiments-2026-09-01/drift.json`](../analysis/experiments-2026-09-01/drift.json)):

| item | topic | duration | Δ(t1−t3) | monotonic? | classification |
|---|---|---:|---:|---|---|
| **EMOT02** | EMOT | 22.6s | **+2.96 dB** | **True** | **FADE** |
| **FACT03** | FACT | 22.0s | **+2.21 dB** | **True** | **FADE** |
| EMOT04 | EMOT | 18.4s | +1.33 | True | mono-decr (small) |
| EMOT05 | EMOT | 15.4s | +1.20 | True | mono-decr (small) |
| FACT01 | FACT | 24.5s | +1.74 | True | mono-decr (small) |
| FACT02 | FACT | 24.2s | +0.14 | True | mono-decr (small) |
| FACT04 | FACT | 19.2s | +0.96 | True | mono-decr (small) |
| TECH01 | TECH | 18.2s | +0.57 | True | mono-decr (small) |
| WARM01 | WARM | 22.0s | +0.91 | True | mono-decr (small) |
| (11 others) | | | 0.08 – 1.26 | mixed | no fade |

- **2 of 20 items fade** at the threshold (10%)
- **9 of 20 items are monotonically decreasing** across thirds (any magnitude — 45%)
- No item was monotonically *increasing*
- **Per topic (fade / total)**: TECH 0/5, WARM 0/5, FACT 1/5, EMOT 1/5

**Verdict**: L03 is **not** a unique text-dependent quirk. On the
same voice and model, ~10% of long-form paragraphs show the
same-shape fade at the same magnitude. This lands squarely in the
"1–3 of 20 → 5–15% base rate" bucket predicted before running.

**Pattern in the fading items** (with n=2 to work with, this is
suggestive only): both faders (EMOT02, FACT03) are >20s duration
with narrative-flowing content and multiple sentences. Non-faders
in the TECH category tend to be 15-19s with short imperative
sentences. Not enough data to claim a triggering pattern, but the
"long, narrative, multiple-sentence" clustering matches L03's
character.

---

## Experiment B — is the fade voice-specific? *(headline: PARTIAL)*

**Design.** L03 text unchanged. Generated on 5 different ElevenLabs
voices via `eleven_multilingual_v2`. Compare drift on each.

**Results:**

| voice | timbre | duration | Δ(t1−t3) | monotonic? | classification |
|---|---|---:|---:|---|---|
| **charlotte** *(pinned narration)* | female calm | 83.1s | **+2.79 dB** | **True** | **FADE** |
| **josh** | male deep narrator | 87.2s | **+2.92 dB** | **True** | **FADE** |
| rachel | female calm | 82.5s | +0.65 | True | mono-decr (small) |
| antoni | male well-rounded | 84.5s | −0.22 | False | no fade (actually louder at end) |
| bella | female soft | 79.6s | +0.43 | False | no fade |

- **2 of 5 voices fade** on the same L03 text at the threshold
- **1 of 5** shows small monotonic decreasing (below threshold)
- **2 of 5** show no fade at all — one (antoni) is actually louder at the end

**Verdict**: The fade **is not purely a property of the text**. It
also **is not purely a property of the voice**. It's a **text × voice
interaction** — the same L03 text triggers a large fade on some voices
(charlotte, josh) and none on others (antoni, bella).

The two fading voices (charlotte, josh) are both narrator-style
voices with slower cadence; the two non-faders (antoni, bella) are
more energetic-conversational styles. n=5 is too small to make this
into a rule, but the pattern is suggestive: **narrator-tagged
ElevenLabs voices may be more susceptible to the fade** than
conversational-tagged ones.

---

## Experiment C — does chunking help? *(headline: YES)*

**Design.** L03 text split in half at a natural sentence boundary
("The announcement was welcomed by opposition leaders…" starts half 2).
Half 1 = 641 chars, half 2 = 703 chars. Both rendered on the
ElevenLabs pinned narration voice, independent calls.

**Results:**

| segment | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ(t1−t3) | monotonic? |
|---|---:|---:|---:|---:|---:|---|
| **Full L03** (from Experiment B) | 83.1s | −20.43 | −20.94 | −23.22 | **+2.79 dB** | **True — FADE** |
| L03 half 1 (first 641 chars) | 40.0s | −20.19 | −21.20 | −22.09 | **+1.89 dB** | **True** — mono-decr (small, just under threshold) |
| L03 half 2 (last 703 chars) | 40.7s | −20.91 | −22.12 | −21.72 | +0.81 dB | False — no fade |

**Verdict**: **The fade is a cumulative phenomenon that builds up over
the duration of a single generation call**. When L03 is generated as
one 83s call, it fades 2.79 dB. When the same text is split into two
independent ~40s calls, the fade drops sharply — half 1 shows a
smaller monotonic decrease (1.89 dB, just below threshold), half 2
shows no fade at all.

Notably, both halves *start* at similar loudness (−20.2 and −20.9
LUFS) — the fresh call resets the loudness envelope. This is
consistent with an **internal state that decays as the model
processes more tokens** and resets at the start of each new call.

**Observation**: chunking L03 into ≤500-char halves substantially
reduces the measured fade on charlotte-family voices in this
experiment. The mechanism is consistent with a per-generation
internal-state decay that resets on each fresh call. Whether
chunking eliminates the fade entirely or only reduces it is not
settled by n=2 halves. Advisory phrasing of this observation
(e.g., what production narration workflows should do about it)
lives in [06 § F-6](06_KEY_FINDINGS.md#f-6--monotonic-loudness-fade-on-long-form-tts-narration--a-cross-vendor-phenomenon-at-5-25-base-rate)
and [08 finding #12](08_KEY_FINDINGS_PLAIN.md), not here.

---

## Experiment D — 2 more latency sessions (S4 + S5) for ElevenLabs + OpenAI

**Design.** Two fresh latency-mode runs of 50 serial trials each,
on the same S01 conversational item, for both ElevenLabs Flash v2.5
and OpenAI gpt-4o-mini-tts (the pre-registered conversational
model; latency sessions all ran the S01 conversational item).
Same-day (2026-09-01), separated by ~1 hour.

⚠ **Same-day caveat**: F-11's methodology note specifies that
characterizing session-to-session variance properly needs **≥5
sessions across ≥2 weeks**. S4+S5 both on the same day contribute
two more data points but do not fully satisfy the multi-day
requirement. Read them as strengthening the "the S3 outlier was
real, but S1-style values are more typical" story, not as closing
the variance characterization.

**Six-session data table:**

### ElevenLabs

| session | p50 (ms) | p90 (ms) | n |
|---|---:|---:|---:|
| S1a (2026-08-09 21:41) | 439 | 479 | 50 |
| S1b (2026-08-09 22:23) | 440 | 474 | 50 |
| S2  (2026-08-11) | 424 | 469 | 40 |
| S3  (2026-08-12) | 694 | 816 | 40 |
| **S4  (2026-09-01 18:57)** | **412** | **461** | 50 |
| **S5  (2026-09-01 19:10)** | **421** | **468** | 50 |

**ElevenLabs p50 range across 6 sessions: 412–694 ms** (+68% spread)
**ElevenLabs p90 range across 6 sessions: 461–816 ms** (+77% spread)

### OpenAI

| session | p50 (ms) | p90 (ms) | n |
|---|---:|---:|---:|
| S1a (2026-08-09 21:41) | 736 | 956 | 50 |
| S1b (2026-08-09 22:23) | 762 | 946 | 50 |
| S2  (2026-08-11) | 936 | 1493 | 50 |
| S3  (2026-08-12) | 1369 | 1882 | 50 |
| **S4  (2026-09-01 19:07)** | **772** | **1212** | 50 |
| **S5  (2026-09-01 20:10)** | **783** | **1206** | 50 |

**OpenAI p50 range across 6 sessions: 736–1369 ms** (+86% spread)
**OpenAI p90 range across 6 sessions: 946–1882 ms** (+99% spread)

**Observations:**

- **ElevenLabs S4+S5 land right in the S1/S2 cluster** (412-421 ms
  p50 vs 424-440 for S1/S2). S3 remains an outlier at 694 ms —
  today's data corroborates that S3 was unusual, not the new normal.
- **OpenAI S4+S5 land closer to S1 than S2/S3** (772-783 ms p50 vs
  736-762 for S1a/S1b). The 900+ p50 in S2/S3 remains outlier
  territory today.
- **The 6-session spread is still substantial** (68% for ElevenLabs
  p50, 86% for OpenAI p50). Even excluding S3 outliers, the
  everyday variance is 3-7% for ElevenLabs and 6-9% for OpenAI.
- The overall F-11 finding (rank stable, absolutes not) **holds
  under 6 sessions** — ElevenLabs faster than OpenAI in every
  single session including S4/S5.

**What this does NOT close**: the multi-week variance question.
Same-day S4+S5 tell us the S3 outlier wasn't repeated *today*, but
say nothing about whether such spikes recur at some periodic rate.
Genuinely characterizing that needs ≥5 sessions across ≥2 weeks
per F-11's original workstream.

---

## Experiment E — alt-voice sweep for OpenAI / Fish / Deepgram / Google

**Design.** Take the 8 long-narration items (L01..L08) unchanged, and
regenerate each on a **different voice within the same vendor** than
the one used in the primary campaign. Alt-voice picks:

| vendor | pinned voice | alt voice (this experiment) | note |
|---|---|---|---|
| OpenAI | `onyx` (male, deep) | `nova` (female) | different gender |
| Fish | `e3cd3841…` (narration-tagged) | `9a9cf477…` (conv-tagged, different voice/gender) | uses Fish's verified conv voice_id |
| Deepgram | `aura-2-orion-en` (male) | `aura-2-luna-en` (female) | different gender |
| Google | `en-US-Chirp3-HD-Charon` (male) | `en-US-Chirp3-HD-Kore` (female) | different gender |

**Full quality/WER analysis completed in Follow-up 4** below (~5.3 h
of CPU analyzer time on the 32 alt-voice WAVs; synthetic run-store
at `runs/experiments-2026-09-01-E/`, analyzer output at
[`analysis/experiments-2026-09-01-E/`](../analysis/experiments-2026-09-01-E/)).
This section retains the **drift analysis** — the same LUFS-thirds
check that surfaced the F-6 fade — because it answered an adjacent
question that Follow-up 4's quality tables don't cover:

### E drift results — the fade shows up in OpenAI's `nova` voice too

| vendor | items with fade / total | fade rate | fading items |
|---|---:|---:|---|
| Deepgram (luna alt) | 0 / 8 | 0% | – |
| Fish (conv voice as alt) | 0 / 8 | 0% | – |
| Google (Kore alt) | 0 / 8 | 0% | – |
| **OpenAI (nova alt)** | **2 / 8** | **25%** | **L02 (2.89 dB), L04 (3.75 dB)** |

Two of OpenAI's `nova` voice generations on long narration items
(L02, L04) show the **same-shape monotonic loudness fade** as
ElevenLabs' L03 — Δ ≥ 2 dB, monotonically decreasing across thirds.

**Verdict on E's original question** (does Speechify's voice-agnostic
Simba-3.2 story hold for other vendors?): **answered in
[Follow-up 4](#follow-up-4--alt-voice-qualitywer-analysis-on-experiment-e-audio)**
below via full Audiobox + DNSMOS + WER on the alt-voice audio.
Short answer: every alt voice tested (4 vendors) produces a
statistically significant AB.PQ shift from its pinned counterpart
on n=8 items (paired-z 3.28σ to 13.46σ). The "voice-choice matters"
observation is real; the gender-swap confound on every alt-voice
pair prevents attributing the effect to voice-model choice alone.

**Verdict on E's unexpected finding** (loudness fade on other
vendors): **OpenAI's `nova` voice also fades** at 25% rate on the
same 8 long narration items. Not just ElevenLabs, not just charlotte.

---

## Follow-up 1 — cross-vendor pinned-voice fade rate on the primary campaign

Data: R3 primary-campaign L01..L08 narration audio for all 8 vendors'
pinned narration voices — 64 WAVs already on disk, no new API calls.
Drift analyzer applied identically to Experiment A's method.

| vendor | n_items | fade rate (threshold ≥2 dB, monotonic) | mono-decreasing any magnitude | fading items |
|---|---:|---:|---:|---|
| cartesia | 8 | 0 / 8 (0%) | 0 / 8 | – |
| deepgram | 8 | 1 / 8 (12%) | 2 / 8 | L01 (+2.49 dB) |
| **elevenlabs** | 8 | **2 / 8 (25%)** | 4 / 8 | **L02 (+2.59 dB), L06 (+2.86 dB)** |
| fish | 8 | 0 / 8 (0%) | 3 / 8 | – |
| google | 8 | 0 / 8 (0%) | 1 / 8 | – |
| openai | 8 | 0 / 8 (0%) | 1 / 8 | – |
| orpheus | 8 | 1 / 8 (12%) | 2 / 8 | L02 (+2.18 dB) |
| speechify | 8 | 0 / 8 (0%) | 2 / 8 | – |

**Cross-vendor aggregate: 4 / 64 = 6.2%** items fade at threshold on
their vendor's pinned narration voice. **Mono-decreasing at any
magnitude: 15 / 64 = 23.4%**.

**The most striking single finding**: **L03 does NOT fade on
ElevenLabs charlotte in the R3 campaign audio.** Its actual R3
numbers are t1 = −20.94, t2 = −21.70, t3 = **−20.68** LUFS —
delta = **−0.26 dB** (the ending is actually *louder* than the
beginning), and the trajectory is non-monotonic. Yet in Experiment
B — same charlotte voice, same L03 text, generated on the same day
(2026-09-01) — the fade is 2.79 dB. And in the R2 primary campaign
(2026-08-09), F-6's original observation reported 2.7-3.6 dB fade on
L03. So **on the same voice × text combination, one run fades and
another doesn't**. What R3 charlotte did produce was fade on L02
(+2.59 dB) and L06 (+2.86 dB) — different items than the R2 flag.

**Implication for F-6**: the "L03 is a reproducible text-dependent
quirk" framing does not survive this data. The fade behaviour is
better described as **run-level stochastic** — some fraction of
long-form generations on affected voices fade, and the specific
items that fade shift across runs. Advisory phrasing of what this
implies for production monitoring lives in
[06 § F-6](06_KEY_FINDINGS.md#f-6--monotonic-loudness-fade-on-long-form-tts-narration--a-cross-vendor-phenomenon-at-5-25-base-rate)
and [08 finding #12](08_KEY_FINDINGS_PLAIN.md); this section
describes what the R3 charlotte data showed.

Detail: [`analysis/experiments-2026-09-01/item1_primary_narration_drift.json`](../analysis/experiments-2026-09-01/item1_primary_narration_drift.json)

---

## Follow-up 2 — Cost reconciliation

Approximate cost tracking during the experiment run was
"~$0.62 total" (the pre-flight estimate quoted in the executive
summary at the top of this document); the reconciled total from
the actual api_log rows is:

| segment | rows (ok) | metered USD |
|---|---:|---:|
| Experiment A (20 ElevenLabs) | 20 | $1.1410 |
| Experiment B (5 ElevenLabs voices) | 5 | $1.2105 |
| Experiment C (2 L03 halves ElevenLabs) | 2 | $0.2419 |
| Experiment E (32 items × 4 vendors) | 32 | $0.6702 |
| **Experiments subtotal** | **59** | **$3.2636** |
| D S4 ElevenLabs (18:57Z) | 50 | $0.1250 |
| D S4 OpenAI (19:07Z) | 50 | $0.0188 |
| D S5 ElevenLabs (19:10Z) | 50 | $0.1250 |
| D S5 OpenAI (20:10Z) | 50 | $0.0188 |
| **D subtotal (4 runs)** | **200** | **$0.2875** |
| **Total experiment pack spend** | **259** | **$3.5511** |

The prior "$0.62" was an eyeball estimate that undercounted the
ElevenLabs calls (Creator plan effective rate is ~$180/1M chars =
$0.18/1K chars, so 20 A items × ~350 chars = ~$1.14; earlier
estimate treated ElevenLabs as if it were on the cheap tier).
The corrected total is ~5.7× the eyeball number but still under
$4 — well within the $5 spend caps I set per experiment.

**Interesting sub-observation**: 4 D latency sessions at ~$0.29
total (~$0.07 per 50-trial session, 2 vendors). That's an extremely
cheap way to add a session — the F-11 v2 workstream of "5 more
sessions across 2 weeks" would land under $1 in metered spend.

Detail script: [`scripts/_item2_cost_reconciliation.py`](../scripts/_item2_cost_reconciliation.py)

---

## Follow-up 3 — D latency sanity check

**Ranking hold — 6 of 6 sessions**: ElevenLabs faster than OpenAI
on **both p50 AND p90** in every single measured session from
2026-08-09 through 2026-09-01.

| session date | EL p50 | OA p50 | EL p90 | OA p90 | rank hold? |
|---|---:|---:|---:|---:|:---:|
| 2026-08-09 21:41 (S1a) | 439 | 736 | 479 | 956 | ✓✓ |
| 2026-08-09 22:23 (S1b) | 440 | 762 | 474 | 946 | ✓✓ |
| 2026-08-11 (S2) | 424 | 936 | 469 | 1493 | ✓✓ |
| 2026-08-12 (S3) | 694 | 1369 | 816 | 1882 | ✓✓ |
| **2026-09-01 EL 18:57 / OAI 19:07 (S4)** | **412** | **772** | **461** | **1212** | ✓✓ |
| **2026-09-01 EL 19:10 / OAI 20:10 (S5)**¹ | **421** | **783** | **468** | **1206** | ✓✓ |

¹ S5 OpenAI's 19:10 attempt crashed (run-dir collision with the
concurrent EL run); the successful rerun is `latency-20260901T201051Z`
at T20:10 UTC, one hour after S5 EL. See F-11 for the per-session
run-ID table.

**Cross-session mean-p50 shift** (S4+S5 vs S1a/S1b/S2/S3):
- ElevenLabs: pre-mean 499 ms → new-mean 416 ms (**−17%**)
- OpenAI: pre-mean 951 ms → new-mean 778 ms (**−18%**)

Both vendors are **faster today than the pre-mean** because the
pre-mean includes the S3 outlier (which pushed the numbers up). S4
and S5 land in the S1-style baseline range for both vendors.
Excluding S3 from the pre-mean: ElevenLabs pre-mean drops to 434 ms
(new is close — within ~4%); OpenAI pre-mean drops to 811 ms (new
is slightly lower). Consistent with "S3 was a real transient, not
the new normal."

**Within-run tail behaviour** (max TTFA in the 50-trial run) is
where the OpenAI variance shows up:

| run | provider | p50 | p90 | max | SD |
|---|---|---:|---:|---:|---:|
| S4 elevenlabs | elevenlabs | 412 | 461 | **894** | 78 |
| S4 openai | openai | 772 | 1212 | **1935** | 278 |
| S5 elevenlabs | elevenlabs | 421 | 468 | **716** | 62 |
| S5 openai | openai | 783 | 1206 | **4313** | 555 |

OpenAI's S5 shows a single-trial max of **4.3 seconds** (vs a p90
of 1.2 s) — a one-off spike. OpenAI's within-run SD is 3.5-9× that
of ElevenLabs in the same session, consistent with the earlier
"OpenAI has a wider tail" observation from Phase 2c.

Detail script: [`scripts/_item3_latency_sanity.py`](../scripts/_item3_latency_sanity.py)

---

## Follow-up 4 — Alt-voice quality/WER analysis on Experiment E audio

The 32 alt-voice E WAVs (OpenAI nova, Fish alt, Deepgram luna,
Google Kore — 8 items each) were run through the full veval
analyzer chain (Audiobox + DNSMOS + two-judge WER) via a synthetic
run-store at `runs/experiments-2026-09-01-E/`. Total analyzer time
~5.3 hours on CPU. Output at
[`analysis/experiments-2026-09-01-E/`](../analysis/experiments-2026-09-01-E/).

Original design question — the **T6-style test** — was: does the
"Speechify's Audiobox lead is a model-family property, not a
voice-luck property" story from F-7 generalise to other vendors?
For each vendor, does the alt voice score similarly to the pinned
voice on the SAME 8 long items?

### The comparison table (alt voice vs pinned voice, L01..L08)

| vendor | axis | pinned (R3) mean | alt (E) mean | Δ (alt − pinned) | % change | n |
|---|---|---:|---:|---:|---:|---:|
| **openai** | AB.PQ | 7.619 | 7.473 | −0.146 | −1.9% | 8 |
| **openai** | AB.CE | 6.274 | 6.155 | −0.119 | −1.9% | 8 |
| **openai** | DN.ovrl | 3.484 | 3.447 | −0.037 | −1.1% | 8 |
| **openai** | WER | 0.0936 | 0.1028 | +0.009 | +9.9% | 8 |
| fish | AB.PQ | 7.710 | 7.869 | +0.159 | +2.1% | 8 |
| fish | AB.CE | 6.394 | 6.452 | +0.058 | +0.9% | 8 |
| fish | DN.ovrl | 3.473 | 3.284 | **−0.189** | **−5.5%** | 8 |
| fish | WER | 0.0956 | 0.0923 | −0.003 | −3.5% | 8 |
| **deepgram** | AB.PQ | 7.948 | 7.468 | **−0.480** | **−6.0%** | 8 |
| **deepgram** | AB.CE | 6.499 | 6.310 | −0.189 | −2.9% | 8 |
| **deepgram** | DN.ovrl | 3.514 | 3.249 | **−0.265** | **−7.6%** | 8 |
| **deepgram** | WER | 0.1066 | 0.1243 | **+0.018** | **+16.7%** | 8 |
| google | AB.PQ | 8.032 | 7.927 | −0.105 | −1.3% | 8 |
| google | AB.CE | 6.571 | 6.400 | −0.171 | −2.6% | 8 |
| google | DN.ovrl | 3.414 | 3.493 | +0.079 | +2.3% | 5* |
| google | WER | 0.1010 | 0.1094 | +0.008 | +8.3% | 8 |

*Google DNSMOS DN.ovrl row is computed on the 5-item intersection of items
valid on both sides — a survivor-selected subset, not the full 8 —
because DNSMOS refused **3 of 8 pinned-voice** files (L02, L03, L04,
all peak-out-of-range from clipping) and 1 of 8 alt-voice files
(L02, same cause). Only 5 items (L01, L05, L06, L07, L08) survive
on both sides. Both means and Δ above are recomputed on that
intersection so the delta is a paired difference on matched items
(pinned 3.414, alt 3.493, Δ +0.079; SE_diff 0.025, paired z = +3.16).
The direction and rough magnitude of the previously-published
unpaired 3.414 (5 items) vs 3.490 (7 items) comparison survive
the correction; the method label ("paired delta on matched items")
now does too. Same defect class as
[CORRECTIONS row 19](../CORRECTIONS.md) (mismatched groupings
across adjacent tables) and 04's Cartesia survivor-subset
footnote pattern.

### Paired-z per vendor (the project's standard inferential test)

The right test on 8 matched pairs is a paired t/z on the per-item
differences — the same test used in the R2-vs-R3 replication check
and in 04's Rankings summary. On AB.PQ (the axis carrying the
Speechify claim in F-7):

| vendor | pinned R3 mean | alt E mean | mean Δ | SD_diff | SE_diff | **paired z** | p (two-sided) |
|---|---:|---:|---:|---:|---:|---:|---:|
| OpenAI | 7.619 | 7.473 | −0.146 | 0.126 | 0.044 | **−3.28σ** | ≈ 0.001 |
| Fish | 7.710 | 7.869 | +0.159 | 0.089 | 0.031 | **+5.06σ** | ≈ 4×10⁻⁷ |
| Google | 8.032 | 7.927 | −0.105 | 0.040 | 0.014 | **−7.35σ** | ≈ 2×10⁻¹³ |
| Deepgram | 7.948 | 7.468 | −0.480 | 0.101 | 0.036 | **−13.46σ** | ≈ 0 |

Reproducible from
[`analysis/experiments-2026-09-01-E/quality.json`](../analysis/experiments-2026-09-01-E/quality.json)
`audiobox_files[].audiobox.production_quality` vs
[`analysis/campaign-20260831T175358Z/quality.json`](../analysis/campaign-20260831T175358Z/quality.json)
`audiobox_files[].audiobox.production_quality`, keyed on
(provider, item_id) for L01..L08.

**All four alt voices produce a statistically significant AB.PQ
shift** from the pinned voice on the same 8 items. Direction
varies (Fish positive, others negative); magnitude ranges 3×
(OpenAI 0.146 → Deepgram 0.480). Under the paired test the
project uses for every other quality claim, **no alt voice
"holds within noise" against its pinned counterpart at n=8**.

Prior "HOLDS / SHIFTS" verdict column retracted; see
[CORRECTIONS row 25](../CORRECTIONS.md).

### Gender confound

All four alt voices tested crossed gender against the pinned
voice — OpenAI onyx (male) → nova (female), Deepgram orion
(male) → luna (female), Google Charon (male) → Kore (female).
Fish uses opaque UUIDs so gender is not directly verifiable from
configs, but the alt was Fish's conversational-tagged voice — a
different design confound (voice-purpose swap). **T6's Speechify
comparison split by use case**: conversational was cross-gender
(geffen_32 female → edmund_32 male), but **narration was
same-gender** (wyatt_32 male → edmund_32 male; T6 verdict says
of the narration pair "same gender (both male)"). The T6
narration same-gender leg (recomputed paired-z
on 20 T6 items) is **+4.02σ AB.PQ**, so a within-vendor voice
swap already produces a >3σ shift **even when gender is
matched** on the one vendor where the same-gender test has been
done. The four Follow-up-4 cross-gender pairs cannot on their
own separate voice-choice from gender across the other 7
vendors; T6 narration establishes that voice-choice ≥3σ effects
exist independent of gender on at least Speechify.

### What the data actually supports

- Every alt voice tested produced a statistically significant
  AB.PQ shift from its pinned counterpart on the paired-z test:
  Speechify T6 narration (n=20, same-gender) +4.02σ; Speechify
  T6 conversational (n=20, cross-gender) +6.05σ; Follow-up 4's
  4 vendors on L01–L08 (n=8 each, cross-gender) 3.28σ–13.46σ.
- **T6's Speechify narration leg is same-gender** and already
  establishes a >3σ voice-choice effect independent of gender
  on at least one vendor; the four Follow-up-4 cross-gender
  pairs do not on their own separate voice-choice from gender
  across the other 7 vendors, but "voice choice matters within
  a vendor" is now supported directly rather than being written
  off as a possible gender artefact.
- Speechify's T6 result — alt voice scored +0.30 higher on
  conv (cross-gender) and +0.10 higher on narr (same-gender)
  and still ranked #1 — remains a **rank-preservation**
  observation at the vendor level, not a "quality holds within
  noise" claim at the item level.
- Deepgram's Δ = −0.480 (13.5σ) is the largest per-vendor shift
  observed and would remain a large shift even after subtracting
  the maximum plausible gender component.

### What a v2 same-gender sweep would need

- 2 same-gender voices per vendor × 8 vendors × 8 items × 1 draw
  = 128 fresh generations; ~$0.30 spend; ~1 hour synthesis;
  ~5 hours analyzer wall-clock.
- Compute the same paired-z per vendor per axis. If same-gender
  paired-z is <2σ across vendors, the gender confound is
  eliminated as an explanation and the current 3.3–13.5σ shifts
  can be attributed to voice-model differences within the
  vendor. If same-gender paired-z remains >3σ, the current
  shifts are voice-choice effects that survive gender matching.

Detail script: [`scripts/_item4_e_vs_pinned.py`](../scripts/_item4_e_vs_pinned.py)

---

## Consolidated finding — F-6 upgrade candidate

**The current F-6 in 06_KEY_FINDINGS.md** describes the observation
as: *"Item L03 in the narration corpus produces a reproducible
monotonic loudness fadeout across the audio on ElevenLabs."*

**What this experiment pack shows**: that framing understates the
finding on three axes:

1. **Not L03-specific** — Experiment A: 2/20 fresh long-form
   paragraphs on the same voice show the same-shape fade at the
   threshold (~10% base rate). The direction of the effect (some
   downward slope) is present in 9/20 (~45%).
2. **Not ElevenLabs-specific** — Experiment E: 2/8 alt-voice OpenAI
   long-narration items fade (~25% rate for OpenAI's `nova` voice).
3. **Not fully voice-agnostic within a vendor** — Experiment B: 2/5
   ElevenLabs voices fade on the same L03 text, 3/5 don't. The
   phenomenon lives in the text × voice interaction, not purely in
   either dimension.
4. **Chunkable** — Experiment C: splitting the paragraph into two
   ~40s halves cuts the fade sharply. Suggests the mechanism is a
   cumulative-state effect that resets on a fresh call.

**F-6 rewrite landed** in
[06 § F-6](06_KEY_FINDINGS.md#f-6--monotonic-loudness-fade-on-long-form-tts-narration--a-cross-vendor-phenomenon-at-5-25-base-rate)
based on Follow-up 1 (the cross-vendor pinned-voice fade table
below). Plain-language version in
[08 finding #12](08_KEY_FINDINGS_PLAIN.md). Advisory phrasing
("production narration workflows should include a loudness-drift
monitor over each generated audio") lives in those two files, not
here — this document reports the measurements the rewrite was
based on.

---

## Additional observations

### Adjacent observation — the fade is not always monotonic-decreasing

Of the 20 items in Experiment A, 9 are monotonic-decreasing (some
magnitude of fade), 0 are monotonic-increasing, and 11 are
non-monotonic (t1→t2 and t2→t3 in different directions). This
asymmetry is suggestive — voices don't spontaneously get louder
across a paragraph, but they do drift down about half the time.
"Voice envelope trends toward attenuation" is a weaker claim than
"the model fades" but is consistent with an internal-state-decay
mechanism.

### Adjacent observation — process transparency

**Total spend for the 5-experiment pack**: **$3.55 metered** across
259 rows — see [Follow-up 2](#follow-up-2--cost-reconciliation)
for the per-experiment and per-vendor breakdown.

**Wall clock**: ~2.5 hours end-to-end for generation, plus retry
cycles for misconfigured voice IDs and Rich TUI encoding failures.
The generation phase itself was <90 min.

**Compute time**: drift analysis on 73 experiment WAVs + 64
primary-campaign WAVs took under 60 seconds. The Audiobox +
DNSMOS + WER analyzer pass on the 32 Experiment E WAVs completed
in ~5.3 hours wall-clock on CPU (a synthetic run-store,
`runs/experiments-2026-09-01-E/`, made the standard
`veval analyze` command work on the E audio). Results are in
Follow-up 4.

---

## What was NOT tested (v2 candidates)

1. **The fading mechanism itself**. We observed the fade and its
   chunk-mitigation, but ElevenLabs' and OpenAI's models are closed
   — we can measure the output, not inspect why the internal state
   drifts. Even n=100 more probes would probably characterize
   *rate* and *voice-susceptibility* better without cracking the
   mechanism.
2. **Whether "narrator-tagged" voices systematically fade more than
   "conversational-tagged" voices**. Experiment B suggests this
   (charlotte + josh vs antoni + bella) but n=5 is too small to
   establish a rule. Would need ~20 narrator voices vs ~20
   conversational voices on the same 5-10 test paragraphs
   (~$5, ~1 hour to probe).
3. **Whether Speechify, Cartesia, and Fish narration voices fade
   on their own long-form corpus items**. E only tested each
   vendor's alt voice, not their pinned narration voices, on the
   *same 8 items* used originally. A follow-up would apply drift
   analysis to the R2/R3 primary-campaign narration audio for every
   vendor's pinned narration voice — data is already on disk, just
   needs the drift analyzer run over
   `runs/campaign-20260831T175358Z/audio/*/narration/L*.wav`.
4. ~~Whether the alt voices in Experiment E score similarly to the
   pinned voices on Audiobox/DNSMOS/WER~~ — **answered in
   [Follow-up 4](#follow-up-4--alt-voice-qualitywer-analysis-on-experiment-e-audio)**;
   paired-z 3.28σ–13.46σ on AB.PQ across 4 vendors, plus T6's
   Speechify narration same-gender leg at +4.02σ AB.PQ.
   Residual v2: same-gender alt-voice sweep across the **other 7
   vendors** (T6 narration answered it for Speechify at +4.02σ,
   so we already know within-vendor voice-choice ≥3σ effects
   exist independent of gender on at least one vendor).
5. **Multi-week variance for D**. S4+S5 today are same-day; genuinely
   answering F-11's ≥5-sessions-across-≥2-weeks question needs
   sessions on different calendar dates.

---

## Reproducibility

Every experiment is reproducible from a single script:

```bash
uv run python scripts/_experiment_pack.py A     # 20 new items
uv run python scripts/_experiment_pack.py B     # 5 voices on L03
uv run python scripts/_experiment_pack.py C     # L03 halves
uv run python scripts/_experiment_pack.py D     # latency S4+S5
uv run python scripts/_experiment_pack.py E     # alt-voice sweep
uv run python scripts/_experiment_pack.py drift # analyze all WAVs
uv run python scripts/_experiment_report.py     # render this report body
```

**Inputs**:
- 20 authored items for A: [`analysis/experiments-2026-09-01/inputs/A_items.json`](../analysis/experiments-2026-09-01/inputs/A_items.json)
- L03 halves for C: [`analysis/experiments-2026-09-01/inputs/C_l03_halves.json`](../analysis/experiments-2026-09-01/inputs/C_l03_halves.json)
- Long items (L01..L08) for E: [`analysis/experiments-2026-09-01/inputs/E_long_items.json`](../analysis/experiments-2026-09-01/inputs/E_long_items.json)

**Outputs**:
- All 73 WAVs: `analysis/experiments-2026-09-01/audio/{A_new_items, B_voices, C_halves, E_altvoice/{openai,fish,deepgram,google}}/*.wav`
- Drift stats: [`analysis/experiments-2026-09-01/drift.json`](../analysis/experiments-2026-09-01/drift.json)
- API logs: `analysis/experiments-2026-09-01/logs/{A,B,C,D,E}_*.log` + `_api_log.jsonl`
- 4 fresh D latency runs: `runs/latency-20260901T{185715,190715,191000,201051}Z/`
