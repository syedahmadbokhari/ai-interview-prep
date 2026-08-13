"""Run Phase 5 assertion ablation experiments.

Mock mode is the default and validates infrastructure only:
    python -m evals.experiments.ablation --mode mock --runs 1

Live mode requires working model credentials and available provider credit:
    python -m evals.experiments.ablation --mode live --runs 3
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.experiments.analysis import (
    build_comparisons,
    experiment_configurations,
)
from evals.experiments.failure_analysis import build_failure_analysis
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
)
from evals.schemas import load_dataset, validate_dataset
from rag.pipeline import load_pipeline

RESULTS_ROOT = Path("evals/results/experiments")
NOTICE_MOCK = "MOCK INFRASTRUCTURE VALIDATION ONLY"
NOTICE_LIVE_MISSING = "LIVE ABLATION STUDY NOT YET EXECUTED"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _load_dotenv_keys()
    run_dir = _run_dir(args)

    pipeline = _load_mock_pipeline(args.index_dir) if args.mode == "mock" else load_pipeline(args.index_dir)
    project_registry = sorted({chunk.project for chunk in pipeline.store.chunks})
    items = load_dataset(args.dataset)
    if args.category:
        items = [item for item in items if item.category == args.category]
    if args.limit is not None:
        items = items[: args.limit]

    errors = validate_dataset(items, project_registry)
    if errors:
        raise SystemExit("Dataset validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    configs = experiment_configurations(args.assertion)
    records: list[dict[str, Any]] = []
    for run_number in range(1, args.runs + 1):
        for experiment_config, spec in configs.items():
            for item in items:
                record = _evaluate_item(
                    item=item,
                    config=spec["runner_config"],
                    mode=args.mode,
                    pipeline=pipeline,
                    project_registry=project_registry,
                    run_number=run_number,
                    disabled_assertions=set(spec["disabled_assertions"]),
                )
                record["configuration"] = experiment_config
                record["disabled_assertions"] = spec["disabled_assertions"]
                record["experiment_phase"] = "phase5_assertion_ablation"
                records.append(record)

    summary = {
        "metadata": _metadata(args, list(configs), len(items)),
        "aggregates": aggregate_results(records),
        "notice": NOTICE_MOCK if args.mode == "mock" else None,
    }
    comparisons = build_comparisons(records)
    failure_analysis = build_failure_analysis(records)

    write_outputs(run_dir, records, summary)
    _write_experiment_outputs(run_dir, records, summary, comparisons, failure_analysis)
    print(f"Phase 5 assertion ablation complete ({args.mode}). Results written to {run_dir}")
    if args.mode == "mock":
        print(f"NOTE: {NOTICE_MOCK}; {NOTICE_LIVE_MISSING}.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--assertion", default=None)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args(argv)


def _run_dir(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return args.output_dir
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return RESULTS_ROOT / f"assertion_ablation_{timestamp}"


def _metadata(args: argparse.Namespace, configs: list[str], dataset_size: int) -> dict[str, Any]:
    return {
        "experiment": "phase5_assertion_ablation",
        "dataset_version": _dataset_version(args.dataset),
        "dataset_path": str(args.dataset),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "configurations": configs,
        "runs": args.runs,
        "category_filter": args.category,
        "assertion_filter": args.assertion,
        "retrieval_settings": {"index_dir": str(args.index_dir)},
        "git_commit": _git_commit(),
        "python_version": platform.python_version(),
        "dataset_size": dataset_size,
        "scoring_version": SCORING_VERSION,
        "live_ablation_executed": args.mode == "live",
        "mock_notice": NOTICE_MOCK if args.mode == "mock" else None,
    }


def _write_experiment_outputs(
    run_dir: Path,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    comparisons: dict[str, Any],
    failure_analysis: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(summary["metadata"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "comparisons.json").write_text(
        json.dumps(comparisons, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "failure_analysis.json").write_text(
        json.dumps(failure_analysis, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_failure_analysis_markdown(run_dir / "FAILURE_ANALYSIS.md", failure_analysis, summary)
    _write_human_review_csv(run_dir / "human_review_phase5.csv", failure_analysis["review_sample"])
    _write_tables(run_dir / "tables", summary, comparisons)
    _write_charts(run_dir / "charts", summary, comparisons)
    (run_dir / "PHASE5_REPORT.md").write_text(
        _render_phase5_report(summary, comparisons, failure_analysis), encoding="utf-8"
    )


def _write_tables(
    table_dir: Path, summary: dict[str, Any], comparisons: dict[str, Any]
) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)
    _write_dict_csv(table_dir / "architecture_comparison.csv", summary["aggregates"]["by_configuration"])
    _write_dict_csv(table_dir / "category_results.csv", summary["aggregates"]["by_category"])
    _write_dict_csv(table_dir / "assertion_ablation.csv", comparisons["marginal_deltas"])
    _write_nested_cost_csv(table_dir / "operational_cost.csv", comparisons["operational_cost"])


def _write_dict_csv(path: Path, rows: dict[str, dict[str, Any]]) -> None:
    fields = sorted({field for row in rows.values() for field in row})
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", *fields])
        writer.writeheader()
        for name, values in sorted(rows.items()):
            writer.writerow({"name": name, **values})


def _write_nested_cost_csv(path: Path, rows: dict[str, dict[str, Any]]) -> None:
    fields = [
        "name",
        "latency_mean",
        "latency_median",
        "latency_p95",
        "tool_calls_mean",
        "model_calls_mean",
        "retry_rate",
        "safe_fallback_rate",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for name, values in sorted(rows.items()):
            latency = values["latency_ms"]
            writer.writerow(
                {
                    "name": name,
                    "latency_mean": latency["mean"],
                    "latency_median": latency["median"],
                    "latency_p95": latency["p95"],
                    "tool_calls_mean": values["tool_calls_mean"],
                    "model_calls_mean": values["model_calls_mean"],
                    "retry_rate": values["retry_rate"],
                    "safe_fallback_rate": values["safe_fallback_rate"],
                }
            )


def _write_human_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "question_id",
        "configuration",
        "run",
        "category",
        "labels",
        "human_correctness_0_2",
        "human_grounding_0_2",
        "false_positive",
        "false_negative",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "question_id": row["question_id"],
                    "configuration": row["configuration"],
                    "run": row["run"],
                    "category": row["category"],
                    "labels": ";".join(row["labels"]),
                    "human_correctness_0_2": "",
                    "human_grounding_0_2": "",
                    "false_positive": "",
                    "false_negative": "",
                    "notes": "",
                }
            )


def _write_failure_analysis_markdown(
    path: Path, failure_analysis: dict[str, Any], summary: dict[str, Any]
) -> None:
    lines = [
        "# Phase 5 Failure Analysis",
        "",
        _notice(summary),
        "",
        "## Taxonomy Counts",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in failure_analysis["taxonomy_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Review Queues",
            "",
            f"- False-positive candidates: {len(failure_analysis['false_positives'])}",
            f"- False-negative candidates: {len(failure_analysis['false_negatives'])}",
            f"- Correction failures: {len(failure_analysis['correction_failures'])}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_charts(chart_dir: Path, summary: dict[str, Any], comparisons: dict[str, Any]) -> None:
    chart_dir.mkdir(parents=True, exist_ok=True)
    by_config = summary["aggregates"]["by_configuration"]
    _bar_svg(
        chart_dir / "fact_coverage_by_configuration.svg",
        "Fact coverage by configuration",
        {name: values.get("fact_coverage_mean") for name, values in by_config.items()},
    )
    _bar_svg(
        chart_dir / "faithfulness_by_configuration.svg",
        "Faithfulness by configuration",
        {name: values.get("faithfulness_mean") for name, values in by_config.items()},
    )
    _bar_svg(
        chart_dir / "latency_by_configuration.svg",
        "Mean latency by configuration",
        {name: values.get("latency_ms_mean") for name, values in by_config.items()},
    )
    _bar_svg(
        chart_dir / "leave_one_out_faithfulness_delta.svg",
        "Leave-one-out faithfulness delta",
        {
            name: values.get("faithfulness_mean")
            for name, values in comparisons["marginal_deltas"].items()
        },
    )


def _bar_svg(path: Path, title: str, values: dict[str, float | None]) -> None:
    width = 900
    bar_height = 28
    gap = 10
    left = 260
    top = 46
    clean = {name: (0.0 if value is None else float(value)) for name, value in values.items()}
    max_value = max([abs(value) for value in clean.values()] + [1.0])
    height = top + len(clean) * (bar_height + gap) + 30
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="20" y="28" font-family="Arial" font-size="18" fill="#111111">{_xml(title)}</text>',
    ]
    for index, (name, value) in enumerate(sorted(clean.items())):
        y = top + index * (bar_height + gap)
        bar_width = int(abs(value) / max_value * (width - left - 80))
        color = "#2f6f73" if value >= 0 else "#a94442"
        lines.append(f'<text x="20" y="{y + 20}" font-family="Arial" font-size="12" fill="#111111">{_xml(name)}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}"/>')
        lines.append(f'<text x="{left + bar_width + 8}" y="{y + 20}" font-family="Arial" font-size="12" fill="#111111">{value:.3f}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_phase5_report(
    summary: dict[str, Any], comparisons: dict[str, Any], failure_analysis: dict[str, Any]
) -> str:
    lines = [
        "# Phase 5 Assertion Ablation Study",
        "",
        _notice(summary),
        "",
        "## Scope",
        "",
        "This run compares the retrieval pipeline, ReAct agent without assertions, ReAct agent with all assertions, and leave-one-out assertion ablations using the existing evaluation runner and `disabled_assertions` control.",
        "",
        "## Primary Metrics",
        "",
        "| Configuration | Count | Fact Coverage | Faithfulness | Adversarial Refusal | Safe Fallback | Latency ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for config, values in summary["aggregates"]["by_configuration"].items():
        lines.append(
            f"| {config} | {values['count']} | {_fmt(values['fact_coverage_mean'])} | "
            f"{_fmt(values['faithfulness_mean'])} | {_fmt(values['adversarial_refusal_rate'])} | "
            f"{_fmt(values['safe_fallback_rate'])} | {_fmt(values['latency_ms_mean'])} |"
        )
    lines.extend(
        [
            "",
            "## Marginal Deltas",
            "",
            "Deltas are leave-one-out minus `agent_with_assertions`.",
            "",
            json.dumps(comparisons["marginal_deltas"], indent=2),
            "",
            "## Failure Analysis",
            "",
            json.dumps(failure_analysis["taxonomy_counts"], indent=2),
            "",
            "## API Freeze Recommendation",
            "",
        ]
    )
    for item in comparisons["api_freeze_recommendations"]:
        lines.append(f"- `{item['surface']}`: {item['recommendation']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `manifest.json`, `results.json`, `results.csv`, `summary.json`, `failures.jsonl`",
            "- `comparisons.json`, `failure_analysis.json`, `FAILURE_ANALYSIS.md`",
            "- `human_review_phase5.csv`, `tables/`, `charts/`",
        ]
    )
    return "\n".join(lines) + "\n"


def _notice(summary: dict[str, Any]) -> str:
    if summary["metadata"]["mode"] == "mock":
        return f"**{NOTICE_MOCK}. {NOTICE_LIVE_MISSING}. Do not treat these results as live model evidence.**"
    return "**LIVE ABLATION STUDY EXECUTED. Interpret with run count, dataset size, and human review limits.**"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    raise SystemExit(main())
