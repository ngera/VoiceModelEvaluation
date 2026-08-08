"""Shared helpers for analyzers — RunReader and AnalysisWriter.

RunReader turns `runs/<run_id>/` into an iterator of AudioRecord tuples
that every analyzer consumes. Cached rows (no fresh network call) are
kept for correctness — the WAV still needs to be checked — but callers
that measure timings (latency.py) filter them out.

AnalysisWriter writes JSON atomically to `analysis/<run_id>/`, mirroring
the SynthesisCache pattern (temp file + os.replace) so an interrupted
write never leaves a half-JSON on disk that a later pass would parse.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AudioRecord:
    """One synthesized WAV plus the api_log row that produced it.

    `api_row` is None only when the manifest lists an audio file the log
    lost track of (a class of bug the acceptance gate exists to flag).
    """

    provider: str
    use_case: str
    item_id: str
    draw: int
    wav_path: Path
    api_row: dict[str, Any] | None


class RunReader:
    """Iterate over the audio + api_log rows of one run directory."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.manifest_path = run_dir / "manifest.json"
        self.api_log_path = run_dir / "api_log.jsonl"
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"No manifest.json under {run_dir}")

    def manifest(self) -> dict[str, Any]:
        with self.manifest_path.open("r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    def api_log(self) -> Iterator[dict[str, Any]]:
        if not self.api_log_path.exists():
            return
        with self.api_log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def records(self, *, only_status: str | None = "ok") -> Iterator[AudioRecord]:
        """Yield one AudioRecord per api_log row that produced a file.

        `only_status="ok"` (default) skips error rows — they have no audio.
        Pass `only_status=None` to include everything (analyzers that want
        to count errors, e.g. cost, use that).
        """
        for row in self.api_log():
            if only_status is not None and row.get("status") != only_status:
                continue
            audio_rel = row.get("audio_path")
            if not audio_rel:
                continue
            # api_log stores audio_path with the platform separator that wrote
            # it (Windows uses `\`); normalize both here so a run written on
            # Windows is readable on Linux and vice versa.
            wav_path = self.run_dir / audio_rel.replace("\\", "/")
            yield AudioRecord(
                provider=row["provider"],
                use_case=row["use_case"],
                item_id=row["item_id"],
                draw=row.get("draw", 0),
                wav_path=wav_path,
                api_row=row,
            )


class AnalysisWriter:
    """Write JSON outputs atomically under `analysis/<run_id>/`."""

    def __init__(self, run_id: str, base_dir: Path | None = None) -> None:
        root = base_dir or Path(os.environ.get("VEVAL_ANALYSIS_DIR", "analysis"))
        self.dir = root / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: Any) -> Path:
        """Atomic JSON write. `name` includes the extension (`acceptance.json`)."""
        path = self.dir / name
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return path
