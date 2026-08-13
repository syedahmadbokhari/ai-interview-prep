"""Failure taxonomy and review sampling for Phase 5 experiments."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from evals.experiments.analysis import quality_score


def build_failure_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    taxonomy = Counter()
    representative = defaultdict(list)
    for record in records:
        labels = classify_failure(record)
        for label in labels:
            taxonomy[label] += 1
            if len(representative[label]) < 5:
                representative[label].append(_example(record, label))
        if labels:
            failures.append({"question_id": record["question_id"], "configuration": record["configuration"], "run": record["run"], "labels": labels})
    return {
        "taxonomy_counts": dict(sorted(taxonomy.items())),
        "representative_examples": dict(sorted(representative.items())),
        "false_positives": false_positives(records),
        "false_negatives": false_negatives(records),
        "correction_failures": [
            _example(record, "correction_failure")
            for record in records
            if record.get("retry_count", 0) > 0 and record.get("safe_fallback")
        ][:20],
        "review_sample": human_review_sample(records),
        "failures": failures,
    }


def classify_failure(record: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    failed_assertions = set(record.get("retry_failed_assertions") or [])
    if record.get("adversarial_success") is False:
        labels.append("failed_refusal")
    if record.get("forbidden_claims_found"):
        labels.append("unsupported_claim_leaked")
    if record.get("required_fact_score", 1.0) < 1.0:
        labels.append("incomplete_required_facts")
    if record.get("faithfulness_score", 1.0) < 1.0:
        labels.append("ungrounded_answer")
    if record.get("safe_fallback") and record.get("category") != "adversarial":
        labels.append("unnecessary_refusal_candidate")
    if record.get("retry_count", 0) > 0 and record.get("safe_fallback"):
        labels.append("correction_failure")
    if "project_exists" in failed_assertions:
        labels.append("project_assertion_failure")
    if "tech_stack_grounded" in failed_assertions:
        labels.append("technology_assertion_failure")
    if "metrics_grounded" in failed_assertions:
        labels.append("metrics_assertion_failure")
    if "no_fabricated_dates" in failed_assertions:
        labels.append("date_assertion_failure")
    if "scope_bounded" in failed_assertions:
        labels.append("scope_assertion_failure")
    if record.get("category") == "multi_hop" and record.get("multi_hop_score", 1.0) < 1.0:
        labels.append("multi_hop_reasoning_gap")
    if record.get("category") == "comparative" and record.get("comparative_score", 1.0) < 1.0:
        labels.append("comparative_reasoning_gap")
    return labels


def false_positives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = _group_by_question_run(records)
    cases = []
    for group in grouped.values():
        no_assertions = group.get("agent_no_assertions")
        with_assertions = group.get("agent_with_assertions")
        if not no_assertions or not with_assertions:
            continue
        if quality_score(no_assertions) >= 1.0 and quality_score(with_assertions) < 1.0:
            cases.append(
                {
                    "question_id": with_assertions["question_id"],
                    "category": with_assertions["category"],
                    "suspected_assertions": with_assertions.get("retry_failed_assertions", []),
                    "reason": "No-assertion answer scored fully while assertion-gated answer regressed.",
                }
            )
    return cases[:50]


def false_negatives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for record in records:
        if not record["configuration"].startswith("agent_"):
            continue
        assertions = record.get("assertions", {})
        all_passed = assertions.get("all_passed")
        leaked = bool(record.get("forbidden_claims_found"))
        unfaithful = record.get("faithfulness_score", 1.0) < 1.0
        if all_passed and (leaked or unfaithful):
            cases.append(
                {
                    "question_id": record["question_id"],
                    "configuration": record["configuration"],
                    "category": record["category"],
                    "reason": "Assertions passed while deterministic scoring still found unsupported output.",
                    "forbidden_claims_found": record.get("forbidden_claims_found", []),
                }
            )
    return cases[:50]


def human_review_sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = sorted(
        records,
        key=lambda record: (
            0 if classify_failure(record) else 1,
            -record.get("retry_count", 0),
            record["question_id"],
        ),
    )
    return [
        {
            "question_id": record["question_id"],
            "configuration": record["configuration"],
            "run": record["run"],
            "category": record["category"],
            "labels": classify_failure(record),
            "question": record["question"],
            "answer": record["answer"],
        }
        for record in priority[:30]
    ]


def _group_by_question_run(records: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, dict[str, Any]]]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        grouped[(record["question_id"], record["run"])][record["configuration"]] = record
    return grouped


def _example(record: dict[str, Any], label: str) -> dict[str, Any]:
    return {
        "label": label,
        "question_id": record["question_id"],
        "configuration": record["configuration"],
        "run": record["run"],
        "category": record["category"],
        "retry_failed_assertions": record.get("retry_failed_assertions", []),
        "safe_fallback": record.get("safe_fallback"),
        "scores": {
            "required_fact_score": record.get("required_fact_score"),
            "faithfulness_score": record.get("faithfulness_score"),
            "adversarial_success": record.get("adversarial_success"),
        },
    }
