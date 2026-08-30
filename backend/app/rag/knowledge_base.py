"""Knowledge base loader.

Loads the organization's knowledge base articles from the markdown files
in backend/knowledge_base/*.md using LangChain's DirectoryLoader, rather
than hard-coding article content in Python. This is the actual document
source the RAG pipeline (app/rag/engine.py) is built from.

Each markdown file is expected to start with a level-1 heading
(`# Article Title`) which is used as the article's display title.
"""

import logging
import re
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# backend/app/rag/knowledge_base.py -> backend/knowledge_base/
KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"

# Filename (without .md) -> category. Matches the category set used by
# ticket classification in app/services/llm.py.
_CATEGORY_MAP = {
    "vpn_setup": "IT",
    "password_reset": "IT",
    "email_configuration": "IT",
    "software_installation": "IT",
    "laptop_request": "IT",
    "employee_id_access": "IT",
    "leave_application": "HR",
    "expense_reimbursement": "Finance",
}
_DEFAULT_CATEGORY = "Other"

_TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _extract_title(text: str, fallback: str) -> str:
    """Pull the first level-1 markdown heading out as the article title."""
    match = _TITLE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return fallback


def load_knowledge_base_documents() -> list[Document]:
    """Load every .md file in backend/knowledge_base/ as a LangChain Document.

    Returns:
        A list of Documents, one per article, each with metadata:
        id, title, category, source_file. Content chunking happens
        downstream in app/rag/engine.py.
    """
    if not KNOWLEDGE_BASE_DIR.is_dir():
        logger.error(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return []

    loader = DirectoryLoader(
        str(KNOWLEDGE_BASE_DIR),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    raw_docs = loader.load()

    documents: list[Document] = []
    for doc in raw_docs:
        source_path = Path(doc.metadata.get("source", ""))
        article_id = source_path.stem  # e.g. "vpn_setup"
        fallback_title = article_id.replace("_", " ").title()
        title = _extract_title(doc.page_content, fallback_title)
        category = _CATEGORY_MAP.get(article_id, _DEFAULT_CATEGORY)

        documents.append(
            Document(
                page_content=doc.page_content,
                metadata={
                    "id": f"kb-{article_id}",
                    "title": title,
                    "category": category,
                    "source_file": source_path.name,
                },
            )
        )

    # Sort for deterministic ordering (DirectoryLoader order can vary by OS).
    documents.sort(key=lambda d: d.metadata["id"])

    logger.info(f"Loaded {len(documents)} knowledge base articles from {KNOWLEDGE_BASE_DIR}")
    return documents
