import pytest
from app.services.llm import _parse_classification
from app.rag.engine import retrieve_relevant_articles
from app.schemas.ticket import TicketCreate

def test_parse_classification_valid():
    """Test that valid JSON classification is parsed correctly."""
    raw = '{"category": "IT", "priority": "High"}'
    result = _parse_classification(raw)
    assert result["category"] == "IT"
    assert result["priority"] == "High"


def test_parse_classification_markdown():
    """Test that markdown code blocks are stripped from JSON."""
    raw = '```json\n{"category": "HR", "priority": "Low"}\n```'
    result = _parse_classification(raw)
    assert result["category"] == "HR"
    assert result["priority"] == "Low"


def test_parse_classification_fallback():
    """Test fallback to defaults when LLM output is invalid."""
    raw = 'This is not JSON'
    result = _parse_classification(raw)
    assert result["category"] == "Other"
    assert result["priority"] == "Medium"


@pytest.mark.asyncio
async def test_retrieve_relevant_articles_serialization():
    """Test that RAG engine returns native floats that are JSON serializable."""
    import json
    # Use a dummy query
    sources = await retrieve_relevant_articles("VPN connection issue", top_k=1)
    if sources:
        # This will raise TypeError if the float is a numpy.float32
        json_str = json.dumps([dict(s) for s in sources])
        assert isinstance(json_str, str)
        assert "relevance_score" in json_str

def test_ticket_strict_validation():
    """Test that pydantic strict validation works."""
    from pydantic import ValidationError
    
    # Valid ticket
    ticket = TicketCreate(title="Test", description="Test desc")
    assert ticket.title == "Test"
    
    # Extra fields should be forbidden
    with pytest.raises(ValidationError):
        TicketCreate(title="Test", description="Desc", extra_field="hacker")
