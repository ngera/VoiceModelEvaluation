---
title: Voice AI Evaluation — Portfolio Edition
version: "1.0"
status: Active plan (supersedes the public-benchmark scoping for this build)
audience_of_project: Hiring managers & interviewers, ~10 minutes of attention
companion: voice_ai_eval_plan_v1_descoped.md (full methodology — still the reference for HOW; this doc redefines WHAT and HOW MUCH)
timeline: ~3 weeks part-time (15–20 hrs/wk)
budget: ~$30–45
people_needed: 1–2
---

# Voice AI Evaluation — Portfolio Edition

**The reframe:** the full plan was engineered for *credibility at distance* — strangers trusting a public benchmark without meeting its author. A portfolio project runs on *credibility in person*: you narrate it. Every hour previously budgeted for external-proof machinery (rater panels, reproducer programs, publication legal armor) is reallocated to making the artifacts **legible** and the story **sharp**.

What a reviewer must perceive within 10 minutes: *this person frames problems, pre-commits criteria, kills their own bad ideas, and turns noisy data into a defensible decision.*

---

## 1. What changes from the full plan

| Area | Full plan | Portfolio edition | Why |
|---|---|---|---|
| Publication | Public site, launch posts, HI audit published | **Private results**, shown 1:1; public repo optional (method only) | Kills the entire legal apparatus — no ToS review, no lawyer, no right-of-reply, no audio-license audit |
| Providers | 11 (HI roster) + control | **6** (see §2) | Provider #7–11 add coverage, not narrative. The story is identical at 6 |
| D4 rating | Target n=10–25 external raters | **Blinded self-rating, n=1, disclosed** | Method demonstration, not leaderboard power. The blinding script + consistency re-judge remain — they ARE the demonstration |
| Reproducers | 3–5 alpha testers + public program | Devcontainer + one fresh-VM run by you; **optionally one friend** | Code verified; docs polished for *reading*, not reproducing |
| Operate phase | Monthly re-runs, drift changelog, community | **One re-run ~4 weeks later**, then archive with a dated banner | One re-run is enough to *demonstrate* the drift story ("two providers changed models in a month") — the portfolio point is made |
| Tester/comms pack | Full welcome pack, 3 tiers | Not needed | No external program |
| Legal register | Full Appendix F.3 | One line: results private; keys out of git | Exposure attached to publication, which no longer happens |
| Timeline | 4–5 weeks | **~3 weeks** | Cuts above |
| Budget | $60–90 | **~$30–45** | Smaller roster; most riding free credits |

**Unchanged — because it is the signal:** gates + Pareto decision layer, pre-registration with git receipts, hybrid corpus with contamination probe, the tool re-derivation (VERSA, TTSDS2 + Audiobox, two-judge WER, VAD + LUFS), −18 LUFS normalization before A/B, the red-team discipline, both use cases. The methodology appendices of the full plan remain the authoritative HOW.

---

## 2. Roster (6 providers)

One per archetype — chosen so the frontier chart has a story at every point:

| Provider | Archetype | Cost note |
|---|---|---|
| ElevenLabs | Quality leader | ~$22 (one Creator month) — the biggest line |
| Cartesia | Latency leader | ~$4–8 (Pro month) |
| Fish Audio | Value pick / HI #3 | $0 (free S2.1-Pro window — **run before Aug 31**) |
| Google Cloud TTS | Hyperscaler baseline | $0 (monthly free tier; card required at signup) |
| Deepgram | Off-index control (HI's cloning gate excludes it) | $0 ($200 signup credit) |
| Canopy Orpheus | Open-source floor ("how close is free?") | ~$5–10 (Replicate; latency scored N/A-hosted) |

Dropped to the "one re-run later, if curious" list: Speechify, OpenAI, MiniMax, xAI, Inworld. The HI cross-check still works — four of the six above appear on their board.

---

## 3. The deliverable stack (inverted: presentation first)

Ordered by how a reviewer actually encounters the project. Budget polish time in this order.

1. **The case study (2–3 pages) — the product.** Problem → constraints ($100, solo, 3 weeks) → the 5 decisive calls with reasons (descoped from a 16-dimension spec; killed the weighted composite; pre-registered gates; re-derived every tool; caught 10 flaws in my own plan) → frontier charts → the two recommendations → "with 10× resources I would…". Written so a skimmer gets the arc from headers alone.
2. **Two frontier charts** — the money images. Quality × cost and quality × latency, dominated providers greyed, frontier labeled with the trade-off each point represents. If a reviewer sees one artifact, it's this.
3. **Two 1-page decision memos** — the artifact a PM interviewer recognizes as their own job: recommendation, trade-off accepted, cost at three scale points, risks, revisit-triggers.
4. **The repo, structured as a 10-minute tour.** README ordered for a skimmer: case study link → charts → memos → "how it works" → "receipts" (the prereg git tag, the DEVIATIONS log, the red-team appendix) → full docs. Reproducibility instructions exist but live below the fold.
5. **Supporting docs** (already written): full plan, runbook, tool rationale, diagrams. They exist to be *discovered* — depth behind the summary is what converts a good impression into a strong one.

**Interview talking points that fall out for free** (rehearse these; they're the ROI):
- "I inherited a 400-hour spec and shipped the decision it was for in 60 — here's the descoping table."
- "I killed my own weighted-composite design; here's why gates + Pareto is more honest."
- "Here's the git commit proving my acceptance criteria predate my data."
- "The public leaderboard I benchmarked against still ranks a company that shut down eight months ago — mine re-runs in one command."
- "Two ASR judges, because one judge can't tell its own errors from the system's."

---

## 4. Three-week timeline

| Week | Work | Output |
|---|---|---|
| **1** | Eval brief + gates (git-tagged `prereg-v1`); curate corpus (novel + probe set); D8 capability audit (6 providers); accounts/keys; harness + devcontainer; $1 pilot end-to-end; **Fish runs first** | Brief · gates.yaml · corpus · working pipeline |
| **2** | Full generation campaign; latency (serial trials, pinned VM, 2 days) + RTF; analyzers (two-judge WER, TTSDS2/Audiobox, hygiene); anchor recordings (the one friend); loudness-normalize; start blinded pairwise sessions | Run store · analysis JSONs · early judgments |
| **3** | Finish pairwise + consistency re-judge; Bradley–Terry; gates → frontiers → robustness; **write the case study and memos**; build charts; structure the repo tour; cancel subscriptions | Case study · charts · memos · repo |
| *(+4 wks later, 2–3 hrs)* | One cached re-run; write the drift note ("what changed in a month"); archive with dated banner | The drift talking point, made real |

Week 3 is deliberately half analysis, half writing — under-polishing the case study to over-polish the data is the classic engineer's mistake this plan exists to avoid.

---

## 5. People, cost, risk

**People (1–2):** one friend for the anchor voice recordings (~20 min, quiet room; consent needed only if their audio ever leaves your machine — it doesn't have to). Optionally one person to read the case study cold and mark where they got lost — the portfolio equivalent of the repro test, and the higher-value favor of the two.

**Cost (~$30–45):** ElevenLabs ~$22 · Cartesia ~$4–8 · Orpheus/Replicate ~$5–10 · latency VM ~$2 · everything else on free credits.

**Risks:**

| Risk | Mitigation |
|---|---|
| Fish free window closes (Aug 31) | Fish is first in Week 1's pilot and Week 2's campaign |
| Windows toolchain (NeMo/VERSA/TTSDS2) | Devcontainer/WSL2 decided Week 1 — same as full plan (E1) |
| Week 3 writing squeezed by analysis overruns | Charts + memos have priority over any additional analysis; a smaller analyzed set with a finished case study beats the reverse |
| Scope creep back toward the public benchmark | Any "we could publish this!" impulse goes to a future-work note. The full plan still exists if that day comes — this build doesn't serve it |

**If it goes public later:** nothing here forecloses it. The full plan's Appendices F–G (legal, distribution) reactivate, the roster extends, and the private results become the seed campaign. Portfolio-first is a sequencing decision, not a one-way door.

---

## 6. Definition of done

- [ ] A stranger skimming the repo for 10 minutes can state the problem, the method's two cleverest ideas, and both recommendations
- [ ] Case study readable in 5 minutes; every claim traceable to a dated artifact
- [ ] `prereg-v1` tag predates all result files in git history
- [ ] Both frontier charts render; memos complete
- [ ] Consistency re-judge number computed and disclosed next to every D4 figure
- [ ] Total spend ≤ $50, logged
- [ ] Subscriptions cancelled
- [ ] Drift re-run scheduled (calendar reminder, +4 weeks)
