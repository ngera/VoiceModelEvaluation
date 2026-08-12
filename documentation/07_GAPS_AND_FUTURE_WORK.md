# 07 · Gaps and future work

*What v1 didn't cover, why, and what a v2 pass would add.*

> **⚠ Scope disclaimer** · Findings as of 2026-08-11 on specific
> vendor accounts (paid public tiers) and one voice per vendor per
> use case. No financial relationship with any vendor. Full scope
> in [../DISCLAIMER.md](../DISCLAIMER.md).

---

## Structural gaps (cannot fully mitigate in v1 scope)

These are limits inherent to a single-person, three-week, ~$56
project. Each is documented as an explicit v2 workstream rather
than glossed over.

### 1. No human perceptual validation (n=1 rater is not enough)

The pre-registered plan called for a 168-judgment Bradley-Terry
rating campaign with clustered bootstrap 95% CIs. At n=1 self-rater,
those CIs would be **conditional on the single rater** — a different
rater could produce non-overlapping "95% CIs" on opposite
preferences, both statistically valid, both worthless as
human-preference evidence.

Executing the ceremony and disclaiming the result would be a shape of
over-claim this project refuses to make. See
[06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-phase-3-bt-deferred)
for the full rationale.

**v2 workstream**: recruit 15–30 blinded raters, run the existing
`veval rate build/score` pipeline (fully implemented in `src/veval/rate/`),
compare rankings to the two machine-pipeline rankings, publish
which pipeline aligns better with human perception on which use
case.

### 2. One voice per vendor per use case

Each vendor was tested with one representative voice per use case,
locked in `configs/voices.yaml` before results existed. Voice choice
within a vendor can shift scores by up to ~35% of the cross-vendor
spread on the aesthetic axis (measured for Speechify via T6, where
the alt voice `edmund_32` scored +0.30 higher on Audiobox PQ than
the pinned `geffen_32`).

**v2 workstream**: run 3–5 alternate voices per vendor per use case
(20-item pilot each; ~$5 total). Answer whether vendor rankings
survive across the voice space, and where vendor tag-taxonomy
(warm / bright / dynamic / etc.) reliably predicts aesthetic score.

### 3. Corpus authored by the evaluator

The 75-item corpus per use case was authored to a documented brief
(support-agent turn distribution + long-form narrative structure).
Corpus is committed to git; another evaluator can reproduce with
different content. **The finding that provider strengths cluster
orthogonally on this corpus is not necessarily portable to a very
different corpus** (e.g., poetry, technical documentation, dialog
with heavy dialect).

**v2 workstream**: repeat the campaign against 2–3 additional
corpora sampled from public sources (LibriSpeech test-clean for
narration; SIP-audio traces for conversational). Test whether
rankings survive the corpus change.

### 4. English only

Vendors' multilingual claims are untested here. Several vendors
advertise multi-language voices as differentiators; we can neither
confirm nor refute those claims.

**v2 workstream**: repeat the campaign on Spanish + Mandarin + one
low-resource language (e.g., Swahili) using the same methodology.

### 5. Client-side latency measured from a residential Windows 11 environment

Absolute TTFA / RTF numbers are upper bounds on what an
enterprise-cloud-VM deployment would see. Provider *rankings* on
latency are portable; absolute *values* are labeled ceilings in
every table + figure caption. See
[06_KEY_FINDINGS.md § D-G](06_KEY_FINDINGS.md#d-g-enterprise-portability).

**v2 workstream**: re-measure TTFA/RTF from AWS + GCP VMs colocated
with each vendor's serving region. Publish an "enterprise ceiling
+ residential ceiling" pair per vendor.

### 6. Subscription-tier serving priority may differ from enterprise contracts

Measurements were taken on paid public tiers: Speechify Starter
$10/mo, ElevenLabs Creator, Cartesia Pro $5/mo, Deepgram $200 signup
credit, OpenAI Tier 1, Replicate pay-per-use, Google Cloud pay-per-use,
Fish Audio paid. Enterprise SLAs and volume-negotiated contracts
may produce materially different behavior on rate limits, latency
SLAs, cost per unit, and model access.

**v2 workstream**: partner with a mid-market buyer's actual
enterprise deployment (with permission), replay the corpus, compare
rankings across tier boundaries.

### 7. CPU-only analyzer execution

No validity impact on scores (deterministic transforms of audio
bytes) or rankings. Only affects wall-clock cost for reproducers.
GPU reproducers should observe identical scores at 5-10× the speed.
Documented in [`configs/hardware.yaml`](../configs/hardware.yaml).

**v2 workstream**: (optional) publish a GPU wall-clock benchmark
against the CPU baseline as a reproducibility receipt.

---

## Gaps addressed in v1

Documented for completeness — these were on the original threats
list and got substantive mitigation during the project:

- **wav2vec2 judge inflates absolute WER** (F-2) — mitigated by
  reporting WER as *relative-ranking-only*, never absolute. The 6-signal
  quality panel gives triangulation for aggregate quality claims.
- **TTSDS2 skipped** (D-A) — mitigated by adding DNSMOS as the second
  MOS pipeline (D-B / D-011); the 6-signal + cross-pipeline agreement
  analysis substitutes for the missing D3 primary.
- **Single-session latency** (D-1) — mitigated by T5 + T7 adding a
  second 50-trial session on a different day; produced the "stability
  is a distinct axis from speed" finding.
- **Cartesia clipping: systemic or batch?** (T1 hypothesis) — mitigated
  by F-4a's independent-pipeline corroboration; T1 verdict Confirmed
  before Phase 2c even began.
- **Ranking depends on MOS predictor family choice** (F-8) — mitigated
  by *publishing both matrices* rather than aggregating into a single
  quality score, and naming the specific rank inversions (OpenAI,
  Speechify, Cartesia) as F-8 findings.

---

## Deferred by scope (not attempted in v1)

Explicit "not in this version" list. Each is a valid v2 workstream.

- **No cross-lingual measurement** — English only
- **No accent or style variation per provider** — one voice per vendor
  per use case, locked in configs
- **No streaming-quality measurement** — buffered playback only; on-the-fly
  quality (mid-utterance artefacts, streaming latency variance) not tested
- **No conversation-flow / context effects** — items evaluated in isolation;
  no turn-taking, no context carryover across items
- **No robustness-to-interruption testing** — barge-in and mid-utterance
  correction behavior not exercised
- **No production-load / concurrency behavior at scale** — measured
  1–3 concurrent requests per provider; enterprise 100+ concurrent
  behavior untested
- **No prompt-injection / adversarial-input robustness** — corpus is
  well-formed English; behavior on malformed / adversarial input
  (very long tokens, non-printable characters, prompt-injection strings)
  untested

---

## What a v2 pass would look like

If someone were to fund a proper v2 today, the priority-ordered
workstream list would be:

1. **Multi-rater BT panel** (highest-leverage, answers F-8's
   "which construct maps to human perception?" question) —
   15-30 raters, ~1 week of coordination + $500 for rater
   compensation
2. **Alt-voice sweep per vendor** — 3-5 voices × 8 vendors ×
   20 items = 480 fresh generations, ~$5, ~2 hrs
3. **Enterprise-VM latency baseline** — AWS + GCP colocated
   measurements per vendor's inference region, ~1-3 days of
   VM setup + $50 cloud spend
4. **Cross-lingual pass** — Spanish + Mandarin + 1 low-resource
   language against the same 8 vendors, ~$50-100 depending on
   vendor pricing
5. **Alt-corpus robustness** — 2 additional corpora (LibriSpeech
   + SIP dialogs), same 8 vendors, ~$50
6. **Enterprise-tier partner replay** — 1-2 real enterprise
   deployments (with permission), same corpus, compare to our
   public-tier results
7. **Streaming-quality measurement** — extend the harness to
   analyse on-the-fly audio quality, then replay the campaign

**Estimated v2 total cost**: ~$700-1500 in cloud + rater fees.
**Estimated v2 wall-clock**: ~3-4 weeks of coordinated work.

This project is designed so a v2 can be built additively on the
existing infrastructure — every gap above is a targeted extension
of the existing analyzer chain rather than a rewrite.

---

## Where to go next

- [../DISCLAIMER.md](../DISCLAIMER.md) — full scope + no-affiliation disclosure
- [06_KEY_FINDINGS.md § threats-to-validity](06_KEY_FINDINGS.md#threats-to-validity) —
  same items linked back to the specific decisions that drove them
- [05_CASE_STUDY.md § "What wasn't done and why"](05_CASE_STUDY.md#what-wasnt-done-and-why) —
  the same gaps in narrative form
- [06_KEY_FINDINGS.md § D-H](06_KEY_FINDINGS.md#d-h-bt-deferred-to-v2) —
  the specific reasoning for the biggest omission (BT panel)
