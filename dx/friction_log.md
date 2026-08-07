# dx/friction_log.md — D7 developer-experience log

Live log for D7 (spec §3.7, A.7). **Cannot be reconstructed later — event
timestamps and specific errors are the measurement.** Start the clock at
"open provider docs" for each provider and log every friction event as it
happens.

Protocol per provider (spec §A.7):
- Start clock at "open docs"
- Stop at "first audio plays from a fresh venv"
- Log every: signup hurdle · key provisioning · missing/wrong sample ·
  undocumented header · confusing error · SDK ergonomic issue
- Same developer for all providers, consistent order noted below

Reported column in the final table: **DX minutes** (time from doc-open to
first-audio) + a friction summary per provider.

Onboarding order — matches Phase C build order (easiest → hardest,
Fish first because of Aug 31 free window):
1. Deepgram (baseline — completed as part of Phase A walking skeleton)
2. Fish Audio (Phase C day 1)
3. Google Cloud TTS
4. Cartesia
5. ElevenLabs
6. Canopy Orpheus (Replicate)

---

## Deepgram — baseline (Phase A)

**Wall-clock:** ~12 min from doc-open to first-audio (Phase A walking
skeleton). Not a real D7 measurement — the adapter was built before D7
was defined, so this row is provisional and will be re-run in a clean
throwaway session to make the measurement comparable (spec §A.7, defect
3.34).

**Friction events (retroactive, incomplete):**
- Streamed WAV shipped with a placeholder length header (`0x7FFFAC00` =
  44,737 seconds declared for a 2.8-second clip). Silent — downstream
  metrics would have read the lie. Fixed via `finalize_wav_header()` in
  `adapters/base.py`. **This is a portable-across-all-adapters gotcha
  now**, not a Deepgram-specific one — every streaming adapter will hit
  it.

**Status:** ⏳ Re-run needed for comparable D7 timing.

---

## Fish Audio — Phase C day 1 (2026-08-07)

**Wall-clock:** TODO — start when you open [docs.fish.audio](https://docs.fish.audio/)
in a fresh browser tab, stop when `veval doctor --provider fish` returns
✅ against a wav that plays.

**Assumptions in the adapter code that need verification** (I wrote the
adapter from prior knowledge — every one of these is a candidate
friction event to log):

- [ ] Endpoint is `POST https://api.fish.audio/v1/tts`
- [ ] Auth header format: `Authorization: Bearer <API_KEY>`
- [ ] `model` selected via HTTP header, not JSON body
- [ ] `reference_id` is the JSON key for voice_id (not `voice_id`, not `voice`)
- [ ] `format` in body accepts `"wav"` and `"mp3"`
- [ ] Streaming: response is chunked; `iter_bytes()` yields non-empty chunks
- [ ] Request-id returned in `x-request-id` or `request-id` header
- [ ] Free tier `s2.1-pro-free` is accessible with the standard API key
      (no separate "free tier flag" required)

**Friction events (2026-08-07 live probe):**
- **Zero fixes needed on first probe.** All 8 assumptions in the adapter
  were correct on first live call. Green ✅ against `s2.1-pro-free` with
  `9a9cf47702da476aa4629e2506d4a857` (conv voice), probe text
  "The quick brown fox jumps over the lazy dog."
- **Free-tier TTFA: 2279 ms** — high but exactly as spec §3.1 R9
  predicted ("best-effort with no SLA"). Would fail the conversational
  `ttfa_p90_ms < 400ms` gate by ~5×. Vindicates the
  `split_model_from_quality: true` design in voices.yaml: quality/WER
  runs on free, latency runs on paid `s2.1-pro`.
- Total round-trip: 2851 ms · 270,380 bytes of WAV audio · run written
  to `runs/doctor-20260807T215037Z/`.

**D7 timing caveat:** the wall-clock time for adapter authoring is NOT
a valid D7 measurement here — the adapter was drafted from prior
knowledge before the user opened Fish docs. Same asterisk as Deepgram.
Fish's D7 would need a clean re-run where a developer starts from
`docs.fish.audio` and builds forward. See §A.7 caveat.

**Status:** ✅ Adapter green end-to-end on first probe.

---

## Google Cloud TTS — Phase C (2026-08-07)

**Wall-clock:** TODO — start when you retry `veval doctor --provider google`.

**Auth path chosen (Path A):** raw httpx + API key via `?key=<KEY>`
query parameter. Alternative (service-account JSON + google-auth SDK)
was rejected on D1 comparability grounds — mixing SDK and raw-httpx
transports would asymmetrise the latency measurement across providers.
Service-account JSON stays in `.secrets/` unused. **Decision documented
in friction log rather than as a prereg deviation** because
`configs/providers.yaml` already declared `env_key: GOOGLE_API_KEY`
(matches Path A); no prereg change needed, no re-tag.

**Assumptions in the adapter to verify:**
- [ ] Endpoint `https://texttospeech.googleapis.com/v1/text:synthesize`
- [ ] Auth via `?key=<API_KEY>` (also works: `X-Goog-Api-Key` header)
- [ ] Body: `input.text`, `voice.name` = full `en-US-Chirp3-HD-Achernar`,
  `voice.languageCode` = derived from first two dash segments
- [ ] `audioConfig.audioEncoding` = `LINEAR16` returns raw PCM
- [ ] `audioContent` in response is base64
- [ ] Sample rate 24000 Hz is the Chirp3-HD default

**Design constraint carried into adapter:**
- REST is buffered → TTFA equals total_ms. `meta.transport =
  "buffered-rest"` recorded on every result. Every downstream table row
  for Google needs an on-chart footnote that its D1 numbers are not
  comparable to streaming providers' TTFA. Defect 3.15's "test
  streaming for 15 min first" is deferred to Phase D — first make
  buffered work, then probe.

**Friction events (2026-08-07 live probe):**
- **Zero fixes needed on first probe.** All 6 assumptions in the adapter
  were correct on first live call. Green ✅ against
  `en-US-Chirp3-HD-Achernar` (conv voice); probe text
  "The quick brown fox jumps over the lazy dog."
- **Total: 1099 ms** (buffered REST, TTFA=None as designed). WAV output
  144,088 bytes.
- Comparability caveat holds as expected: Google's 1099 ms is the full
  synthesis-plus-delivery time; Fish's 2851 ms includes only the first
  audio chunk arrival on the streaming path — the two numbers are NOT
  comparable as latency. This is exactly the "Google TTFA carries a
  footnote" story from spec §3.1.

**D7 timing caveat:** same as Deepgram + Fish — adapter authored before
user opened Google docs, so wall-clock time is not a true D7 measurement.

**Status:** ✅ Adapter green end-to-end on first probe.

---

## Cartesia — Phase C (2026-08-07)

**Wall-clock:** TODO — start when you run `veval doctor --provider cartesia`.

**Assumptions in the adapter to verify:**
- [ ] Endpoint `https://api.cartesia.ai/tts/bytes`
- [ ] Auth: `X-API-Key` header (Cartesia's own scheme, not Bearer)
- [ ] Required header: `Cartesia-Version` — pinned to `"2024-11-13"`.
      **Most likely friction event** — if Cartesia deprecated this
      date, HTTP 400 with a version-error body will tell us the current
      one. Bump + log to DEVIATIONS.md.
- [ ] Body: `model_id="sonic-2"`, `transcript` (not `text`),
      `voice.mode="id"`, `voice.id=<uuid>`,
      `output_format.container="wav"`, `output_format.encoding="pcm_s16le"`,
      `output_format.sample_rate=24000`, `language="en"`
- [ ] Response streams WAV chunks; first chunk has placeholder length
      header (same defect class as Deepgram, `finalize_wav_header`
      handles it)
- [ ] Request-id in `x-request-id` header

**Design constraints not enforced at the adapter level:**
- Concurrency cap (2 free / 3 Pro) — runner responsibility (Phase D)
- Free tier is non-commercial — user is on Pro per voices.yaml

**Friction events (2026-08-07 live probe):**
- **Zero fixes needed on first probe.** All 6 assumptions correct
  including the `Cartesia-Version: 2024-11-13` pin. Green ✅ against
  UUID `db6b0ed5-d5d3-463d-ae85-518a07d3c2b4` (conv voice).
- **TTFA: 1084 ms** — higher than expected for Sonic-2 (marketed as
  latency-optimised). Two possible causes to isolate in Phase D:
  cold-start first request effect, or regional edge routing.
- Total: 1660 ms · 122,394 bytes WAV · request-id `716a9179-...`

**D7 timing caveat:** same as prior three — adapter authored before
user opened Cartesia docs.

**Status:** ✅ Adapter green end-to-end on first probe.

---

## ElevenLabs — Phase C (2026-08-07)

**Wall-clock:** TODO — start when you run `veval doctor --provider elevenlabs`.

**Assumptions in the adapter to verify:**
- [ ] Endpoint uses voice_id in the PATH:
      `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream`
- [ ] Auth: `xi-api-key` header (not Bearer)
- [ ] `output_format` is a QUERY parameter (not body); `pcm_24000` for WAV
- [ ] Body: `text` + `model_id` (not `model` or `model_name`)
- [ ] `model_id="eleven_flash_v2_5"` is a valid model string for
      conversational (from voices.yaml). If it's deprecated, ElevenLabs
      returns 400 with a valid-models list — bump + log.
- [ ] Streaming: response is chunked raw PCM; TTFA measurable

**Design note carried into adapter:** `voice_settings` (stability,
similarity_boost, style) NOT sent — spec §3.4 requires sampling
parameters at documented defaults. Adding them here would be a prereg
deviation.

**Cost warning:** ElevenLabs is the biggest single-line-item provider
in the project (~$22 for one Creator month, spec §8). Doctor probe is
cheap (~5 characters × per-char cost) but future campaigns will burn
Creator credits fast.

**Friction events (2026-08-07 live probe):**
- **First non-zero-fixes event in Phase C.** HTTP 402 payment_required
  on the free tier:
  > "Free users cannot use library voices via the API. Please upgrade
  > your subscription to use this voice."
- **The friction is not an adapter bug** — ElevenLabs' access model
  separates browse from API-use. Library voices (community-uploaded)
  can be browsed on any tier but require a paid subscription to
  synthesize against via API. Only ElevenLabs' curated "premade"
  voices work on the free-tier API.
- **This is a real DX finding** for the case study: a developer
  picking a voice from the library UI on free tier gets a 402 only
  when they try to synthesize, not when they browse or copy the ID.
  Discoverability is misaligned with the access model.
- **Adapter otherwise correct** — HTTP 402 with a structured JSON
  error body was properly wrapped in `ProviderError` and the doctor
  reported it clearly, not a crash.

**Resolution (2026-08-07):** upgraded to ElevenLabs Creator plan ($22,
matches spec §8 budget for "one Creator month"). Re-ran with pinned
voice unchanged: green ✅. TTFA 565 ms · total 637 ms · 120,416 bytes.
No prereg amendment — voice + model in voices.yaml are unchanged.

**Subscription clock:** Creator month starts 2026-08-07, ends ~2026-09-07.
All ElevenLabs generation (campaign + any re-runs) must land inside that
window. Spec §8 rule: cancel after campaign to avoid auto-renewal charge.

**Status:** ✅ Adapter green end-to-end (after account upgrade).

---

## Canopy Orpheus (Replicate) — Phase C (2026-08-07)

**Wall-clock:** TODO — start when you set REPLICATE_API_TOKEN in `.env`
and run `veval doctor --provider orpheus`.

**Structurally different from the other 5 adapters.** Replicate is
async by design: POST creates a prediction, response returns an ID +
status; you either wait (via `Prefer: wait=<sec>` header, max 60s) or
poll `/v1/predictions/{id}` until terminal, then fetch the audio URL.
Two HTTP roundtrips minimum. D1 is **N/A-hosted per spec §3.1** — hosted
inference measures Replicate's cold-start and queue behaviour, not
Orpheus's first-token time. `ttfa_ms` is always `None`;
`meta.transport = "hosted-inference-poll"`.

**Assumptions in the adapter to verify:**
- [ ] Endpoint pattern `https://api.replicate.com/v1/models/canopyai/orpheus-3b/predictions`
- [ ] Auth `Authorization: Bearer <REPLICATE_API_TOKEN>` (legacy `Token`
      scheme also works; Bearer is current)
- [ ] `Prefer: wait=60` header keeps the create connection open
- [ ] Input schema uses `prompt` for text and `voice` for
      tara/leah/jess/leo/dan/mia/zac
- [ ] Output field is either a URL string or list of URLs to a .wav file
- [ ] Cold-start on first request may take 20-60s (model spin-up);
      subsequent requests are faster while the model stays warm

**Version pinning: TODO(Phase-C).** Adapter uses
`/v1/models/{owner}/{name}/predictions` (auto-latest). For campaign
reproducibility we should pin a specific version SHA in
providers.yaml or analyzers.yaml before Phase D, and log to
DEVIATIONS if the pinned SHA becomes stale during the campaign.

**Cost profile:** ~$0.003/generation at L40S GPU (spec §8 +
DEFECT_REGISTER 3.6 — corrected from the earlier $0.08 figure that
was 24× too high). Doctor probe cost: rounding-error negligible.

**Friction events:** (fill in on live probe)

**Status:** ⏳ Adapter drafted, awaiting first live probe. Needs
REPLICATE_API_TOKEN in `.env` (currently the missing 6/6 env key).

---

## OpenAI — Phase C.1 (2026-08-07, added prereg-v1.1)

**Wall-clock:** TODO — start when you run `veval doctor --provider openai`.

**Rationale for addition:** LLM-ecosystem-default archetype (see
DEVIATIONS.md D-003). Not in original 6; added after Phase C round
because "why not OpenAI?" is the reviewer question that answer-by-presence
handles better than answer-by-rationale.

**Assumptions in the adapter to verify:**
- [ ] Endpoint `https://api.openai.com/v1/audio/speech`
- [ ] Auth: `Authorization: Bearer <OPENAI_API_KEY>`
- [ ] Body: `model` (gpt-4o-mini-tts / gpt-4o-tts), `input` (text),
      `voice` (one of 11), `response_format` (`wav`/`mp3`)
- [ ] Voice IDs: alloy · ash · ballad · coral · echo · fable · nova ·
      onyx · sage · shimmer · verse (all 11 accepted on gpt-4o-* models)
- [ ] Response is raw audio bytes over chunked HTTP (streamable)
- [ ] `instructions` field NOT sent (spec §3.4 defaults rule)

**Friction events (2026-08-07 live probe):**
- **Zero fixes needed on first probe.** All 6 assumptions correct;
  `cedar` voice_id (which post-dates my training cutoff) accepted by
  the API — real voice as of 2026. Green ✅ against `gpt-4o-mini-tts`
  with `fable`.
- **TTFA: 1410 ms · Total: 1874 ms · 168,044 bytes.** Streaming works
  as expected over chunked HTTP; TTFA is real (first-byte time from
  streamed response).
- OpenAI ecosystem-default archetype now represented in the roster
  per DEVIATIONS.md D-003.

**D7 timing caveat:** same as the other adapters — authored offline
from prior API knowledge, so wall-clock isn't a valid D7 measurement.

**Status:** ✅ Adapter green end-to-end on first probe.

---

## Speechify — Phase C.1 (2026-08-07, added prereg-v1.1)

**Wall-clock:** TODO — start when you run `veval doctor --provider speechify`.

**Rationale for addition:** audit HI #1 archetype (see DEVIATIONS.md
D-003). Speechify sits at HI #1 (score 99); the direct like-for-like
run against that ranking is the "does the top of the leaderboard
hold up?" story.

**Assumptions in the adapter to verify:**
- [ ] Endpoint `https://api.sws.speechify.com/v1/audio/speech`
- [ ] Auth: `Authorization: Bearer <SPEECHIFY_API_KEY>`
- [ ] Body: `model="simba-3.2"`, `input` (text), `voice_id`,
      `audio_format` (`wav`/`mp3`), `language="en-US"`
- [ ] Voice ID format: short string like `simba-english` or per-voice
      UUID from Speechify voice library
- [ ] Response is raw audio bytes streamed over chunked HTTP

**Cost warning:** Speechify's free tier caps at 50K chars/mo —
insufficient for campaign volume. Starter plan ($10/mo, 1M chars)
required. Doctor probe: rounding-error cost.

**Friction events (2026-08-07 voice-ID research):**
- **Speechify's UI made voice_id discovery hard** — voice IDs are not
  surfaced in a copyable form in the browser voice library. Instead
  had to query the `/v1/voices` API directly with the account API key
  to enumerate. Portfolio-worthy DX observation: the browsing surface
  doesn't expose the API primary key (voice_id).
- **Only 8 of 956 voices support the flagship `simba-3.2` model**
  (verified via API 2026-08-07). Speechify's premium model has narrow
  voice coverage relative to older Simba variants. Constraint on
  pinning: `simba-3.2` forces one of 8, all English.
- Voice picks based on tag inspection:
  - Conversational: `geffen_32` (en-US, female, warm/intriguing;
    only voice in the 8 tagged both `conversational` AND
    `customer-service-ivr`)
  - Narration: `wyatt_32` (en-US, male, sophisticated/textured,
    middle-aged; all three narration tags present)

**Friction events (live probe pending):** (fill in when probed)

**Status:** ⏳ Voices locked; awaiting first live synthesis probe.

---

## Environment gotchas — not per-provider, but re-runners will hit them

Non-D7 friction: toolchain / venv / OS-portability issues encountered
during Phase C onboarding. Kept here rather than in a separate file so
the whole DX story is in one place; not part of the D7 measurement.

### `.venv` created in devcontainer breaks under native Windows `uv sync`
**Encountered:** 2026-08-07, at first `uv run veval doctor --provider fish`
after moving from devcontainer to native Windows.
**Symptom:**
```
error: failed to remove file `C:\...\voiceAgentEvals\.venv\lib64`:
Access is denied. (os error 5)
```
**Cause:** Linux venvs create a `lib64` symlink; when `uv sync` runs
under native Windows it tries to prune the existing venv and fails on
`lib64` because the symlink target is a Linux path Windows can't touch.
**Fix:**
```powershell
Remove-Item -Recurse -Force .venv
uv sync --extra admin --extra dev
```
**For re-runners:** if you develop under both the devcontainer and
native Windows, never share the same `.venv`. Nuke and re-sync when
switching.

### pytest test_log_api_serializes_non_json_values fails on Windows
**Encountered:** pre-existing since Phase A closeout, still open.
**Symptom:** `assert '\\tmp\\x' == '/tmp/x'` — `Path("/tmp/x")` on
Windows normalises to `\tmp\x` and the test's expected literal doesn't
match.
**Cause:** the test uses a POSIX-style path string as the expected
literal; on Windows the `default=str` serialiser converts to
Windows-style separators.
**Fix:** Not fixed yet. Options for a real fix: (a) use `pathlib.Path`
for the expected value too, (b) normalise separators before compare,
(c) skip on Windows. Deferred — not a functional regression, and it
predates Phase C.

---

## Friction taxonomy (for the final table)

Categories to score per provider on the final case-study DX friction table:

- **Signup:** email-only vs card-required; steps to reach an API key
- **Auth:** header format clarity; docs-to-code correctness
- **First call:** which sample from docs runs unmodified? none = friction
- **Undocumented behavior:** headers, body fields, or error codes the
  docs don't mention
- **Errors as data:** are provider error responses machine-actionable
  (status code + typed body) or free-form prose?
- **Streaming ergonomics:** does the docs sample stream correctly, or
  demonstrate only buffered?
- **Model/voice selection:** how obvious is the mapping from
  provider-visible voice/model choices to API parameters?

Each provider gets a one-liner in the final results table:
*"Provider X — 11 minutes; Provider Y — 74 minutes and an undocumented header."*
That's the artifact spec §A.7 exists to produce.
