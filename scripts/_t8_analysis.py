"""One-shot T8 analysis: pull Replicate predict_time, WAV duration, char length,
compute per-item and aggregate cost + linear-scaling test."""

from __future__ import annotations

import json
import os
import statistics
import wave
from pathlib import Path

import requests
from dotenv import load_dotenv
from scipy.stats import spearmanr


def main() -> None:
    load_dotenv(".env")
    token = os.environ.get("REPLICATE_API_TOKEN")
    assert token, "REPLICATE_API_TOKEN not set"

    run_dir = Path("runs/campaign-20260811T183847Z")
    log = run_dir / "api_log.jsonl"
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]

    print("T8 · Orpheus cost & scaling analysis")
    print("=" * 100)
    header = f'{"item":6s}  {"chars":>6s}  {"exp_dur_s":>10s}  {"actual_s":>10s}  {"predict_s":>10s}  {"chars/audio_s":>14s}'
    print(header)
    print("-" * 100)

    per_item = []
    for r in rows:
        if r.get("status") != "ok":
            continue
        pid = r["meta"]["prediction_id"]
        resp = requests.get(
            f"https://api.replicate.com/v1/predictions/{pid}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        predict_time = resp.json().get("metrics", {}).get("predict_time") or 0

        wav_path = run_dir / r["audio_path"].replace("\\", "/")
        with wave.open(str(wav_path), "rb") as w:
            actual_dur_s = w.getnframes() / w.getframerate()

        chars = r["chars_billed"]
        expected_dur_s = chars / 14.6  # ~175 wpm, 5 chars/word

        per_item.append({
            "item": r["item_id"], "chars": chars,
            "expected_s": expected_dur_s, "actual_s": actual_dur_s,
            "predict_s": predict_time,
        })
        print(f'{r["item_id"]:6s}  {chars:>6d}  {expected_dur_s:>10.1f}  '
              f'{actual_dur_s:>10.2f}  {predict_time:>10.3f}  '
              f'{chars/actual_dur_s:>14.1f}')

    n = len(per_item)
    mean_pt = statistics.mean(p["predict_s"] for p in per_item)
    stdev_pt = statistics.stdev(p["predict_s"] for p in per_item)
    spread_pt = max(p["predict_s"] for p in per_item) - min(p["predict_s"] for p in per_item)

    print(f"\n=== Aggregates (n={n}) ===")
    print(f"predict_time: mean={mean_pt:.2f}s  stdev={stdev_pt:.2f}s  spread={spread_pt:.2f}s")
    mean_actual = statistics.mean(p["actual_s"] for p in per_item)
    stdev_actual = statistics.stdev(p["actual_s"] for p in per_item)
    print(f"actual_audio: mean={mean_actual:.2f}s  stdev={stdev_actual:.2f}s")
    mean_expected = statistics.mean(p["expected_s"] for p in per_item)
    print(f"expected@175wpm: mean={mean_expected:.2f}s")

    trunc_ratios = [p["actual_s"] / p["expected_s"] for p in per_item]
    mean_trunc = statistics.mean(trunc_ratios)
    print(f"\ntruncation ratio (actual / expected): mean={mean_trunc:.2%}")
    print(f"  items were truncated to ~{mean_trunc:.0%} of the expected reading duration")

    print(f"\n=== Cost calculation ===")
    print(f"Nvidia T4  ($0.000225/sec): cost/call = {mean_pt:.2f} x 0.000225 = ${mean_pt*0.000225:.4f}  "
          f"(pricing.yaml $0.003; ratio {mean_pt*0.000225/0.003:.2f}x)")
    print(f"Nvidia L40S ($0.000975/sec): cost/call = {mean_pt:.2f} x 0.000975 = ${mean_pt*0.000975:.4f}  "
          f"(pricing.yaml $0.003; ratio {mean_pt*0.000975/0.003:.2f}x)")
    print(f"Nvidia A100 ($0.001400/sec): cost/call = {mean_pt:.2f} x 0.001400 = ${mean_pt*0.001400:.4f}  "
          f"(pricing.yaml $0.003; ratio {mean_pt*0.001400/0.003:.2f}x)")

    print(f"\n=== Linear-scaling hypothesis ===")
    chars_range = (min(p["chars"] for p in per_item), max(p["chars"] for p in per_item))
    pt_range = (min(p["predict_s"] for p in per_item), max(p["predict_s"] for p in per_item))
    print(f"chars range: {chars_range[0]}-{chars_range[1]}  "
          f"({100*(chars_range[1]-chars_range[0])/statistics.mean(p['chars'] for p in per_item):.0f}% spread)")
    print(f"predict_time range: {pt_range[0]:.2f}-{pt_range[1]:.2f}s  "
          f"({100*(pt_range[1]-pt_range[0])/mean_pt:.0f}% spread)")
    r_chars = spearmanr([p["chars"] for p in per_item], [p["predict_s"] for p in per_item])
    r_audio = spearmanr([p["actual_s"] for p in per_item], [p["predict_s"] for p in per_item])
    print(f"Spearman rho(chars, predict_time)         = {r_chars.statistic:+.3f}  (p={r_chars.pvalue:.3f})")
    print(f"Spearman rho(actual_audio, predict_time)  = {r_audio.statistic:+.3f}  (p={r_audio.pvalue:.3f})")


if __name__ == "__main__":
    main()
