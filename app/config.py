import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Enterprise Multi-Agent IT Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Knowledge Base & Storage
    KB_FILE_PATH: str = str(BASE_DIR / "data" / "company_kb.txt")
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "it_support_kb"

    # Chunking: Sliced into chunks of 250 characters as specified in PRD
    CHUNK_SIZE: int = 250
    CHUNK_OVERLAP: int = 25

    # LLM Settings (OpenAI)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Security Guardrail Settings
    IP_REDACTION_TOKEN: str = "[REDACTED IP]"

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
