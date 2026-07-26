"""FAISS vector store: build, persist, load, search.

IndexFlatIP (exact inner-product search) rather than an ANN index like
IVF/HNSW: with ~100 chunks, exact search is microseconds and has zero
recall loss — approximate structures only earn their complexity at
millions of vectors. Vectors are L2-normalized upstream, so inner
product is cosine similarity and scores are directly comparable to the
no-result threshold in the pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .chunking import Chunk
from .embeddings import Embedder


@dataclass
class SearchResult:
    chunk: Chunk
    score: float  # cosine similarity in [-1, 1]


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        import faiss

        self._faiss = faiss
        self.embedder = embedder
        self.index = faiss.IndexFlatIP(embedder.dim)
        self.chunks: list[Chunk] = []

    @staticmethod
    def _embedding_text(chunk: Chunk) -> str:
        return f"{chunk.citation()}: {chunk.text}"

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        vectors = self.embedder.embed([self._embedding_text(c) for c in chunks])
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        if not self.chunks:
            return []
        query_vec = self.embedder.embed([query])
        top_k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_vec, top_k)
        return [
            SearchResult(chunk=self.chunks[i], score=float(s))
            for s, i in zip(scores[0], indices[0])
            if i != -1
        ]

    # --- persistence -------------------------------------------------

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._faiss.write_index(self.index, str(directory / "index.faiss"))
        payload = [c.to_dict() for c in self.chunks]
        (directory / "chunks.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(cls, directory: Path, embedder: Embedder) -> "VectorStore":
        import faiss

        store = cls(embedder)
        store.index = faiss.read_index(str(directory / "index.faiss"))
        payload = json.loads((directory / "chunks.json").read_text(encoding="utf-8"))
        store.chunks = [Chunk.from_dict(d) for d in payload]
        return store
