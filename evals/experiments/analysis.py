"""Phase 5 comparative analysis for assertion ablation studies."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from evals.metrics import aggregate_results
from evals.experiments.statistics import summarize_numbers

BASE_CONFIGS = {
    "pipeline": {"runner_config": "pipeline", "disabled_assertions": []},
    "agent_no_assertions": {
        "runner_config": "agent_no_assertions",
        "disabled_assertions": [],
    },
    "agent_with_assertions": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": [],
    },
}

ABLATION_CONFIGS = {
    "agent_without_project_exists": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": ["project_exists"],
    },
    "agent_without_technology_grounded": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": ["tech_stack_grounded"],
    },
    "agent_without_metrics_grounded": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": ["metrics_grounded"],
    },
    "agent_without_dates_grounded": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": ["no_fabricated_dates"],
    },
    "agent_without_scope_bounded": {
        "runner_config": "agent_with_assertions",
        "disabled_assertions": ["scope_bounded"],
    },
}

ASSERTION_ALIASES = {
    "project": "project_exists",
    "project_exists": "project_exists",
    "technology": "tech_stack_grounded",
    "tech": "tech_stack_grounded",
    "tech_stack_grounded": "tech_stack_grounded",
    "metrics": "metrics_grounded",
    "metric": "metrics_grounded",
    "metrics_grounded": "metrics_grounded",
    "dates": "no_fabricated_dates",
    "date": "no_fabricated_dates",
    "no_fabricated_dates": "no_fabricated_dates",
    "scope": "scope_bounded",
    "scope_bounded": "scope_bounded",
}


def experiment_configurations(assertion_filter: str | None = None) -> dict[str, dict[str, Any]]:
    configs = dict(BASE_CONFIGS)
    if assertion_filter is None:
        configs.update(ABLATION_CONFIGS)
        return configs
    configs[assertion_filter_to_config(assertion_filter)] = ABLATION_CONFIGS[
        assertion_filter_to_config(assertion_filter)
    ]
    return configs


def assertion_filter_to_config(assertion_filter: str) -> str:
    canonical = ASSERTION_ALIASES.get(assertion_filter, assertion_filter)
    for config, spec in ABLATION_CONFIGS.items():
        if canonical in spec["disabled_assertions"]:
            return config
    raise ValueError(f"Unknown assertion filter: {assertion_filter}")


def build_comparisons(records: list[dict[str, Any]]) -> dict[str, Any]:
    aggregates = aggregate_results(records)
    return {
        "architecture_primary_metrics": aggregates["by_configuration"],
        "assertion_level_metrics": aggregates["assertions"],
        "marginal_deltas": marginal_deltas(aggregates["by_configuration"]),
        "paired_comparisons": paired_comparisons(records),
        "assertion_category_matrix": assertion_category_matrix(records),
        "correction_effectiveness": correction_effectiveness(records),
        "safety_usefulness_tradeoff": safety_usefulness_tradeoff(records),
        "operational_cost": operational_cost(records),
        "api_freeze_recommendations": api_freeze_recommendations(
            live_executed=any(record.get("mode") == "live" for record in records)
        ),
    }


def marginal_deltas(by_config: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    baseline = by_config.get("agent_with_assertions", {})
    metrics = [
        "fact_coverage_mean",
        "faithfulness_mean",
        "adversarial_refusal_rate",
        "safe_fallback_rate",
        "correction_rate",
        "latency_ms_mean",
    ]
    deltas: dict[str, dict[str, Any]] = {}
    for config in sorted(ABLATION_CONFIGS):
        values = by_config.get(config)
        if not values:
            continue
        deltas[config] = {}
        for metric in metrics:
            left = values.get(metric)
            right = baseline.get(metric)
            deltas[config][metric] = None if left is None or right is None else left - right
    return deltas


def paired_comparisons(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        grouped[(record["question_id"], record["run"])][record["configuration"]] = record

    pairs = [
        ("pipeline", "agent_no_assertions"),
        ("agent_no_assertions", "agent_with_assertions"),
        *[("agent_with_assertions", config) for config in sorted(ABLATION_CONFIGS)],
    ]
    comparisons = []
    for left_name, right_name in pairs:
        wins = losses = ties = count = 0
        metric_deltas = defaultdict(list)
        for group in grouped.values():
            if left_name not in group or right_name not in group:
                continue
            left = group[left_name]
            right = group[right_name]
            count += 1
            left_score = quality_score(left)
            right_score = quality_score(right)
            if left_score > right_score:
                wins += 1
            elif left_score < right_score:
                losses += 1
            else:
                ties += 1
            for metric in ("required_fact_score", "faithfulness_score", "latency_ms"):
                metric_deltas[metric].append((right.get(metric) or 0) - (left.get(metric) or 0))
        comparisons.append(
            {
                "left": left_name,
                "right": right_name,
                "count": count,
                "left_wins": wins,
                "right_wins": losses,
                "ties": ties,
                "mean_right_minus_left": {
                    metric: _mean(values) for metric, values in sorted(metric_deltas.items())
                },
            }
        )
    return comparisons


def assertion_category_matrix(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    matrix: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"run": 0, "failed": 0})
    )
    for record in records:
        for assertion in _assertion_results(record):
            if assertion.get("skipped"):
                continue
            cell = matrix[assertion["assertion"]][record["category"]]
            cell["run"] += 1
            if not assertion["passed"]:
                cell["failed"] += 1
    return {
        assertion: {
            category: {
                **counts,
                "failure_rate": counts["failed"] / counts["run"] if counts["run"] else None,
            }
            for category, counts in sorted(categories.items())
        }
        for assertion, categories in sorted(matrix.items())
    }


def correction_effectiveness(records: list[dict[str, Any]]) -> dict[str, Any]:
    attempts = [record for record in records if record.get("retry_count", 0) > 0]
    successful = [record for record in attempts if _ok(record)]
    by_assertion: dict[str, dict[str, int]] = defaultdict(lambda: {"attempts": 0, "successful": 0})
    for record in attempts:
        names = record.get("retry_failed_assertions") or ["unknown"]
        for name in names:
            by_assertion[name]["attempts"] += 1
            if _ok(record):
                by_assertion[name]["successful"] += 1
    return {
        "attempts": len(attempts),
        "successful": len(successful),
        "safe_fallback_after_retry": sum(1 for record in attempts if record.get("safe_fallback")),
        "success_rate": len(successful) / len(attempts) if attempts else None,
        "by_assertion": {
            name: {
                **counts,
                "success_rate": counts["successful"] / counts["attempts"]
                if counts["attempts"]
                else None,
            }
            for name, counts in sorted(by_assertion.items())
        },
    }


def safety_usefulness_tradeoff(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        grouped[(record["question_id"], record["run"])][record["configuration"]] = record
    helped = hurt = neutral = 0
    examples = []
    for group in grouped.values():
        without = group.get("agent_no_assertions")
        with_assertions = group.get("agent_with_assertions")
        if not without or not with_assertions:
            continue
        delta = quality_score(with_assertions) - quality_score(without)
        if delta > 0:
            helped += 1
        elif delta < 0:
            hurt += 1
            if len(examples) < 10:
                examples.append(
                    {
                        "question_id": with_assertions["question_id"],
                        "category": with_assertions["category"],
                        "delta": delta,
                        "safe_fallback": with_assertions.get("safe_fallback"),
                        "retry_failed_assertions": with_assertions.get(
                            "retry_failed_assertions", []
                        ),
                    }
                )
        else:
            neutral += 1
    total = helped + hurt + neutral
    return {
        "paired_items": total,
        "assertions_helped": helped,
        "assertions_hurt": hurt,
        "neutral": neutral,
        "help_rate": helped / total if total else None,
        "hurt_rate": hurt / total if total else None,
        "hurt_examples": examples,
    }


def operational_cost(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["configuration"]].append(record)
    output = {}
    for config, group in sorted(grouped.items()):
        latency = summarize_numbers([record.get("latency_ms") for record in group])
        output[config] = {
            "latency_ms": latency,
            "tool_calls_mean": _mean([record.get("tool_calls", 0) for record in group]),
            "model_calls_mean": _mean([record.get("model_calls", 0) for record in group]),
            "retry_rate": _mean([1.0 if record.get("retry_count", 0) else 0.0 for record in group]),
            "safe_fallback_rate": _mean([1.0 if record.get("safe_fallback") else 0.0 for record in group]),
        }
    return output


def api_freeze_recommendations(live_executed: bool) -> list[dict[str, str]]:
    prefix = "" if live_executed else "PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: "
    return [
        {
            "surface": "EvidenceItem",
            "recommendation": prefix + "keep stable; core citation contract is used across assertions.",
        },
        {
            "surface": "AssertionResult",
            "recommendation": prefix + "keep stable; add fields only with defaults.",
        },
        {
            "surface": "ValidationResult",
            "recommendation": prefix + "keep stable for gating and experiment serialization.",
        },
        {
            "surface": "AssertionRunner(disabled_assertions=...)",
            "recommendation": prefix + "keep; it is the ablation control point.",
        },
        {
            "surface": "Individual assertion names",
            "recommendation": prefix + "avoid renames; aliases can expand without breaking results.",
        },
    ]


def quality_score(record: dict[str, Any]) -> float:
    parts = [
        record.get("required_fact_score"),
        record.get("faithfulness_score"),
        record.get("project_entity_score"),
    ]
    if record.get("multi_hop_score") is not None:
        parts.append(record.get("multi_hop_score"))
    if record.get("comparative_score") is not None:
        parts.append(record.get("comparative_score"))
    if record.get("adversarial_success") is not None:
        parts.append(1.0 if record.get("adversarial_success") else 0.0)
    if record.get("safe_fallback") and record.get("adversarial_success") is not True:
        parts.append(0.0)
    numeric = [float(value) for value in parts if value is not None]
    return sum(numeric) / len(numeric) if numeric else 0.0


def _assertion_results(record: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for event in record.get("validation_events", []):
        results.extend(event.get("validation", {}).get("results", []))
    if not results:
        results = record.get("assertions", {}).get("results", [])
    return results


def _ok(record: dict[str, Any]) -> bool:
    return (
        record.get("required_fact_score", 0.0) >= 1.0
        and record.get("faithfulness_score", 0.0) >= 1.0
        and record.get("adversarial_success") is not False
        and not record.get("safe_fallback")
    )


def _mean(values: list[float]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return sum(clean) / len(clean) if clean else None
