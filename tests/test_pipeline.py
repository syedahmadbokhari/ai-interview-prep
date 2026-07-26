from __future__ import annotations

from rag.pipeline import NO_RESULT_ANSWER, RAGPipeline
from rag.vector_store import VectorStore
from tests.conftest import FakeEmbedder
from tests.test_retrieval import make_corpus


class SpyGenerator:
    def __init__(self, reply: str = "Grounded answer. Sources: crime > Warehouse") -> None:
        self.calls: list[tuple] = []
        self.reply = reply

    def generate(self, question, results):
        self.calls.append((question, results))
        return self.reply


def make_pipeline(generator=None) -> RAGPipeline:
    store = VectorStore(FakeEmbedder())
    store.add(make_corpus())
    return RAGPipeline(store, generator=generator or SpyGenerator())


def test_relevant_question_is_answered_and_cited():
    gen = SpyGenerator()
    pipeline = make_pipeline(gen)
    result = pipeline.ask("What warehouse does the crime project use, DuckDB?")
    assert result.grounded is True
    assert len(gen.calls) == 1
    assert result.sources  # citations available for the caller
    assert "crime > Warehouse" in result.sources


def test_irrelevant_question_takes_no_result_path_without_llm_call():
    gen = SpyGenerator()
    pipeline = make_pipeline(gen)
    result = pipeline.ask("What is the capital of France?")
    assert result.grounded is False
    assert result.answer == NO_RESULT_ANSWER
    assert result.results == []
    assert gen.calls == []  # LLM must never be called on the no-result path


def test_low_scoring_chunks_are_filtered_by_threshold():
    pipeline = make_pipeline()
    results = pipeline.retrieve("What is the capital of France?")
    assert results == []


def test_generator_receives_only_above_threshold_chunks():
    gen = SpyGenerator()
    pipeline = make_pipeline(gen)
    pipeline.ask("kafka streaming consumer")
    _, passed_results = gen.calls[0]
    assert passed_results
    assert all(r.score >= 0.30 for r in passed_results)
