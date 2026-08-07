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

ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "deepgram": DeepgramAdapter,
    "fish": FishAdapter,
    "google": GoogleAdapter,
    "cartesia": CartesiaAdapter,
    "elevenlabs": ElevenLabsAdapter,
}

__all__ = [
    "ADAPTERS",
    "CartesiaAdapter",
    "DeepgramAdapter",
    "ElevenLabsAdapter",
    "FishAdapter",
    "GoogleAdapter",
    "ProviderAdapter",
    "ProviderError",
    "SynthesisOptions",
    "SynthesisResult",
]
