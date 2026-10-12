import json
import logging
import re
from typing import Dict, Any
from app.state import AgentState
from app.llm_client import llm_client

logger = logging.getLogger(__name__)

ACTION_SYSTEM_PROMPT = """You are an Enterprise IT Ticket Escalation Agent.
Your job is to parse the employee's request and construct a machine-readable JSON IT ticket payload.
You DO NOT read external documentation; you extract details strictly from the user's query.

You must return a valid JSON object with the following schema:
{
  "ticket_type": "<Category>",
  "priority": "<Priority>",
  "description": "<Concise summary of the reported issue>",
  "suggested_action": "<Operational resolution step>"
}

Valid Categories for ticket_type:
- Hardware_Repair (e.g., broken screen, damaged keyboard, faulty monitor, defective battery)
- Network_Access_Reset (e.g., VPN failure, Wi-Fi connectivity, DNS errors)
- Software_Access_Request (e.g., application installation, license request)
- Account_Support (e.g., password locked, MFA reset)
- General_IT_Escalation (e.g., other issues)

Valid Priorities:
- Critical (System down, business stopping)
- High (Hardware damaged, cannot work, VPN failure)
- Medium (Software access request, standard issue)
- Low (Non-urgent cosmetic or general inquiry)

STRICT RULE:
Output ONLY valid, parseable JSON. Do not include markdown code blocks or conversational text."""


class ActionAgent:
    """
    Agent 3: Escalation Action Agent
    Bypasses vector retrieval and constructs structured JSON payloads for the IT service desk.
    """
    def __init__(self, client=None):
        self.llm = client or llm_client

    def execute(self, state: AgentState) -> AgentState:
        query = state.query
        prompt = f"User Issue: {query}\nGenerate structured JSON IT ticket payload:"

        raw_output = self.llm.generate(
            prompt=prompt,
            system_prompt=ACTION_SYSTEM_PROMPT,
            temperature=0.0
        )

        ticket_data = self._parse_json(raw_output, query)
        state.draft_response = ticket_data
        state.log_step(f"Pipeline 4 (Action Agent): Bypassed Vector DB and generated ticket payload for type '{ticket_data.get('ticket_type')}'")
        logger.info(f"ActionAgent generated ticket payload: {ticket_data}")
        return state

    def _parse_json(self, raw_output: str, original_query: str) -> Dict[str, Any]:
        """
        Safely extracts JSON from LLM output, with resilient fallback.
        """
        # Strip potential markdown fences
        cleaned = re.sub(r"```json\s*", "", raw_output)
        cleaned = re.sub(r"```\s*", "", cleaned).strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "ticket_type" in parsed:
                return parsed
        except Exception:
            pass

        # Resilient fallback extraction
        ticket_type = "General_IT_Escalation"
        priority = "Medium"
        lower_q = original_query.lower()

        if any(w in lower_q for w in ["screen", "monitor", "laptop", "keyboard", "mouse", "hardware"]):
            ticket_type = "Hardware_Repair"
            priority = "High"
        elif any(w in lower_q for w in ["vpn", "network", "wifi", "internet"]):
            ticket_type = "Network_Access_Reset"
            priority = "High"
        elif any(w in lower_q for w in ["access", "permission", "software", "license"]):
            ticket_type = "Software_Access_Request"
            priority = "Medium"
        elif any(w in lower_q for w in ["password", "account", "login", "locked"]):
            ticket_type = "Account_Support"
            priority = "High"

        return {
            "ticket_type": ticket_type,
            "priority": priority,
            "description": original_query,
            "suggested_action": f"Escalate {ticket_type} to Level-2 IT support"
        }
