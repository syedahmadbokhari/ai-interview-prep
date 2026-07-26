from __future__ import annotations

import pytest

from rag.chunking import Chunk
from rag.vector_store import VectorStore
from tests.conftest import FakeEmbedder


def make_corpus() -> list[Chunk]:
    return [
        Chunk(
            text="The pipeline loads data into a DuckDB warehouse from S3.",
            project="crime", source_file="crime.md", heading="Warehouse",
        ),
        Chunk(
            text="Kafka streaming with a producer and consumer in KRaft mode.",
            project="crime", source_file="crime.md", heading="Streaming",
        ),
        Chunk(
            text="BigQuery partition pruning reduced bytes scanned by 58.7%.",
            project="retail", source_file="retail.md", heading="BigQuery",
        ),
        Chunk(
            text="Adidas dominates revenue; discount products drive volume.",
            project="retail", source_file="retail.md", heading="Insights",
        ),
    ]


@pytest.fixture()
def store() -> VectorStore:
    s = VectorStore(FakeEmbedder())
    s.add(make_corpus())
    return s


def test_known_query_returns_correct_top1(store):
    results = store.search("Which warehouse stores the data, DuckDB?", top_k=2)
    assert results[0].chunk.heading == "Warehouse"
    assert results[0].chunk.project == "crime"


def test_scores_are_descending_and_metadata_preserved(store):
    results = store.search("kafka streaming consumer", top_k=4)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0].chunk.heading == "Streaming"
    assert results[0].chunk.citation() == "crime > Streaming"


def test_top_k_respects_corpus_size(store):
    results = store.search("duckdb", top_k=50)
    assert len(results) == 4


def test_distinct_queries_hit_distinct_projects(store):
    bigquery = store.search("bigquery partition bytes", top_k=1)[0]
    revenue = store.search("adidas revenue discount", top_k=1)[0]
    assert bigquery.chunk.project == "retail"
    assert bigquery.chunk.heading == "BigQuery"
    assert revenue.chunk.heading == "Insights"


def test_save_and_load_roundtrip(store, tmp_path):
    store.save(tmp_path / "idx")
    loaded = VectorStore.load(tmp_path / "idx", FakeEmbedder())
    assert [c.chunk_id for c in loaded.chunks] == [c.chunk_id for c in store.chunks]
    original = store.search("duckdb warehouse", top_k=2)
    restored = loaded.search("duckdb warehouse", top_k=2)
    assert [r.chunk.heading for r in restored] == [r.chunk.heading for r in original]
    assert restored[0].score == pytest.approx(original[0].score)


def test_empty_store_returns_no_results():
    s = VectorStore(FakeEmbedder())
    assert s.search("anything", top_k=3) == []
