"""Standalone generation harness for the F-6 experiment pack.

Bypasses configs/voices.yaml + corpus/ so we can send arbitrary text
to arbitrary voice_ids without amending pre-registration. Writes WAVs
to analysis/experiments-2026-09-01/audio/<exp>/<label>.wav, and per-
experiment API logs to analysis/experiments-2026-09-01/logs/.

Also includes a lightweight drift analyzer (thirds LUFS) that reads
each WAV and reports fade magnitude, direction, and monotonicity —
avoids running the full veval analyzer stack.

Usage:
    uv run python scripts/_experiment_pack.py A     # 20 new items
    uv run python scripts/_experiment_pack.py B     # 5 voices on L03
    uv run python scripts/_experiment_pack.py C     # L03 halves
    uv run python scripts/_experiment_pack.py D     # latency S4/S5
    uv run python scripts/_experiment_pack.py E     # alt-voice sweep
    uv run python scripts/_experiment_pack.py drift # analyze all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")

from veval.adapters import ADAPTERS
from veval.adapters.base import ProviderError, SynthesisOptions
from veval.config import load_providers

OUT = Path("analysis/experiments-2026-09-01")
(OUT / "audio").mkdir(parents=True, exist_ok=True)
(OUT / "logs").mkdir(parents=True, exist_ok=True)
(OUT / "inputs").mkdir(parents=True, exist_ok=True)


# ============================================================================
# Corpus for Experiment A (20 new items, ~200-500 chars, 5 topics)
# ============================================================================

EXPERIMENT_A_ITEMS = {
    # Technical instructions (5)
    "TECH01": "To reset the device, hold the power button for ten seconds until the indicator light flashes amber. Release the button. The device will restart automatically and display the setup screen within thirty seconds. If the light turns solid red instead, contact support and quote the serial number printed on the base.",
    "TECH02": "Before installation, verify the following: the mounting surface is level, the electrical supply is rated 220 to 240 volts, and there is at least forty centimetres of clearance above the unit. Failure to meet any of these requirements may void the warranty and create a fire hazard.",
    "TECH03": "The API returns a JSON object with three fields: status, data, and error. When status equals success, data contains the requested payload and error is null. When status equals failure, data is null and error contains a human-readable message and a numeric code. Retry logic should back off exponentially on 5xx errors only.",
    "TECH04": "Charge the battery for at least four hours before first use. During charging the indicator will be red; when fully charged it will turn green. Do not use the device while charging. A fully charged battery provides approximately twelve hours of continuous operation under normal conditions.",
    "TECH05": "To pair a new sensor with the hub, press and hold the pair button on the hub for three seconds until the LED begins blinking blue. Within sixty seconds, press the small button inside the sensor's battery compartment. A confirmation tone will play when pairing succeeds.",
    # Warm storytelling (5)
    "WARM01": "My grandmother's kitchen always smelled of cinnamon and warm butter. Every Sunday morning she would wake before the rest of the house and start baking, and the smell would drift up the stairs and into our dreams. By the time we came down, sleepy and rumpled, there would be a plate of golden pastries on the table and a pot of coffee just beginning to bubble.",
    "WARM02": "The old dog padded across the wooden floor and settled at his usual spot by the fire, letting out a long contented sigh. He'd been my companion for twelve years now, through moves, through job changes, through the quiet years and the loud ones. Some evenings I would just sit and watch him breathe, and think how much smaller the room would feel without him.",
    "WARM03": "When I was eight my father built me a wooden treehouse in the oak behind our garden. It had a ladder made of rope and a small window that opened onto the field beyond. That summer I read every book in the house up there, one at a time, with the leaves rustling and the smell of the wood warm in the afternoon sun.",
    "WARM04": "The first time I heard her laugh I was standing in a bookshop in the rain, holding a copy of a novel I would never actually read. She was three aisles away, laughing at something her friend had said. I remember thinking that if the rest of the world sounded like that, everything would be easier.",
    "WARM05": "There was a stretch of road between the village and the sea that we always walked at sunset, my mother and I, when the sky turned that particular shade of blue you only get in late September. She would tell me about her own childhood, in a house that no longer stood, and I would listen without interrupting.",
    # Dry factual (5)
    "FACT01": "The Amazon rainforest covers approximately five and a half million square kilometres across nine countries in South America, with roughly sixty percent falling within Brazilian territory. It contains an estimated three hundred and ninety billion individual trees representing more than sixteen thousand distinct species, and produces around six percent of the world's atmospheric oxygen.",
    "FACT02": "The Great Wall of China was constructed in multiple stages over more than two thousand years, beginning around the seventh century BCE and continuing through the Ming dynasty in the sixteenth century CE. Contemporary estimates place its total length, including all branches and reconstructions, at around twenty one thousand kilometres. Only a small fraction of the original structure remains intact today.",
    "FACT03": "Water covers roughly seventy one percent of the Earth's surface. Of that, approximately ninety seven percent is saline ocean water; only three percent is freshwater. Of the freshwater, about sixty eight percent is locked in glaciers and ice caps, thirty percent is groundwater, and less than one percent is in surface bodies such as rivers and lakes.",
    "FACT04": "The human brain contains approximately eighty six billion neurons and consumes about twenty percent of the body's total energy despite representing only two percent of body mass. Signals travel between neurons at speeds ranging from around one metre per second to more than one hundred metres per second, depending on axon type.",
    "FACT05": "The International Space Station orbits the Earth at an altitude of approximately four hundred kilometres, completing one full revolution every ninety two minutes. It travels at roughly twenty eight thousand kilometres per hour and has been continuously inhabited since November two thousand. The station is a collaboration between NASA, Roscosmos, JAXA, ESA, and CSA.",
    # Emotional (5)
    "EMOT01": "I don't know how to tell you this, so I'll just say it. Dad passed away this morning. It was quick, and he wasn't in pain, and Mum was with him. I know you were planning to come see him next month, and I'm so sorry that isn't going to happen now. Please call when you can. There's no rush.",
    "EMOT02": "You did it. You actually did it. All those years of studying, all those late nights, all the times you thought you couldn't do it and then did it anyway. And now here you are, standing in a graduation gown, holding the piece of paper that says you were right about yourself all along. I am so proud of you I could burst.",
    "EMOT03": "I've been holding onto this for a long time, and I need to say it before I lose the courage. I love you. I've loved you since the day we met, and probably before that if we're being honest. I don't need you to say anything back right now. I just needed you to know.",
    "EMOT04": "Something is wrong with me. I don't know what it is, and I don't know how to fix it, but I know that I can't keep pretending everything is fine. I'm asking for help. I've never asked for help before and I don't know how to do it well, so please be patient with me.",
    "EMOT05": "The house is quiet now, in a way it has never been. Her shoes are still by the door where she left them; her coffee cup is still on the counter. Every room I walk into holds the shape of her absence, and I don't know yet how I'm going to fill any of them.",
}


# ============================================================================
# Voices for Experiment B (5 well-known ElevenLabs voices)
# ============================================================================

EXPERIMENT_B_VOICES = [
    # (label, voice_id, description)
    ("charlotte_pinned", "qSeXEcewz7tA0Q0qk9fH", "current pinned narration voice (control)"),
    ("rachel", "21m00Tcm4TlvDq8ikWAM", "calm en-US female"),
    ("antoni", "ErXwobaYiN019PkySvjV", "well-rounded en-US male"),
    ("bella", "EXAVITQu4vr4xnSDxMaL", "soft en-US female"),
    ("josh", "TxGEqnHWrfWFTfGW9XjX", "deep en-US male narrator"),
]


# ============================================================================
# Alt voices for Experiment E (one alt per vendor)
# ============================================================================

EXPERIMENT_E_ALT_VOICES = [
    # (provider, use_case, voice_id, model, description)
    ("openai",   "narration", "nova",              "tts-1-hd",           "female alt vs pinned onyx"),
    # Fish alt = the CONVERSATIONAL-tagged voice_id (a real Fish voice with different gender/style
    # from the pinned narration voice e3cd3841... . Using it for narration text is a valid alt.)
    ("fish",     "narration", "9a9cf47702da476aa4629e2506d4a857", "s2.1-pro", "Fish's conv-tagged voice as narration alt (voice_id verified in R3 campaign)"),
    ("deepgram", "narration", "aura-2-luna-en",    "aura-2-luna-en",     "female alt vs pinned orion (male)"),
    ("google",   "narration", "en-US-Chirp3-HD-Kore", "en-US-Chirp3-HD-Kore", "female alt vs pinned charon (male)"),
]


# ============================================================================
# L03 text for Experiments B and C (from analysis/campaign-*/wer.json)
# ============================================================================

L03_TEXT = (
    "Good evening. I'm Sarah Chen, and this is the 6 o'clock news. Our top story tonight: "
    "the government has announced an emergency package worth 14 billion pounds to help "
    "households and businesses with rising energy costs. The Chancellor confirmed the "
    "measures in a statement to Parliament this afternoon, saying the package would take "
    "effect from the 1st of May. Under the plan, households will receive a flat payment "
    "of 400 pounds, with additional support for the lowest-income families of up to 650 "
    "pounds. Businesses in the hospitality, retail, and manufacturing sectors will "
    "receive rebates on their energy bills for a period of six months. The announcement "
    "was welcomed by opposition leaders, though the shadow chancellor called it too "
    "little too late, pointing out that average household bills have risen by 67 percent "
    "over the past 18 months. Industry groups broadly welcomed the support but said "
    "longer-term solutions were still needed. The cost of the package will be funded "
    "partly through a windfall tax on energy companies, which the government is extending "
    "for a further two years. Several energy firms said they would review planned "
    "investment in domestic production following the announcement. We'll have more on "
    "this story throughout the evening. Now let's go to our economics correspondent "
    "James Okafor, who is outside the Treasury."
)

# Split L03 for Experiment C (natural boundary at sentence mid-paragraph)
_L03_SPLIT_BOUNDARY = L03_TEXT.find("The announcement was welcomed")
L03_HALF1 = L03_TEXT[:_L03_SPLIT_BOUNDARY].strip()
L03_HALF2 = L03_TEXT[_L03_SPLIT_BOUNDARY:].strip()


# ============================================================================
# Helpers
# ============================================================================


def _cfg():
    from types import SimpleNamespace
    return SimpleNamespace(providers=load_providers(Path("configs/providers.yaml")))


def _synthesize(provider: str, text: str, voice_id: str, model: str, out_wav: Path, item_id: str, use_case: str = "narration"):
    """Call the vendor adapter directly, save WAV, return log row."""
    cfg = _cfg()
    provider_cfg = next(p for p in cfg.providers.providers if p.name == provider)
    api_key = os.environ.get(provider_cfg.env_key) if provider_cfg.env_key else None
    if provider_cfg.env_key and not api_key:
        raise RuntimeError(f"missing env var: {provider_cfg.env_key}")

    adapter_cls = ADAPTERS[provider]
    endpoint = getattr(provider_cfg, "endpoint", None) or getattr(provider_cfg, "base_url", None)
    version = getattr(provider_cfg, "version", None)
    adapter = adapter_cls(api_key=api_key or "", model=model, endpoint=endpoint, version=version)

    opts = SynthesisOptions(text=text, voice_id=voice_id, output_format="wav", streaming=False)
    t0 = time.perf_counter()
    result = adapter.synthesize(opts)
    elapsed = time.perf_counter() - t0

    # Persist audio to a WAV
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    out_wav.write_bytes(result.audio_bytes)

    return {
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "provider": provider,
        "voice_id": voice_id,
        "model": model,
        "item_id": item_id,
        "use_case": use_case,
        "n_chars": len(text),
        "elapsed_s": round(elapsed, 3),
        "audio_bytes": len(result.audio_bytes),
        "chars_billed": result.chars_billed,
        "wav_path": str(out_wav.relative_to(OUT.parent.parent)),
    }


def _write_log(exp: str, rows: list[dict]):
    log_path = OUT / "logs" / f"{exp}_api_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


# ============================================================================
# LUFS-thirds drift analyzer (avoids full veval stack)
# ============================================================================


def _lufs_of(samples: np.ndarray, sr: int) -> float | None:
    """LUFS via pyloudnorm on a mono float32 array; None if pyloudnorm errs."""
    try:
        import pyloudnorm as pyln
    except ImportError:
        return None
    if len(samples) < sr * 0.4:
        return None
    try:
        meter = pyln.Meter(sr)
        return float(meter.integrated_loudness(samples.astype(np.float64)))
    except Exception:
        return None


def _thirds_lufs(wav_path: Path) -> dict:
    """Read a WAV, split into 3 equal-time thirds, compute LUFS of each."""
    with wave.open(str(wav_path), "rb") as w:
        sr = w.getframerate()
        n_frames = w.getnframes()
        n_channels = w.getnchannels()
        raw = w.readframes(n_frames)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)
    third_len = len(samples) // 3
    t1 = _lufs_of(samples[:third_len], sr)
    t2 = _lufs_of(samples[third_len:2 * third_len], sr)
    t3 = _lufs_of(samples[2 * third_len:], sr)
    if None in (t1, t2, t3):
        return {"lufs_t1": t1, "lufs_t2": t2, "lufs_t3": t3, "monotonic_decreasing": None, "delta_t1_t3": None, "duration_s": len(samples) / sr}
    delta = t1 - t3  # positive = fade
    monotonic = (t1 > t2 > t3) or (t1 == t2 > t3) or (t1 > t2 == t3)
    return {
        "lufs_t1": round(t1, 3),
        "lufs_t2": round(t2, 3),
        "lufs_t3": round(t3, 3),
        "monotonic_decreasing": bool(monotonic),
        "delta_t1_t3": round(delta, 3),
        "duration_s": round(len(samples) / sr, 2),
    }


def analyze_all():
    """Run drift analyzer over every WAV under analysis/experiments-2026-09-01/audio/."""
    all_rows = []
    for wav in sorted((OUT / "audio").rglob("*.wav")):
        rel = wav.relative_to(OUT / "audio")
        stats = _thirds_lufs(wav)
        all_rows.append({"wav": str(rel), **stats})
    out = OUT / "drift.json"
    out.write_text(json.dumps({"n_files": len(all_rows), "items": all_rows}, indent=2), encoding="utf-8")
    print(f"drift analysis written: {out}  (n={len(all_rows)})")
    return all_rows


# ============================================================================
# Experiment runners
# ============================================================================


def run_C():
    """Split L03 into two halves; generate each on ElevenLabs; log."""
    rows = []
    for label, text in [("l03_half1", L03_HALF1), ("l03_half2", L03_HALF2)]:
        out_wav = OUT / "audio" / "C_halves" / f"{label}.wav"
        print(f"C: generating {label} ({len(text)} chars)...")
        r = _synthesize("elevenlabs", text, "qSeXEcewz7tA0Q0qk9fH", "eleven_multilingual_v2", out_wav, label)
        rows.append(r)
        print(f"  ok: {r['audio_bytes']} bytes in {r['elapsed_s']}s")
    _write_log("C", rows)
    # Also write the input text
    (OUT / "inputs" / "C_l03_halves.json").write_text(
        json.dumps({"l03_full": L03_TEXT, "half1": L03_HALF1, "half2": L03_HALF2, "boundary_at_char": _L03_SPLIT_BOUNDARY}, indent=2),
        encoding="utf-8",
    )
    return rows


def run_B():
    """Generate L03 on 5 different ElevenLabs voices."""
    rows = []
    for label, voice_id, desc in EXPERIMENT_B_VOICES:
        out_wav = OUT / "audio" / "B_voices" / f"{label}.wav"
        print(f"B: generating on {label} ({desc})...")
        try:
            r = _synthesize("elevenlabs", L03_TEXT, voice_id, "eleven_multilingual_v2", out_wav, f"L03__{label}")
            r["voice_label"] = label
            r["voice_description"] = desc
            rows.append(r)
            print(f"  ok: {r['audio_bytes']} bytes in {r['elapsed_s']}s")
        except Exception as e:
            print(f"  FAIL: {type(e).__name__}: {e}")
            rows.append({"voice_label": label, "voice_id": voice_id, "error": str(e), "provider": "elevenlabs"})
    _write_log("B", rows)
    return rows


def run_A():
    """Generate 20 new items on ElevenLabs pinned narration voice."""
    (OUT / "inputs" / "A_items.json").write_text(json.dumps(EXPERIMENT_A_ITEMS, indent=2), encoding="utf-8")
    rows = []
    for item_id, text in EXPERIMENT_A_ITEMS.items():
        out_wav = OUT / "audio" / "A_new_items" / f"{item_id}.wav"
        print(f"A: generating {item_id} ({len(text)} chars)...")
        try:
            r = _synthesize("elevenlabs", text, "qSeXEcewz7tA0Q0qk9fH", "eleven_multilingual_v2", out_wav, item_id)
            rows.append(r)
            print(f"  ok: {r['audio_bytes']} bytes in {r['elapsed_s']}s")
        except Exception as e:
            print(f"  FAIL: {type(e).__name__}: {e}")
            rows.append({"item_id": item_id, "error": str(e), "provider": "elevenlabs"})
    _write_log("A", rows)
    return rows


def run_E(only_provider: str | None = None, skip_existing: bool = False):
    """Alt-voice sweep: generate 8 long narration items per (vendor, alt-voice)."""
    # Load original narration long items (L01..L08) from the corpus so we're
    # measuring identical text
    import glob
    w_path = glob.glob("analysis/campaign-20260831T175358Z/wer.json")[0]
    w = json.loads(Path(w_path).read_text(encoding="utf-8"))
    long_items = {}
    for it in w["items"]:
        if it["use_case"] == "narration" and it["item_id"].startswith("L"):
            long_items[it["item_id"]] = it["reference"]
    long_items = dict(sorted(long_items.items())[:8])  # L01..L08
    (OUT / "inputs" / "E_long_items.json").write_text(json.dumps(long_items, indent=2), encoding="utf-8")

    rows = []
    for provider, use_case, voice_id, model, desc in EXPERIMENT_E_ALT_VOICES:
        if only_provider and provider != only_provider:
            continue
        print(f"\nE: {provider} on alt voice {voice_id} ({desc})...")
        for item_id, text in long_items.items():
            out_wav = OUT / "audio" / "E_altvoice" / provider / f"{item_id}.wav"
            if skip_existing and out_wav.exists():
                print(f"  {provider} {item_id}: SKIP (exists)")
                continue
            print(f"  {provider} {item_id} ({len(text)} chars)...", end=" ", flush=True)
            try:
                r = _synthesize(provider, text, voice_id, model, out_wav, f"{item_id}__altvoice", use_case=use_case)
                r["voice_description"] = desc
                rows.append(r)
                print(f"ok ({r['audio_bytes']} bytes, {r['elapsed_s']}s)")
            except Exception as e:
                print(f"FAIL: {type(e).__name__}: {str(e)[:120]}")
                rows.append({"provider": provider, "item_id": item_id, "voice_id": voice_id, "error": str(e)})
    _write_log("E", rows)
    return rows


def run_D():
    """Two more latency sessions (S4 same day, S5 later same day) on ElevenLabs + OpenAI."""
    # Just spawn `veval generate --mode latency` twice for each vendor with distinct run_ids
    # Actually simplest: reuse scripts/latency_with_ping.py if it exists
    import subprocess
    for session_label in ["S4", "S5"]:
        for provider in ["elevenlabs", "openai"]:
            print(f"\nD: {session_label} {provider} — 50 trials of S01...")
            try:
                proc = subprocess.run(
                    ["uv", "run", "veval", "generate", "--mode", "latency", "--provider", provider, "--trials", "50", "--spend-cap", "5.0"],
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    capture_output=True, text=True, timeout=1200,
                )
                print(f"  exit={proc.returncode}")
                if proc.returncode != 0:
                    print(proc.stderr[-500:])
            except subprocess.TimeoutExpired:
                print(f"  TIMEOUT after 20 min")
        # Sleep between S4 and S5 to give some spacing
        if session_label == "S4":
            print("D: pausing 60s before S5...")
            time.sleep(60)
    print("D: complete (results in newest runs/latency-* directories)")


# ============================================================================
# CLI
# ============================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", choices=["A", "B", "C", "D", "E", "E_fish", "E_openai_retry", "drift", "all"])
    args = ap.parse_args()
    if args.experiment == "A": run_A()
    elif args.experiment == "B": run_B()
    elif args.experiment == "C": run_C()
    elif args.experiment == "D": run_D()
    elif args.experiment == "E": run_E()
    elif args.experiment == "E_fish": run_E(only_provider="fish", skip_existing=True)
    elif args.experiment == "E_openai_retry": run_E(only_provider="openai", skip_existing=True)
    elif args.experiment == "drift": analyze_all()
    elif args.experiment == "all":
        run_C()
        run_B()
        run_A()
        run_E()
        run_D()
        analyze_all()


if __name__ == "__main__":
    main()
