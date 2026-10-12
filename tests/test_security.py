import pytest
from app.state import AgentState
from app.agents.security_agent import SecurityAgent


def test_security_agent_redacts_ipv4_in_string():
    agent = SecurityAgent()
    state = AgentState(query="What is the VPN server IP?")
    state.draft_response = (
        "The secure backend corporate IP server is 192.168.1.100. "
        "Also internal gateway is 10.0.0.1 for testing."
    )

    state = agent.sanitize(state)

    assert state.redacted is True
    assert state.redactions_count == 2
    assert "192.168.1.100" not in state.final_response
    assert "10.0.0.1" not in state.final_response
    assert "[REDACTED IP]" in state.final_response


def test_security_agent_redacts_ipv4_in_dict():
    agent = SecurityAgent()
    state = AgentState(query="Server down")
    state.draft_response = {
        "ticket_type": "Network_Access_Reset",
        "description": "Host 172.16.254.1 is unreachable",
        "suggested_action": "Check gateway at 192.168.1.1"
    }

    state = agent.sanitize(state)

    assert state.redacted is True
    assert state.redactions_count == 2
    assert "172.16.254.1" not in state.final_response["description"]
    assert "192.168.1.1" not in state.final_response["suggested_action"]
    assert "[REDACTED IP]" in state.final_response["description"]
    assert "[REDACTED IP]" in state.final_response["suggested_action"]


def test_security_agent_leaves_clean_text_intact():
    agent = SecurityAgent()
    state = AgentState(query="What is the leave policy?")
    clean_text = "Full-time employees are entitled to 20 days of paid time off."
    state.draft_response = clean_text

    state = agent.sanitize(state)

    assert state.redacted is False
    assert state.redactions_count == 0
    assert state.final_response == clean_text
