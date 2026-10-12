import logging
from typing import Literal
from app.state import AgentState
from app.llm_client import llm_client

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """You are an expert IT Service Desk Intent Router.
Your job is to analyze the employee's query and classify their intent into exactly ONE of two words:
1. info
2. action

Definitions:
- 'info': The employee is asking a question, inquiring about company policy, looking for instructions, asking how something works, or requesting factual clarification (e.g., "What is the VPN server IP?", "What is our leave policy?", "How many PTO days do I have?").
- 'action': The employee is requesting a fix, reporting a broken device/issue, demanding an escalation, asking for ticket creation, or requesting direct operational assistance (e.g., "My screen is broken, open a ticket.", "Please reset my VPN connection.", "I need a replacement keyboard.").

STRICT INSTRUCTION:
You MUST reply with ONLY the single word 'action' or 'info'. Do NOT provide any punctuation, reasoning, or additional words."""


class RouterAgent:
    """
    Agent 1: Semantic Intent Router
    Evaluates natural language and classifies user intent into 'info' or 'action'
    without relying on brittle keyword matching.
    """
    def __init__(self, client=None):
        self.llm = client or llm_client

    def route(self, state: AgentState) -> AgentState:
        query = state.query
        prompt = f"Employee Query: \"{query}\"\nIntent (reply strictly 'info' or 'action'):"

        raw_output = self.llm.generate(
            prompt=prompt,
            system_prompt=ROUTER_SYSTEM_PROMPT,
            temperature=0.0
        )

        cleaned = raw_output.strip().lower()
        if "action" in cleaned:
            intent = "action"
            route_target = "Pipeline 4: Escalation Pipeline (Action Agent)"
        else:
            intent = "info"
            route_target = "Pipeline 3: Knowledge Pipeline (RAG Agent)"

        state.intent = intent
        state.route = route_target
        state.log_step(f"Pipeline 2 (Router Agent): Classified intent as '{intent}' -> Routed to {route_target}")

        logger.info(f"RouterAgent classified '{query}' as '{intent}'")
        return state
