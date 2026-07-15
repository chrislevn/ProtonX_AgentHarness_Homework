"""
Vector Store Service - Qdrant for agent long-term memory.
"""

import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import QDRANT_HOST, QDRANT_PORT, MEMORY_COLLECTION, EMBEDDING_DIM

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collection():
    """Ensure the Qdrant collection exists."""
    collections = [c.name for c in client.get_collections().collections]
    if MEMORY_COLLECTION not in collections:
        client.create_collection(
            collection_name=MEMORY_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def save_memory(text: str, embedding: list[float], metadata: dict = None):
    """Save a single memory entry to the vector store."""
    ensure_collection()
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={"text": text, "metadata": metadata or {}},
    )
    client.upsert(collection_name=MEMORY_COLLECTION, points=[point])


def search_memory(query_vector: list[float], top_k: int = 5) -> list[dict]:
    """Search memory by semantic similarity."""
    ensure_collection()
    results = client.query_points(
        collection_name=MEMORY_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "text": point.payload.get("text", ""),
            "score": point.score,
            "metadata": point.payload.get("metadata", {}),
        }
        for point in results.points
    ]


def list_all_memories(limit: int = 100) -> list[dict]:
    """List all stored memories."""
    ensure_collection()
    points, _ = client.scroll(
        collection_name=MEMORY_COLLECTION,
        limit=limit,
        with_payload=True,
    )
    return [
        {
            "id": str(point.id),
            "text": point.payload.get("text", ""),
            "metadata": point.payload.get("metadata", {}),
        }
        for point in points
    ]
