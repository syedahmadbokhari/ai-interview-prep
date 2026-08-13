"""Result serialization and human-readable reporting."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_outputs(run_dir: Path, records: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "results.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_csv(run_dir / "results.csv", records)
    _write_failures(run_dir / "failures.jsonl", records)
    _write_comparative_failures(run_dir / "comparative_failures.json", records)
    _write_human_review_template(run_dir / "human_review_template.csv", records)
    (run_dir / "REPORT.md").write_text(_render_report(records, summary), encoding="utf-8")


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "question_id",
        "category",
        "configuration",
        "run",
        "required_fact_score",
        "faithfulness_score",
        "project_entity_score",
        "multi_hop_score",
        "comparative_score",
        "adversarial_success",
        "tool_calls",
        "model_calls",
        "retry_count",
        "latency_ms",
        "safe_fallback",
        "input_tokens",
        "output_tokens",
        "total_tokens",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {field: record.get(field) for field in fields}
            usage = record.get("token_usage", {})
            row["input_tokens"] = usage.get("input_tokens")
            row["output_tokens"] = usage.get("output_tokens")
            row["total_tokens"] = usage.get("total_tokens")
            writer.writerow(row)


def _write_failures(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            if _is_failure(record):
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_comparative_failures(path: Path, records: list[dict[str, Any]]) -> None:
    by_question: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_question.setdefault(record["question_id"], []).append(record)
    cases = []
    for question_id, group in by_question.items():
        by_config = {record["configuration"]: record for record in group}
        if len(by_config) < 2:
            continue
        notes = []
        pipeline = by_config.get("pipeline")
        no_assert = by_config.get("agent_no_assertions")
        with_assert = by_config.get("agent_with_assertions")
        if pipeline and no_assert and _ok(pipeline) and not _ok(no_assert):
            notes.append("pipeline_correct_agent_no_assertions_incorrect")
        if pipeline and no_assert and not _ok(pipeline) and _ok(no_assert):
            notes.append("agent_no_assertions_correct_pipeline_incorrect")
        if no_assert and with_assert and not _ok(no_assert) and _ok(with_assert):
            notes.append("assertions_helped")
        if no_assert and with_assert and _ok(no_assert) and not _ok(with_assert):
            notes.append("assertions_hurt")
        if notes:
            cases.append({"question_id": question_id, "notes": notes})
    path.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_human_review_template(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "question_id",
        "configuration",
        "run",
        "correctness_0_2",
        "completeness_0_2",
        "relevance_0_2",
        "clarity_0_2",
        "review_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "question_id": record["question_id"],
                    "configuration": record["configuration"],
                    "run": record["run"],
                    "correctness_0_2": "",
                    "completeness_0_2": "",
                    "relevance_0_2": "",
                    "clarity_0_2": "",
                    "review_notes": "",
                }
            )


def _is_failure(record: dict[str, Any]) -> bool:
    return (
        record.get("required_fact_score", 1.0) < 1.0
        or record.get("faithfulness_score", 1.0) < 1.0
        or record.get("adversarial_success") is False
        or record.get("safe_fallback")
        or bool(record.get("forbidden_claims_found"))
    )


def _ok(record: dict[str, Any]) -> bool:
    return (
        record.get("required_fact_score", 0.0) >= 1.0
        and record.get("faithfulness_score", 0.0) >= 1.0
        and record.get("adversarial_success") is not False
        and not record.get("safe_fallback")
    )


def _render_report(records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    metadata = summary["metadata"]
    lines = [
        "# Evaluation Report",
        "",
        "## Executive Summary",
        "",
        f"Dataset: `{metadata['dataset_version']}`. Mode: `{metadata['mode']}`. "
        f"Configurations: {', '.join(metadata['configurations'])}.",
        "",
        "This report is generated from the machine-readable result files in this run directory.",
        "",
        "## Dataset",
        "",
        f"Questions evaluated: {metadata['dataset_size']}. Runs per configuration: {metadata['runs']}.",
        "",
        "## Overall Results",
        "",
        "| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for config, values in summary["aggregates"]["by_configuration"].items():
        lines.append(
            f"| {config} | {values['count']} | {_fmt(values['fact_coverage_mean'])} | "
            f"{_fmt(values['faithfulness_mean'])} | {_fmt(values['project_entity_mean'])} | "
            f"{_fmt(values['adversarial_refusal_rate'])} | {_fmt(values['latency_ms_mean'])} | "
            f"{_fmt(values['tool_calls_mean'])} | {_fmt(values['model_calls_mean'])} | "
            f"{_fmt(values['correction_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Category Results",
            "",
            json.dumps(summary["aggregates"]["by_category"], indent=2),
            "",
            "## Assertion Results",
            "",
            json.dumps(summary["aggregates"]["assertions"], indent=2),
            "",
            "## Failure Analysis",
            "",
            "See `failures.jsonl` for low-coverage, hallucination, failed-refusal, correction-failure, and safe-fallback cases. See `comparative_failures.json` for pipeline-vs-agent and assertion-helped/hurt cases.",
            "",
            "## Human Review",
            "",
            "`human_review_template.csv` is generated for optional 0-2 human scoring of correctness, completeness, relevance, and clarity.",
            "",
            "## Limitations",
            "",
            "- Mocked runs prove infrastructure and scoring, not live model quality.",
            "- Deterministic scoring uses keyword/fact checks and should be supplemented with human review.",
            "- No statistical significance is claimed from a single benchmark run.",
        ]
    )
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
