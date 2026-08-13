"""Cost-controlled live validation before the full benchmark."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.metrics import aggregate_results
from evals.reporting import write_outputs
from evals.runner import (
    DEFAULT_DATASET,
    SCORING_VERSION,
    _dataset_version,
    _evaluate_item,
    _git_commit,
    _load_dotenv_keys,
    _load_mock_pipeline,
    _metadata,
)
from evals.schemas import EvalItem, load_dataset, validate_dataset
from rag.pipeline import load_pipeline

SELECTED_QUESTION_IDS = [
    "single_001",
    "single_007",
    "single_011",
    "multi_001",
    "multi_006",
    "multi_010",
    "comp_001",
    "comp_008",
    "adv_001",
    "adv_008",
]
EXPECTED_CONFIGS = ["agent_no_assertions", "agent_with_assertions", "pipeline"]
RESULTS_ROOT = Path("evals/results")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _load_dotenv_keys()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir or RESULTS_ROOT / f"live_validation_10_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    pipeline = _load_mock_pipeline(args.index_dir) if args.mode == "mock" else load_pipeline(args.index_dir)
    project_registry = sorted({chunk.project for chunk in pipeline.store.chunks})
    items = select_items(load_dataset(args.dataset), SELECTED_QUESTION_IDS)
    errors = validate_dataset(items, project_registry)
    if errors:
        raise SystemExit("Dataset validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    start = time.perf_counter()
    manifest = _manifest(args, run_dir, items, status="running")
    _write_json(run_dir / "live_validation_manifest.json", manifest)

    records: list[dict[str, Any]] = []
    try:
        for config in EXPECTED_CONFIGS:
            for item in items:
                record = _evaluate_item(
                    item=item,
                    config=config,
                    mode=args.mode,
                    pipeline=pipeline,
                    project_registry=project_registry,
                    run_number=1,
                    disabled_assertions=set(),
                )
                records.append(record)
                _write_json(run_dir / "partial_results.json", records)
                _write_json(
                    run_dir / "live_validation_manifest.json",
                    {
                        **manifest,
                        "status": "running",
                        "records_completed": len(records),
                        "expected_records": len(items) * len(EXPECTED_CONFIGS),
                    },
                )
    except Exception:
        _write_json(run_dir / "partial_results.json", records)
        _write_json(
            run_dir / "live_validation_manifest.json",
            {
                **manifest,
                "status": "incomplete",
                "records_completed": len(records),
                "expected_records": len(items) * len(EXPECTED_CONFIGS),
            },
        )
        raise

    runtime_seconds = round(time.perf_counter() - start, 2)
    complete = _completion(records, len(items))
    summary = {
        "metadata": {
            **_metadata(
                args=args,
                configs=EXPECTED_CONFIGS,
                dataset_size=len(items),
                dataset_version=_dataset_version(args.dataset),
            ),
            "experiment": "controlled_live_validation_10",
            "selected_question_ids": SELECTED_QUESTION_IDS,
            "expected_records": len(items) * len(EXPECTED_CONFIGS),
            "actual_records": len(records),
            "complete": complete["complete"],
            "runtime_seconds": runtime_seconds,
        },
        "aggregates": aggregate_results(records),
    }
    write_outputs(run_dir, records, summary)
    final_manifest = {
        **manifest,
        "status": "complete" if complete["complete"] else "incomplete",
        "records_completed": len(records),
        "expected_records": len(items) * len(EXPECTED_CONFIGS),
        "runtime_seconds": runtime_seconds,
        "completion": complete,
        "token_usage": token_totals(records),
    }
    _write_json(run_dir / "live_validation_manifest.json", final_manifest)
    (run_dir / "LIVE_VALIDATION_REPORT.md").write_text(
        render_live_validation_report(run_dir, records, summary, final_manifest),
        encoding="utf-8",
    )
    print(f"Live validation complete ({args.mode}). Results written to {run_dir}")
    return 0 if complete["complete"] else 1


def select_items(items: list[EvalItem], selected_ids: list[str]) -> list[EvalItem]:
    by_id = {item.id: item for item in items}
    missing = [item_id for item_id in selected_ids if item_id not in by_id]
    if missing:
        raise ValueError(f"Selected question IDs missing from dataset: {', '.join(missing)}")
    return [by_id[item_id] for item_id in selected_ids]


def token_totals(records: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    by_config: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )
    for record in records:
        usage = record.get("token_usage", {})
        for key in totals:
            value = int(usage.get(key) or 0)
            totals[key] += value
            by_config[record["configuration"]][key] += value
    return {"total": totals, "by_configuration": dict(sorted(by_config.items()))}


def render_live_validation_report(
    run_dir: Path,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    completion = manifest["completion"]
    categories = Counter({record["question_id"]: record["category"] for record in records}.values())
    disagreements = _disagreements(records)
    assertion_cases = _assertion_cases(records)
    full_estimate = _full_benchmark_estimate(records, manifest["runtime_seconds"])
    recommendation = _recommendation(completion, records)

    lines = [
        "# Controlled Live Validation Report",
        "",
        "## 1. Purpose",
        "",
        "Controlled 10-question live validation before deciding whether to spend credits on the complete 43-question benchmark.",
        "",
        "## 2. Configuration",
        "",
        f"- Mode: `{summary['metadata']['mode']}`",
        f"- Model: `{summary['metadata']['model']}`",
        f"- Dataset: `{summary['metadata']['dataset_version']}`",
        f"- Temperature: `{summary['metadata']['temperature']}`",
        f"- Scoring version: `{summary['metadata']['scoring_version']}`",
        f"- Selected IDs: {', '.join(summary['metadata']['selected_question_ids'])}",
        f"- Scoring notes: {manifest.get('scoring_notes', 'none')}",
        "",
        "## 3. Dataset Subset",
        "",
        f"- single_hop: {categories.get('single_hop', 0)}",
        f"- multi_hop: {categories.get('multi_hop', 0)}",
        f"- comparative: {categories.get('comparative', 0)}",
        f"- adversarial: {categories.get('adversarial', 0)}",
        "",
        "## 4. Completion",
        "",
        f"- Expected records: {completion['expected_total']}",
        f"- Actual records: {completion['actual_total']}",
        f"- Complete: {completion['complete']}",
        "",
        "## 5. Architecture Comparison",
        "",
        _config_table(summary["aggregates"]["by_configuration"]),
        "",
        "## 6. Assertion Behaviour",
        "",
        json.dumps(summary["aggregates"]["assertions"], indent=2),
        "",
        "## 7. Representative Cases",
        "",
        _case_lines(disagreements[:10]),
        "",
        "## 8. Operational Usage",
        "",
        json.dumps({"tokens": manifest["token_usage"], "runtime_seconds": manifest["runtime_seconds"]}, indent=2),
        "",
        "## 9. Full Benchmark Estimate",
        "",
        json.dumps(full_estimate, indent=2),
        "",
        "## 10. Limitations",
        "",
        "- This is a 10-question validation subset, not a statistically significant benchmark.",
        "- Negative results are preserved and should not trigger prompt/assertion tuning without review.",
        "- Token-to-cost estimates are not embedded here because provider pricing is not configured in the repo.",
        "",
        "## 11. GO / NO-GO",
        "",
        recommendation,
        "",
        "## 12. Next Command",
        "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe -m evals.runner --config all --mode live --runs 1 --output-dir evals\\results\\live_full_43_<timestamp>",
        "```",
        "",
        "## Assertion Failure Details",
        "",
        _case_lines(assertion_cases[:20]),
    ]
    return "\n".join(lines) + "\n"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--mode", choices=["mock", "live"], default="live")
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--disable-assertion", action="append", default=[])
    return parser.parse_args(argv)


def _manifest(args: argparse.Namespace, run_dir: Path, items: list[EvalItem], status: str) -> dict[str, Any]:
    return {
        "experiment": "controlled_live_validation_10",
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "dataset_path": str(args.dataset),
        "dataset_version": _dataset_version(args.dataset),
        "mode": args.mode,
        "model": "claude-sonnet-4-6",
        "temperature": 0,
        "retrieval_settings": {"index_dir": str(args.index_dir)},
        "generation_settings": {"agent_max_iterations": 5, "agent_max_tokens": 1200},
        "assertion_configuration": {"disabled_assertions": []},
        "scoring_version": SCORING_VERSION,
        "selected_question_ids": [item.id for item in items],
        "selected_questions": [
            {"id": item.id, "category": item.category, "question": item.question}
            for item in items
        ],
        "configurations": EXPECTED_CONFIGS,
        "output_dir": str(run_dir),
    }


def _completion(records: list[dict[str, Any]], question_count: int) -> dict[str, Any]:
    by_config = Counter(record["configuration"] for record in records)
    expected_per_config = question_count
    return {
        "expected_per_config": expected_per_config,
        "actual_per_config": dict(sorted(by_config.items())),
        "expected_total": expected_per_config * len(EXPECTED_CONFIGS),
        "actual_total": len(records),
        "complete": all(by_config.get(config) == expected_per_config for config in EXPECTED_CONFIGS)
        and len(records) == expected_per_config * len(EXPECTED_CONFIGS),
    }


def _config_table(by_config: dict[str, dict[str, Any]]) -> str:
    lines = [
        "| Configuration | Count | Fact | Faithfulness | Project | Multi-hop | Comparative | Adv Refusal | Latency ms | Model Calls | Tool Calls | Total Tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for config, values in by_config.items():
        lines.append(
            f"| {config} | {values['count']} | {_fmt(values['fact_coverage_mean'])} | "
            f"{_fmt(values['faithfulness_mean'])} | {_fmt(values['project_entity_mean'])} | "
            f"{_fmt(values['multi_hop_mean'])} | {_fmt(values['comparative_mean'])} | "
            f"{_fmt(values['adversarial_refusal_rate'])} | {_fmt(values['latency_ms_mean'])} | "
            f"{_fmt(values['model_calls_mean'])} | {_fmt(values['tool_calls_mean'])} | "
            f"{values.get('total_tokens_total', 0)} |"
        )
    return "\n".join(lines)


def _disagreements(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        grouped[record["question_id"]][record["configuration"]] = record
    cases = []
    for question_id, group in grouped.items():
        pipeline = group.get("pipeline")
        no_assert = group.get("agent_no_assertions")
        with_assert = group.get("agent_with_assertions")
        if pipeline and no_assert and _quality(pipeline) != _quality(no_assert):
            cases.append(_case(question_id, "pipeline_vs_agent_no_assertions", pipeline, no_assert))
        if no_assert and with_assert and _quality(no_assert) != _quality(with_assert):
            cases.append(_case(question_id, "agent_no_assertions_vs_agent_with_assertions", no_assert, with_assert))
    return cases


def _assertion_cases(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for record in records:
        if record["configuration"] != "agent_with_assertions":
            continue
        failed = record.get("assertions", {}).get("results", [])
        failed = [item for item in failed if not item.get("passed") and not item.get("skipped")]
        if failed:
            events = _trace_events(record.get("trace_path"))
            cases.append(
                {
                    "question_id": record["question_id"],
                    "question": record["question"],
                    "answer": record["answer"],
                    "failed_assertions": [
                        {
                            "assertion": item.get("assertion"),
                            "claim": item.get("claim"),
                            "reason": item.get("reason"),
                            "evidence": item.get("evidence", [])[:2],
                        }
                        for item in failed
                    ],
                    "retry_occurred": record.get("retry_count", 0) > 0,
                    "safe_fallback": record.get("safe_fallback"),
                    "trace_stages": [event.get("event") for event in events],
                }
            )
    return cases


def _trace_events(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    try:
        return [
            json.loads(line)
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError:
        return []


def _full_benchmark_estimate(records: list[dict[str, Any]], runtime_seconds: float) -> dict[str, Any]:
    scale = 43 / 10
    tokens = token_totals(records)["total"]
    return {
        "scale_factor": scale,
        "estimated_runtime_seconds": round(runtime_seconds * scale, 2),
        "estimated_model_calls": round(sum(record.get("model_calls", 0) for record in records) * scale),
        "estimated_input_tokens": round(tokens["input_tokens"] * scale),
        "estimated_output_tokens": round(tokens["output_tokens"] * scale),
        "estimated_total_tokens": round(tokens["total_tokens"] * scale),
    }


def _recommendation(completion: dict[str, Any], records: list[dict[str, Any]]) -> str:
    if not completion["complete"]:
        return "NO-GO - incomplete run; do not spend on the full benchmark until completion issues are fixed."
    if any(not record.get("token_usage") for record in records if record.get("model_calls", 0) > 0):
        return "GO WITH CAUTION - benchmark completed, but inspect token accounting gaps before full run."
    return "GO WITH CAUTION - benchmark infrastructure completed; review disagreements and credit estimate before the full 43-question run."


def _quality(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("required_fact_score"),
        record.get("faithfulness_score"),
        record.get("project_entity_score"),
        record.get("multi_hop_score"),
        record.get("comparative_score"),
        record.get("adversarial_success"),
        record.get("safe_fallback"),
    )


def _case(question_id: str, label: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "label": label,
        "left_config": left["configuration"],
        "left_scores": _score_summary(left),
        "left_answer": left["answer"][:500],
        "right_config": right["configuration"],
        "right_scores": _score_summary(right),
        "right_answer": right["answer"][:500],
    }


def _score_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact": record.get("required_fact_score"),
        "faithfulness": record.get("faithfulness_score"),
        "project": record.get("project_entity_score"),
        "adversarial": record.get("adversarial_success"),
        "safe_fallback": record.get("safe_fallback"),
    }


def _case_lines(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "No cases found."
    return "\n\n".join(f"```json\n{json.dumps(case, indent=2, ensure_ascii=False)}\n```" for case in cases)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
