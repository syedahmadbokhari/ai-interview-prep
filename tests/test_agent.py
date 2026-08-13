from __future__ import annotations

import json
from types import SimpleNamespace

from agent.agent import ReActAgent
from rag.vector_store import VectorStore
from tests.conftest import FakeEmbedder
from tests.test_retrieval import make_corpus


class FakeAnthropicClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=self.responses.pop(0))


def make_store() -> VectorStore:
    store = VectorStore(FakeEmbedder())
    store.add(make_corpus())
    return store


def read_trace(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in open(path, encoding="utf-8").read().splitlines()
        if line.strip()
    ]


def test_agent_handles_single_hop_question_end_to_end(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "I should inspect the projects."},
                {"type": "tool_use", "id": "toolu_1", "name": "list_projects", "input": {}},
            ],
            [
                {
                    "type": "text",
                    "text": "The indexed projects are crime and retail. Sources: list_projects",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Which projects are indexed?")

    assert "crime and retail" in result.answer
    assert len(client.calls) == 2
    assert result.trace_path.endswith(".jsonl")
    assert result.retry_triggered is False
    events = read_trace(result.trace_path)
    assert any(event["event"] == "tool_result" for event in events)
    assert any(event["event"] == "validation" for event in events)


def test_agent_handles_multi_hop_question_with_multiple_tool_calls(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "I need the project names first."},
                {"type": "tool_use", "id": "toolu_1", "name": "list_projects", "input": {}},
            ],
            [
                {"type": "text", "text": "Now I need details from the crime project."},
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "get_project_summary",
                    "input": {"project_name": "crime"},
                },
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project uses DuckDB as its warehouse. Sources: crime > Warehouse",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Summarise the crime project warehouse details.")

    assert "DuckDB" in result.answer
    assert result.validation is not None
    assert result.validation.all_passed is True
    assert len(client.calls) == 3
    events = read_trace(result.trace_path)
    tool_results = [event for event in events if event["event"] == "tool_result"]
    assert [event["tool_name"] for event in tool_results] == [
        "list_projects",
        "get_project_summary",
        "search_technical_details",
    ]


def test_agent_respects_max_iterations_and_stops(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Still searching."},
                {"type": "tool_use", "id": "toolu_1", "name": "list_projects", "input": {}},
            ],
            [
                {"type": "text", "text": "Still searching again."},
                {"type": "tool_use", "id": "toolu_2", "name": "list_projects", "input": {}},
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Keep looking forever?", max_iterations=2)

    assert len(client.calls) == 2
    assert result.iterations == 2
    assert "max_iterations" in result.answer
    events = read_trace(result.trace_path)
    assert events[-1]["event"] == "max_iterations_reached"


def test_agent_draft_passes_assertions_without_retry(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Need warehouse evidence."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project used DuckDB as the warehouse. Sources: crime > Warehouse",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Which warehouse did the crime project use?")

    assert result.retry_triggered is False
    assert len(client.calls) == 2
    assert result.validation.all_passed is True


def test_agent_failed_draft_triggers_correction_attempt(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Need evidence."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project achieved 94% accuracy using DuckDB. Sources: crime > Warehouse",
                }
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project used DuckDB as the warehouse. Sources: crime > Warehouse",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Which warehouse did the crime project use?")

    assert result.retry_triggered is True
    assert "94%" not in result.answer
    assert "DuckDB" in result.answer
    assert len(client.calls) == 3
    events = read_trace(result.trace_path)
    assert any(event["event"] == "correction_retry" for event in events)


def test_agent_corrected_answer_passes_and_is_returned(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Need evidence."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project used Snowflake as the warehouse. Sources: crime > Warehouse",
                }
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project used DuckDB as the warehouse. Sources: crime > Warehouse",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Which warehouse did the crime project use?")

    assert result.answer.startswith("The crime project used DuckDB")
    assert result.validation.all_passed is True


def test_agent_persistent_failure_returns_safe_unverifiable_response(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Need evidence."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project achieved 94% accuracy. Sources: crime > Warehouse",
                }
            ],
            [
                {
                    "type": "text",
                    "text": "The crime project achieved 94% accuracy. Sources: crime > Warehouse",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("Which warehouse did the crime project use?")

    assert result.retry_triggered is True
    assert "could not verify" in result.answer
    assert len(client.calls) == 3
    events = read_trace(result.trace_path)
    assert any(event["event"] == "validation_failed_final" for event in events)


def test_agent_retry_happens_at_most_once(tmp_path):
    client = FakeAnthropicClient(
        [
            [
                {"type": "text", "text": "Need evidence."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_technical_details",
                    "input": {"project_name": "crime", "query": "duckdb warehouse"},
                },
            ],
            [
                {
                    "type": "text",
                    "text": "The Java Fraud Detection project achieved 94% accuracy.",
                }
            ],
            [
                {
                    "type": "text",
                    "text": "The Java Fraud Detection project achieved 94% accuracy.",
                }
            ],
        ]
    )
    agent = ReActAgent(make_store(), client=client, trace_dir=tmp_path)

    result = agent.ask("What did my Java Fraud Detection project use?")

    assert result.retry_triggered is True
    assert len(client.calls) == 3
    events = read_trace(result.trace_path)
    assert len([event for event in events if event["event"] == "correction_retry"]) == 1
