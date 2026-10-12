import logging
from typing import Optional
from app.state import AgentState
from app.agents.router_agent import RouterAgent
from app.agents.rag_agent import RAGAgent
from app.agents.action_agent import ActionAgent
from app.agents.security_agent import SecurityAgent

logger = logging.getLogger(__name__)


class MultiAgentITPipeline:
    """
    End-to-end Orchestrator for the Enterprise IT Assistant.
    Coordinates the 5 technical pipelines:
      Pipeline 1: State Initialization & API Contract
      Pipeline 2: Intent Router Agent (Action vs Info)
      Pipeline 3: Knowledge RAG Agent (ChromaDB similarity search)
      Pipeline 4: Escalation Action Agent (JSON Ticket generator)
      Pipeline 5: Security Guardrail Agent (Regex redaction of internal IPs)
    """
    def __init__(
        self,
        router_agent: Optional[RouterAgent] = None,
        rag_agent: Optional[RAGAgent] = None,
        action_agent: Optional[ActionAgent] = None,
        security_agent: Optional[SecurityAgent] = None
    ):
        self.router = router_agent or RouterAgent()
        self.rag = rag_agent or RAGAgent()
        self.action = action_agent or ActionAgent()
        self.security = security_agent or SecurityAgent()

    async def run(self, query: str) -> AgentState:
        """
        Executes the 5-pipeline lifecycle asynchronously.
        """
        # Pipeline 1: State Initialization (Memory Block)
        state = AgentState(query=query)

        # Pipeline 2: Router Agent (Intent Classification)
        state = self.router.route(state)

        # Conditional Branching: Pipeline 3 vs Pipeline 4
        if state.intent == "info":
            # Pipeline 3: Knowledge RAG Pipeline
            state = self.rag.execute(state)
        elif state.intent == "action":
            # Pipeline 4: Escalation Action Pipeline (bypasses DB)
            state = self.action.execute(state)
        else:
            # Fallback if unexpected intent
            state = self.rag.execute(state)

        # Pipeline 5: Validation Guardrail (Security Redaction)
        state = self.security.sanitize(state)

        state.log_step("Pipeline 1: Sanitized response delivered back to client.")
        return state


# Global pipeline instance
orchestrator = MultiAgentITPipeline()
