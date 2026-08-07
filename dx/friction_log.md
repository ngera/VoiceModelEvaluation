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

**Friction events (log as you hit them):**
- (Add rows here with timestamp, event, resolution)

**Status:** ⏳ Adapter drafted, awaiting first live probe.

---

## Google Cloud TTS — Phase C

**Wall-clock:** TODO

**Friction events:** (Add rows as encountered)

**Status:** ⚪ Not started.

---

## Cartesia — Phase C

**Wall-clock:** TODO

**Friction events:**

**Status:** ⚪ Not started.

---

## ElevenLabs — Phase C

**Wall-clock:** TODO

**Friction events:**

**Status:** ⚪ Not started.

---

## Canopy Orpheus (Replicate) — Phase C

**Wall-clock:** TODO

**Friction events:**

**Status:** ⚪ Not started.

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
