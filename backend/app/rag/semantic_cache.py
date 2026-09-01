import logging
from typing import Any
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from app.rag.engine import get_embeddings

logger = logging.getLogger(__name__)


def get_cache_embeddings() -> HuggingFaceEmbeddings:
    """Get the shared embedding model singleton from the RAG engine."""
    return get_embeddings()


class SemanticVectorCache:
    """Vector similarity cache for query deduplication.
    
    If an incoming query embedding matches a cached query embedding with
    similarity >= similarity_threshold, the cached category, priority, and
    draft reply are reused with 0 LLM token cost.
    """

    def __init__(self, similarity_threshold: float = 0.88):
        self.similarity_threshold = similarity_threshold
        # List of dicts: {"query": str, "embedding": np.ndarray, "response": dict}
        self._cache: list[dict[str, Any]] = []

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get(self, query: str) -> dict[str, Any] | None:
        """Check semantic cache for similar query.
        
        Returns:
            Cached response dict if similarity >= threshold, else None.
        """
        if not self._cache:
            return None

        try:
            embeddings_model = get_cache_embeddings()
            query_vec = np.array(embeddings_model.embed_query(query), dtype=np.float32)

            best_score = 0.0
            best_response = None

            for entry in self._cache:
                score = self._cosine_similarity(query_vec, entry["embedding"])
                if score > best_score:
                    best_score = score
                    best_response = entry["response"]

            if best_score >= self.similarity_threshold and best_response:
                logger.info(f"⚡ Semantic Cache HIT! Similarity: {best_score:.4f} >= {self.similarity_threshold}")
                return best_response

            logger.info(f"Semantic Cache MISS. Best similarity: {best_score:.4f}")
            return None

        except Exception as e:
            logger.error(f"Semantic cache lookup failed: {e}")
            return None

    def set(self, query: str, response: dict[str, Any]):
        """Store query embedding and response pair in semantic cache."""
        try:
            embeddings_model = get_cache_embeddings()
            query_vec = np.array(embeddings_model.embed_query(query), dtype=np.float32)
            self._cache.append({
                "query": query,
                "embedding": query_vec,
                "response": response
            })
            logger.info(f"Cached semantic vector entry. Total cached: {len(self._cache)}")
        except Exception as e:
            logger.error(f"Failed to cache semantic entry: {e}")

# Global singleton instance
semantic_cache = SemanticVectorCache(similarity_threshold=0.88)
