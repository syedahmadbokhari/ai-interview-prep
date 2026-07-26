"""Embedding backend.

Model: sentence-transformers/all-MiniLM-L6-v2
- 22M params, ~90MB download, 384-dim vectors — runs comfortably on CPU
  (this corpus embeds in under a second).
- Consistently near the top of the speed/quality frontier for short-passage
  semantic search; larger models (all-mpnet-base-v2, bge-base) score a few
  points higher on retrieval benchmarks but at 3-5x the latency and size,
  which buys nothing on a corpus of ~100 chunks where retrieval quality is
  dominated by chunking and query phrasing, not embedding ceiling.
- Free, local, no API key.

Embeddings are L2-normalized so inner product == cosine similarity, which
lets the FAISS store use a plain IndexFlatIP.

Chunks are embedded with their citation prefixed ("project > heading:
text") — section titles like "Data Warehousing (BigQuery)" carry strong
retrieval signal that the body text alone sometimes lacks.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Embedder(Protocol):
    """Interface the vector store depends on; tests substitute a fake."""

    dim: int

    def embed(self, texts: list[str]) -> np.ndarray:  # (n, dim), L2-normalized
        ...


class SentenceTransformerEmbedder:
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.MODEL_NAME)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype=np.float32)
