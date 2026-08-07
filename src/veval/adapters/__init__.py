from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
)
from veval.adapters.cartesia import CartesiaAdapter
from veval.adapters.deepgram import DeepgramAdapter
from veval.adapters.elevenlabs import ElevenLabsAdapter
from veval.adapters.fish import FishAdapter
from veval.adapters.google import GoogleAdapter
from veval.adapters.orpheus import OrpheusAdapter

ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "deepgram": DeepgramAdapter,
    "fish": FishAdapter,
    "google": GoogleAdapter,
    "cartesia": CartesiaAdapter,
    "elevenlabs": ElevenLabsAdapter,
    "orpheus": OrpheusAdapter,
}

__all__ = [
    "ADAPTERS",
    "CartesiaAdapter",
    "DeepgramAdapter",
    "ElevenLabsAdapter",
    "FishAdapter",
    "GoogleAdapter",
    "OrpheusAdapter",
    "ProviderAdapter",
    "ProviderError",
    "SynthesisOptions",
    "SynthesisResult",
]
