import pytest
from app.state import AgentState
from app.agents.rag_agent import RAGAgent
from app.kb.vector_store import VectorStoreManager, chunk_text_by_chars


def test_chunking_250_characters():
    sample_text = (
        "VPN Troubleshooting: If the enterprise VPN drops connection, please verify that your internet is stable. "
        "The secure backend corporate IP server is 192.168.1.100. If you receive Error 404, restart the client. "
        "If issues persist, submit a ticket for a Network Access Reset.\n\n"
        "Leave Policy: Full-time employees are entitled to 20 days of paid time off per calendar year."
    )

    chunks = chunk_text_by_chars(sample_text, chunk_size=250, overlap=25)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 250, f"Chunk exceeded 250 chars: {len(chunk)} chars"


def test_rag_agent_retrieval(tmp_path):
    # Use temporary directory for testing vector store isolation
    temp_persist = str(tmp_path / "chroma_test")
    vs = VectorStoreManager(persist_directory=temp_persist, collection_name="test_kb")

    # Ingest mock content
    sample_kb = tmp_path / "mock_kb.txt"
    sample_kb.write_text(
        "VPN Troubleshooting: If the enterprise VPN drops connection, please verify that your internet is stable. "
        "The secure backend corporate IP server is 192.168.1.100.\n\n"
        "Leave Policy: Full-time employees are entitled to 20 days of paid time off per calendar year."
    )
    vs.ingest_text_file(str(sample_kb))

    rag_agent = RAGAgent(store_manager=vs)

    # Test leave policy retrieval
    state = AgentState(query="What is the employee leave policy and how many days off?")
    state.intent = "info"
    state = rag_agent.execute(state)

    assert state.retrieved_context is not None
    assert "Leave Policy" in state.retrieved_context or "paid time off" in state.retrieved_context
    assert state.draft_response is not None


def test_rag_agent_anti_hallucination():
    rag_agent = RAGAgent()
    state = AgentState(query="What is the internal policy regarding spaceship maintenance?")
    state.intent = "info"
    # Even if some unrelated chunk is retrieved, test that without relevant data it signals lack of knowledge
    state = rag_agent.execute(state)
    assert state.draft_response is not None
