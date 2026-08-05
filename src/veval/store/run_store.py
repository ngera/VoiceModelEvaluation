"""Immutable run store: runs/<run_id>/{manifest.json, audio/, api_log.jsonl}.

Design rule from CLAUDE.md conventions:
- Run dirs are immutable. Never mutate in place; a failed run gets a new dir.
- Analyzers read from the store and write to `analysis/<run_id>/` — pure functions.
"""

from __future__ import annotations

import json
import os
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Manifest(BaseModel):
    """Written once at run finalization to runs/<run_id>/manifest.json."""

    model_config = ConfigDict(extra="allow")

    run_id: str
    created_at_utc: str
    finalized_at_utc: str | None = None
    kind: str = Field(description="`doctor`, `generate`, `latency`, `pilot`, ...")

    # Environment
    hostname: str
    platform: str
    python_version: str

    # Content
    providers: list[str] = Field(default_factory=list)
    items: list[str] = Field(default_factory=list, description="Corpus item IDs included")
    audio_count: int = 0
    error_count: int = 0

    # Freeform (git sha, region, config paths, etc.)
    extras: dict[str, Any] = Field(default_factory=dict)


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id(kind: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{kind}-{stamp}"


class Run:
    """A single run directory. Instantiate via `RunStore.new_run()`."""

    def __init__(self, dir: Path, manifest: Manifest) -> None:
        self.dir = dir
        self.manifest = manifest
        self.api_log_path = dir / "api_log.jsonl"

    def write_audio(
        self,
        provider: str,
        item_id: str,
        audio_bytes: bytes,
        ext: str = "wav",
    ) -> Path:
        provider_dir = self.dir / "audio" / provider
        provider_dir.mkdir(parents=True, exist_ok=True)
        path = provider_dir / f"{item_id}.{ext}"
        path.write_bytes(audio_bytes)
        if provider not in self.manifest.providers:
            self.manifest.providers.append(provider)
        if item_id not in self.manifest.items:
            self.manifest.items.append(item_id)
        self.manifest.audio_count += 1
        return path

    def log_api(self, entry: dict[str, Any]) -> None:
        """Append one JSON line. Errors are data — log them here, not by crashing."""
        record = {"ts_utc": _utc_now_iso(), **entry}
        with self.api_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
        if entry.get("status") == "error":
            self.manifest.error_count += 1

    def finalize(self) -> Path:
        """Write manifest.json and return its path. Run dir is immutable after this."""
        self.manifest.finalized_at_utc = _utc_now_iso()
        manifest_path = self.dir / "manifest.json"
        manifest_path.write_text(
            self.manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return manifest_path


class RunStore:
    """Factory for `Run` objects rooted at `base_dir`."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def new_run(self, kind: str = "run", extras: dict[str, Any] | None = None) -> Run:
        run_id = _run_id(kind)
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)  # fail loud on collision
        (run_dir / "audio").mkdir()

        manifest = Manifest(
            run_id=run_id,
            created_at_utc=_utc_now_iso(),
            kind=kind,
            hostname=platform.node(),
            platform=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            extras=extras or {},
        )
        return Run(run_dir, manifest)

    def list_runs(self, kind: str | None = None) -> list[Path]:
        """Return run dirs sorted newest first, optionally filtered by kind prefix."""
        if not self.base_dir.exists():
            return []
        runs = [p for p in self.base_dir.iterdir() if p.is_dir()]
        if kind:
            runs = [p for p in runs if p.name.startswith(f"{kind}-")]
        return sorted(runs, key=lambda p: p.name, reverse=True)


def default_run_store() -> RunStore:
    """Store rooted at ./runs relative to CWD (or $VEVAL_RUNS_DIR if set)."""
    root = os.environ.get("VEVAL_RUNS_DIR", "runs")
    return RunStore(Path(root))
