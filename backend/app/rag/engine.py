"""RAG (Retrieval-Augmented Generation) engine.

This module handles:
1. Loading knowledge base articles
2. Creating embeddings using sentence-transformers
3. Building a FAISS vector index
4. Retrieving relevant articles for a given ticket query
"""

import logging
from typing import TypedDict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
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


# Module-level singleton for the vector store
_vector_store: FAISS | None = None
_embeddings: HuggingFaceEmbeddings | None = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    """Get or create the embeddings model (singleton)."""
    global _embeddings
    if _embeddings is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2 ...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully.")
    return _embeddings


def _build_vector_store() -> FAISS:
    """Build the FAISS vector store from knowledge base articles."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    logger.info("Building FAISS vector store from knowledge base...")

    # Load articles from backend/knowledge_base/*.md (see app/rag/knowledge_base.py)
    articles = load_knowledge_base_documents()

    # Split long articles into smaller chunks for better retrieval
    documents: list[Document] = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

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

    embeddings = _get_embeddings()
    _vector_store = FAISS.from_documents(documents, embeddings)
    logger.info("FAISS vector store built successfully.")

    return _vector_store


def get_vector_store() -> FAISS:
    """Get the FAISS vector store, building it if necessary."""
    return _build_vector_store()


async def retrieve_relevant_articles(
    query: str,
    top_k: int = 3,
    score_threshold: float = 0.3,
) -> list[RAGSource]:
    """Retrieve the most relevant knowledge base articles for a query.

    Args:
        query: The search query (typically ticket title + description).
        top_k: Maximum number of results to return.
        score_threshold: Minimum relevance score (0-1, higher = more relevant).

    Returns:
        List of RAGSource dicts with title, category, content preview, and score.
    """
    try:
        store = get_vector_store()

        # similarity_search_with_score returns (doc, distance)
        # Lower distance = more similar for L2, but FAISS with normalized
        # embeddings uses inner product, so we need to handle score properly
        results = store.similarity_search_with_relevance_scores(query, k=top_k)

        sources: list[RAGSource] = []
        seen_titles: set[str] = set()

        for doc, score in results:
            if score < score_threshold:
                continue

            title = doc.metadata.get("title", "Unknown")

            # Deduplicate: only include each article once (even if multiple chunks match)
            if title in seen_titles:
                continue
            seen_titles.add(title)

            sources.append(
                RAGSource(
                    title=title,
                    category=doc.metadata.get("category", ""),
                    content_preview=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    relevance_score=round(float(score), 3),
                )
            )

        logger.info(f"RAG retrieved {len(sources)} relevant sources for query.")
        return sources

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []


async def retrieve_context_for_reply(query: str, top_k: int = 3) -> str:
    """Retrieve relevant KB content as a formatted context string for the LLM.

    This returns the full content of relevant chunks, formatted for injection
    into the AI draft reply prompt.

    Args:
        query: The ticket title + description.
        top_k: Number of relevant chunks to retrieve.

    Returns:
        A formatted string of relevant knowledge base content.
    """
    try:
        store = get_vector_store()
        results = store.similarity_search_with_relevance_scores(query, k=top_k)

        if not results:
            return ""

        context_parts: list[str] = []
        for doc, score in results:
            if score < 0.3:
                continue
            title = doc.metadata.get("title", "Unknown")
            context_parts.append(
                f"--- Knowledge Base: {title} ---\n{doc.page_content}"
            )

        return "\n\n".join(context_parts)

    except Exception as e:
        logger.error(f"RAG context retrieval failed: {e}")
        return ""
