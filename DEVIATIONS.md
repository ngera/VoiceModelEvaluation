# DEVIATIONS.md

Deviations from the pre-registered plan (`prereg-v1` when tagged) or from
the spec/plan docs when they turn out to be wrong. Every entry is logged
with rationale; never silently fixed (CLAUDE.md convention).

The point of this file is asymmetric: entries here are evidence *for*
the project's honesty, not against it. A blown budget disclosed is a
data point; a blown budget discovered by a reader is a credibility
problem.

Format:

```
## D-XXX — one-line summary  (YYYY-MM-DD)

**What changed.**
**Why.**
**Impact on results.**
**Where to look:** commit hash, files touched.
```

---

## D-001 — Interpreter pinned to stable 3.11 (2026-08-05)

**What changed.** The devcontainer base originally installed Ubuntu 22.04's
`python3.11` package, which reports `3.11.0rc1 (main, Aug 12 2022)` — an RC
that never received a stable release. Rebuilt onto a base that installs stable
3.11 via `uv python install`.

**Why.** For a project whose thesis is reproducibility, baking a 2022 release
candidate into every run's `manifest.json` was a bad look and a real bug risk.

**Impact on results.** None — the fix landed before any campaign data existed.
`test_manifest_records_a_stable_interpreter` in the tests suite is the falsifiable
receipt.

**Where to look:** commit `11ff01d`; `.devcontainer/Dockerfile`.

---

## D-008 — Speechify endpoint reverted to `/v1/audio/speech`; TTFA not measurable (2026-08-08)

**What changed.** Speechify adapter now hits `POST /v1/audio/speech`
(JSON envelope) instead of `/v1/audio/stream` (raw bytes). The envelope
delivers base64-encoded WAV; the adapter decodes it before writing to
disk. `ttfa_ms` is set to `None`; `total_ms` is the whole
request/response duration.

**Why.** The Phase E WAV acceptance gate (built 2026-08-08, first live
run against the second D.7 pilot) surfaced two Speechify defects in
sequence:

1. **Original state**: adapter hit `/v1/audio/speech` but treated the
   response as raw bytes — wrote the JSON envelope verbatim to
   `.wav` files. soundfile decode error on every clip.
2. **First fix attempt (same day)**: switched to `/v1/audio/stream`
   for real streaming + TTFA parity with the other adapters. But
   `/stream` returns MP3 (ID3/Lavf-tagged) regardless of the
   `audio_format` field in the body. WAV is only available via
   the JSON envelope.

Third option — accept MP3 on disk and let analyzers handle both
formats — was rejected: a comparability study should hold audio
format constant across providers. MP3 compression artifacts would
contaminate WER, TTSDS2, and hygiene metrics for one provider only.

**Choice.** Take WAV via `/v1/audio/speech`, accept that Speechify
D8 latency is `total_ms` (buffered) rather than TTFA. Speechify
gets an on-chart annotation on the latency frontier — the same
pattern precedent set by Fish's split-model annotation (D-004
paradigm: log the constraint, don't pretend it isn't there).

**Impact on results.**
- Every provider ships lossless WAV to analyzers → no
  format-comparability caveat needed on WER, TTSDS2, hygiene.
- Speechify latency: `total_ms` (full request/response). Not
  directly comparable to other providers' `ttfa_ms`. Reported as
  "N/A — no streaming WAV endpoint" on the conversational-latency
  gate; the `exempt-and-annotate` `na_policy` in gates.yaml
  handles this without dropping Speechify from the use case.
- Adapter code carries a comment explaining the endpoint choice
  so a future reader doesn't "helpfully" switch back to /stream.

**How the gate caught it.** By design. The Phase A defect class was
"streamed WAV headers lie about duration"; the acceptance gate exists
to catch any regression in that class before downstream analyzers
(RTF, LUFS, TTSDS2, VAD) read a lying header. It caught OpenAI
missing `finalize_wav_header()` (fixed 2026-08-08 in the same session)
and Speechify's format mismatch on the same first run. Two silent-
corruption defects, both surfaced before any analysis output was
written. Portfolio-worthy — the guardrail paid for itself the day
it landed.

**Where to look.** `src/veval/adapters/speechify.py` (endpoint,
JSON parse, base64 decode); `src/veval/analyze/acceptance.py`
(the gate that caught it); commits [tbd]. Re-tagged **prereg-v1.6**.

---

## D-007 — OpenAI narration voice cedar → onyx (not in tts-1-hd enum) (2026-08-08)

**What changed.** Second pilot re-run after D-006 still showed 5/10
OpenAI narration failures. New error body: HTTP 400
*"Input should be 'nova', 'shimmer', 'echo', 'onyx', 'fable', 'alloy',
'ash', 'sage' or 'coral'"*. `cedar` is not in `tts-1-hd`'s voice enum
— it exists only on the newer `gpt-4o-*` model family.

Swapped voice_id from `cedar` → `onyx`. Model pin (`tts-1-hd`)
unchanged — that fix in D-006 was correct; the trailing bug was that
D-006 didn't check whether the previously-picked voice_id survived the
model swap.

**Why `onyx` specifically.** Traditional OpenAI narrator archetype:
deep male, present in every OpenAI TTS model's voice enum (both the
classic `tts-1`/`tts-1-hd` family and the newer `gpt-4o-*` family),
which makes it robust to future model pin changes.

**Why not just swap the model back?** Options considered:
- Swap model back to `gpt-4o-mini-tts` (same as conversational,
  cedar works there): loses the "different model per use case" story.
- Swap model to a specific dated variant that includes `cedar`
  (e.g. `gpt-4o-mini-tts-2025-12-15`): would work but pins to a
  dated variant with unclear support lifetime.
- Keep tts-1-hd, swap voice: cleanest — preserves the model
  differentiation, uses a voice that's universally available.

**Impact on results.** OpenAI narration measures now use `tts-1-hd +
onyx`. Perceived quality vs the conversational entry (`gpt-4o-mini-tts
+ fable`) will differ across model AND voice — a buyer would swap
both per use case in practice.

**Where to look.** commits [tbd]; `configs/voices.yaml` OpenAI
narration row. Re-tagged **prereg-v1.5**.

---

## D-006 — OpenAI narration model gpt-4o-tts → tts-1-hd; Speechify concurrency 3 → 1 (2026-08-08)

**What changed.** Two adjacent fixes discovered when the D.7 $1 pilot
returned 60/80 pass:

1. **OpenAI narration model: `gpt-4o-tts` → `tts-1-hd`.** The pilot
   showed 5/10 fail on OpenAI, all in the narration use case; error
   body: *"The model `gpt-4o-tts` does not exist or you do not have
   access to..."*. Doctor probe hadn't caught it because doctor
   defaults to `--use-case conversational` which uses
   `gpt-4o-mini-tts`. Query of `/v1/models` confirmed the account has:
   `gpt-4o-mini-tts` · `tts-1` · `tts-1-hd` (plus dated variants).
   Swapped to `tts-1-hd` — OpenAI's classic HD TTS model, still the
   standard audiobook/narration pick. Voice `cedar` unchanged (works
   on both models).
2. **Speechify concurrency 3 → 1** in `DEFAULT_PROVIDER_CONCURRENCY`.
   Pilot showed 5/10 Speechify fail with HTTP 429
   `"concurrency_limit_reached"` — Starter plan allows exactly 1
   simultaneous request (verified via error body). Not a prereg
   change (concurrency is runtime config), but bundled here since
   both surfaced in the same pilot.

**Why.**
- OpenAI: `gpt-4o-tts` may exist for some accounts / at some
  tiers, but it 404'd here. Rather than gate the whole campaign on
  a maybe-available model, we swap to something confirmed
  available. `tts-1-hd` is a legitimate choice for the
  narration-quality slot — it's been OpenAI's HD TTS since 2023.
- Speechify: adapter-side default was 3 (matched Fish/ElevenLabs);
  Starter's actual limit is 1. Bump-up costs a plan tier upgrade
  we don't need for the campaign volume.

**Impact on results.**
- OpenAI narration measurements will use `tts-1-hd`, not
  `gpt-4o-mini-tts`. The two are meaningfully different models
  (different architecture family, different sampling behaviour) —
  so the "different model per use case" story is preserved.
- Speechify campaign runtime will be longer (1 concurrent vs 3),
  but the concurrency cap is a floor on completion time not the
  measurements themselves. Same audio quality, same TTFA per
  call. Total campaign time slightly higher on Speechify.
- No cost impact.

**Where to look.** commits [tbd]; `configs/voices.yaml` (OpenAI
narration model row), `src/veval/runner/runner.py`
(DEFAULT_PROVIDER_CONCURRENCY['speechify']). Re-tagged
**prereg-v1.4**.

---

## D-005 — Orpheus version SHA pinned; adapter uses version-explicit endpoint (2026-08-07)

**What changed.** Two related fixes to Orpheus discovered when D-004's
corrected slug still hit HTTP 404 on the first live probe:

1. **Endpoint pattern changed** from auto-latest
   `/v1/models/{owner}/{name}/predictions` to version-explicit
   `/v1/predictions` with `version` in the request body. Direct
   verification against the Replicate API 2026-08-07 confirmed the
   auto-latest endpoint returns HTTP 404 for this community model
   (works for some Replicate-featured models only). Only the
   version-explicit path succeeds.
2. **Version SHA pinned in providers.yaml** as
   `79f2a473e6a9720716a473d9b2f2951437dbf91dc02ccb7079fb3d89b881207f`
   (created 2025-03-20; current latest as of the snapshot). New
   `version` field on `ProviderConfig` + `ProviderAdapter.__init__`
   threads it through cleanly for any future provider that needs
   version pinning; today only Orpheus uses it. Adapter now raises a
   clear ProviderError if `version` is missing on Orpheus.

**Why.** The auto-latest bug was the immediate blocker, but pinning
the SHA is a genuine tightening of the prereg discipline: what was
implicitly "whatever Replicate serves right now" is now explicitly
"this specific version, in providers.yaml, under git." Any change to
the SHA requires a new DEVIATIONS entry — drift accountability.

**Impact on results.**
- **Reproducibility strengthened.** The drift re-run (+4 wks per
  spec) will now measure the same Orpheus version SHA. If Replicate
  removes or supersedes this version between runs, we catch it via
  ProviderError rather than silently measuring a different model.
- **Config schema addition.** `ProviderConfig` gains an optional
  `version` field. All other providers leave it `None`; no
  behavioural change to Deepgram/Fish/Google/Cartesia/ElevenLabs/
  OpenAI/Speechify.
- **Payment-method dependency (not a prereg change but flagged
  here).** Replicate rate-limits to 6 req/min with a burst of 1
  until a payment method is added. Doctor probes work; Phase D's
  900-item campaign will not — payment method must be added before
  the campaign run.

**Where to look.** commits [tbd]; `configs/providers.yaml` (Orpheus
gains `version` field + rate-limit note), `src/veval/config.py`
(`ProviderConfig.version`), `src/veval/adapters/base.py`
(`ProviderAdapter.__init__` accepts `version`),
`src/veval/adapters/orpheus.py` (uses version-explicit endpoint;
requires self.version), `src/veval/doctor.py` (passes
`p.version` to adapter). Re-tagged **prereg-v1.3**.

---

## D-004 — Orpheus pinned to community fork; voice + adapter corrected (2026-08-07)

**What changed.** Three related corrections to the Orpheus provider,
discovered when the Replicate model schema was queried before the live
probe:

1. **Model slug: `canopyai/orpheus-3b` → `lucataco/orpheus-3b-0.1-ft`.**
   The pre-v1.1 slug returns 404 on Replicate — Canopy Labs has no
   official Replicate deployment of Orpheus. The actually-reachable
   Orpheus model is `lucataco/orpheus-3b-0.1-ft`, a community
   fine-tune of Canopy's open weights (36K runs, latest version
   `79f2a473...`, verified 2026-08-07 via `GET /v1/models/lucataco/orpheus-3b-0.1-ft`).
2. **Narration voice: `leo` → `dan`.** The fork's voice enum is 4
   (`tara`, `dan`, `josh`, `emma`), not the 7 (`tara`/`leah`/`jess`/
   `leo`/`dan`/`mia`/`zac`) documented against pure Canopy weights.
   `leo` was picked pre-verification; the actual enum does not include
   it. `dan` swapped in as the best narrator archetype from the
   available 4 (male, generic-narrator fit — mirrors the
   "lower-pitch male for narration" intent behind `leo`).
3. **Adapter input field: `prompt` → `text`.** Model schema names the
   input field `text`, not `prompt`. Would have failed at first
   synthesis call with HTTP 422 unprocessable-entity otherwise.

Conversational voice `tara` unchanged (present in both the old and
new voice enums; still Canopy's original sample voice).

**Why.** The pre-v1.1 Orpheus config was based on knowledge about
Canopy's own model documentation rather than what Replicate actually
hosts. Verification against the live schema surfaced all three errors
before the first probe would have hit them.

**Impact on results.**
- **Measurement scope change.** Results for "Orpheus" now measure the
  `lucataco/orpheus-3b-0.1-ft` community fine-tune specifically, not
  pure Canopy weights. This is a real methodological caveat that must
  travel with every Orpheus row in the results table: *"Reference
  implementation caveat — Orpheus was evaluated through the
  lucataco/0.1-ft community fine-tune, which is the reachable
  Replicate deployment. Pure Canopy weights would require self-hosting
  (out of scope for this build)."*
- **Archetype label.** "Open-weights floor" is still accurate — the
  fine-tune inherits the weights' Apache-2.0 licence per the model
  card. The archetype gap the provider fills is preserved.
- **No cost delta.** Same Replicate billing model (~$0.003/gen).
- **Portfolio-worthy DX finding.** Community forks being the actual
  deployment surface for open-weights models is a real DX
  observation. Logged in dx/friction_log.md.

**Where to look.** commits [tbd]; `configs/providers.yaml` (notes
rewritten), `configs/voices.yaml` (model + narration voice),
`src/veval/adapters/orpheus.py` (`prompt` → `text`),
`dx/friction_log.md` Orpheus section, spec §3.1 Orpheus row updated.
Re-tagged **prereg-v1.2**.

---

## D-003 — Provider roster expanded 6 → 8 (2026-08-07)

**What changed.** Two providers added to the locked portfolio-edition
roster after the prereg-v1 tag but before any campaign result exists:

- **OpenAI** — `gpt-4o-mini-tts` (conversational) / `gpt-4o-tts`
  (narration). Fills the *"LLM-ecosystem default"* archetype: the API a
  team building GPT-adjacent products already has credentials for. This
  archetype is not represented by any of the original 6 providers and
  is a foreseeable reviewer question ("why not test OpenAI?").
- **Speechify** — `simba-3.2`. Fills the *"audit the top of the HI
  leaderboard"* story. Speechify sits at HI #1 (score 99) by their own
  measure; a direct like-for-like run against that ranking is a
  differentiator no other provider on our list offers.

Roster after amendment (8):
ElevenLabs · Cartesia · Fish Audio · Google · Deepgram · Canopy Orpheus
· **OpenAI · Speechify**.

**Why.** Spec §2 argued "providers 7–12 add coverage, not narrative;
the story is identical at 6." That was accurate for the original 6
archetypes (quality / latency / value / hyperscaler / off-index /
open-source), but overlooked two distinct archetypes:
"already-in-their-stack" (OpenAI) and "auditable-#1" (Speechify). Both
are genuine axes a buyer navigates that no original roster member
represents. Trade-off explicitly accepted: +2–4 days scope, +$5–15
budget, +33–71% D4 pairwise volume.

**Impact on results.**
- Frontier charts: 4 more points (8 providers × 2 use cases). No
  archetype now unrepresented; reviewer questions on missing providers
  should be answered by presence rather than by rationale.
- D4 pairwise volume: 21 unique pairs → 28 (adding OpenAI only) → 36
  (adding both). Target reps preserved (5 per pair) — total judgments
  360 for 8 providers (was 210). Minimum acceptable still 3 reps = 216.
- Budget: OpenAI absorbs in signup credit / low-volume trivial cost
  (~$0.05 for the doctor probe + campaign trivial). Speechify Starter
  $10 (1 month). New budget subtotal: ~$46–57 (was ~$36–47). Ceiling
  unchanged; contingency band tightens.
- Prereg tag: re-tagged **prereg-v1.1** on the amendment commit.
  prereg-v1 remains reachable as history for the "predates results"
  receipt.

**Where to look.** commits [tbd]; `configs/providers.yaml` (+2 entries),
`configs/voices.yaml` (+4 entries), `configs/pricing.yaml` (+2 rows),
`src/veval/adapters/{openai,speechify}.py` (new), spec §3.1 amended
provider table, CLAUDE.md project-overview roster line updated.

---

## D-002 — Corpus authored fresh, not curated from the parent (2026-08-07)

**What changed.** The spec/plan language framed the 60 novel items per use case
as *"curated and trimmed from the existing corpus after review."* Extraction
against the source docx found the parent corpus contains **only 20 long items
across all 10 parent use cases and nothing in the Short / Medium / Jargon /
Edge sections** (those section headers are present in the docx but empty).
The realistic origin is: the ~4 long items for the two kept use cases are
used directly (with light edits); up to ~12 further long items from the eight
cut parent use cases are rescued into narration where they fit; everything
else (all short/medium/jargon/edge items and the remaining long items) is
**authored fresh** to the same stratum brief the parent used.

**Why.** The pre-registered corpus target (75 items per use case, per spec
§3.3) cannot be met from the parent corpus. Two options were considered and
rejected before authoring:

- **Shrink the corpus.** Cutting to 30–40 items per use case would fall below
  TTSDS2's published 50-item minimum stability floor (spec §A.3, defect 3.7),
  reducing D3 from a headline signal to a supporting one — a real methodology
  hit for a saved day of authoring.
- **Substitute a public TTS corpus (LJSpeech / ARCTIC).** Would break the
  domain-match story: evaluating support-agent voice quality with
  book-reading test items is exactly the confound §3.3 exists to avoid.

Authoring in-scope items to the same per-use-case briefs preserves the
methodology and the volume; the honest change is *how the items got there*.

**Impact on results.**
- The contamination probe (spec §3.3) rests on a weaker claim than "guaranteed
  unseen" — authored English carries no formal guarantee of absence from a
  training corpus, and any items spiralled from the parent's machine-drafted
  seeds sit closer to model output than purely human-written text. Reported
  as a directional observation (as before, spec §3.3), never as a headline.
- Cross-provider WER, TTSDS2 and D4 comparisons are unaffected — every
  provider sees the same items regardless of who wrote them.

**Where to look:** spec §3.3 rewritten; `corpus/*.yaml` (to be written).
