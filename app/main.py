import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.state import ChatRequest, ChatResponse
from app.pipeline import orchestrator
from app.kb.vector_store import vector_store_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("enterprise_it_assistant")


def ensure_kb_initialized():
    """
    Ensures that the knowledge base is loaded into ChromaDB.
    """
    try:
        count = vector_store_manager.collection.count()
        if count == 0:
            logger.info("ChromaDB collection is empty. Ingesting company_kb.txt...")
            vector_store_manager.ingest_text_file(settings.KB_FILE_PATH)
    except Exception as e:
        logger.warning(f"Could not auto-ingest knowledge base: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup & shutdown events.
    On startup, automatically loads and embeds company_kb.txt if collection is empty.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    ensure_kb_initialized()
    yield
    logger.info("Shutting down Enterprise IT Assistant service.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Autonomous Multi-Agent Enterprise IT Assistant using Router Pattern, "
        "ChromaDB RAG, Action Automation, and Regex Security Guardrails."
    ),
    lifespan=lifespan
)

# Enable CORS for web portals and internal intranet tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def root():
    """
    Root status and system overview.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "pipelines": [
            "Pipeline 1: FastAPI Serving Layer",
            "Pipeline 2: Intent Router Agent (Action vs Info)",
            "Pipeline 3: Knowledge RAG Agent (ChromaDB)",
            "Pipeline 4: Escalation Action Agent (JSON Payload)",
            "Pipeline 5: Security Guardrail (IP Redaction)"
        ]
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for Kubernetes, Docker, or monitoring probes.
    """
    try:
        kb_count = vector_store_manager.collection.count()
        return {
            "status": "healthy",
            "vector_store_chunks": kb_count,
            "openai_configured": bool(settings.OPENAI_API_KEY)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse, tags=["IT Assistant"])
async def chat(request: ChatRequest):
    """
    Pipeline 1 Entrypoint:
    Receives employee query, validates data with Pydantic, triggers multi-agent pipeline,
    and returns sanitized, redacted response.
    """
    try:
        ensure_kb_initialized()
        state = await orchestrator.run(query=request.query)

        return ChatResponse(
            query=state.query,
            intent=state.intent or "unknown",
            route=state.route or "unknown",
            response=state.final_response,
            redacted=state.redacted,
            redactions_count=state.redactions_count,
            execution_log=state.execution_log
        )
    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal pipeline error: {str(e)}"
        )


@app.post("/ingest", tags=["Knowledge Base"])
async def reindex_knowledge_base():
    """
    Re-ingests company_kb.txt into ChromaDB on demand.
    """
    try:
        num_chunks = vector_store_manager.ingest_text_file(settings.KB_FILE_PATH)
        return {
            "status": "success",
            "message": f"Successfully indexed {num_chunks} chunks into ChromaDB.",
            "source_file": settings.KB_FILE_PATH
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest knowledge base: {str(e)}"
        )
