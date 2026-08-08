"""Content-hash cache for synthesis results.

Phase D.2. Rationale from CLAUDE.md conventions:

  "Content-hash cache in the runner means re-runs cost only the changed
   items — key to the 'monthly cached re-run' story."

Cache key inputs (all things a provider bills or renders on):
  - provider name
  - model string
  - voice_id
  - text
  - output_format (wav/mp3)
  - sample_rate (nullable)
  - version (Orpheus SHA; None for others)

Cache is CAMPAIGN-MODE ONLY. Variance mode needs three FRESH draws to
measure noise; latency mode measures FRESH TTFA. Both must skip the
cache — enforced by the runner, not by this module.

Cache directory (default `.cache/synthesis/`) is gitignored. Nuking it
loses only compute cost, not measurement data.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CACHE_DIR = Path(".cache/synthesis")


@dataclass
class CacheEntry:
    """One cached synthesis result — the bytes plus enough metadata to
    reconstruct a SynthesisResult without re-calling the provider."""

    audio_bytes: bytes
    audio_format: str
    sample_rate: int | None
    chars_billed: int
    billing_unit: str
    provider: str
    model: str
    voice_id: str
    meta: dict[str, Any]


class SynthesisCache:
    """Content-hash cache. Two files per entry: `<hash>.<ext>` + `<hash>.json`."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(
        self,
        provider: str,
        model: str,
        voice_id: str,
        text: str,
        output_format: str,
        sample_rate: int | None,
        version: str | None,
    ) -> str:
        # sha256 of the tuple that uniquely identifies "what would the
        # provider produce". Includes version so an Orpheus SHA bump
        # naturally invalidates the cache.
        payload = "|".join([
            provider, model, voice_id, text, output_format,
            str(sample_rate or "-"), version or "-",
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _paths(self, key: str, ext: str) -> tuple[Path, Path]:
        return (self.cache_dir / f"{key}.{ext}", self.cache_dir / f"{key}.json")

    def get(
        self,
        provider: str,
        model: str,
        voice_id: str,
        text: str,
        output_format: str,
        sample_rate: int | None = None,
        version: str | None = None,
    ) -> CacheEntry | None:
        """Return the cached entry if it exists, else None."""
        key = self._key(provider, model, voice_id, text, output_format, sample_rate, version)
        audio_path, meta_path = self._paths(key, output_format)
        if not audio_path.exists() or not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            audio_bytes = audio_path.read_bytes()
        except (OSError, json.JSONDecodeError):
            # Cache corrupted — treat as miss. Never crash the runner over cache.
            return None
        return CacheEntry(
            audio_bytes=audio_bytes,
            audio_format=meta["audio_format"],
            sample_rate=meta.get("sample_rate"),
            chars_billed=meta["chars_billed"],
            billing_unit=meta["billing_unit"],
            provider=meta["provider"],
            model=meta["model"],
            voice_id=meta["voice_id"],
            meta=meta.get("meta", {}),
        )

    def put(
        self,
        provider: str,
        model: str,
        voice_id: str,
        text: str,
        output_format: str,
        sample_rate: int | None,
        version: str | None,
        audio_bytes: bytes,
        chars_billed: int,
        billing_unit: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Write an entry. Overwrites silently if already present (idempotent)."""
        key = self._key(provider, model, voice_id, text, output_format, sample_rate, version)
        audio_path, meta_path = self._paths(key, output_format)
        # Write audio atomically: temp file → rename. Prevents half-written
        # cache entries if the process dies mid-write.
        tmp_audio = audio_path.with_suffix(f".{output_format}.tmp")
        tmp_audio.write_bytes(audio_bytes)
        os.replace(tmp_audio, audio_path)
        # Metadata: everything we'd need to reconstruct a SynthesisResult.
        payload = {
            "provider": provider,
            "model": model,
            "voice_id": voice_id,
            "audio_format": output_format,
            "sample_rate": sample_rate,
            "chars_billed": chars_billed,
            "billing_unit": billing_unit,
            "version": version,
            "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
            "meta": meta or {},
        }
        tmp_meta = meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        os.replace(tmp_meta, meta_path)

    def stats(self) -> dict[str, int]:
        """Return {entries, total_bytes} for a quick health check."""
        entries = list(self.cache_dir.glob("*.json"))
        total_bytes = sum(p.stat().st_size for p in self.cache_dir.iterdir() if p.is_file())
        return {"entries": len(entries), "total_bytes": total_bytes}
