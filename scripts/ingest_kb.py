#!/usr/bin/env python3
"""
CLI Script: Ingest and inspect Knowledge Base into ChromaDB.
"""
import sys
import os
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.kb.vector_store import vector_store_manager, chunk_text_by_chars


def main():
    kb_path = settings.KB_FILE_PATH
    print("=" * 70)
    print("  Enterprise Multi-Agent IT Assistant - KB Ingestion CLI")
    print("=" * 70)
    print(f"Target Knowledge Base: {kb_path}")
    print(f"ChromaDB Persist Directory: {settings.CHROMA_PERSIST_DIR}")
    print(f"Configured Chunk Size: {settings.CHUNK_SIZE} characters")
    print(f"Configured Chunk Overlap: {settings.CHUNK_OVERLAP} characters")
    print("-" * 70)

    if not os.path.exists(kb_path):
        print(f"ERROR: Knowledge base file not found at {kb_path}")
        sys.exit(1)

    with open(kb_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_text_by_chars(content, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
    print(f"Raw Document Length: {len(content)} characters")
    print(f"Generated Chunks: {len(chunks)} chunks of <= {settings.CHUNK_SIZE} characters\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk #{i} ({len(chunk)} chars) ---")
        print(chunk)
        print()

    print("-" * 70)
    print("Indexing chunks into ChromaDB...")
    indexed_count = vector_store_manager.ingest_text_file(kb_path)
    print(f"[OK] Successfully indexed {indexed_count} chunks into ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}'!")
    print("=" * 70)


if __name__ == "__main__":
    main()
