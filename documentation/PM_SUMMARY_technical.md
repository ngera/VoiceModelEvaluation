---
title: Voice AI Provider Evaluation — Findings summary (technical)
audience: PM with some technical fluency
purpose: |
  First-pass summary written 2026-08-11 after Phase 2c executed.
  Preserved verbatim as the technical baseline; PM_SUMMARY.md is the
  refined plainer-language version that expands on the technical
  terms with concrete use-case examples.
created: 2026-08-11
evidence_base:
  - 8 providers × 2 use cases (support agent + long-form narration)
  - 75 corpus items per use case
  - 40-item variance subset (3 draws per item)
  - 9-test verification pack (Phase 2c)
  - 6 quality signals per provider from 2 independent MOS pipelines
    (Audiobox Aesthetics — Meta; DNSMOS P.835 — Microsoft)
related:
  - documentation/RESEARCH_LOG.md (F-1 through F-9, decisions D-A–D-G)
  - analysis/verification/ (per-test verdicts)
  - documentation/DEVIATIONS.md (prereg amendments)
---

# Voice AI Provider Evaluation — Findings summary for a decision-maker

Evidence base: 8 providers × 2 use cases (support agent + long-form
narration) × 75 corpus items, plus a 40-item variance subset and a
9-test verification pack. Six quality signals per provider from two
independent MOS pipelines. All artefacts under `analysis/`, all
verdicts under `analysis/verification/`.

---

## The one-slide headline

**There is no universal winner.** Every provider dominates *at least
one* axis and *loses* at least one. The right choice depends on which
axis maps to your listener use case, and on which failure mode you can
tolerate. A weighted composite score would obscure this; the frontier
chart is what you actually need.

---

## Provider archetypes (memo one-liners)

| Provider | One-line archetype | Deal-breaker to know |
|---|---|---|
| **ElevenLabs** | Fast and *stable*. Sub-500ms p90 across 2 sessions, quality mid-to-top | Deterministic loudness fadeout on some text (~2.7 dB drop; observed on L03) |
| **Speechify** | Audiobox #1 on both use cases; **model-level advantage** (survives voice swap) | DNSMOS mid-pack — not the "cleanest" by MS's measure |
| **OpenAI** | *Cleanest* signal per DNSMOS (#1/#1/#2 on narration) | Audiobox says dead last on narration ("clean but flat"); latency 700–950 ms p50 *and highly variable* |
| **Cartesia** | Fast, low-latency-model | **~46% of files fail DNSMOS's peak check**; hygiene analyzer flags 100× more clipping than next-worst |
| **Deepgram** | Mid-everything, off-index control that behaves like a control | Nothing stands out — but nothing screams either |
| **Fish** | Audiobox mid, has a specific-model split | DNSMOS OVRL+SIG *worst on conversational*; noise floor is **+12.6 dB above the median** |
| **Google** | Middling on every quality axis | Noisiest conv audio in the roster (–33.7 dBFS noise floor) |
| **Orpheus** | Cheapest — nominally $0.003/call | **Hard 14.59-second output cap per call, regardless of input length**. Any narration >15s truncates 80%+ of the content |

---

## What the PM actually needs to know

### 1. The two MOS pipelines disagree on ranking (F-8)

Cross-pipeline Spearman ρ across the 8 providers:
- Conversational: **−0.13**
- Narration: **−0.27**

**Meaning:** Audiobox (Meta, trained on aesthetic ratings) rewards
*warmth, expressiveness, engagement*. DNSMOS (Microsoft, trained on
P.835) rewards *clean signal separation*. **These are different
constructs.** A leaderboard reporting one is not measuring the same
thing as a leaderboard reporting the other.

**PM decision rule:**
- **Consumer-facing narration / audiobook / storytelling** → Audiobox
  axis is closer to what your listener cares about → **Speechify**
  (Audiobox #1 both use cases).
- **Enterprise transactional voice / IVR / clean playback** → DNSMOS
  three-scale is closer → **OpenAI** on narration, **ElevenLabs** on
  conversational.
- **Serving *both* archetypes with one vendor** → **ElevenLabs** and
  **Deepgram** are the safe generalists (top-half on both pipelines,
  no red flags).

### 2. Provider strengths are ORTHOGONAL (F-3)

Ranks on the 6 quality signals + latency + cost + reliability show
every provider wins on one axis and loses on another. **A weighted
composite score would obscure this.** The frontier — not the
leaderboard — is the artefact.

### 3. Cartesia has a mastering problem that touches downstream (F-4, F-4a)

Three independent pipelines flag Cartesia unanimously:
- **Hygiene** (sample-level peak detection): 100× more clipped samples
  than the next-worst provider
- **DNSMOS** (MS ONNX): **32/75 conv + 37/75 narr items refused
  outright** for peak > 1.0 (43% + 49% refusal rate). No other
  provider has any DNSMOS refusals except Google narration (4/75).
- **Cartesia's surviving 38 narration items still rank #8 on all
  three DNSMOS three-scale axes** — this isn't *just* clipping; the
  mastering signature is bottom-of-pack even on the non-refused
  subset.

**PM implication:** If you're building on Cartesia, apply a −1 dBFS
peak limiter *before* handing the audio to any downstream (ASR, MOS
predictor, resampler). Otherwise a meaningful fraction of your audio
pipeline will silently reject or degrade it.

### 4. Orpheus is not "cheapest" (T8 major finding)

Orpheus's price list says $0.003 per generation. Our verification
found:

- **Orpheus produces exactly 14.59 seconds of audio per call,
  regardless of input** (stdev = 0.000s across 8 tested items varying
  87–105s of input text)
- This is a **hard output cap in the model**, not a stochastic
  behaviour
- A 1000-character narration = ~6 calls × $0.003–0.017 = **$0.02–0.10
  per 1000 chars**
- This *also mechanically explains* Orpheus's 27% WER on long items
  (it's not intelligibility; it's incompletion)

**PM implication:** Orpheus is cheapest for **conversational** turns
under 15 seconds. For long-form narration, either budget for 5-6× the
nominal per-call cost + build the chunking logic, or use a different
provider. The "cheap open-weights floor" positioning needs a use-case
qualifier.

### 5. Latency **stability** is a distinct axis from latency **speed** (T5 + T7)

Same measurement setup, same 2 days apart:

| Provider | p50 shift session-to-session | p90 shift |
|---|---|---|
| ElevenLabs Flash | **2.7% (dead stable)** | 2.1% |
| OpenAI tts-1-hd | **27%** | **56%** |

**PM implication:** For a support agent where users notice bad
speech-turn latency, ElevenLabs is not just *faster* than OpenAI —
it's *more predictable*. OpenAI's TTFA in production will bracket
**~700–950 ms p50 and ~950–1500 ms p90** across sessions. That's the
number to plan capacity around, not the best-case.

### 6. Voice choice matters less than model choice for Speechify (T6 reversal)

Original hypothesis: "Did we cherry-pick a lucky voice?" Test result:
**the alternate voice scored *higher* on Audiobox** than the
pre-registered one, and still beat all 7 competitors. So Speechify's
Audiobox lead is a **Simba-3.2 model** property, not a voice property.
Portable insight.

### 7. All providers are non-deterministic (F-1)

**Not one provider we tested produces byte-identical output across
draws.** If your product needs byte-reproducible playback (e.g., a
caching layer with cryptographic content hashes), you need to save
the audio bytes yourself; you cannot regenerate them and expect
equality.

---

## The three-frame PM decision framework

**Frame 1: hard constraint check.** For your use case, does any
provider have a *structural incompatibility*?
- Long-form narration: **Orpheus is out** (14.59s cap)
- Any audio into a MOS/ASR/resample pipeline: **Cartesia needs a peak
  limiter first**, or accept ~46% loss
- Sub-500 ms p90 required: **only ElevenLabs Flash and Deepgram**
- Byte-identical caching needed: **impossible with any provider**

**Frame 2: pipeline-alignment check.** Does the MOS predictor your
evaluation used map to your listener use case?
- Aesthetic / consumer-facing: use **Audiobox rankings** (Speechify wins)
- Signal-cleanliness / enterprise / accessibility: use **DNSMOS
  three-scale** (OpenAI/ElevenLabs win narration; OpenAI conv)
- If unsure, **publish both** — a leaderboard that reports one is
  measuring a different thing than a leaderboard that reports the
  other

**Frame 3: risk-adjusted cost.** For the fraction of items that fail
or need retries at each provider, what's the *effective* per-1K-chars
cost?
- Orpheus nominal $0.003 → effective ~$0.02–0.10 for narration
  (chunking overhead)
- Cartesia nominal cheap → effective +cost of a downstream
  peak-limiter step
- OpenAI variable latency → effective +cost of higher p99 capacity
  provisioning

---

## Meta-takeaway for the PM

**What this exercise actually proves is that the vendor pitch decks
are wrong in specific, measurable ways.** For every claim we tested,
we found either the claim was supported *for a specific use case
only* (Speechify #1, Orpheus cheapest), or the headline number was on
the high side of a natural range (ElevenLabs L03 fadeout), or the
"leaderboard rank" depended entirely on which MOS predictor was
picked (F-8).

**The frontier chart with confidence intervals + a per-provider
"gotcha to know" line is the artefact that helps a PM buy.** Not a
weighted composite score, and not a leaderboard.

**Next action for a PM using this report:** decide which axis your
users actually care about, then look at the frontier for that axis
with the "gotchas to know" column visible. If you can't pick just
one axis, you've got a two-provider deployment story (fast+stable
for turn-of-conversation, quality-optimised for long segments) —
that's a legitimate answer.
