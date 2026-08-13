from __future__ import annotations

import json
from pathlib import Path

from assertions import AssertionRunner, EvidenceItem
from evals.metrics import aggregate_results
from evals.reporting import write_outputs
from evals.schemas import EvalItem, load_dataset, validate_dataset
from evals.scoring import score_answer


DATASET = Path("evals/datasets/interview_prep_v1.jsonl")
PROJECTS = ["uk-crime-data-pipeline", "uk-retail-data-platform"]


def test_dataset_schema_validation_passes_for_v1():
    items = load_dataset(DATASET)
    errors = validate_dataset(items, PROJECTS)
    assert errors == []
    assert 40 <= len(items) <= 50


def test_dataset_has_required_category_distribution():
    items = load_dataset(DATASET)
    counts = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1
    assert counts == {
        "adversarial": 10,
        "comparative": 9,
        "multi_hop": 12,
        "single_hop": 12,
    }


def test_dataset_duplicate_detection():
    item = load_dataset(DATASET)[0]
    errors = validate_dataset([item, item], PROJECTS)
    assert any("duplicate id" in error for error in errors)
    assert any("duplicate question" in error for error in errors)


def test_dataset_category_validation():
    data = load_dataset(DATASET)[0].to_dict()
    data["category"] = "bad"
    errors = validate_dataset([EvalItem.from_dict(data)], PROJECTS)
    assert any("invalid category" in error for error in errors)


def test_dataset_rejects_unsupported_project():
    data = load_dataset(DATASET)[0].to_dict()
    data["expected_projects"] = ["missing-project"]
    errors = validate_dataset([EvalItem.from_dict(data)], PROJECTS)
    assert any("unsupported project" in error for error in errors)


def test_scoring_required_fact_coverage():
    item = load_dataset(DATASET)[0]
    score = score_answer(item, "The UK Crime Data Pipeline uses DuckDB as its warehouse.")
    assert score.required_fact_score == 1.0
    miss = score_answer(item, "The project uses Snowflake.")
    assert miss.required_fact_score == 0.0


def test_scoring_adversarial_refusal():
    item = next(i for i in load_dataset(DATASET) if i.id == "adv_001")
    good = score_answer(item, "The indexed documentation does not contain that project.")
    bad = score_answer(item, "The Java Fraud Detection project used XGBoost.")
    assert good.adversarial_success is True
    assert bad.adversarial_success is False


def test_scoring_adversarial_negated_forbidden_claim_is_not_leak():
    item = next(i for i in load_dataset(DATASET) if i.id == "adv_008")
    answer = (
        "The Retail Data Platform does not deploy a production Kubernetes cluster. "
        "The documentation does not contain enough information to support that premise."
    )

    score = score_answer(item, answer)

    assert score.forbidden_claims_found == []
    assert score.adversarial_success is True


def test_aggregation_computes_configuration_metrics():
    records = [
        {
            "configuration": "pipeline",
            "category": "single_hop",
            "required_fact_score": 1.0,
            "faithfulness_score": 1.0,
            "project_entity_score": 1.0,
            "multi_hop_score": None,
            "comparative_score": None,
            "adversarial_success": None,
            "latency_ms": 10.0,
            "tool_calls": 0,
            "model_calls": 1,
            "retry_count": 0,
            "safe_fallback": False,
            "assertions": {},
        },
        {
            "configuration": "pipeline",
            "category": "adversarial",
            "required_fact_score": 0.0,
            "faithfulness_score": 0.0,
            "project_entity_score": 0.0,
            "multi_hop_score": None,
            "comparative_score": None,
            "adversarial_success": False,
            "latency_ms": 20.0,
            "tool_calls": 0,
            "model_calls": 1,
            "retry_count": 0,
            "safe_fallback": False,
            "assertions": {},
        },
    ]
    summary = aggregate_results(records)
    assert summary["by_configuration"]["pipeline"]["count"] == 2
    assert summary["by_configuration"]["pipeline"]["fact_coverage_mean"] == 0.5


def test_assertion_metric_aggregation():
    records = [
        {
            "configuration": "agent_with_assertions",
            "category": "single_hop",
            "required_fact_score": 1.0,
            "faithfulness_score": 1.0,
            "project_entity_score": 1.0,
            "multi_hop_score": None,
            "comparative_score": None,
            "adversarial_success": None,
            "latency_ms": 1,
            "tool_calls": 1,
            "model_calls": 2,
            "retry_count": 0,
            "safe_fallback": False,
            "assertions": {
                "results": [
                    {"assertion": "metrics_grounded", "passed": True, "skipped": False},
                    {"assertion": "scope_bounded", "passed": False, "skipped": False},
                ]
            },
        }
    ]
    summary = aggregate_results(records)
    assert summary["assertions"]["total_run"] == 2
    assert summary["assertions"]["by_type"]["scope_bounded"]["failed"] == 1


def test_assertions_can_be_disabled_for_ablation():
    runner = AssertionRunner(disabled_assertions={"scope"})
    validation = runner.validate(
        answer="The pipeline deployed a Kubernetes cluster.",
        retrieved_context=[EvidenceItem("c", "uk-crime-data-pipeline", "DuckDB warehouse")],
        project_registry=PROJECTS,
    )
    scope = next(result for result in validation.results if result.assertion == "scope_bounded")
    assert scope.skipped is True
    assert scope.passed is True


def test_configuration_switching_concepts():
    assert "pipeline" != "agent_no_assertions"
    assert "agent_no_assertions" != "agent_with_assertions"


def test_result_serialization_and_failure_extraction(tmp_path):
    records = [
        {
            "question_id": "q1",
            "category": "adversarial",
            "configuration": "pipeline",
            "run": 1,
            "required_fact_score": 0.0,
            "faithfulness_score": 0.0,
            "project_entity_score": 0.0,
            "multi_hop_score": None,
            "comparative_score": None,
            "adversarial_success": False,
            "tool_calls": 0,
            "model_calls": 1,
            "retry_count": 0,
            "latency_ms": 1.0,
            "safe_fallback": False,
            "assertions": {},
        }
    ]
    summary = {
        "metadata": {
            "dataset_version": "test",
            "mode": "mock",
            "configurations": ["pipeline"],
            "dataset_size": 1,
            "runs": 1,
        },
        "aggregates": aggregate_results(records),
    }
    write_outputs(tmp_path, records, summary)
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "results.csv").exists()
    failures = (tmp_path / "failures.jsonl").read_text(encoding="utf-8").strip()
    assert json.loads(failures)["question_id"] == "q1"
