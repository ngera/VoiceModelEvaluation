from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
)
from veval.adapters.deepgram import DeepgramAdapter

ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "deepgram": DeepgramAdapter,
}

__all__ = [
    "ADAPTERS",
    "DeepgramAdapter",
    "ProviderAdapter",
    "ProviderError",
    "SynthesisOptions",
    "SynthesisResult",
]
