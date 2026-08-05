"""Pydantic config schemas + loaders.

Configs are pre-registered (git-tagged `prereg-v1`) BEFORE any results exist.
Every runtime read goes through these models so typos fail loud.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

UseCase = Literal["conversational", "narration"]


class ProviderConfig(BaseModel):
    """One provider entry in providers.yaml."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Short key used in paths and CLI: `deepgram`, `elevenlabs`...")
    display_name: str = Field(description="Human-readable: `Deepgram Aura-2`")
    model: str = Field(description="Exact model string sent to the provider API")
    endpoint: str | None = Field(
        default=None, description="Base URL override; adapter default if None"
    )
    env_key: str = Field(description="Env var holding the API key, e.g. `DEEPGRAM_API_KEY`")
    tier: Literal["core", "control", "stretch"] = "core"
    notes: str = ""


class ProvidersFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: list[ProviderConfig]

    def by_name(self, name: str) -> ProviderConfig:
        for p in self.providers:
            if p.name == name:
                return p
        raise KeyError(f"Provider `{name}` not in providers.yaml")


class VoiceSelection(BaseModel):
    """One voice locked for one provider × use case."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    use_case: UseCase
    voice_id: str
    reasoning: str = Field(description="One line: why this voice for this use case")


class VoicesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voices: list[VoiceSelection]

    def get(self, provider: str, use_case: UseCase) -> VoiceSelection:
        for v in self.voices:
            if v.provider == provider and v.use_case == use_case:
                return v
        raise KeyError(f"No voice locked for {provider} × {use_case}")


class Gate(BaseModel):
    """One hard gate for one use case. Failing = provider is out of that use case."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(description="e.g. `ttfa_p90_ms`, `rtf`, `clipping_pct`")
    op: Literal["lt", "lte", "gt", "gte", "eq"]
    threshold: float
    rationale: str = Field(description="One sentence: why this gate exists")


class UseCaseGates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: UseCase
    gates: list[Gate]


class GatesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[UseCaseGates]


# --- Loaders ---


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


def load_providers(path: Path) -> ProvidersFile:
    return ProvidersFile.model_validate(_load_yaml(path))


def load_voices(path: Path) -> VoicesFile:
    return VoicesFile.model_validate(_load_yaml(path))


def load_gates(path: Path) -> GatesFile:
    return GatesFile.model_validate(_load_yaml(path))
