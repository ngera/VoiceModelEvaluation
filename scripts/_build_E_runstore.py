"""Build a synthetic veval run-store for the E alt-voice audio.

The E audio lives under analysis/experiments-2026-09-01/audio/E_altvoice/{vendor}/*.wav.
This script constructs runs/experiments-2026-09-01-E/ with the layout the veval
analyzer expects: audio/{provider}/{use_case}/{item_id}.wav + api_log.jsonl.

WAVs are copied (not symlinked — Windows portability). Total size ~130 MB.
"""

from __future__ import annotations

import json
import shutil
import wave
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path("analysis/experiments-2026-09-01/audio/E_altvoice")
DEST = Path("runs/experiments-2026-09-01-E")

# Alt voices for E (must match _experiment_pack.py's EXPERIMENT_E_ALT_VOICES)
ALT = {
    "openai":   ("nova",              "tts-1-hd"),
    "fish":     ("9a9cf47702da476aa4629e2506d4a857", "s2.1-pro"),
    "deepgram": ("aura-2-luna-en",    "aura-2-luna-en"),
    "google":   ("en-US-Chirp3-HD-Kore", "en-US-Chirp3-HD-Kore"),
}


def _decoded_seconds(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as w:
        return w.getnframes() / w.getframerate()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "audio").mkdir(exist_ok=True)

    api_rows = []
    for vendor_dir in sorted(SOURCE.iterdir()):
        if not vendor_dir.is_dir():
            continue
        vendor = vendor_dir.name
        if vendor not in ALT:
            print(f"skipping {vendor} (no alt-voice config)")
            continue
        voice_id, model = ALT[vendor]

        dst_dir = DEST / "audio" / vendor / "narration"
        dst_dir.mkdir(parents=True, exist_ok=True)

        for wav_src in sorted(vendor_dir.glob("*.wav")):
            item_id = wav_src.stem  # L01, L02, ...
            dst = dst_dir / f"{item_id}.wav"
            if not dst.exists():
                shutil.copy2(wav_src, dst)
            n_bytes = dst.stat().st_size
            decoded_s = _decoded_seconds(dst)
            api_rows.append({
                "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "provider": vendor,
                "use_case": "narration",
                "item_id": item_id,
                "draw": 0,
                "status": "ok",
                "ttfa_ms": None,
                "total_ms": None,
                "chars_billed": 1400,  # approximate; not used by quality/wer
                "billing_unit": "characters",
                "audio_bytes": n_bytes,
                "audio_path": f"audio/{vendor}/narration/{item_id}.wav",
                "voice_id": voice_id,
                "model": model,
                "attempts": 1,
                "cache": "off",
                "estimated_call_usd": 0.0,
                "meta": {"experiment": "E_alt_voice", "source_dir": str(wav_src)},
            })

    log_path = DEST / "api_log.jsonl"
    with log_path.open("w", encoding="utf-8") as f:
        for r in api_rows:
            f.write(json.dumps(r) + "\n")

    manifest = {
        "run_id": "experiments-2026-09-01-E",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "campaign",
        "n_files": len(api_rows),
        "note": "Synthetic run-store built from experiments-2026-09-01/audio/E_altvoice/ for veval analyze compatibility.",
    }
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(api_rows)} audio rows + manifest to {DEST}")
    for vendor in ALT:
        vd = DEST / "audio" / vendor / "narration"
        n = len(list(vd.glob("*.wav"))) if vd.exists() else 0
        print(f"  {vendor}: {n} WAVs in {vd}")


if __name__ == "__main__":
    main()
