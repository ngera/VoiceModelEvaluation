# 08 · Key findings, in plain language

*The same findings as [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md), rewritten
for a reader who doesn't want the σ ratios and JSON pointers. Every
finding here maps to a specific technical entry — the F-code in
parentheses at the end of each section tells you where to go for the
receipts.*

> **Scope reminder** · Findings apply to specific vendor accounts on
> paid public tiers, one voice per vendor per use case, measured
> across August-September 2026 from a residential Windows 11
> environment. Full scope in [../DISCLAIMER.md](../DISCLAIMER.md).

> **How this got here in two phases**: **Phase 1** (2026-08-09 to
> 2026-08-31) established the baseline findings — two full campaign
> runs three weeks apart, 8 vendors × 2 use cases × 75 items each,
> replicated cleanly. Phase 1 raised three specific questions that a
> targeted **Phase 2 experiment pack** (2026-09-01) then answered
> for ~$3.55 more in vendor spend. Findings 4, 6, and 12 are where
> Phase 2 sharpened or extended the Phase 1 story. Everything is
> traced back to committed artefacts under
> [`analysis/`](../analysis/) and the audit trail is in
> [../CORRECTIONS.md](../CORRECTIONS.md).

---

## 1. Cartesia's audio is jammed against a numeric ceiling — and it breaks tools

**Think of audio like water filling a glass.** Every voice has quiet
moments (a whisper) and loud moments (an emphasized word). A digital
audio file has a **maximum loudness ceiling** — the top of the glass —
and every sound has to fit under it.

Cartesia's audio pours right up to the rim. Other vendors leave some
empty space at the top. When Cartesia's louder syllables hit the
ceiling, the top of the sound wave gets **flattened** — like water
that overflows the glass gets wasted. That's called **clipping**.

**Concrete example**: on a 1,460-character medical instruction ("Your
upper endoscopy is scheduled for Wednesday the 22nd at 9:30 AM…"),
four vendors read the exact same text. Headroom at the top:

| Vendor | Headroom at the top |
|---|---|
| **OpenAI** | Roomy — leaves half the space empty |
| **ElevenLabs** | Small margin, but a margin |
| **Speechify** | Small margin, but a margin |
| **Cartesia** | **None. Zero. Right at the ceiling.** |

Cartesia's audio ran into the ceiling **36 times** in 87 seconds.
Each event is under half a millisecond, so it sounds like faint
crackle rather than a serious defect.

**Why it matters even if you can barely hear it**:

1. **Quality-check tools refuse to read it.** One of the two industry-
   standard MOS scoring tools (Microsoft DNSMOS) refused **46% of
   Cartesia's files on our first run and 41% on our replication
   run** — pooled across both use cases; roughly half in every
   round — because they hit the ceiling.
   No quality score is computable for those files. The ruler
   couldn't even measure them.
2. **Anything downstream can make it worse.** Change the volume,
   convert to a phone-system format, feed into speech recognition,
   add a filter — those operations can push already-at-the-ceiling
   audio *over* the ceiling, producing a scratchy, distorted sound.
   Every other vendor's audio survives these operations fine;
   Cartesia's often doesn't.

**Not a one-off**: the same pattern showed up in both our campaign
runs, three weeks apart, on the same corpus — Cartesia had **429
clipped samples across 68 narration files the first time, 420
across 70 the second**, 11-14× more than the next-worst (R2 429/39 = 11.0×; R3 420/30 = 14.0×)
vendor on narration (Google, 39/30). On conversational the gap is
even wider — Cartesia 406/377 vs the next-worst (Speechify 1
sample on R2, ElevenLabs 1 sample on R3), so ~400× more. Two other
vendors also fail the narration long-stratum clipping gate at
lower magnitudes (Google 36/28 clipped samples on the 8 long
items; Speechify 3/10), so "only Cartesia clips" is not quite
right — Cartesia is the dominant case by 1–2 orders of magnitude,
but not the only one.

**What a customer would do about it**: add a one-line audio
"peak-limiter" step that pulls the loudest samples back by about
1 dB (a change nobody would hear). That rescues the roughly
half of files (46% R2 / 41% R3, pooled across use cases) DNSMOS
currently refuses. If you don't want to build that step,
pick a different vendor.

**Finding referenced in the technical docs as F-4 + F-4a.**

---

## 2. The "cheapest" vendor's output is capped at 14.59 seconds

**Think of it like a phone plan that says "unlimited talk" but
cuts you off at 14 seconds if you're on a long call.** Orpheus
lists at $0.003 per generation — the lowest price on the roster.
The catch: the audio Orpheus produces per call is **capped at
14.59 seconds** at this hosted endpoint. If your text fits under
that limit, you get a complete recording. If it doesn't, everything
past 14.59 seconds is silently dropped.

On our 8-item long-narration test (T8, 60–90 s of expected audio
per item), every one of the 8 items hit the cap and was truncated.
On the full 75-item narration corpus, **27 items (36%) were
truncated** at the cap; the other 48 came back complete because
they were short enough to fit. If you send Orpheus a two-sentence
text (fits under 14 seconds), you get a complete recording. Send
it a one-paragraph text that would take 90 seconds to read aloud
and everything after the first 14 seconds is silently lost.

**Why this makes the "cheapest" label misleading**: for anything
longer than a short conversational turn, you have to chunk the text
into pieces short enough to fit, pay for each piece separately, and
stitch the audio back together. Once you do that math honestly, the
per-word cost is around **$0.07-0.09 per 1,000 words** — right in
the same range as OpenAI ($0.075). Not cheap.

**Where the misleading $0.03 number comes from**: our cost model
assumed each call produced 100 words of audio (a typical
"conversation turn"). Orpheus actually produces about 35 words per
call because of the cap. The $0.03 is what the model predicted; the
actual per-word math is 2-3× higher.

**Where Orpheus is genuinely useful**: any use case where every
individual utterance comfortably fits in 14.59 seconds — a short
prompt, an alert message, a quick reply. Beyond that, look
elsewhere.

**Finding referenced in the technical docs as F-5 + F-9 test T8.**

---

## 3. If you ask the same voice to say the same sentence twice, you get two different recordings

**None of the 8 vendors produces bit-identical audio when you send
the same text twice.** Every request creates a fresh generation.

For most product use cases this doesn't matter — the audio sounds
the same to a listener. But it matters if:

- You cache audio by content hash to avoid re-billing → you can't,
  because the bytes are different every time
- You have automated regression tests that check "this audio matches
  the golden file" → they'll fail on every run
- You need to compare "did the audio change after we updated our
  prompt?" → you can't tell from the audio alone

**What to do**: save the audio yourself the first time you generate
it. Re-requesting is not the same file.

**This is universal across all 8 vendors.** Not a vendor to blame,
just a property of modern TTS systems that customers routinely
assume otherwise about.

**Finding referenced in the technical docs as F-1.**

---

## 4. How fast a vendor answers can swing session-to-session — for OpenAI a lot, for ElevenLabs mostly not (six-session view; one big S3 outlier)

**We measured the same "how quickly does the voice start speaking"
metric across six separate sessions over four different days.** On
the same conversational text, on the same vendor, from the same
computer:

| Session | ElevenLabs (UTC → p90) | OpenAI (UTC → p90) |
|---|---|---|
| S1a | 2026-08-09 21:41 → 479 ms | 2026-08-09 21:41 → 956 ms |
| S1b | 2026-08-09 22:23 → 474 ms | 2026-08-09 22:23 → 946 ms |
| S2 | 2026-08-11 → 469 ms | 2026-08-11 → 1,493 ms |
| **S3** | **2026-08-12 → 816 ms** ← outlier | **2026-08-12 → 1,882 ms** ← outlier |
| **S4** | **2026-09-01 18:57 → 461 ms** | 2026-09-01 19:07 → 1,212 ms |
| **S5** | **2026-09-01 19:10 → 468 ms** | 2026-09-01 20:10 → 1,206 ms |

Neither vendor is "stable" in an operational sense. Both swing by
more than half of their own values across sessions — ElevenLabs
range 461-816 ms (+77%), OpenAI 946-1,882 ms (+99%).

**What Phase 2 added**: Sessions 4 and 5 (2026-09-01) landed back
in the S1 baseline range for both vendors. That **confirms S3 was
a real transient outlier, not the new normal**. But the wider
"variance is high" finding stands — but not equally: excluding
S3, **ElevenLabs is tight at 3.9–6.8%** (p50 412–440 ms, p90
461–479 ms) while **OpenAI swings 27–58%** (p50 736–936 ms, p90
946–1,493 ms).

**What we ruled out**: it's not our internet connection. We ran a
background network check during the third session — the network
was clean and fast. Something else is slowing both vendors down on
that day, and it affects them in similar amounts. Best guess:
something on our own laptop (a background scan, an OS update, a
Python quirk on that specific run). But we can't prove it even
with six sessions.

**What survives the finding**: the **ranking** is portable —
ElevenLabs is consistently faster than OpenAI in all 6 sessions.
But the specific absolute number (like "ElevenLabs is 469 ms")
isn't something you should quote as a spec.

**What this means for you**: if latency matters to your product,
**measure it from your own environment across at least 5 sessions
on different days**. Don't provision from a single measurement, and
be sceptical of any vendor's own marketing latency number too —
those are usually best-case measurements from a datacenter next to
their servers, not from where your users will actually be.

**Finding referenced in the technical docs as F-11.**

---

## 5. Two respected "audio quality" tools disagree about which vendor is best

**We used two independent tools for measuring audio quality, both
from major AI labs (Meta and Microsoft), both peer-reviewed, both
industry-standard.** They ranked the 8 vendors *differently*.

Here's the thing that took us a while to understand: **it's not
that one of them is "wrong."** They actually measure different
things underneath the surface. And the split isn't neatly between
the two tools — it's between the two *axes* Meta's tool measures:

- **Meta's Audiobox has two axes.** They behave differently:
  - **PQ ("production quality")** is the **technical-cleanliness**
    axis. Meta trains it against exactly the kind of criteria
    Microsoft's DNSMOS uses — timbre, absence of distortion.
    Empirically the two agree: Audiobox PQ has a mean Spearman
    correlation of **+0.24** with DNSMOS across the 8 vendors
    (strongest single pair: +0.57 against DNSMOS's P.808
    single-model listening-quality MOS).
  - **CE ("content enjoyment")** is the **warmth/aesthetic** axis
    — the one that rewards a voice sounding engaging rather than
    just clean. It **anti-correlates** with DNSMOS (mean Spearman
    ρ = −0.51 across 8 vendors), which is why the two-pipeline
    aggregate ρ comes out negative.
- **Microsoft's DNSMOS** measures the same *technical-cleanliness*
  construct as Audiobox PQ, from a different training pipeline. It
  does not measure warmth.

**What the data actually says** — Speechify's lead over the #2
vendor on each axis, reported as unpaired SE(diff) between
per-vendor means (04's default reporting; the paired-per-item
values in 04 § Rankings summary are larger, 6.0–17.2σ, because
they use item-level pairing):

| axis (what it measures) | conv Speechify lead | narr Speechify lead |
|---|---|---|
| **AB.PQ** (Audiobox cleanliness) | **+3.71σ** ✓ significant | **+9.48σ** ✓ significant |
| **AB.CE** (Audiobox warmth) | **+5.91σ** ✓ significant | **+7.28σ** ✓ significant |
| DNSMOS OVRL (Microsoft cleanliness) | OpenAI +1.27σ over ElevenLabs (**TIE**; 2.0σ paired — 04 calls this borderline) | OpenAI +0.68σ over Orpheus (**TIE**) |

Two things about this table are load-bearing:

1. **Speechify wins BOTH quality axes Audiobox measures — the
   cleanliness axis AND the warmth axis.** Not one or the other.
   On both use cases, at 3.7σ and higher significance. This is not
   a "warm-vendor" vs "clean-vendor" split; Speechify is #1 on
   both by the project's own SE(diff) test.
2. **There is no "clear winner" on DNSMOS cleanliness.** The tie
   band composition depends on the use case: on conversational,
   OpenAI + ElevenLabs are tied at the top (Δ 1.27σ) with
   Orpheus #3 at 9.3σ behind; on narration, OpenAI is tied with
   **Orpheus (0.68σ)**, **Deepgram (1.07σ)**, and **Speechify
   (1.58σ)** — ElevenLabs is #7 at 6.75σ behind, not part of the
   narration tie. Every 04 ranking table labels the tied cluster
   as a tie, not as a win.

Prior "Speechify clear winner on warmth / OpenAI clear winner on
cleanliness" wording retracted; see
[CORRECTIONS rows 9 + 10 + 33](../CORRECTIONS.md).

**Why this matters for you**: any single "quality score" reported
by one MOS predictor is measuring a specific version of quality.
"Vendor X is best on DNSMOS" translates to "vendor X sounds
cleanest" — and even then, "cleanest" often means "cleanest of a
cluster that's statistically tied", not a clear win. "Vendor Y is
best on Audiobox" needs to specify *which* Audiobox axis: PQ
tracks cleanliness (agrees with DNSMOS), CE tracks warmth
(disagrees). Match the axis to the sound your users actually want.

**Finding referenced in the technical docs as F-8.**

---

## 6. Voice choice inside a vendor changes measured quality — Speechify's same-gender swap already shows a >3σ shift, so it's not just a male-vs-female artefact

**A hostile reviewer's first objection would be: "you got lucky with
the voice you picked."** Every vendor offers dozens of voices; maybe
we happened to pick each vendor's one good one, or its one weak one.

Phase 1 checked this only on Speechify. **Phase 2 extended the check
to four more vendors** (OpenAI, Fish, Deepgram, Google) by running
the same 8-item narration text through each vendor's original voice
and a deliberately different alternate voice, then comparing quality
scores.

**What we actually measured** — the paired difference in Meta's
Audiobox "production quality" score, item-by-item, for each vendor:

| Vendor | mean quality shift (alt vs pinned) | how sure we are it's real |
|---|---:|---|
| OpenAI (onyx → nova) | −0.15 | 3.3 standard errors — real |
| Google (Charon → Kore) | −0.11 | 7.3 SE — real |
| Fish (opaque UUIDs) | +0.16 | 5.1 SE — real |
| Deepgram (orion → luna) | **−0.48** | **13.5 SE — real and big** |

**Every alt voice shifts the score by more than 3 standard
errors.** No vendor's ranking "held within noise." The magnitudes
range from OpenAI's 0.15 to Deepgram's 0.48 (3× larger). Direction
isn't stable either — Fish's alt voice scored *higher* than its
pinned voice; the other three scored lower.

**The confound that makes this hard to interpret**: every alt-voice
pair in the Phase 2 batch crossed gender against the pinned voice
— OpenAI's onyx (male) vs nova (female), Deepgram's orion (male)
vs luna (female), Google's Charon (male) vs Kore (female). Fish
uses opaque UUIDs so we can't check gender directly. **But
Speechify's earlier T6 test split by use case**: conversational
was cross-gender (geffen female → edmund male), and **narration
was same-gender** (wyatt male → edmund male, both male). Recomputed
on the 20 T6 items, the same-gender narration swap still produces
a **+4-standard-error AB.PQ shift**. So voice choice within a
vendor produces a ≥3σ quality shift *even when gender is
matched*, on at least one vendor — the "male-vs-female confound"
story does not explain away the Speechify result.

Prior "HOLDS / SHIFTS" split retracted; see
[CORRECTIONS row 25](../CORRECTIONS.md).

**What this means for you**:

- **Don't pick a voice from any vendor's catalogue expecting
  aggregate reported quality to transfer to your specific voice
  choice.** Every alt voice we tested produced a measurable
  quality shift on the same content — including the one
  same-gender comparison we have (Speechify wyatt→edmund on
  narration).
- **Audition your candidate voices on your own text before
  committing.** This applies to all five vendors we tested.
- **Deepgram is the largest observed shift** among the four
  Phase 2 cross-gender pairs, big enough to survive any plausible
  gender component.

**Caveat**: still only 2 voices per vendor. A v2 sweep would test
2 same-gender alt voices per vendor across the other 7 vendors —
we've already established a >3σ same-gender voice-choice effect
on Speechify (T6 narration), so the residual question is whether
the same pattern holds on the other vendors. Design in
[07_GAPS_AND_FUTURE_WORK.md gap #2](07_GAPS_AND_FUTURE_WORK.md).

**Finding referenced in the technical docs as F-7; Phase 2
evidence in
[EXPERIMENTS_2026-09-01.md § Follow-up 4](EXPERIMENTS_2026-09-01.md).**

---

## 7. Every measured vendor missed the pre-registered response-time bar

**Before we ran any measurements, we committed to a specific
"real-time voice" bar: the 90th-percentile response time must be
under 400 milliseconds.** The 400 ms figure is a **deliberate
headroom margin** below the ~500-600 ms perception threshold that
research literature calls "noticeably laggy" — we picked it lower
so a TTS-latency claim leaves budget for the LLM and network
that also sit in the end-to-end response time.

**Best result any vendor achieved across all 6 sessions**:
ElevenLabs S4 at **461 ms** (S1a 479, S1b 474, S2 469, S3 816,
S4 461, S5 468). That's 15% over the 400 ms bar.

The other measured vendors were further off:

- Cartesia: 529 ms (32% over)
- Deepgram: 670 ms (68% over)
- OpenAI: 946 ms (137% over — more than double)

**Every measured vendor failed our pre-committed real-time bar**,
in every session we measured.

**Why this doesn't automatically kill any vendor**: 400 ms was a
conservative bar (we picked it to leave headroom below the ~500 ms
"noticeably laggy" threshold from research literature). A vendor
at 461 ms is still perceptually fine for most conversational
products. But nobody in the roster is a slam dunk for real-time
voice.

**What this means for you**: if response time is a genuine hard
requirement, budget for the possibility that you'll need to
measure from your own environment, and remember that any specific
number can shift day-to-day by 50%+ (see finding #4). "This vendor
hits 400 ms" is not a claim you should take from anyone's
marketing page without your own replication.

**Finding referenced in the technical docs as F-11 and the
[TTFA-gate admission](04_RESULTS.md#ttfa-gate-admission).**

---

## 8. No single vendor is the "best" one to pick

**Across the measurement axes we tracked** (response time, cost,
Audiobox's two quality axes, DNSMOS's four cleanliness axes), the
top spot goes to a different vendor depending on the axis — but
several axes have **statistical ties** at the top rather than a
clear winner, so the honest form is:

- Fastest response → **ElevenLabs** (rank stable across all 6
  latency sessions)
- Cheapest per 1,000 words → **OpenAI** or **Fish** (tied at
  $0.075/1K, at any volume)
- Audiobox cleanliness (PQ) + Audiobox warmth (CE), on both use
  cases → **Speechify** (only vendor to win both axes at ≥3.7σ;
  see finding #5)
- DNSMOS OVRL (Microsoft's cleanliness axis) → tie band depends
  on use case: **conversational** = OpenAI + ElevenLabs only
  (Δ 1.27σ); **narration** = OpenAI + Orpheus + Deepgram +
  Speechify (Δ 0.68–1.58σ, ElevenLabs is #7 at 6.75σ behind on
  narration)
- Loudest headroom / cleanest waveform packaging → **OpenAI**
- Fewest words dropped or mispronounced → close cluster of 4-5
  vendors, no clean winner

**This is not a "measurement was noisy" problem — it's the actual
finding.** The picture that emerges when you respect the tie bands
is:

- Support-agent voice bot (real-time, short turns) → **ElevenLabs**
  is fastest; no vendor clears the pre-registered 400 ms p90 gate
  (see finding #7).
- Long-form narration where any quality measure is what matters →
  **Speechify** wins Audiobox on both axes at ≥3.7σ.
- Enterprise IVR / phone agent (conversational, clean signal
  above all) → **OpenAI**. The conversational DNSMOS OVRL tie
  band is only OpenAI + ElevenLabs (Δ 1.27σ), and of those two
  ElevenLabs fails the pre-registered conversational
  `clipped_samples == 0` gate on R3 (1 clipped sample, and R3's
  Cartesia has 377 as the dominant failure). OpenAI passes the
  conv clipping gate on both runs. Deepgram is *not* in the conv
  tie band (6.4σ behind OpenAI on OVRL conv) and has an audible
  −46 dBFS background floor (see finding #9), so it is not the
  right IVR recommendation despite being in the *narration* tie
  band. See [04's gate table](04_RESULTS.md#pre-registered-gate-outcomes).
- Long-form narration where clean-signal DNSMOS is what matters
  → **OpenAI alone**. The narration DNSMOS OVRL tie band contains
  OpenAI + Orpheus + Deepgram + Speechify, but of those four
  **only OpenAI passes all three pre-registered narration gates**:
  Deepgram fails the RTF gate (long-stratum rtf_p50 = 2.14, well
  below the pre-registered `rtf ≥ 3.0` threshold); Orpheus flipped
  from pass to fail on the R3 noise-floor gate (worst-of-8 shifted
  to −27.8 dB); Speechify fails the long-stratum clipping gate (3
  samples on R2, 10 on R3). See 04's [RTF admission](04_RESULTS.md#rtf-admission)
  and [gate table](04_RESULTS.md#pre-registered-gate-outcomes).
- Cheapest for very-short quick replies → **OpenAI** or **Fish**.

**What this means for you**: the "which is the best voice AI
vendor?" question has no single correct answer. The right vendor
depends on **which axis matters most for your product**. Use the
cheat sheet above to name the top pick per use case, not any
single quality score that flattens the six machine-quality signals
we track into one number.

**Finding referenced in the technical docs as F-3.**

---

## 9. If your product is a phone system, listen carefully to Fish and Google before committing

**"Background noise" in a recording is the quiet hiss you hear when
nobody is talking.** Perfect audio has a very quiet background —
you can only hear it if you crank the volume way up. Noisy audio
has an audible hiss even at normal volume.

The scale we use is **dBFS** ("decibels below full scale") — it
measures how quiet the background is *relative to the loudest
possible sample in a digital audio file*, not against any real-
world reference. **More negative is quieter, less negative is
louder.** Digital silence is −∞ dBFS. For our loudness-normalised
audio (all clips normalised to −18 LUFS speech level) the graded
listener rubric is:

| dBFS range | Listener label |
|---|---|
| ≤ −55 | very quiet, professional |
| −54 to −48 | quiet, broadcast-clean |
| −47 to −41 | slight audible hiss |
| −40 to −36 | audible hiss on quiet phone systems |
| ≥ −35 | loudest background — most audible hiss |

The dBFS scale is not comparable to any real acoustic measurement
without a playback level and room reference; the ordering below
is what matters, not the absolute values. **DISCLAIMER § Language
and framing** carries the same rubric so the audit trail agrees
with the presentation here.

Where each vendor sits on that scale (sorted by value, ascending
= quiet to loud), averaged across their conversational audio:

| Vendor | Conversational background noise | Reads as |
|---|---:|---|
| Cartesia | −57 dBFS | very quiet, professional |
| Speechify | −57 dBFS | very quiet, professional |
| Orpheus | −53 dBFS | quiet, broadcast-clean |
| OpenAI | −52 dBFS | quiet, broadcast-clean |
| ElevenLabs | −52 dBFS | quiet, broadcast-clean |
| Deepgram | −46 dBFS | slight audible hiss |
| **Fish** | **−39.7 dBFS** | **audible hiss on quiet phone systems** |
| **Google** | **−34 dBFS** | **loudest background — most audible hiss** |

Fish and Google are **17-23 dB louder** in their background hiss
than the cleanest vendors (Cartesia and Speechify at −57 dBFS).
That's not a small margin — it's the difference between "sounds
like a studio recording" and "sounds like a call from 20 years ago."

**Why this matters even if the voice itself sounds good**:
enterprise IVR systems, accessibility tools, and phone-agent
products get judged on the *overall* audio experience, not just
the words. If a customer picks up the phone and hears audible hiss
underneath the voice, they interpret it as a low-quality call.
Vendors like Cartesia, Speechify, OpenAI, ElevenLabs, and Orpheus
produce audio that sounds professionally recorded. Fish and Google
audibly don't, at least not on the paid tiers we tested.

**What to do about it**:

- **For phone-system / IVR / accessibility use cases**: audition Fish
  and Google on real conversational text through your actual playback
  environment (phone speaker, hearing aid, etc.) before committing.
  They may be fine for your use case, but the risk is higher than
  with the quieter-background vendors.
- **For any use case where the audio is played over loud content**
  (games, videos with music underneath, background of an app):
  probably fine. The hiss is masked by whatever else is playing.
- **The cleanliness gap isn't fixable downstream** in the way
  Cartesia's clipping problem is. Noise floor is baked into the
  generation — a noise-reduction filter on the output will make the
  voice sound artificial too.

**Finding referenced in the technical docs as N2 (Fish specifically)
and the acoustic-noise-floor readings across all vendors in
`hygiene.json`.**

---

## 10. Speechify's "cheap warm vendor" label reverses at low volume

**Speechify has been the "cheap warm-quality winner" in most of our
findings.** At 100,000 words per month it's $0.10 per 1,000 words —
about half of ElevenLabs' $0.22.

But there's a plot twist: **Speechify's Starter plan is a flat
$10 per month for 100,000 words included.** That works out beautifully
at exactly 100K/mo. It works even better at 1M/mo (you pay per
million on top, but the per-word rate drops to about $0.04).

**Below 100K/mo, though, you're paying the full $10 subscription no
matter how few words you use.** At 10,000 words per month, that $10
divided by 10,000 words = **$1.00 per 1,000 words** — the second-most-
expensive vendor in the roster, only ElevenLabs Creator is worse.

Here's how it looks across three volume tiers:

| Vendor | 10K words/mo | 100K words/mo | 1M words/mo |
|---|---:|---:|---:|
| OpenAI | $0.075/1K | $0.075/1K | $0.075/1K |
| Fish | $0.075/1K | $0.075/1K | $0.075/1K |
| **Speechify** | **$1.00/1K** ⚠ | **$0.10/1K** ✓ | **$0.04/1K** ✓✓ |
| Deepgram | $0.15/1K | $0.15/1K | $0.15/1K |
| ElevenLabs | $2.20/1K | $0.22/1K | $0.24/1K |

Notice the pattern: **the two vendors with a monthly subscription
model (Speechify, ElevenLabs) are dramatically expensive at low
volume and dramatically cheap at high volume.** OpenAI, Fish,
Deepgram, and Google are flat pay-per-use — same per-word rate at
any volume.

**Who this matters for**:

- **A startup or prototype at <10,000 words/month**: Speechify's warm
  quality is real, but the *cheapest* way to get that warm quality
  is not Speechify at that scale. OpenAI or Fish at $0.075/1K flat
  will be much cheaper for a small workload. Speechify only earns
  its "cheap warm-quality" title above 100K words/month.
- **A production app running >100K words/month**: Speechify's
  Starter plan turns into a genuine bargain — cheaper per word than
  every alternative at 100K/mo, and *much* cheaper at 1M/mo.
- **A hobbyist / occasional-use product**: even a $10/mo subscription
  might be too much overhead — OpenAI's pay-per-use will cost you
  literal cents per month at that scale.

**The general lesson**: any vendor with a "starter plan" model has
this same math. Match the pricing model to your actual volume, not
to the marketing headline.

**Finding referenced in the technical docs as the
[Cost calculus section in 04_RESULTS.md](04_RESULTS.md#cost-calculus).**

---

## 11. Two independent runs of the whole experiment produced the same answers

**Three weeks after our first campaign, we re-ran the entire thing
from scratch** — same 8 vendors, same 150-item corpus (75
conversational + 75 narration = 1,200 outputs across 8 vendors),
fresh generations from every vendor's live API, no cached data.

**12 of the 14 "top-1 winner" positions came out identical.** The
two positions that flipped were both inside the noise floor (small
margins on axes that no headline claim depends on) — DN.p808 on
narration (Cartesia → Fish, by 0.024 on a 5-point scale) and WER on
conversational (OpenAI → Speechify, by 0.00346, with three vendors
— Speechify, Fish, ElevenLabs — sitting inside a 0.007 band of
each other and five vendors sitting inside 0.01).

> **WER caveat carried through this whole doc**: the WER numbers
> we quote include the 15 famous-sentence contamination-probe
> items per use case (Harvard sentences + literary openings —
> spec § 3.3). Those items transcribe about five times more
> accurately than the sentences we wrote ourselves, so every
> vendor's WER looks **~3 percentage points lower** than it
> would on the 60 non-probe items alone. **The top-1 winner is
> the same either way** — OpenAI has the cleanest conversational
> WER on both readings (16.94% probe-excluded vs 13.70% all-75),
> Cartesia leads narration on both. What actually moves is
> 3rd/4th place on conversational: Speechify passes ElevenLabs
> under probe exclusion. Quality scores (Audiobox / DNSMOS
> rankings) are not affected — this is a WER-only issue. Full
> technical details in
> [04 § WER-gate admission](04_RESULTS.md#wer-gate-admission)
> and [02 § Contamination probe](02_METHODOLOGY.md#probe).

- Speechify won **both** Audiobox axes (PQ + CE) on **both** use
  cases: **same in both runs**
- OpenAI won DNSMOS OVRL + SIG on both use cases: **same in both
  runs**. The tie-band composition differs by use case:
  conversational is OpenAI + ElevenLabs only (Δ 1.27σ); narration
  is OpenAI + Orpheus + Deepgram + Speechify (Δ 0.68–1.58σ, ElevenLabs
  is #7 at 6.75σ behind on narration).
- Cartesia's clipping problem: **same magnitude in both runs**
  (429/420 samples on narration; 406/377 on conversational)

**One thing that also came out of the R3 replication**: we run
each audio file through **three separate scoring models** — Meta's
Audiobox (which outputs two axes, PQ + CE), Microsoft's DNSMOS
P.808 single-model predictor (which outputs one axis), and
Microsoft's DNSMOS P.835 three-scale predictor (which outputs
three axes: overall, signal, background). **Two of those three
scoring models detected a downward ElevenLabs drift between R2
and R3; the third didn't.** There are 6 Audiobox + P.808 cells
(2 use cases × 3 axes); 5 of the 6 survived multiple-comparison
correction (all except conv DN.p808 at z = −2.26σ). None of the
6 P.835 cells did. Whether P.835 missed the drift because it's
less sensitive to whatever ElevenLabs changed, or because
ElevenLabs changed something P.835 genuinely doesn't measure,
isn't separable from this data.

Three non-ElevenLabs cells also crossed the |z| > 2 threshold
before correction (Speechify narration on two axes, Fish narration
on one), but across 96 statistical tests you'd expect roughly five
of that size by chance — none survives correction, so we treat
them as noise. **ElevenLabs is the only vendor with any
correction-surviving shift.**

**A single-model update doesn't explain it**: ElevenLabs uses a
different underlying model for conversational (Flash v2.5) than
for narration (Multilingual v2), and both models drift together
— pointing at something shared (voice embedding, serving
pipeline) rather than a model release. The honest R2→R3 interval
is bounded by R2's cache-only synthesis (the manifest records
only the cache-hit date of 2026-08-09, not the underlying
synthesis date, which is unrecorded and earlier) and R3's fresh
generation on 2026-08-31. Full write-up with the paired-z table,
scorer-architecture split, and mechanism discussion in
[F-12](06_KEY_FINDINGS.md#f-12).

*(We do not list "per-word costs matched to 4 decimal places
across the two runs" as replication evidence: modelled cost =
chars × rate, and both runs used the same corpus, so cost matches
by construction regardless of what audio came back. It would
match if every vendor had returned silence.)*

**Why this matters**: it's one thing to run an experiment once and
publish an answer. It's another to run it again three weeks later
and get the same answer. The findings above are not luck-of-the-
draw artefacts.

**What did change between R2 and R3**: (a) ElevenLabs shifted
significantly downward on 5 of 6 Audiobox + DNSMOS P.808 cells
(see finding #11 above and the technical F-12 write-up), and
(b) response-time absolute values move session-to-session by
50–90% p50 in the outlier session (see finding #4) — although the
latency series is on its own schedule (six sessions across four
dates), not R2 vs R3. Rankings held on both quality and latency.

---

## 12. Long narrations sometimes fade out mid-way — across multiple vendors, not just one

**On a long piece of narration, some vendors quietly get quieter as
the text goes on.** Not a dramatic fade — more like the voice
starting at normal volume, then dropping ~2-3 dB by the end. A
listener would probably describe it as "sounds like it trailed off."

Phase 1 caught this on one specific ElevenLabs item (L03) and we
initially assumed it was a one-off quirk of that particular text.
**Phase 2 tested that assumption by generating fresh long-form
narrations across all 8 vendors and measuring the loudness curve
end-to-end.**

**The result**: it's not one-off, and it's not just ElevenLabs.

| Vendor | Fade rate on long narrations |
|---|---:|
| **ElevenLabs** | **25%** (2 of 8 items faded) |
| **Deepgram** | **12%** (1 of 8 items faded) |
| **Orpheus** | **12%** (1 of 8 items faded) |
| OpenAI | 0% (0 of 8) |
| Speechify | 0% (0 of 8) |
| Cartesia | 0% (0 of 8) |
| Fish | 0% (0 of 8) |
| Google | 0% (0 of 8) |
| **Aggregate** | **6.2%** (4 of 64 items across all vendors) |

**Stochastic, not deterministic**: re-generating a "faded" item
often produces a clean version, and re-generating a "clean" item
sometimes produces a faded version. It's not "these specific
sentences always fade" — it's "any long enough narration can fade
on some percentage of runs."

**Chunking mitigates it**: if the text is split into shorter
paragraphs (each ~1-2 sentences) and stitched back, the fade
drops sharply. In Experiment C on ElevenLabs L03, the full text
faded 2.79 dB; splitting into two ~40-second halves left the
first half at 1.89 dB fade (still detectable, still below the
2 dB threshold) and the second half at no measurable fade. This
is consistent with a per-generation cumulative-state drift that
resets on each fresh call.

**What this means for you**:

- **For narration products with paying listeners** (audiobooks,
  podcasts, meditation apps): don't ship long generations
  end-to-end. Chunk the text into paragraphs, generate each, stitch
  back together. This costs slightly more per API call and drops
  the fade sharply (see the earlier note on Experiment C).
- **For preview or one-off use** (dictation, quick playback): a 6%
  fade rate is annoying but usually not blocking. Regenerate if it
  happens.
- **For monitoring / QA**: run a simple loudness-across-time check
  on every long generation. Vendors don't warn you when this
  happens — you have to catch it yourself.

**Not a "bad vendor" finding**: 6.2% is small enough that a spot-
check listener would miss it, and every vendor is affected in
principle even if the ones at 0% didn't happen to trigger it in
our 8-item sample. It's a **property of neural TTS at long context
lengths**, not a scandal about any one company.

**Finding referenced in the technical docs as F-6; Phase 2 evidence
in [EXPERIMENTS_2026-09-01.md § Follow-up 1](EXPERIMENTS_2026-09-01.md)
and the cross-vendor drift JSON at
[analysis/experiments-2026-09-01/item1_primary_narration_drift.json](../analysis/experiments-2026-09-01/item1_primary_narration_drift.json).**

---

## Where to go next

- **Which vendor should I actually pick?** →
  [04_RESULTS.md § Decision framework](04_RESULTS.md#decision-framework-three-questions)
- **How did you measure this?** →
  [02_METHODOLOGY.md](02_METHODOLOGY.md)
- **Full per-vendor data table** →
  [04_RESULTS.md](04_RESULTS.md)
- **The technical version of these findings, with σ ratios and
  JSON pointers** → [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md)
- **What we didn't measure and why** →
  [07_GAPS_AND_FUTURE_WORK.md](07_GAPS_AND_FUTURE_WORK.md)
