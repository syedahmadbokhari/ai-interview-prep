"""Aggregate benchmark metrics."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any


def aggregate_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_config = _group(records, "configuration")
    by_category = _group(records, "category")
    return {
        "by_configuration": {
            key: _aggregate_group(value) for key, value in sorted(by_config.items())
        },
        "by_category": {
            key: _aggregate_group(value) for key, value in sorted(by_category.items())
        },
        "assertions": _aggregate_assertions(records),
    }


def _group(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record[key]].append(record)
    return grouped


def _aggregate_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    def values(name: str):
        return [r[name] for r in records if r.get(name) is not None]

    latency = values("latency_ms")
    correction_attempts = sum(1 for r in records if r.get("retry_count", 0) > 0)
    safe_fallbacks = sum(1 for r in records if r.get("safe_fallback"))
    adversarial = [r["adversarial_success"] for r in records if r.get("adversarial_success") is not None]
    input_tokens = [r.get("token_usage", {}).get("input_tokens") for r in records if r.get("token_usage", {}).get("input_tokens") is not None]
    output_tokens = [r.get("token_usage", {}).get("output_tokens") for r in records if r.get("token_usage", {}).get("output_tokens") is not None]
    total_tokens = [r.get("token_usage", {}).get("total_tokens") for r in records if r.get("token_usage", {}).get("total_tokens") is not None]
    return {
        "count": len(records),
        "fact_coverage_mean": _mean(values("required_fact_score")),
        "faithfulness_mean": _mean(values("faithfulness_score")),
        "project_entity_mean": _mean(values("project_entity_score")),
        "multi_hop_mean": _mean(values("multi_hop_score")),
        "comparative_mean": _mean(values("comparative_score")),
        "adversarial_refusal_rate": _mean([1.0 if v else 0.0 for v in adversarial]),
        "latency_ms_mean": _mean(latency),
        "latency_ms_std": pstdev(latency) if len(latency) > 1 else 0.0,
        "tool_calls_mean": _mean(values("tool_calls")),
        "model_calls_mean": _mean(values("model_calls")),
        "retry_count_mean": _mean(values("retry_count")),
        "correction_rate": correction_attempts / len(records) if records else 0.0,
        "safe_fallback_rate": safe_fallbacks / len(records) if records else 0.0,
        "input_tokens_mean": _mean(input_tokens),
        "output_tokens_mean": _mean(output_tokens),
        "total_tokens_mean": _mean(total_tokens),
        "input_tokens_total": sum(input_tokens) if input_tokens else 0,
        "output_tokens_total": sum(output_tokens) if output_tokens else 0,
        "total_tokens_total": sum(total_tokens) if total_tokens else 0,
    }


def _aggregate_assertions(records: list[dict[str, Any]]) -> dict[str, Any]:
    per_type: dict[str, dict[str, int]] = defaultdict(lambda: {"run": 0, "passed": 0, "failed": 0})
    retry_causes: dict[str, int] = defaultdict(int)
    total_run = total_passed = total_failed = 0
    for record in records:
        assertion_results = []
        for event in record.get("validation_events", []):
            assertion_results.extend(event.get("validation", {}).get("results", []))
        if not assertion_results:
            assertion_results = record.get("assertions", {}).get("results", [])
        for assertion in assertion_results:
            if assertion.get("skipped"):
                continue
            name = assertion["assertion"]
            per_type[name]["run"] += 1
            total_run += 1
            if assertion["passed"]:
                per_type[name]["passed"] += 1
                total_passed += 1
            else:
                per_type[name]["failed"] += 1
                total_failed += 1
        for name in record.get("retry_failed_assertions", []):
            retry_causes[name] += 1
    return {
        "total_run": total_run,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "pass_rate": total_passed / total_run if total_run else None,
        "by_type": {
            name: {
                **counts,
                "pass_rate": counts["passed"] / counts["run"] if counts["run"] else None,
                "failure_rate": counts["failed"] / counts["run"] if counts["run"] else None,
            }
            for name, counts in sorted(per_type.items())
        },
        "retry_causes": dict(sorted(retry_causes.items())),
    }


def _mean(values: list[float]) -> float | None:
    return mean(values) if values else None
