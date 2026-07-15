"""
Embedding Service - Uses OpenAI text-embedding-3-small.
"""

import os
from openai import OpenAI
from config import EMBEDDING_MODEL

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into vectors."""
    response = _get_client().embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    """Embed a single query text."""
    return embed_texts([query])[0]
