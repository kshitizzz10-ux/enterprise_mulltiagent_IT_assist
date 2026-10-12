import logging
from typing import Optional
from app.state import AgentState
from app.llm_client import llm_client
from app.kb.vector_store import vector_store_manager

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are an Enterprise IT Knowledge Support Assistant.
Answer the employee's query strictly and truthfully based on the retrieved context below.
Eliminate all AI hallucinations.

STRICT RULE:
If the answer is not in the text, say you do not know.
Do not assume, invent, or speculate about policies or procedures not present in the context."""


class RAGAgent:
    """
    Agent 2: Knowledge Pipeline (RAG Agent)
    Executes when Router intent is 'info'.
    Performs similarity search in ChromaDB, retrieves the closest matching chunk,
    and synthesizes a grounded, hallucination-free answer.
    """
    def __init__(self, client=None, store_manager=None):
        self.llm = client or llm_client
        self.vector_store = store_manager or vector_store_manager

    def execute(self, state: AgentState) -> AgentState:
        query = state.query

        # Step 1: Vector Search against ChromaDB
        search_results = self.vector_store.similarity_search(query=query, n_results=1)

        if not search_results:
            state.retrieved_context = ""
            state.draft_response = "I do not know based on the provided enterprise documentation."
            state.log_step("Pipeline 3 (RAG Agent): No matching context found in ChromaDB.")
            return state

        closest = search_results[0]
        context_text = closest["document"]
        chunk_id = closest.get("id", "unknown")
        distance = closest.get("distance")

        state.retrieved_context = context_text
        state.log_step(
            f"Pipeline 3 (RAG Agent): Retrieved chunk '{chunk_id}' via ChromaDB similarity search (distance: {distance})."
        )

        # Step 2: Generation with strict anti-hallucination constraint
        prompt = (
            f"Context from Enterprise Knowledge Base:\n\"\"\"{context_text}\"\"\"\n\n"
            f"Employee Question: {query}\n\n"
            f"Answer:"
        )

        answer = self.llm.generate(
            prompt=prompt,
            system_prompt=RAG_SYSTEM_PROMPT,
            temperature=0.0
        )

        state.draft_response = answer
        state.log_step("Pipeline 3 (RAG Agent): Synthesized answer strictly from retrieved context.")
        logger.info(f"RAGAgent generated response for '{query}' based on chunk '{chunk_id}'")
        return state
