# N1 · OpenAI narration is "clinically clean but low aesthetic warmth"

- **Provider**: OpenAI (`tts-1-hd`, voice `onyx` — D-006 + D-007)
- **Use case**: narration
- **Test type**: manual listen (self-mark warmth / cleanliness)
- **Created**: 2026-08-11 (new outlier surfaced by F-8 rank inversion)
- **Cost**: $0
- **Wall-clock**: ~10 min

## Outlier (surfaced by F-8, campaign)

OpenAI narration sits at *opposite ends* of the two MOS pipelines:

| axis | OpenAI narr score | rank of 8 |
|---|---|---|
| Audiobox PQ | 7.62 | **#8** (dead last) |
| Audiobox CE | 6.18 | **#8** (dead last) |
| DNSMOS p808_mos | 3.98 | #8 |
| DNSMOS ovrl_mos | 3.46 | **#1** |
| DNSMOS sig_mos | 3.68 | **#1** |
| DNSMOS bak_mos | 4.18 | **#2** |

Perfect-inversion on the ITU-T P.835 three-scale MOS vs Audiobox. The
P808 rank (#8) tracks Audiobox rather than the three-scale — probably
because P808 is a single-model MOS prediction rather than the
separated speech / background / overall trio.

## Hypothesis

OpenAI's `onyx` on `tts-1-hd` is a **clinically clean but low-warmth**
voice signature: exceptionally low background noise and consistent
speech-signal cleanliness (why DNSMOS three-scale rewards it), but
low expressiveness, warmth, prosodic engagement (why Audiobox
penalizes it). This is a real trade-off in voice design, not a
methodology artefact — and would show up to a human listener as
"technically flawless but a bit robotic."

## Success criterion (pre-registered)

Self-marked **cleanliness ≥ 4/5 AND warmth ≤ 3/5** on **≥ 3 of 5**
sampled narration items. If <3/5 show the pattern, the hypothesis is
refuted — the F-8 inversion is a pipeline calibration issue, not a
listener-audible property.

## Items to listen to

5 narration items spanning the strata:

| # | item | stratum |
|---|---|---|
| 1 | S01 | short |
| 2 | M01 | medium |
| 3 | L01 | long |
| 4 | J01 | jargon |
| 5 | E01 | edge |

Paths: `runs/campaign-20260809T204608Z/audio/openai/narration/{item_id}_dr0.wav`

## Method

For each item, listen through **once** and self-mark on two 1–5 scales
before writing the note (blind ordering — don't peek at other
providers first):

- **Cleanliness (1–5)** — no hiss, no background artefacts, no
  breath pops. 5 = "sounds like a studio recording"; 1 = "audible
  noise floor, breath, or artefacts throughout"
- **Warmth (1–5)** — expressive, engaged, human-sounding
  intonation. 5 = "sounds like a person who cares about the text";
  1 = "flat monotone, no prosodic variation"

Then one-line note on what specifically drove the ratings ("dead
monotone but no breath sounds", "some sibilance but expressive
cadence", etc.).

## Result

<!-- Fill during execution -->

| # | item | cleanliness (1-5) | warmth (1-5) | pattern (clean≥4 AND warm≤3) | note |
|---|---|---|---|---|---|
| 1 | S01 | | | | |
| 2 | M01 | | | | |
| 3 | L01 | | | | |
| 4 | J01 | | | | |
| 5 | E01 | | | | |

**Pattern count:** ___ / 5

## Verdict

<!-- Confirmed / Refuted / Inconclusive -->

## Notes for memo / paper

<!-- - This is the strongest single case for F-8's "two constructs"
     reading. If confirmed, the memo can name OpenAI as "the clean
     narrator" and Speechify as "the warm narrator" — direct
     positioning for a buyer.
   - fill after execution
-->
