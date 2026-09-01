"""RAG (Retrieval-Augmented Generation) engine.

This module handles:
1. Loading knowledge base articles
2. Creating embeddings using sentence-transformers (initialized once on startup)
3. Building a FAISS vector index (built once on startup)
4. Retrieving relevant articles for a given ticket query in milliseconds
"""

import asyncio
import logging
import threading
import time
from typing import TypedDict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.rag.knowledge_base import load_knowledge_base_documents

logger = logging.getLogger(__name__)


class RAGSource(TypedDict):
    """A retrieved knowledge base source."""
    title: str
    category: str
    content_preview: str
    relevance_score: float


# Module-level singletons protected by an initialization lock
_vector_store: FAISS | None = None
_embeddings: HuggingFaceEmbeddings | None = None
_init_lock = threading.Lock()
_is_initialized: bool = False


def initialize_rag() -> bool:
    """Initialize the embedding model and FAISS vector store once per process.

    This function is thread-safe and idempotent. It should be called during
    FastAPI lifespan startup to ensure zero request-time initialization latency.
    """
    global _embeddings, _vector_store, _is_initialized

    if _is_initialized and _vector_store is not None and _embeddings is not None:
        return True

    with _init_lock:
        if _is_initialized and _vector_store is not None and _embeddings is not None:
            return True

        init_start = time.perf_counter()
        logger.info("Initializing RAG engine (embedding model and FAISS vector store)...")

        # 1. Load SentenceTransformer Embeddings Model (Singleton)
        try:
            emb_start = time.perf_counter()
            logger.info("Loading embedding model: all-MiniLM-L6-v2 ...")
            _embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            emb_duration = time.perf_counter() - emb_start
            logger.info(f"Embedding model initialized successfully in {emb_duration:.2f} seconds.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return False

        # 2. Load Knowledge Base Documents
        try:
            articles = load_knowledge_base_documents()
            if not articles:
                logger.warning("No knowledge base documents found.")
                _is_initialized = True
                return False

            # 3. Split into Chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", " ", ""],
            )

            documents: list[Document] = []
            for article in articles:
                chunks = text_splitter.split_text(article.page_content)
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "id": article.metadata["id"],
                            "title": article.metadata["title"],
                            "category": article.metadata["category"],
                            "chunk_index": i,
                        },
                    )
                    documents.append(doc)

            logger.info(f"Created {len(documents)} document chunks from {len(articles)} articles.")

            # 4. Build FAISS Index with Max Inner Product Strategy (Cosine Similarity for normalized vectors)
            faiss_start = time.perf_counter()
            logger.info("Building FAISS vector store from knowledge base...")
            _vector_store = FAISS.from_documents(
                documents,
                _embeddings,
                distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
            )
            faiss_duration = time.perf_counter() - faiss_start
            logger.info(f"FAISS vector store initialized successfully in {faiss_duration:.2f} seconds.")

            total_duration = time.perf_counter() - init_start
            logger.info(f"RAG initialization completed in {total_duration:.2f} seconds.")
            _is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to build FAISS vector store: {e}")
            return False


async def async_initialize_rag() -> bool:
    """Async helper to run CPU-bound RAG initialization in a separate thread."""
    return await asyncio.to_thread(initialize_rag)


def get_embeddings() -> HuggingFaceEmbeddings:
    """Get the shared embedding model instance, initializing if not already loaded."""
    global _embeddings
    if _embeddings is None:
        initialize_rag()
    if _embeddings is None:
        raise RuntimeError("Embedding model failed to initialize.")
    return _embeddings


def get_vector_store() -> FAISS | None:
    """Get the singleton FAISS vector store, initializing if not already loaded."""
    global _vector_store
    if _vector_store is None:
        initialize_rag()
    return _vector_store


async def retrieve_relevant_articles(
    query: str,
    top_k: int = 3,
    score_threshold: float = 0.3,
) -> list[RAGSource]:
    """Retrieve the most relevant knowledge base articles for a query using the pre-loaded FAISS index.

    Args:
        query: The search query (typically ticket title + description).
        top_k: Maximum number of results to return.
        score_threshold: Minimum relevance score (0-1, higher = more relevant).

    Returns:
        List of RAGSource dicts with title, category, content preview, and score.
    """
    start_time = time.perf_counter()
    try:
        store = get_vector_store()
        if store is None:
            logger.warning("RAG vector store is unavailable. Skipping article retrieval.")
            return []

        # Run fast in-memory similarity search (MAX_INNER_PRODUCT returns exact cosine similarity)
        results = store.similarity_search_with_score(query, k=top_k)

        sources: list[RAGSource] = []
        seen_titles: set[str] = set()

        for doc, score in results:
            score_val = float(score)
            if score_val < score_threshold:
                continue

            title = doc.metadata.get("title", "Unknown")

            # Deduplicate: only include each article once
            if title in seen_titles:
                continue
            seen_titles.add(title)

            sources.append(
                RAGSource(
                    title=title,
                    category=doc.metadata.get("category", ""),
                    content_preview=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    relevance_score=round(score_val, 3),
                )
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"RAG retrieval took {duration_ms:.2f} ms (found {len(sources)} relevant sources).")
        return sources

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []


async def retrieve_context_for_reply(query: str, top_k: int = 3) -> str:
    """Retrieve relevant KB content as a formatted context string for the LLM.

    Args:
        query: The ticket title + description.
        top_k: Number of relevant chunks to retrieve.

    Returns:
        A formatted string of relevant knowledge base content.
    """
    start_time = time.perf_counter()
    try:
        store = get_vector_store()
        if store is None:
            return ""

        results = store.similarity_search_with_score(query, k=top_k)
        if not results:
            return ""

        context_parts: list[str] = []
        for doc, score in results:
            if float(score) < 0.3:
                continue
            title = doc.metadata.get("title", "Unknown")
            context_parts.append(
                f"--- Knowledge Base: {title} ---\n{doc.page_content}"
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"RAG context retrieval took {duration_ms:.2f} ms.")
        return "\n\n".join(context_parts)

    except Exception as e:
        logger.error(f"RAG context retrieval failed: {e}")
        return ""


