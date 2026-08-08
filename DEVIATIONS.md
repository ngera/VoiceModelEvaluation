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
