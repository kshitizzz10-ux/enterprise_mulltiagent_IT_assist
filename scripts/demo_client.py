#!/usr/bin/env python3
"""
CLI Script: Interactive & Automated Demonstration of the 5 Multi-Agent Pipelines.
"""
import sys
import json
import asyncio
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import orchestrator
from app.kb.vector_store import vector_store_manager
from app.config import settings

DEMO_QUERIES = [
    {
        "title": "Scenario 1: Knowledge RAG Query with Sensitive IP Redaction",
        "query": "What is the secure corporate VPN server IP and troubleshooting steps?",
        "expected_intent": "info",
        "expected_route": "Pipeline 3 (RAG) -> Pipeline 5 (Security Guardrail)"
    },
    {
        "title": "Scenario 2: Action Request - Broken Hardware Escalation",
        "query": "My screen is broken, please open a ticket immediately.",
        "expected_intent": "action",
        "expected_route": "Pipeline 4 (Escalation Action) -> Pipeline 5 (Security Guardrail)"
    },
    {
        "title": "Scenario 3: Company Policy Inquiry (RAG)",
        "query": "What is our leave policy and how many PTO days do full-time employees receive?",
        "expected_intent": "info",
        "expected_route": "Pipeline 3 (RAG) -> Pipeline 5 (Security Guardrail)"
    },
    {
        "title": "Scenario 4: Action Request - VPN Network Access Reset",
        "query": "My VPN keeps dropping connection, reset my network access and raise a ticket.",
        "expected_intent": "action",
        "expected_route": "Pipeline 4 (Escalation Action) -> Pipeline 5 (Security Guardrail)"
    },
    {
        "title": "Scenario 5: Out-of-Scope Query (Anti-Hallucination Guardrail)",
        "query": "What is the company stock purchase plan and discount rate?",
        "expected_intent": "info",
        "expected_route": "Pipeline 3 (RAG) -> Strictly 'do not know'"
    }
]


async def run_demo():
    print("=" * 80)
    print("      ENTERPRISE MULTI-AGENT IT ASSISTANT - INTERACTIVE PIPELINE DEMO")
    print("=" * 80)

    # Ensure KB is loaded
    print("\n[Setup] Ensuring ChromaDB knowledge base is populated...")
    vector_store_manager.ingest_text_file(settings.KB_FILE_PATH)
    total_chunks = vector_store_manager.collection.count()
    print(f"[Setup] ChromaDB ready with {total_chunks} indexed 250-character chunks.\n")

    for i, test_case in enumerate(DEMO_QUERIES, 1):
        print("=" * 80)
        print(f"TEST {i}: {test_case['title']}")
        print(f"Target Route: {test_case['expected_route']}")
        print(f"Employee Query: \"{test_case['query']}\"")
        print("-" * 80)

        state = await orchestrator.run(query=test_case["query"])

        print(f"-> Classified Intent : {state.intent.upper()}")
        print(f"-> Active Route       : {state.route}")
        print(f"-> Redaction Applied  : {state.redacted} ({state.redactions_count} pattern(s) sanitized)")

        print("\n[Execution Pipeline Audit Trail]")
        for log in state.execution_log:
            print(f"   * {log}")

        print("\n[Final Sanitized Response]")
        if isinstance(state.final_response, dict):
            print(json.dumps(state.final_response, indent=2))
        else:
            print(state.final_response)
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
