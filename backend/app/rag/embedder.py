import hashlib
import math
import re
from functools import lru_cache
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import get_settings


class EmbeddingAdapter(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def aclose(self) -> None: ...


_TOKEN = re.compile(r"[\w'-]+", re.UNICODE)


class LocalHashEmbedder:
    """Deterministic, normalized local embeddings for offline development and tests."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    async def aclose(self) -> None:
        return None

    def _embed_one(self, text: str) -> list[float]:
        terms = [term.casefold() for term in _TOKEN.findall(text)]
        features = terms + [f"{left}_{right}" for left, right in zip(terms, terms[1:])]
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings: list[list[float]] = []
        for offset in range(0, len(texts), 128):
            batch = texts[offset : offset + 128]
            kwargs: dict[str, object] = {"model": self.model, "input": batch}
            if self.model.startswith("text-embedding-3"):
                kwargs["dimensions"] = self.dimensions
            response = await self.client.embeddings.create(**kwargs)
            ordered = sorted(response.data, key=lambda item: item.index)
            embeddings.extend(item.embedding for item in ordered)
        return embeddings

    async def aclose(self) -> None:
        await self.client.close()


@lru_cache
def get_embedder() -> EmbeddingAdapter:
    settings = get_settings()
    if settings.embedding_provider == "local":
        return LocalHashEmbedder(settings.embedding_dimensions)
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI embedding provider")
        return OpenAIEmbedder(
            settings.openai_api_key,
            settings.embedding_model,
            settings.embedding_dimensions,
        )
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


async def close_embedder() -> None:
    await get_embedder().aclose()
    get_embedder.cache_clear()
