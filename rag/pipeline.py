"""End-to-end RAG pipeline: retrieve -> threshold gate -> generate.

The no-result gate lives here, not in the LLM prompt: if the best
retrieved chunk scores below RELEVANCE_THRESHOLD cosine similarity, the
pipeline returns an honest "nothing relevant found" answer without
calling the LLM at all. This is deliberately defense-in-depth with the
prompt's own refusal rule — an off-topic question ("capital of France?")
never gets the chance to be answered fluently from model priors.

Threshold choice: measured with all-MiniLM-L6-v2 on the real corpus
(evaluation/run_eval.py): the 10 on-topic eval questions scored
0.469-0.722 against their best chunk, while the off-topic controls
peaked at 0.161. 0.30 sits in the wide gap between those bands.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .vector_store import SearchResult, VectorStore

RELEVANCE_THRESHOLD = 0.30
DEFAULT_TOP_K = 4

NO_RESULT_ANSWER = (
    "No relevant information was found in the indexed project documentation "
    "for this question, so I won't attempt an answer."
)


@dataclass
class AnswerResult:
    question: str
    answer: str
    grounded: bool  # False => the no-result path fired
    results: list[SearchResult]
    token_usage: dict[str, int] | None = None

    @property
    def sources(self) -> list[str]:
        return [r.chunk.citation() for r in self.results]


class RAGPipeline:
    def __init__(self, store: VectorStore, generator=None) -> None:
        self.store = store
        self._generator = generator  # lazily constructed so retrieval-only use needs no API key

    @property
    def generator(self):
        if self._generator is None:
            from .generation import GroqGenerator

            self._generator = GroqGenerator()
        return self._generator

    def retrieve(self, question: str, top_k: int = DEFAULT_TOP_K) -> list[SearchResult]:
        results = self.store.search(question, top_k=top_k)
        return [r for r in results if r.score >= RELEVANCE_THRESHOLD]

    def ask(self, question: str, top_k: int = DEFAULT_TOP_K) -> AnswerResult:
        results = self.retrieve(question, top_k=top_k)
        if not results:
            return AnswerResult(
                question=question, answer=NO_RESULT_ANSWER, grounded=False, results=[]
            )
        answer = self.generator.generate(question, results)
        return AnswerResult(
            question=question,
            answer=answer,
            grounded=True,
            results=results,
            token_usage=getattr(self.generator, "last_token_usage", {}),
        )


def load_pipeline(index_dir: Path, generator=None) -> RAGPipeline:
    from .embeddings import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder()
    store = VectorStore.load(index_dir, embedder)
    return RAGPipeline(store, generator=generator)
