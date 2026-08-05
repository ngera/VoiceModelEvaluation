"""Config loading. config.py promises "typos fail loud" — these hold it to it.

These configs are the pre-registered ones (git-tagged `prereg-v1`), so a typo
that silently loads as a default is worse here than a crash: it would change
what was measured while still looking pre-committed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from veval.config import load_gates, load_providers, load_voices

VALID_PROVIDERS = """
providers:
  - name: deepgram
    display_name: "Deepgram Aura-2"
    model: "aura-2-thalia-en"
    env_key: DEEPGRAM_API_KEY
    tier: control
    notes: "Off-index control."
"""

VALID_VOICES = """
voices:
  - provider: deepgram
    use_case: conversational
    voice_id: aura-2-thalia-en
    reasoning: "Neutral US English, low affect."
"""

VALID_GATES = """
use_cases:
  - use_case: conversational
    gates:
      - metric: ttfa_p90_ms
        op: lt
        threshold: 400
        rationale: "Above this, turn-taking feels broken."
"""


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_load_providers_roundtrip(tmp_path: Path) -> None:
    providers = load_providers(_write(tmp_path, "providers.yaml", VALID_PROVIDERS))

    assert len(providers.providers) == 1
    entry = providers.by_name("deepgram")
    assert entry.model == "aura-2-thalia-en"
    assert entry.tier == "control"
    assert entry.endpoint is None  # optional, defaults to adapter's


def test_unknown_provider_key_is_rejected(tmp_path: Path) -> None:
    """extra='forbid': a misspelled key must not be silently dropped."""
    typo = VALID_PROVIDERS.replace("env_key:", "env_keys:")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", typo))


def test_missing_required_field_is_rejected(tmp_path: Path) -> None:
    incomplete = VALID_PROVIDERS.replace('    model: "aura-2-thalia-en"\n', "")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", incomplete))


def test_invalid_tier_is_rejected(tmp_path: Path) -> None:
    bad = VALID_PROVIDERS.replace("tier: control", "tier: premium")
    with pytest.raises(ValidationError):
        load_providers(_write(tmp_path, "providers.yaml", bad))


def test_by_name_raises_for_unknown_provider(tmp_path: Path) -> None:
    providers = load_providers(_write(tmp_path, "providers.yaml", VALID_PROVIDERS))
    with pytest.raises(KeyError):
        providers.by_name("elevenlabs")


def test_missing_file_raises_filenotfound(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_providers(tmp_path / "absent.yaml")


def test_load_voices_and_lookup(tmp_path: Path) -> None:
    voices = load_voices(_write(tmp_path, "voices.yaml", VALID_VOICES))

    assert voices.get("deepgram", "conversational").voice_id == "aura-2-thalia-en"
    with pytest.raises(KeyError):
        voices.get("deepgram", "narration")


def test_invalid_use_case_is_rejected(tmp_path: Path) -> None:
    bad = VALID_VOICES.replace("use_case: conversational", "use_case: podcast")
    with pytest.raises(ValidationError):
        load_voices(_write(tmp_path, "voices.yaml", bad))


def test_load_gates_roundtrip(tmp_path: Path) -> None:
    gates = load_gates(_write(tmp_path, "gates.yaml", VALID_GATES))

    conversational = gates.use_cases[0]
    assert conversational.use_case == "conversational"
    assert conversational.gates[0].op == "lt"
    assert conversational.gates[0].threshold == 400


def test_invalid_gate_operator_is_rejected(tmp_path: Path) -> None:
    bad = VALID_GATES.replace("op: lt", "op: less_than")
    with pytest.raises(ValidationError):
        load_gates(_write(tmp_path, "gates.yaml", bad))


def test_shipped_providers_yaml_is_valid() -> None:
    """The real config must load — it is the pre-registered artifact."""
    repo_root = Path(__file__).resolve().parent.parent
    providers = load_providers(repo_root / "configs" / "providers.yaml")
    assert providers.by_name("deepgram").env_key == "DEEPGRAM_API_KEY"
