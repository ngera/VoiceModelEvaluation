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
