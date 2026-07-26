"""Build the FAISS index from the READMEs in docs/.

Usage:
    python ingest.py [--docs-dir docs] [--index-dir index]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag.chunking import load_and_chunk
from rag.embeddings import SentenceTransformerEmbedder
from rag.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    args = parser.parse_args()

    doc_paths = sorted(args.docs_dir.glob("*.md"))
    if not doc_paths:
        raise SystemExit(f"No .md files found in {args.docs_dir}")

    chunks = load_and_chunk(doc_paths)
    print(f"Loaded {len(doc_paths)} documents -> {len(chunks)} chunks:")
    for path in doc_paths:
        n = sum(1 for c in chunks if c.source_file == path.name)
        print(f"  {path.name}: {n} chunks")

    embedder = SentenceTransformerEmbedder()
    store = VectorStore(embedder)
    store.add(chunks)
    store.save(args.index_dir)
    print(f"Index written to {args.index_dir}/ (index.faiss + chunks.json)")


if __name__ == "__main__":
    main()
