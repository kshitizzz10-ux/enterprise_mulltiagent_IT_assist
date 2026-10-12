from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class AgentState(dict):
    """
    State Dictionary (Memory Block)
    Maintains the state across the 5 pipelines:
    - query: Original employee query
    - intent: 'action' or 'info' (Router Agent)
    - route: Target pipeline name
    - retrieved_context: Relevant chunks fetched from ChromaDB (RAG Agent)
    - draft_response: Unsanitized generated response (RAG or Action Agent)
    - final_response: Sanitized response (Security Agent)
    - redacted: Boolean flag indicating if sensitive data was scrubbed
    - redactions_count: Number of redactions made
    - execution_log: Sequential audit trail of agent steps
    """
    def __init__(self, query: str):
        super().__init__({
            "query": query,
            "intent": None,
            "route": None,
            "retrieved_context": None,
            "draft_response": None,
            "final_response": None,
            "redacted": False,
            "redactions_count": 0,
            "execution_log": [f"Pipeline 1: State Initialized for query '{query}'"]
        })

    @property
    def query(self) -> str:
        return self["query"]

    @property
    def intent(self) -> Optional[str]:
        return self["intent"]

    @intent.setter
    def intent(self, val: str):
        self["intent"] = val

    @property
    def route(self) -> Optional[str]:
        return self["route"]

    @route.setter
    def route(self, val: str):
        self["route"] = val

    @property
    def retrieved_context(self) -> Optional[str]:
        return self["retrieved_context"]

    @retrieved_context.setter
    def retrieved_context(self, val: str):
        self["retrieved_context"] = val

    @property
    def draft_response(self) -> Optional[Any]:
        return self["draft_response"]

    @draft_response.setter
    def draft_response(self, val: Any):
        self["draft_response"] = val

    @property
    def final_response(self) -> Optional[Any]:
        return self["final_response"]

    @final_response.setter
    def final_response(self, val: Any):
        self["final_response"] = val

    @property
    def redacted(self) -> bool:
        return self["redacted"]

    @redacted.setter
    def redacted(self, val: bool):
        self["redacted"] = val

    @property
    def redactions_count(self) -> int:
        return self["redactions_count"]

    @redactions_count.setter
    def redactions_count(self, val: int):
        self["redactions_count"] = val

    @property
    def execution_log(self) -> List[str]:
        return self["execution_log"]

    def log_step(self, message: str):
        self["execution_log"].append(message)


# ============================================================================
# Pydantic Schemas for API Serialization & Validation
# ============================================================================

class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="The employee's natural language query or support request",
        examples=["My screen is broken, open a ticket.", "What is the company leave policy?"]
    )


class ITTicket(BaseModel):
    ticket_type: str = Field(
        ...,
        description="Classified ticket category, e.g., Hardware_Repair, Network_Access_Reset, Software_Access_Request"
    )
    priority: str = Field(
        ...,
        description="Priority level: Critical, High, Medium, or Low"
    )
    description: str = Field(
        ...,
        description="Summary of the issue extracted from the user query"
    )
    suggested_action: str = Field(
        ...,
        description="Recommended next operational action for the IT service desk"
    )


class ChatResponse(BaseModel):
    query: str
    intent: str
    route: str
    response: Any
    redacted: bool
    redactions_count: int
    execution_log: List[str]
