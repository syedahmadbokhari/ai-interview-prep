from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeEmbedder:
    """Deterministic bag-of-words embedder over a fixed vocabulary.

    Gives fully predictable similarities: texts sharing vocabulary terms
    get high cosine similarity, disjoint texts get ~0. No model download,
    no network, no randomness.
    """

    VOCAB = [
        "duckdb", "warehouse", "s3", "kafka", "streaming", "bigquery",
        "partition", "revenue", "discount", "adidas", "crime", "police",
        "airflow", "dag", "dbt", "test", "dashboard", "streamlit",
        "france", "capital", "weather",
    ]

    def __init__(self) -> None:
        self.dim = len(self.VOCAB)

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = text.lower().split()
            for col, term in enumerate(self.VOCAB):
                out[row, col] = sum(1 for t in tokens if term in t)
            norm = np.linalg.norm(out[row])
            if norm > 0:
                out[row] /= norm
            # else: all-zero vector -> similarity 0 with everything (OOV text)
        return out
