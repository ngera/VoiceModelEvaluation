# Implementation plan — reconstructed 2026-08-04

> **Provenance note.** The original plan was agreed in a Claude session whose
> transcript was lost when the devcontainer was rebuilt. This file is
> reconstructed from the surviving evidence in the repo — the Phase letters and
> their contents are quoted from code comments written during that session, not
> invented here. Sources are cited per phase. Anything marked **(unverified)**
> is inference, not recovered fact — confirm or correct it.
>
> This file exists so the plan lives in the repo, not in a chat transcript.

## Phase map

Seven phases, A–G. The lettering appears nowhere in the `documentation/*.md`
source docs — it was created in the lost session and survives only in code
comments, which is why those comments are quoted as the citation for each row.

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| **A** | Skeleton: package, `veval doctor`, run store, base adapter, one adapter (Deepgram), devcontainer, admin panel + Doctor page | 🟡 **in progress — broken** | `cli.py` docstring "doctor (Phase A)"; `providers.yaml` "Phase A stub" |
| **B** | Configs + corpus: `voices.yaml`, `gates.yaml`, corpus extraction from `documentation/*.docx`; git init + tag `prereg-v1` | ⬜ not started | `doctor.py`: "Used in Phase A before Phase B has written providers.yaml" |
| **C** | Remaining 5 adapters: ElevenLabs, Cartesia, Fish, Google, Orpheus/Replicate | ⬜ not started | `providers.yaml` "Phase C will add the remaining five providers"; `.env.example` "--- Providers (Phase C) ---" |
| **D** | `veval generate` — campaign runner: async httpx, retry/backoff, content-hash cache, spend cap | ⬜ not started | `cli.py` "generate (Phase D)"; admin table "Run \| D" |
| **E** | `veval analyze` — two-judge WER, TTSDS2/Audiobox, hygiene, latency/RTF | ⬜ not started | `cli.py` "analyze (Phase E)"; admin table "Results \| E" |
| **F** | Voting UI: static A/B page, Vercel, Formspree/Basin, tokened rater URLs, anchor recordings | ⬜ not started | `.env.example` "--- Voting UI / Vercel deploy (Phase F) ---" |
| **G** | `veval score` + `veval report` — gates, Pareto frontiers, charts, memos | ⬜ not started | `cli.py` "score (Phase G)", "report (Phase G)"; admin table "Frontier \| G" |

Phase A–C ≈ Week 1, D–E ≈ Week 2, F–G ≈ Week 3 in the portfolio edition's
three-week timeline **(unverified — the mapping is consistent with
`voice_ai_eval_portfolio_edition.md` §4 but was not recovered explicitly).**

## Where Phase A actually stopped

`veval` does not run. The CLI dies at import:

```
File "src/veval/cli.py", line 23
    from veval.doctor import DoctorResult, run_doctor
ImportError: cannot import name 'DoctorResult' from 'veval.doctor'
```

`doctor.py` defines `DoctorReport` and `AdapterCheck`; there is no
`DoctorResult`. The session was interrupted mid-rename. Phase A is otherwise
complete in outline — every file exists and reads as finished work.

### Phase A punch list (to close it out)

1. **Fix the import** — `cli.py:23` → `DoctorReport`. Also drop the unused
   `os` import at `cli.py:14`, and type `_print_doctor_report(results:
   DoctorReport)` (the `noqa: ANN001` comment claims an import cycle that
   doesn't exist — `cli` already imports from `doctor`).
2. **Fix the Streamlit dead code** — `admin/pages/1_Doctor.py:44` reads
   `_guess_env_key(name) if False else None`, calling a function defined at the
   bottom of the same file. Unreachable today, `NameError` the moment anyone
   flips the condition. Either wire the env-key display up properly or delete
   both halves.
3. **Run `veval doctor` against Deepgram** — `DEEPGRAM_API_KEY` is set, so this
   is the real end-to-end proof: config → adapter → run store → manifest.
4. **Add `tests/`** — `pytest` is already a dev dep and no test dir exists.
   Minimum: run-store immutability, config validation, `ProviderError` mapping.
5. **`git init`.** The repo is not under version control. This blocks Phase B's
   `prereg-v1` tag, which is the receipt the entire case study leans on
   ("`prereg-v1` tag predates all result files in git history" — Definition of
   Done). Nothing else in the project is as cheap to do or as expensive to fake
   later.

## Open items flagged during reconstruction

These are conflicts and judgment calls found while reading the tree. They were
**not** part of the recovered plan — they need your call.

- **`.gitignore` ignores `uv.lock`.** For an application whose selling point is
  reproducibility, the lock file is normally committed. Recommend un-ignoring.
- **`eval_harness_architecture.mermaid:4` still shows `weights.yaml`** with
  "per-use-case weights + rationale". CLAUDE.md records that the weighted
  composite was killed in favour of pre-committed gates + Pareto frontiers. The
  diagram is stale relative to the locked decision. Per CLAUDE.md meta-rule 3
  this is flagged, not silently fixed.
- **Env keys still empty:** `FISH_API_KEY`, `CARTESIA_API_KEY`,
  `ELEVENLABS_API_KEY`, `GOOGLE_API_KEY`. Fish is the time-boxed one — the free
  window closes **Aug 31** and the portfolio edition puts Fish first in both the
  Week 1 pilot and the Week 2 campaign. That is 27 days out.
- **`configs/` holds only `providers.yaml`** (Deepgram alone). `voices.yaml`,
  `gates.yaml`, and the corpus are Phase B and unwritten, though `config.py`
  already has validated loaders for all three.
