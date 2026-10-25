# v1 release checklist

*What has to be true before this repo is complete and worth pointing
someone at. Compiled 2026-09-05 against the working tree and the live
public repo at `github.com/ngera/VoiceModelEvaluation`.*

**Estimated total: ~1.5 working days.** The findings are done. What
remains is release hygiene, four unresolved claims, and one legal file.

> **Context that changes the priority order:** the repo is **already
> public**. Every gap below is currently visible to anyone who opens
> it. P0 items are things the repo says about itself that are not
> presently true.

---

## P0 · Blockers — the repo currently misrepresents itself

### 1. Add a LICENSE file
README closes with *"Everything in this repo is committed under a
permissive open-source license; fork and adapt freely."* **There is no
LICENSE file in the repo.** Absent one, the default is
all-rights-reserved — the sentence grants nothing and is inaccurate on
a public page.

- Pick **Apache-2.0** over MIT: the patent grant and NOTICE discipline
  read as more considered for an evaluation harness, and it is the
  safer default when vendors are named
- Add a second license line for the **non-code assets** — corpus,
  documentation, figures — under CC BY 4.0. Code and data licenses
  differ, and the corpus is the part a fork-and-adapt reader most wants
  to reuse
- State both in README where the current sentence sits

*10 minutes. Do this one first.*

### 2. Secrets audit across git history, not just the working tree
`.env`, `.env.*`, `*.pem`, `*.key`, `.secrets/` and
`.streamlit/secrets.toml` are all correctly ignored **now**. But the
repo has 64 commits, `.gitignore` was last edited 2026-09-02, and eight
vendor API keys have been live in this tree since August.

```bash
gitleaks detect --source . --no-git=false
# or
trufflehog git file://. --only-verified
```

Rotate anything that surfaces. This is the only item on the list where
being wrong is expensive rather than embarrassing.

*30 minutes. Do it before you send the link to anyone.*

### 3. Push the unpushed bundle
Last push was `43a06e7`. Everything since — the R3 replication campaign,
`08_KEY_FINDINGS_PLAIN.md`, the Phase 2 experiment pack, and
`documentation/EXPERIMENTS_2026-09-01.md` — is local only.

### 4. `docs/index.html` is missing from the published tree
README's **"Have 10 minutes? Start here"** link — the primary entry
point, the thing you want every reader to open first — points at
`docs/index.html`. The published tree has no `docs/` directory at all.
**That link 404s right now.**

- Push it
- Enable **GitHub Pages** (main branch, `/docs` folder) so the brief
  has a real URL rather than a raw-HTML file path
- Put that URL at the top of the README and in the repo's **About**
  field

*The one-pager is the product. It is currently the only thing readers
cannot reach.*

### 5. Repo front-door metadata
A visitor currently sees a bare repo name. Set the **About**
description, add **topics** (`tts`, `evaluation`, `benchmark`,
`voice-ai`, `pre-registration`), and link the Pages URL. Five seconds of
a reader's attention is decided here, before the README loads.

---

## P1 · Completeness — claims that do not resolve

### 6. Run T10 (Orpheus `max_new_tokens`)
README headline finding #2 ends: *"Cap may be model-intrinsic OR a
deployment-config parameter (`max_new_tokens`) — untested;
recommendations differ."*

Publishing a headline finding whose actionable half is unresolved —
when the test costs **under $0.15 and thirty minutes** and is already
scaffolded in `03_RUNBOOK.md` — is the single most likely thing a
sharp reader will fault. Running it collapses the recommendation from
"either/or" to one path.

*Highest ROI item in the entire repo.*

### 7. Run the sample-rate header sweep
Same bucket: scaffolded, under $0.15, confirms no vendor still ships a
placeholder WAV sample rate after the Deepgram `finalize_wav_header()`
fix. Related to F-1a.

### 8. Close gap 9(a)/(b) — pin the analyzer revisions
README leads with pre-registration, then discloses an honest exception:
three neural-model revisions (`audiobox_revision`, wav2vec2,
faster-whisper) carry `TODO_pin_sha_before_campaign` placeholders that
propagated into every `wer.json`.

- Resolve each to a real HuggingFace commit SHA (one API call per repo)
- Lift the normaliser hash `75379ec8…` from runtime into
  `analyzers.yaml` so a fresh clone reads a pre-committed value
- Upgrade `veval doctor` to **refuse to run** if `analyzers.yaml`
  contains any `TODO_` string, any `null` in a pre-registered numeric
  field, or a value a later DEVIATIONS entry superseded
- Tag `prereg-v1.11`

*Minutes of work. Converts your most-cited caveat into a receipt.*

### 9. Re-sync the stale MDD block
`analyzers.yaml` lines 207-208 still read `n_judgments_target: 210` /
`n_judgments_minimum: 126`. D-009 (`prereg-v1.7`) superseded both with
216/216. The config currently contradicts the operative amendment, and
no gate cross-references it — which is exactly how it survived several
review rounds.

### 10. Fix the stale cache gap in `07_GAPS_AND_FUTURE_WORK.md`
07's deferred list still says: *"Campaign ran fully from content-hash
cache… Fix: a `--no-cache` primary-campaign re-run (~$40, ~30 min)
would give per-item `synthesis_time` (adjudicating RTF as a bonus)."*

**That re-run happened.** R3 (`campaign-20260831T175358Z`) was a
`--no-cache` fresh generation, it adjudicated the RTF gate 5-pass /
3-fail, and it cost **$7.85, not $40** — the same document says so
sixty lines earlier. A reader who notices a document contradicting
itself about whether its own biggest gap is closed will discount
everything else in it.

Rewrite the bullet to scope the residual limitation to R2 only.

### 11. Reconcile the project-cost figure
07 opens with *"a single-person, three-week, ~$13 project"*; README says
**~$16.15**. Pick one, propagate. Small, but this is precisely the class
of defect CORRECTIONS.md exists to catch, and it is sitting in the
document about honest limits.

### 12. Add the Orpheus conversational truncation footnote
You footnote the 14.59-s cap on the narration column and not on
conversational, where 25/75 files hit the same cap. You have already
identified this as an asymmetric-scrutiny gap in 07. One paragraph plus
a copy of the per-stratum AB.PQ analysis already done for narration.

### 13. Answer the question your headline raises — in the README
The pull-quote asks *"quality on which axis?"* The reader's immediate
next question is *"which axis matches human perception?"* and the answer
— we don't know, and here is why we refused to guess — is currently
spread across 02 § D4, 06 § D-H, 07 gap 1, and README's "what's not in
v1."

Put **one paragraph directly under the pull-quote**: what F-8 found,
that the human-validation question is open, that n=1 self-rating cannot
close it, and what would. This converts the project's biggest hole from
something a reader discovers into a visible act of judgment. It is the
most PM-flavored paragraph in the repo and it does not exist yet.

### 14. Full link audit on the *published* tree
`docs/index.html` proves that "the link works locally" is not the same
as "the link works." Run both existing checks, then verify against what
is actually pushed:

```bash
python -X utf8 scripts/check_internal_links.py
# plus the rule-4 retraction-narrative sweep from CORRECTIONS.md
```

Specifically confirm these resolve on GitHub: `docs/index.html`,
`documentation/figures/f1..f3.png`, `configs/hardware.yaml`,
`analysis/verification/`, and every `analysis/campaign-*/` and
`analysis/latency-*/` path un-ignored by `.gitignore`.

---

## P2 · Credibility — cheap signals a public repo is judged on

### 15. CI running the test suite
~236 pytest tests and no badge. A green check on every push is the
cheapest credibility signal available on a public repo, and its absence
is conspicuous on a project whose entire pitch is measurement
discipline.

### 16. Wire the two pre-commit checks into CI as well
CORRECTIONS.md rule 5 already concludes the rule-4 sweep must run
**pre-commit, not post-mortem**. Make it a GitHub Action alongside the
internal-link checker. "Zero hits" becomes enforced rather than
remembered — and a CI job that gates on *editorial* discipline, not just
tests, is itself a portfolio artifact worth pointing at.

### 17. Give CORRECTIONS.md a reader-facing header
137 KB, 156 rows, 29 review rounds. Nobody will read it — but its
*existence* is one of the strongest things about the project, and right
now the artifact that best demonstrates intellectual honesty is the
least legible one.

Add five lines at the top: how many rounds, how many retractions, which
three changed a headline finding (T8, F-11, F-6), and a link to the
process. Then it can be skimmed in thirty seconds and cited in an
interview in one sentence.

### 18. Delete or archive `site/`
Gitignored, so it will not publish — but it holds an auto-generated
case study from 2026-08-09 that says *"No recommendation available: no
frontier data yet"* and cites TTSDS2, Parakeet, and a fitted BT model.
All three were dropped from v1 (D-A, D-010, D-H). If it ever leaks into
the tree it directly contradicts the final documents. Delete it, or move
it to `documentation/archive/`.

### 19. Confirm the one-pager carries the whole decision
`04_RESULTS.md` is 95 KB. `docs/index.html` is what most readers will
actually consume. Verify it holds — and holds *only* — the three-question
framework, the 8 vendors × 5 dimensions table with gate verdicts, the
axis-split chart, cost with the Orpheus and Speechify caveats inline, and
the "what I got wrong" box. Everything else is appendix by design.

---

## Explicitly cut from v1

Name these as decisions in `07`, not omissions. They are already
documented there; the point is not to let any of them reopen scope.

- **D6 controllability / D7 text-normalization / D8 procurement matrix /
  D9 availability canary** — the parameter gaps identified 2026-09-05.
  These are a **v1.5 addendum pack**, a separate document, and must not
  reopen `01`–`08`
- Multi-rater BT panel, cross-lingual, enterprise-VM latency baseline,
  alt-corpus robustness, enterprise-tier replay, streaming quality —
  all already in 07's v2 list, all stay there
- **Review round 30.** Rows 155-156 of CORRECTIONS.md are corrections to
  the arithmetic bases of the corrections. The loop has converged. Tag
  `v1.0-final` and stop.

---

## Definition of done

v1 ships when all of the following are true:

- [ ] LICENSE file present; README's licensing sentence is accurate
- [ ] History scanned for secrets; anything found is rotated
- [ ] Local bundle pushed; `docs/index.html` live on GitHub Pages
- [ ] Every README link resolves **on the published tree**
- [ ] T10 and the sample-rate sweep are run; no headline finding ends
      in "untested"
- [ ] `analyzers.yaml` has zero `TODO_` strings and zero `null`
      pre-registered numerics; `doctor` refuses both; tagged
      `prereg-v1.11`
- [ ] 07 contains no gap that later work already closed
- [ ] Project-cost figure is identical in every document
- [ ] README answers "which axis matches humans?" in one paragraph
- [ ] CI is green and gates the link + retraction checks
- [ ] Tagged `v1.0-final`

Then it is published — which means **sent to people**, not merely
public. A repo nobody has been pointed at has the same readership as a
private one.
