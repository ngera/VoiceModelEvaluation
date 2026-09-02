# 08 · Key findings, in plain language

*The same findings as [06_KEY_FINDINGS.md](06_KEY_FINDINGS.md), rewritten
for a reader who doesn't want the σ ratios and JSON pointers. Every
finding here maps to a specific technical entry — the F-code in
parentheses at the end of each section tells you where to go for the
receipts.*

> **Scope reminder** · Findings apply to specific vendor accounts on
> paid public tiers, one voice per vendor per use case, measured from
> a residential Windows 11 environment across three weeks in August
> 2026. Full scope in [../DISCLAIMER.md](../DISCLAIMER.md).

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
   Cartesia's files** — nearly half — because they hit the ceiling.
   No quality score is computable for those files. The ruler
   couldn't even measure them.
2. **Anything downstream can make it worse.** Change the volume,
   convert to a phone-system format, feed into speech recognition,
   add a filter — those operations can push already-at-the-ceiling
   audio *over* the ceiling, producing a scratchy, distorted sound.
   Every other vendor's audio survives these operations fine;
   Cartesia's often doesn't.

**Not a one-off**: the same pattern showed up in both our campaign
runs, three weeks apart, on the same corpus — 429 clipped samples
on Cartesia narration the first time, 420 the second. The other
seven vendors: 0 or ≤12 clipped samples in either run.

**What a customer would do about it**: add a one-line audio
"peak-limiter" step that pulls the loudest samples back by about
1 dB (a change nobody would hear). That rescues the 46% of files
DNSMOS currently refuses. If you don't want to build that step,
pick a different vendor.

**Finding referenced in the technical docs as F-4 + F-4a.**

---

## 2. The "cheapest" vendor stops speaking after 14.59 seconds — always

**Think of it like a phone plan that says "unlimited talk" but hangs
up at exactly 14 seconds no matter what.** Orpheus lists at $0.003
per generation — the lowest price on the roster. The catch: no
matter how long the text you send, Orpheus produces exactly 14.59
seconds of audio and stops.

Send it a two-sentence text (fits under 14 seconds): you get a
complete recording.

Send it a one-paragraph text (would take 90 seconds to read aloud):
you get the first 14 seconds and everything after that is silently
lost. **You paid for the whole paragraph. You got 16% of it.**

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

## 4. How fast a vendor answers changes by more than 50% day-to-day

**We measured the same "how quickly does the voice start speaking"
metric three separate days, three weeks apart.** On the same
conversational text, on the same vendor, from the same computer:

| Vendor | Day 1 | Day 3 | Day 4 | Range |
|---|---:|---:|---:|---:|
| **ElevenLabs** | 479 ms | 469 ms | **816 ms** | +70% |
| **OpenAI** | 956 ms | 1,493 ms | **1,882 ms** | +97% |

Neither vendor is "stable" in an operational sense. Both swing by
more than half of their own values across sessions.

**What we ruled out**: it's not our internet connection. We ran a
background network check during the third session — the network
was clean and fast. Something else is slowing both vendors down on
that day, and it affects them in similar amounts. Best guess:
something on our own laptop (a background scan, an OS update, a
Python quirk on that specific run). But we can't prove it with
three sessions.

**What survives the finding**: the **ranking** is portable —
ElevenLabs is consistently faster than OpenAI in every session. But
the specific absolute number (like "ElevenLabs is 469 ms") isn't
something you should quote as a spec.

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
things underneath the surface:

- **Microsoft's DNSMOS** rewards **clean audio** (no background
  hiss, no distortion, clear signal) — the kind of quality you
  want for a business phone system
- **Meta's Audiobox has two axes**:
  - One (called PQ — "production quality") *agrees* with DNSMOS
    on cleanliness — they both flag OpenAI as top-tier
  - The other (CE — "content enjoyment") rewards **warmth and
    expressiveness** — that's where Speechify wins big

**In one sentence**: **Speechify is the clear winner on
warmth/expressiveness. OpenAI is the clear winner on technical
cleanliness. Neither is universally "better" — they're both real
kinds of quality, and different products need different ones.**

**Why this matters for you**: any leaderboard that reports a single
"quality score" from one MOS predictor is measuring a specific
version of quality. If a review site says "vendor X is best on
DNSMOS," that translates to "vendor X sounds cleanest." If they say
"vendor Y is best on Audiobox," that could mean "cleanest" OR
"warmest" depending on which axis they used. Match the predictor
to the sound your users actually want.

**Finding referenced in the technical docs as F-8.**

---

## 6. Speechify's quality wins survive a voice change

**A hostile reviewer's first objection would be: "you got lucky with
the voice you picked."** Speechify offers dozens of voices; maybe we
picked the one good one.

To check, we re-ran Speechify's narration test with a completely
different voice — a UK male "bright and dynamic" voice instead of
the US female "warm and intriguing" one we originally used. The
biggest voice-signature swap Speechify's library offers.

**The result**: the alternate voice scored **higher** than the
original one, not lower. Speechify would have still won even if
we'd cherry-picked in the opposite direction.

**What this means for you**: Speechify's Audiobox lead is a
property of the underlying model (Simba-3.2), not a lucky
voice pick. You can browse Speechify's voice library based on
which one matches your brand, without worrying about a big quality
drop-off between voices.

**Caveat**: this only tests two voices, both within Speechify. It
doesn't tell you whether other vendors' rankings would similarly
survive their own voice-space (that's a v2 follow-up). It also
tests only Speechify's *cleanliness/PQ* axis specifically; the
warm/enjoyment axis wasn't voice-swap-verified.

**Finding referenced in the technical docs as F-7 and F-9 test T6.**

---

## 7. Every vendor missed the pre-registered response-time bar

**Before we ran any measurements, we committed to a specific
"real-time voice" bar: the 90th-percentile response time must be
under 400 milliseconds.** That's the threshold at which a
conversation starts feeling responsive (versus laggy).

**Best result any vendor achieved**: ElevenLabs, 469 ms. That's
17% over the bar.

The other measured vendors were further off:

- Cartesia: 529 ms (32% over)
- Deepgram: 670 ms (68% over)
- OpenAI: 946 ms (137% over — more than double)

**Every measured vendor failed our pre-committed real-time bar**,
in every session we measured.

**Why this doesn't automatically kill any vendor**: 400 ms was a
conservative bar (we picked it to leave headroom below the ~500 ms
"noticeably laggy" threshold from research literature). A vendor
at 469 ms is still perceptually fine for most conversational
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

**Across the seven measurement axes we tracked** (response time,
cost, two quality axes, cleanliness axis, and two intelligibility
axes), **the top spot goes to a different vendor almost every time**:

- Fastest response → **ElevenLabs**
- Cheapest per 1,000 words → **OpenAI** or **Fish** (tied)
- Cleanest audio (DNSMOS) → **OpenAI**
- Warmest/most engaging → **Speechify**
- Loudest headroom / cleanest waveform packaging → **OpenAI**
- Fewest words dropped or mispronounced → close cluster of 4-5
  vendors, no clean winner

**This is not a "measurement was noisy" problem — it's the actual
finding.** Different vendors are genuinely optimised for different
use cases:

- Support-agent voice bot (real-time, short turns) → **ElevenLabs**
- Long-form narration where warmth matters → **Speechify**
- Enterprise IVR / accessibility (clean signal above all) → **OpenAI**
- Cheapest for very-short quick replies → **OpenAI** or **Fish**

**What this means for you**: the "which is the best voice AI
vendor?" question has no single correct answer. The right vendor
depends on **which axis matters most for your product**. A cheat
sheet in the results doc names the top pick per use case; use
that, not a marketing leaderboard that flattens everything into
one score.

**Finding referenced in the technical docs as F-3.**

---

## 9. If your product is a phone system, listen carefully to Fish and Google before committing

**"Background noise" in a recording is the quiet hiss you hear when
nobody is talking.** Perfect audio has a very quiet background —
you can only hear it if you crank the volume way up. Noisy audio
has an audible hiss even at normal volume.

The scale we use is **dBFS**, and it's counter-intuitive: **more
negative is quieter, less negative is louder.** Silence would be
−∞ dBFS. A pin drop in a quiet room is around −60 dBFS. An audible
hiss on a phone call is around −40 dBFS. Anything above −40 dBFS
starts sounding like a bad connection.

Where each vendor sits on that scale, averaged across their
conversational audio:

| Vendor | Conversational background noise | Reads as |
|---|---:|---|
| Cartesia | −57 dBFS | very quiet, professional |
| Speechify | −57 dBFS | very quiet, professional |
| OpenAI | −52 dBFS | quiet, broadcast-clean |
| ElevenLabs | −52 dBFS | quiet, broadcast-clean |
| Orpheus | −54 dBFS | quiet, broadcast-clean |
| Deepgram | −46 dBFS | slight audible hiss |
| **Fish** | **−39 dBFS** | **audible hiss on quiet phone systems** |
| **Google** | **−33 dBFS** | **loudest background — most audible hiss** |

Fish and Google are both **10-24 dB louder** in their background
hiss than the cleanest vendors. That's not a small margin — it's
the difference between "sounds like a studio recording" and
"sounds like a call from 20 years ago."

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
from scratch** — same 8 vendors, same 1,200-file corpus, fresh
generations from every vendor's live API, no cached data.

**14 of the 16 "top-1 winner" positions came out identical.** The
two positions that flipped were both inside the noise floor (small
margins on axes that no headline claim depends on).

- Speechify won both Audiobox axes on both use cases: **same in
  both runs**
- OpenAI won all three DNSMOS cleanliness axes: **same in both
  runs**
- Cartesia's clipping problem: **same magnitude in both runs**
  (429/420 samples vs the pack's 0/12)
- Vendors' per-word costs: **matched to 4 decimal places** across
  the two runs (except Orpheus, off by less than a cent because
  of one failed generation)

**Why this matters**: it's one thing to run an experiment once and
publish an answer. It's another to run it again three weeks later
and get the same answer. The findings above are not luck-of-the-
draw artefacts.

**The only measurement that changed materially**: response time.
Absolute latency numbers moved 50-90% between the runs (see
finding #4). Rankings on latency held, but the specific values did
not.

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
