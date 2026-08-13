import json
from pathlib import Path

from evals.experiments.ablation import main as ablation_main
from evals.experiments.analysis import (
    ABLATION_CONFIGS,
    assertion_filter_to_config,
    build_comparisons,
    experiment_configurations,
    operational_cost,
    paired_comparisons,
)
from evals.experiments.failure_analysis import (
    build_failure_analysis,
    classify_failure,
    false_negatives,
    false_positives,
)
from evals.experiments.statistics import percentile, summarize_numbers


def _record(
    question_id="q1",
    configuration="agent_with_assertions",
    category="single_hop",
    required_fact_score=1.0,
    faithfulness_score=1.0,
    adversarial_success=None,
    safe_fallback=False,
    retry_count=0,
    retry_failed_assertions=None,
    assertions=None,
):
    return {
        "question_id": question_id,
        "category": category,
        "configuration": configuration,
        "run": 1,
        "question": "Question?",
        "answer": "Answer.",
        "required_fact_score": required_fact_score,
        "faithfulness_score": faithfulness_score,
        "project_entity_score": 1.0,
        "multi_hop_score": None,
        "comparative_score": None,
        "adversarial_success": adversarial_success,
        "forbidden_claims_found": [],
        "tool_calls": 1,
        "retrieval_operations": 1,
        "model_calls": 2,
        "retry_count": retry_count,
        "latency_ms": 10.0,
        "token_usage": {},
        "assertions": assertions or {"all_passed": True, "results": []},
        "validation_events": [],
        "retry_failed_assertions": retry_failed_assertions or [],
        "safe_fallback": safe_fallback,
        "trace_path": None,
        "mode": "mock",
    }


def test_phase5_configurations_include_all_leave_one_out_runs():
    configs = experiment_configurations()

    assert set(configs) == {
        "pipeline",
        "agent_no_assertions",
        "agent_with_assertions",
        *set(ABLATION_CONFIGS),
    }
    assert configs["agent_without_technology_grounded"]["disabled_assertions"] == [
        "tech_stack_grounded"
    ]


def test_assertion_filter_accepts_aliases():
    assert assertion_filter_to_config("technology") == "agent_without_technology_grounded"
    assert assertion_filter_to_config("metrics_grounded") == "agent_without_metrics_grounded"


def test_assertion_filter_reduces_ablation_set_to_one():
    configs = experiment_configurations("scope")

    assert "agent_without_scope_bounded" in configs
    assert "agent_without_metrics_grounded" not in configs
    assert "agent_with_assertions" in configs


def test_percentile_and_number_summary_are_dependency_free():
    assert percentile([1, 2, 3, 4, 5], 95) == 4.8
    assert summarize_numbers([3, 1, 2]) == {"mean": 2, "median": 2, "p95": 2.9}


def test_paired_comparisons_detect_assertion_improvement():
    records = [
        _record(configuration="agent_no_assertions", required_fact_score=0.0),
        _record(configuration="agent_with_assertions", required_fact_score=1.0),
    ]

    comparison = next(
        item
        for item in paired_comparisons(records)
        if item["left"] == "agent_no_assertions"
        and item["right"] == "agent_with_assertions"
    )

    assert comparison["right_wins"] == 1
    assert comparison["mean_right_minus_left"]["required_fact_score"] == 1.0


def test_build_comparisons_includes_required_phase5_sections():
    records = [
        _record(configuration="agent_with_assertions"),
        _record(configuration="agent_without_metrics_grounded", retry_failed_assertions=[]),
    ]

    comparisons = build_comparisons(records)

    assert "marginal_deltas" in comparisons
    assert "assertion_category_matrix" in comparisons
    assert "api_freeze_recommendations" in comparisons


def test_failure_taxonomy_labels_retry_safe_fallback():
    record = _record(
        required_fact_score=0.0,
        faithfulness_score=0.0,
        safe_fallback=True,
        retry_count=1,
        retry_failed_assertions=["metrics_grounded"],
    )

    labels = classify_failure(record)

    assert "correction_failure" in labels
    assert "metrics_assertion_failure" in labels
    assert "unnecessary_refusal_candidate" in labels


def test_false_positive_candidates_compare_no_assertions_to_assertions():
    records = [
        _record(configuration="agent_no_assertions"),
        _record(
            configuration="agent_with_assertions",
            required_fact_score=0.0,
            safe_fallback=True,
            retry_failed_assertions=["scope_bounded"],
        ),
    ]

    cases = false_positives(records)

    assert cases[0]["suspected_assertions"] == ["scope_bounded"]


def test_false_negative_candidates_require_passed_assertions_and_bad_score():
    records = [
        _record(
            configuration="agent_with_assertions",
            faithfulness_score=0.0,
            assertions={"all_passed": True, "results": []},
        )
    ]

    assert false_negatives(records)


def test_failure_analysis_builds_review_sample():
    records = [
        _record(configuration="agent_with_assertions"),
        _record(
            configuration="agent_with_assertions",
            question_id="q2",
            safe_fallback=True,
            retry_count=1,
        ),
    ]

    analysis = build_failure_analysis(records)

    assert "taxonomy_counts" in analysis
    assert analysis["review_sample"][0]["question_id"] == "q2"


def test_operational_cost_includes_latency_percentiles():
    costs = operational_cost(
        [
            _record(configuration="pipeline", question_id="q1"),
            _record(configuration="pipeline", question_id="q2"),
        ]
    )

    assert costs["pipeline"]["latency_ms"]["p95"] == 10.0
    assert costs["pipeline"]["model_calls_mean"] == 2.0


def test_ablation_cli_mock_smoke_writes_phase5_artifacts(tmp_path: Path):
    run_dir = tmp_path / "phase5"

    exit_code = ablation_main(
        [
            "--mode",
            "mock",
            "--runs",
            "1",
            "--limit",
            "1",
            "--output-dir",
            str(run_dir),
        ]
    )

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert manifest["mode"] == "mock"
    assert (run_dir / "comparisons.json").exists()
    assert (run_dir / "failure_analysis.json").exists()
    assert (run_dir / "PHASE5_REPORT.md").exists()
    assert (run_dir / "tables" / "operational_cost.csv").exists()
    assert (run_dir / "charts" / "faithfulness_by_configuration.svg").exists()
