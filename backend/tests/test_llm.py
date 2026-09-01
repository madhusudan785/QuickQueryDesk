import pytest
from unittest.mock import patch, MagicMock
from app.services.llm import (
    _parse_classification,
    _create_fallback_draft,
    classify_ticket,
    generate_draft_reply_ext,
)
from app.rag.engine import retrieve_relevant_articles
from app.schemas.ticket import TicketCreate


def test_parse_classification_valid():
    """Test that valid JSON classification is parsed correctly."""
    raw = '{"category": "IT", "priority": "High"}'
    result = _parse_classification(raw)
    assert result["category"] == "IT"
    assert result["priority"] == "High"
    assert result["status"] == "CLASSIFIED"


def test_parse_classification_markdown():
    """Test that markdown code blocks are stripped from JSON."""
    raw = '```json\n{"category": "HR", "priority": "Low"}\n```'
    result = _parse_classification(raw)
    assert result["category"] == "HR"
    assert result["priority"] == "Low"
    assert result["status"] == "CLASSIFIED"


def test_parse_classification_fallback():
    """Test fallback to defaults when LLM output is invalid."""
    raw = "This is not JSON"
    result = _parse_classification(raw)
    assert result["category"] == "Other"
    assert result["priority"] == "Medium"
    assert result["is_fallback"] is True
    assert result["status"] == "CLASSIFICATION_FAILED"


@pytest.mark.asyncio
async def test_retrieve_relevant_articles_serialization():
    """Test that RAG engine returns native floats that are JSON serializable and scores are in [0, 1]."""
    import json
    sources = await retrieve_relevant_articles("VPN connection issue", top_k=2)
    if sources:
        json_str = json.dumps([dict(s) for s in sources])
        assert isinstance(json_str, str)
        assert "relevance_score" in json_str
        for s in sources:
            assert 0.0 <= s["relevance_score"] <= 1.0


def test_create_fallback_draft_with_and_without_rag():
    """Test fallback draft creation both with RAG context and without RAG context."""
    # With RAG context
    draft_with_rag = _create_fallback_draft("VPN Issue", "Cannot connect", "VPN Guide Content")
    assert "VPN Guide Content" in draft_with_rag
    assert "Based on our Knowledge Base" in draft_with_rag

    # Without RAG context
    draft_no_rag = _create_fallback_draft("VPN Issue", "Cannot connect", "")
    assert 'regarding "VPN Issue"' in draft_no_rag
    assert "Our support team has received your request" in draft_no_rag


@pytest.mark.asyncio
async def test_classify_ticket_success():
    """Test successful LLM classification mock."""
    with patch("app.services.llm.get_settings") as mock_settings, patch("app.services.llm._sync_call_llm_classification") as mock_call:
        mock_settings.return_value.LLM_API_KEY = "gsk_test_key"
        mock_settings.return_value.LLM_MODEL = "groq/compound-mini"
        mock_call.return_value = '{"category": "IT", "priority": "High"}'
        res = await classify_ticket("VPN down", "Cannot connect to VPN")
        assert res["category"] == "IT"
        assert res["priority"] == "High"
        assert res["is_fallback"] is False
        assert res["status"] == "CLASSIFIED"


@pytest.mark.asyncio
async def test_classify_ticket_failure_fallback():
    """Test LLM classification failure falls back gracefully to defaults without throwing exceptions."""
    with patch("app.services.llm._sync_call_llm_classification") as mock_call:
        mock_call.side_effect = Exception("403 Access Denied")
        res = await classify_ticket("VPN down", "Cannot connect to VPN")
        assert res["category"] == "Other"
        assert res["priority"] == "Medium"
        assert res["is_fallback"] is True
        assert res["status"] == "CLASSIFICATION_FAILED"


@pytest.mark.asyncio
async def test_generate_draft_reply_ext_llm_success():
    """Test successful LLM draft generation mock."""
    with patch("app.services.llm.get_settings") as mock_settings, patch("app.services.llm._sync_call_llm_draft") as mock_draft:
        mock_settings.return_value.LLM_API_KEY = "gsk_test_key"
        mock_settings.return_value.LLM_MODEL = "groq/compound-mini"
        mock_draft.return_value = "Hi, 1. Open GlobalProtect. 2. Click Connect."
        draft, status = await generate_draft_reply_ext("VPN down", "Cannot connect to VPN", "IT", "High")
        assert "GlobalProtect" in draft
        assert status == "COMPLETED"


@pytest.mark.asyncio
async def test_generate_draft_reply_ext_llm_failure_fallback():
    """Test LLM draft generation failure generates a high-quality fallback draft response."""
    with patch("app.services.llm._sync_call_llm_draft") as mock_draft:
        mock_draft.side_effect = Exception("API connection error")
        draft, status = await generate_draft_reply_ext("Cannot connect to VPN", "Timeout error when connecting", "IT", "High")
        assert len(draft) > 0
        assert "VPN" in draft or "support ticket" in draft
        assert status == "COMPLETED_FALLBACK"


def test_ticket_strict_validation():
    """Test that pydantic strict validation works."""
    from pydantic import ValidationError

    ticket = TicketCreate(title="Test", description="Test desc")
    assert ticket.title == "Test"

    with pytest.raises(ValidationError):
        TicketCreate(title="Test", description="Desc", extra_field="hacker")


def test_rag_initialization_singleton_reuse():
    """Test that RAG initialization is idempotent and reuses singletons."""
    from app.rag.engine import initialize_rag, get_embeddings, get_vector_store
    from app.rag.semantic_cache import get_cache_embeddings

    success = initialize_rag()
    assert success is True

    emb1 = get_embeddings()
    store1 = get_vector_store()

    success2 = initialize_rag()
    assert success2 is True

    emb2 = get_embeddings()
    store2 = get_vector_store()

    assert emb1 is emb2, "Embeddings instance must be a singleton"
    assert store1 is store2, "Vector store instance must be a singleton"

    cache_emb = get_cache_embeddings()
    assert cache_emb is emb1, "Semantic cache must share the RAG embedding model"


def test_sensitive_data_filter_redacts_tokens():
    """Test that SensitiveDataFilter masks JWT tokens from log records."""
    from app.main import SensitiveDataFilter

    log_filter = SensitiveDataFilter()
    record = MagicMock()
    record.msg = 'GET /ws/agent?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.xyz HTTP/1.1'

    log_filter.filter(record)
    assert "token=[REDACTED]" in record.msg
    assert "eyJhbGciOiJIUzI1Ni" not in record.msg
