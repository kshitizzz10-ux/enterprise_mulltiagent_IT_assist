import os
import re
import math
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import settings

logger = logging.getLogger(__name__)


def chunk_text_by_chars(text: str, chunk_size: int = 250, overlap: int = 25) -> List[str]:
    """
    Slices text into chunks of 250 characters as explicitly specified in the PRD.
    Preserves meaningful segment boundaries where possible while strictly capping at chunk_size.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    # Clean redundant whitespaces
    cleaned_text = re.sub(r"\r\n|\r", "\n", cleaned_text)
    paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]

    chunks = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            # Slice into sliding windows of chunk_size characters
            start = 0
            while start < len(para):
                end = min(start + chunk_size, len(para))
                chunk = para[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                if end == len(para):
                    break
                start += chunk_size - overlap

    return chunks


class DeterministicFallbackEmbeddingFunction(EmbeddingFunction):
    """
    Lightweight, deterministic local embedding function.
    Converts text chunks into a 64-dimensional normalized vector using character and token hashing.
    Used when OpenAI is not configured and for offline unit testing without external downloads.
    """
    def __init__(self, dimension: int = 64):
        self.dimension = dimension

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for doc in input:
            vec = [0.0] * self.dimension
            tokens = re.findall(r"\w+", doc.lower())
            if not tokens:
                tokens = [doc.lower()]
            for token in tokens:
                for i, char in enumerate(token):
                    idx = (ord(char) * 31 + i) % self.dimension
                    vec[idx] += 1.0

            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings


class VectorStoreManager:
    """
    Manages ChromaDB persistent vector storage, 250-character chunking,
    embedding generation, and mathematical similarity search.
    """
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        self.embedding_fn = self._init_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "Enterprise IT Policy Knowledge Base"}
        )

    def _init_embedding_function(self):
        """
        Chooses the best available embedding function:
        1. OpenAI Embeddings if OPENAI_API_KEY is available.
        2. ChromaDB default MiniLM embedding if available.
        3. DeterministicFallbackEmbeddingFunction for instant offline operation.
        """
        if settings.OPENAI_API_KEY:
            try:
                from chromadb.utils import embedding_functions
                logger.info("Using OpenAI Embedding Function for ChromaDB.")
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name=settings.OPENAI_EMBEDDING_MODEL
                )
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI embeddings: {e}. Falling back.")

        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            logger.info("Using deterministic fallback embedding function.")
            return DeterministicFallbackEmbeddingFunction()

    def ingest_text_file(self, file_path: Optional[str] = None) -> int:
        """
        Reads company_kb.txt, splits into 250-character chunks, and indexes in ChromaDB.
        """
        target_path = file_path or settings.KB_FILE_PATH
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Knowledge base file not found at: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text_by_chars(
            content,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )

        if not chunks:
            logger.warning("No chunks generated from knowledge base.")
            return 0

        # Create unique IDs and metadata for each chunk
        ids = [f"chunk_{i+1:03d}" for i in range(len(chunks))]
        metadatas = [
            {"source": os.path.basename(target_path), "chunk_index": i, "char_len": len(c)}
            for i, c in enumerate(chunks)
        ]

        # Upsert documents into collection
        self.collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

        logger.info(f"Ingested {len(chunks)} chunks into ChromaDB collection '{self.collection_name}'.")
        return len(chunks)

    def similarity_search(self, query: str, n_results: int = 1) -> List[Dict[str, Any]]:
        """
        Performs mathematical similarity search against ChromaDB.
        Returns closest matching chunk(s).
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        matched_items = []
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)
            metas = results.get("metadatas", [[]])[0] if "metadatas" in results else [{}] * len(docs)

            for i, doc in enumerate(docs):
                matched_items.append({
                    "id": ids[i] if i < len(ids) else f"chunk_{i}",
                    "document": doc,
                    "distance": distances[i] if i < len(distances) else None,
                    "metadata": metas[i] if i < len(metas) else {}
                })

        return matched_items


# Global vector store manager instance
vector_store_manager = VectorStoreManager()
