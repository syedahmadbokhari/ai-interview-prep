"""Run Phase 3 benchmark configurations and write reproducible reports.

Safe default:
    python -m evals.runner --config all

The default mode is mocked, so it exercises the full evaluation pipeline without
external model calls. Use --mode live only when API keys and cost are intended.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import DEFAULT_MODEL, ReActAgent  # noqa: E402
from rag_assertions import AssertionRunner  # noqa: E402
from evals.metrics import aggregate_results  # noqa: E402
from evals.reporting import write_outputs  # noqa: E402
from evals.schemas import VALID_CONFIGS, EvalItem, load_dataset, validate_dataset  # noqa: E402
from evals.scoring import score_answer  # noqa: E402
from rag.pipeline import load_pipeline  # noqa: E402
from rag.chunking import Chunk  # noqa: E402
from rag.vector_store import VectorStore  # noqa: E402

DEFAULT_DATASET = Path("evals/datasets/interview_prep_v1.jsonl")
RESULTS_ROOT = Path("evals/results")
SCORING_VERSION = "1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--config", default="all", choices=["all", *sorted(VALID_CONFIGS)])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--disable-assertion", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    _load_dotenv_keys()

    pipeline = (
        _load_mock_pipeline(args.index_dir)
        if args.mode == "mock"
        else load_pipeline(args.index_dir)
    )
    project_registry = sorted({chunk.project for chunk in pipeline.store.chunks})
    items = load_dataset(args.dataset)
    if args.limit is not None:
        items = items[: args.limit]
    errors = validate_dataset(items, project_registry)
    if errors:
        raise SystemExit("Dataset validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    configs = sorted(VALID_CONFIGS) if args.config == "all" else [args.config]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir or RESULTS_ROOT / f"{timestamp}_{args.mode}_{args.config}"

    records: list[dict[str, Any]] = []
    for run_number in range(1, args.runs + 1):
        for config in configs:
            for item in items:
                records.append(
                    _evaluate_item(
                        item=item,
                        config=config,
                        mode=args.mode,
                        pipeline=pipeline,
                        project_registry=project_registry,
                        run_number=run_number,
                        disabled_assertions=set(args.disable_assertion),
                    )
                )

    summary = {
        "metadata": _metadata(
            args=args,
            configs=configs,
            dataset_size=len(items),
            dataset_version=_dataset_version(args.dataset),
        ),
        "aggregates": aggregate_results(records),
    }
    write_outputs(run_dir, records, summary)
    print(f"Evaluation complete ({args.mode}). Results written to {run_dir}")
    if args.mode == "mock":
        print("NOTE: mocked evaluation only; no live performance conclusion can be made.")


def _evaluate_item(
    item: EvalItem,
    config: str,
    mode: str,
    pipeline,
    project_registry: list[str],
    run_number: int,
    disabled_assertions: set[str],
) -> dict[str, Any]:
    start = time.perf_counter()
    model_calls = 0
    tool_calls = 0
    retry_count = 0
    trace_path = None
    validation = None
    token_usage: dict[str, int] = {}

    if config == "pipeline":
        if mode == "mock":
            answer = _mock_pipeline_answer(item)
            grounded = item.expected_behavior == "answer"
        else:
            result = pipeline.ask(item.question)
            answer = result.answer
            grounded = result.grounded
            model_calls = 1 if grounded else 0
            token_usage = result.token_usage or {}
    else:
        enable_assertions = config == "agent_with_assertions"
        if mode == "mock":
            client = _MockAnthropicClient(item, enable_assertions=enable_assertions)
        else:
            client = None
        runner = AssertionRunner(disabled_assertions=disabled_assertions)
        agent = ReActAgent(
            pipeline.store,
            client=client,
            assertion_runner=runner,
            enable_assertions=enable_assertions,
        )
        result = agent.ask(item.question)
        answer = result.answer
        validation = result.validation
        retry_count = 1 if result.retry_triggered else 0
        trace_path = result.trace_path
        model_calls = _count_model_calls(result.messages)
        tool_calls = _count_tool_calls(result.messages)
        token_usage = result.token_usage or _token_usage_from_client(client)
        validation_events = _validation_events(trace_path)
        retry_failed_assertions = _retry_failed_assertions(trace_path)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    scores = score_answer(item, answer, validation)
    assertions = validation.to_dict() if validation is not None else {}
    return {
        "question_id": item.id,
        "category": item.category,
        "configuration": config,
        "run": run_number,
        "question": item.question,
        "answer": answer,
        **scores.to_dict(),
        "tool_calls": tool_calls,
        "retrieval_operations": tool_calls if config != "pipeline" else 1,
        "model_calls": model_calls,
        "retry_count": retry_count,
        "latency_ms": elapsed_ms,
        "token_usage": token_usage,
        "assertions": assertions,
        "validation_events": validation_events if config != "pipeline" else [],
        "retry_failed_assertions": retry_failed_assertions if config != "pipeline" else [],
        "safe_fallback": "could not verify enough" in answer.lower(),
        "trace_path": trace_path,
        "mode": mode,
    }


def _mock_pipeline_answer(item: EvalItem) -> str:
    if item.expected_behavior == "refuse_false_premise":
        if item.forbidden_claims:
            return f"The {item.forbidden_claims[0]} was implemented successfully."
        return "This unsupported premise appears to be true."
    return " ".join(fact.fact for fact in item.required_facts) + " Sources: benchmark"


class _MockGenerator:
    def generate(self, question, results):
        return " ".join(r.chunk.text.split(".")[0] for r in results[:2])


def _load_mock_pipeline(index_dir: Path):
    chunks = [
        Chunk.from_dict(item)
        for item in json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
    ]
    store = VectorStore(_EvalEmbedder())
    store.add(chunks)
    return SimpleNamespace(store=store, ask=lambda question: None)


class _EvalEmbedder:
    dim = 64

    def embed(self, texts: list[str]):
        import numpy as np

        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.lower().replace("-", " ").split():
                idx = sum(ord(ch) for ch in token) % self.dim
                out[row, idx] += 1
            norm = np.linalg.norm(out[row])
            if norm:
                out[row] /= norm
        return out


class _MockAnthropicClient:
    def __init__(self, item: EvalItem, enable_assertions: bool) -> None:
        self.item = item
        self.enable_assertions = enable_assertions
        self.calls: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        call_number = len(self.calls)
        if call_number == 1:
            return SimpleNamespace(content=self._tool_plan())
        if self.enable_assertions and call_number == 3:
            return SimpleNamespace(content=[{"type": "text", "text": self._corrected_answer()}])
        return SimpleNamespace(content=[{"type": "text", "text": self._draft_answer()}])

    def _tool_plan(self):
        if self.item.expected_behavior == "refuse_false_premise":
            return [
                {"type": "text", "text": "I need to inspect the project registry."},
                {"type": "tool_use", "id": f"{self.item.id}_list", "name": "list_projects", "input": {}},
            ]
        projects = self.item.expected_projects or ["uk-crime-data-pipeline"]
        blocks = [{"type": "text", "text": "I need evidence from the indexed projects."}]
        for idx, project in enumerate(projects):
            blocks.append(
                {
                    "type": "tool_use",
                    "id": f"{self.item.id}_{idx}",
                    "name": "search_technical_details",
                    "input": {"project_name": project, "query": self.item.question},
                }
            )
        return blocks

    def _draft_answer(self) -> str:
        if self.item.expected_behavior == "refuse_false_premise":
            forbidden = self.item.forbidden_claims[0] if self.item.forbidden_claims else "unsupported project"
            return f"The {forbidden} used XGBoost and achieved 94% accuracy."
        return " ".join(fact.fact for fact in self.item.required_facts) + " Sources: benchmark"

    def _corrected_answer(self) -> str:
        if self.item.expected_behavior == "refuse_false_premise":
            return "The indexed documentation does not contain support for that premise, so I cannot verify an answer."
        return self._draft_answer()


def _count_model_calls(messages: list[dict[str, Any]]) -> int:
    return sum(1 for message in messages if message["role"] == "assistant")


def _count_tool_calls(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        if message["role"] != "assistant":
            continue
        content = message.get("content", [])
        if isinstance(content, list):
            total += sum(1 for block in content if block.get("type") == "tool_use")
    return total


def _token_usage_from_client(client) -> dict[str, int]:
    if client is None:
        return {}
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _validation_events(trace_path: str | None) -> list[dict[str, Any]]:
    if not trace_path:
        return []
    events = []
    try:
        for line in Path(trace_path).read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("event") == "validation":
                events.append(
                    {
                        "stage": event.get("stage"),
                        "validation": event.get("validation", {}),
                    }
                )
    except OSError:
        return []
    return events


def _retry_failed_assertions(trace_path: str | None) -> list[str]:
    if not trace_path:
        return []
    names: list[str] = []
    try:
        for line in Path(trace_path).read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("event") == "correction_retry":
                for assertion in event.get("failed_assertions", []):
                    names.append(assertion.get("assertion", ""))
    except OSError:
        return []
    return [name for name in names if name]


def _metadata(args, configs: list[str], dataset_size: int, dataset_version: str) -> dict[str, Any]:
    return {
        "dataset_version": dataset_version,
        "dataset_path": str(args.dataset),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "model": DEFAULT_MODEL,
        "configurations": configs,
        "runs": args.runs,
        "temperature": 0,
        "retrieval_settings": {"index_dir": str(args.index_dir)},
        "disabled_assertions": args.disable_assertion,
        "git_commit": _git_commit(),
        "python_version": platform.python_version(),
        "dataset_size": dataset_size,
        "scoring_version": SCORING_VERSION,
    }


def _dataset_version(path: Path) -> str:
    return path.stem


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def _load_dotenv_keys() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


if __name__ == "__main__":
    main()
