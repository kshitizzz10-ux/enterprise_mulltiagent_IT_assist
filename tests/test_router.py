import pytest
from app.state import AgentState
from app.agents.router_agent import RouterAgent


def test_router_classifies_info_intent():
    router = RouterAgent()
    queries = [
        "What is the company leave policy?",
        "How many vacation days do full-time employees receive?",
        "Explain how the VPN troubleshooting process works.",
        "What is the internal gateway address for corporate Wi-Fi?"
    ]

    for q in queries:
        state = AgentState(query=q)
        state = router.route(state)
        assert state.intent == "info", f"Expected 'info' for query '{q}', got '{state.intent}'"
        assert "Pipeline 3" in state.route


def test_router_classifies_action_intent():
    router = RouterAgent()
    queries = [
        "My screen is broken, open a ticket.",
        "Please reset my network access immediately.",
        "Replace my damaged laptop keyboard.",
        "My laptop crashed and won't turn on, create an urgent IT ticket."
    ]

    for q in queries:
        state = AgentState(query=q)
        state = router.route(state)
        assert state.intent == "action", f"Expected 'action' for query '{q}', got '{state.intent}'"
        assert "Pipeline 4" in state.route
