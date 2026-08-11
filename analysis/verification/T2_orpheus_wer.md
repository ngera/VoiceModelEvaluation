# T2 · Orpheus 27% WER is real intelligibility, not judge bias

- **Provider**: Orpheus (`lucataco/orpheus-3b-0.1-ft` — D-004 community fork)
- **Use cases**: conversational + narration (worst cases are long stratum)
- **Test type**: manual listen (self-mark unclear / clear)
- **Created**: 2026-08-11
- **Cost**: $0
- **Wall-clock**: ~20 min

## Original outlier (from Phase 2)

Orpheus's mean `agreement_wer` on the campaign is ~2× the next-worst
provider. Both judges (wav2vec2 + faster-whisper) agree at the
per-item level. Original hypothesis was that ~27% aggregate WER
reflected real intelligibility issues rather than a shared bias
between the two ASR judges against Orpheus's voice signature.

## Hypothesis

Orpheus long-item WER is dominated by **truncation** (the model
stops mid-item on long text), not by hard-to-transcribe voice
timbre. Two-judge agreement on `agreed_word_drop_runs ≥ 3` on the
worst items should reflect real dropped content, not shared ASR
misinterpretation. When a human listener hears the file, ≥5 of 10
should be self-marked "unclear or truncated" — with truncation the
dominant cause.

## Success criterion (pre-registered)

**≥5/10 self-marked "unclear or truncated"** on the 10 worst-WER
Orpheus items. If the listener marks 5+/10 as *clear* (i.e., audible
speech but the ASR still measured high WER), the outlier is *refuted*
— the judges are biased against Orpheus's voice, not the audio is
broken.

## Items to listen to (from campaign wer.json, sorted worst-first)

All 10 have `truncation=True` per the campaign wer.json events block:

| # | item | UC | draw | WER | band |
|---|---|---|---|---|---|
| 1 | L07 | narration | 0 | 0.947 | C |
| 2 | L05 | narration | 0 | 0.910 | C |
| 3 | L06 | narration | 0 | 0.860 | C |
| 4 | L08 | conversational | 0 | 0.858 | C |
| 5 | L03 | narration | 0 | 0.853 | C |
| 6 | L01 | narration | 0 | 0.841 | C |
| 7 | L04 | narration | 0 | 0.839 | C |
| 8 | L01 | conversational | 0 | 0.829 | C |
| 9 | L08 | narration | 0 | 0.817 | C |
| 10 | L02 | narration | 0 | 0.811 | C |

## Method

For each item:
1. Play the WAV at `runs/campaign-20260809T204608Z/audio/orpheus/{use_case}/{item_id}_dr0.wav`
2. Follow along with the reference text in `corpus/{use_case}.yaml`
   for that item
3. Self-mark ONE of:
   - **`truncated`** — audio stops before the reference ends
   - **`unclear`** — audio plays fully but words are hard to make out
     (mumbling, wrong pronunciation, artefacts obscuring speech)
   - **`clear`** — audio plays fully and the words are audibly correct
     (WER penalty is a judge issue, not the audio)
4. Record 1–2 word note on cause where obvious ("stops after 5s",
   "monotone drone", etc.)

## Result

<!-- Fill during execution -->

| # | item | UC | verdict (`truncated` / `unclear` / `clear`) | note |
|---|---|---|---|---|
| 1 | L07 | narration | | |
| 2 | L05 | narration | | |
| 3 | L06 | narration | | |
| 4 | L08 | conversational | | |
| 5 | L03 | narration | | |
| 6 | L01 | narration | | |
| 7 | L04 | narration | | |
| 8 | L01 | conversational | | |
| 9 | L08 | narration | | |
| 10 | L02 | narration | | |

**Totals:** truncated=___ / unclear=___ / clear=___

## Verdict

<!-- Confirmed / Refuted / Inconclusive -->

## Notes for memo / paper

<!-- fill after execution — if truncation dominates, name it. -->
