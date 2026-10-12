import pytest
from app.state import AgentState, ITTicket
from app.agents.action_agent import ActionAgent


def test_action_agent_generates_valid_ticket_json():
    agent = ActionAgent()
    state = AgentState(query="My screen is broken, please open a ticket.")
    state.intent = "action"

    state = agent.execute(state)

    assert state.draft_response is not None
    assert isinstance(state.draft_response, dict)
    assert "ticket_type" in state.draft_response
    assert "priority" in state.draft_response
    assert "description" in state.draft_response
    assert "suggested_action" in state.draft_response

    # Verify Pydantic ITTicket schema validation
    validated = ITTicket(**state.draft_response)
    assert validated.ticket_type == "Hardware_Repair"
    assert validated.priority in ["Critical", "High", "Medium", "Low"]


def test_action_agent_network_ticket():
    agent = ActionAgent()
    state = AgentState(query="My VPN connection failed and I need a network access reset.")
    state.intent = "action"

    state = agent.execute(state)
    payload = state.draft_response
    assert payload["ticket_type"] == "Network_Access_Reset"
