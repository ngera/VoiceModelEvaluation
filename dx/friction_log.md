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

**Friction events:** (to fill in on live probe)

**Status:** ⏳ Adapter drafted, awaiting first live probe.

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
