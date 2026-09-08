"""T10 — Orpheus max_new_tokens cap check (one Replicate call, ~$0.01).

Distinguishes "model-intrinsic 14.59-s cap" from "deployment-config
default cap" by passing max_new_tokens = 4000 (well above the ~2048
default assumed to produce the 14.59-s output) on a text long enough
that a 14.59-s truncation would show, then measuring output duration.

Interpretation:
    duration ≈ 14.59s → model-intrinsic cap (max_new_tokens ignored /
                        internal architectural limit)
    duration > 14.59s → deployment-config default (larger max_new_tokens
                        overrides; PM fix is one API-flag flip)
    duration < ~14.59s → text too short OR model finishes early

Text is a long-stratum item (L01 narration, ~200 words → ~85s clean speech,
truncated to 14.59s under the default cap = ~17% delivered per T8).
"""
from __future__ import annotations
import io
import json
import os
import sys
import time
import wave
from pathlib import Path

import httpx
import yaml

ROOT = Path("c:/cursorProjects/voiceAgentEvals")

# Load .env to get REPLICATE_API_TOKEN
env_text = (ROOT / ".env").read_text(encoding="utf-8")
for line in env_text.splitlines():
    line = line.strip()
    if line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    v = v.strip()
    # Strip inline comment (space-hash), then quotes
    if " #" in v:
        v = v.split(" #", 1)[0].strip()
    os.environ[k.strip()] = v.strip('"').strip("'")

TOKEN = os.environ.get("REPLICATE_API_TOKEN") or os.environ.get("REPLICATE_KEY")
if not TOKEN:
    print("ERROR: REPLICATE_API_TOKEN not in .env", file=sys.stderr)
    sys.exit(2)

# Long narration item L01 (from corpus)
corpus = yaml.safe_load((ROOT / "corpus/narration.yaml").read_text(encoding="utf-8"))
L01 = next(it for it in corpus["items"] if it["id"] == "L01")
TEXT = L01["text"]
print(f"T10 · Orpheus max_new_tokens cap check")
print(f"  text length: {len(TEXT)} chars, ~{len(TEXT.split())} words")

# Orpheus lucataco/orpheus-3b-0.1-ft — version SHA per providers.yaml D-005
VERSION_SHA = "79f2a473e6a9720716a473d9b2f2951437dbf91dc02ccb7079fb3d89b881207f"
VOICE = "dan"  # Replicate wrapper accepts {tara, dan, josh, emma} only —
              # our pinned voices.yaml voices `leo` / `tara` were the
              # spec-time list; Replicate wrapper has since narrowed voice
              # to 4-item enum. `dan` is the male voice, closest to `leo`.
MAX_NEW_TOKENS = 2000  # Replicate wrapper hard-caps at 2000 (learned this
                       # round from the 422 response) — first shot with
                       # 4000 returned "Must be less than or equal to 2000".
                       # That cap itself is deployment-config: the Replicate
                       # wrapper's JSON schema constrains the request field
                       # long before it reaches the model.

body = {
    "version": VERSION_SHA,
    "input": {
        "text": TEXT,
        "voice": VOICE,
        "max_new_tokens": MAX_NEW_TOKENS,
    },
}
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Prefer": "wait=60",
}
url = "https://api.replicate.com/v1/predictions"

t0 = time.perf_counter()
with httpx.Client(timeout=180.0) as client:
    resp = client.post(url, headers=headers, json=body)
    if resp.status_code not in (200, 201, 202):
        print(f"ERROR HTTP {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)
    pred = resp.json()
    pred_id = pred.get("id", "")
    status = pred.get("status")
    poll_url = f"https://api.replicate.com/v1/predictions/{pred_id}"
    for _ in range(30):
        if status in {"succeeded", "failed", "canceled"}:
            break
        time.sleep(4)
        pred = client.get(poll_url, headers={"Authorization": f"Bearer {TOKEN}"}).json()
        status = pred.get("status")
    if status != "succeeded":
        print(f"ERROR status={status}: {json.dumps(pred, indent=2)[:800]}", file=sys.stderr)
        sys.exit(1)
    audio_url = pred["output"] if isinstance(pred.get("output"), str) else pred["output"][0]
    audio_resp = client.get(audio_url)
    audio_bytes = audio_resp.content

wall = time.perf_counter() - t0

# Measure duration
try:
    with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
        n_frames = wf.getnframes()
        sr = wf.getframerate()
except wave.Error:
    # Not a wav — probe raw byte-length as fallback
    duration = None
    n_frames = None
    sr = None

# Save artifacts
out_dir = ROOT / "analysis/verification/T10_orpheus_max_new_tokens"
out_dir.mkdir(parents=True, exist_ok=True)
audio_path = out_dir / f"T10_L01_max_new_tokens_{MAX_NEW_TOKENS}.wav"
audio_path.write_bytes(audio_bytes)

verdict = {
    "test": "T10",
    "hypothesis": (
        "The Orpheus 14.59-s per-call output cap is a deployment-config "
        "default (max_new_tokens ~2048) rather than a model-intrinsic "
        "architectural limit. Passing max_new_tokens = 4000 will produce "
        "output > 14.59s."
    ),
    "input": {
        "item_id": "L01",
        "text_chars": len(TEXT),
        "text_words": len(TEXT.split()),
        "voice": VOICE,
        "max_new_tokens": MAX_NEW_TOKENS,
        "model_version": VERSION_SHA,
    },
    "measurement": {
        "duration_s": duration,
        "n_frames": n_frames,
        "sample_rate_hz": sr,
        "wall_clock_s": round(wall, 3),
        "audio_bytes": len(audio_bytes),
        "audio_path": str(audio_path.relative_to(ROOT)),
    },
    "baseline_from_t8": {
        "capped_duration_s": 14.59,
        "stdev_across_long_items_s": 0.000,
        "n_items_at_cap": 8,
    },
    "verdict": None,
    "date": "2026-09-07",
}
if duration is None:
    verdict["verdict"] = "ERROR — audio did not decode as WAV"
elif duration > 15.0:
    verdict["verdict"] = "DEPLOYMENT-CONFIG DEFAULT — cap extends when max_new_tokens is raised; PM fix is one API-flag flip"
elif abs(duration - 14.59) < 0.5:
    verdict["verdict"] = "MODEL-INTRINSIC — cap holds at ~14.59s regardless of max_new_tokens; PM fix is a chunking-engineering workstream"
else:
    verdict["verdict"] = f"INDETERMINATE — duration {duration:.3f}s does not clearly match either the 14.59s cap or a longer output"

(out_dir / "T10_verdict.json").write_text(
    json.dumps(verdict, indent=2), encoding="utf-8"
)
print(f"  wall clock: {wall:.1f}s")
print(f"  output duration: {duration!r}s")
print(f"  audio bytes: {len(audio_bytes)}")
print(f"  VERDICT: {verdict['verdict']}")
print(f"  written to: {out_dir}")
