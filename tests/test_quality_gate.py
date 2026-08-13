from __future__ import annotations

import copy
import json

from evals.baseline import approve_baseline, validate_baseline
from evals.quality_gate import evaluate_gate, main as gate_main


def summary(value: float = 1.0):
    return {
        "metadata": {
            "dataset_version": "interview_prep_v1",
            "scoring_version": "1",
            "model": "claude-sonnet-4-6",
            "dataset_size": 43,
            "configurations": [
                "pipeline",
                "agent_no_assertions",
                "agent_with_assertions",
            ],
        },
        "aggregates": {
            "by_configuration": {
                "pipeline": {
                    "fact_coverage_mean": value,
                    "faithfulness_mean": value,
                    "adversarial_refusal_rate": None,
                },
                "agent_no_assertions": {
                    "fact_coverage_mean": value,
                    "faithfulness_mean": value,
                    "adversarial_refusal_rate": 0.5,
                },
                "agent_with_assertions": {
                    "fact_coverage_mean": value,
                    "faithfulness_mean": value,
                    "adversarial_refusal_rate": value,
                },
            },
            "assertions": {"by_type": {}},
        },
    }


def policy():
    return {
        "name": "test",
        "hard_failures": {
            "expected_dataset_size": 43,
            "required_configurations": [
                "pipeline",
                "agent_no_assertions",
                "agent_with_assertions",
            ],
        },
        "compatibility": {"required_equal": ["dataset_version", "scoring_version"]},
        "regression_limits": [
            {"metric": "pipeline.fact_coverage_mean", "max_regression": 0.03}
        ],
        "absolute_minimums": [
            {"metric": "agent_with_assertions.adversarial_refusal_rate", "minimum": 0.85}
        ],
        "cross_config_rules": [
            {
                "left": "agent_with_assertions.adversarial_refusal_rate",
                "operator": ">=",
                "right": "agent_no_assertions.adversarial_refusal_rate",
                "tolerance": 0.0,
            }
        ],
    }


def test_gate_passing_case():
    result = evaluate_gate(summary(1.0), summary(1.0), policy())
    assert result.passed is True


def test_gate_allowed_regression_passes():
    current = summary(0.98)
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is True


def test_gate_excessive_regression_fails():
    current = summary(0.8)
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is False
    assert any(check.name == "regression.pipeline.fact_coverage_mean" for check in result.checks)


def test_gate_absolute_minimum_fails():
    current = summary(0.8)
    current["aggregates"]["by_configuration"]["pipeline"]["fact_coverage_mean"] = 1.0
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is False
    assert any(check.name.startswith("minimum.") for check in result.checks)


def test_gate_missing_metric_fails():
    current = summary(1.0)
    del current["aggregates"]["by_configuration"]["pipeline"]["fact_coverage_mean"]
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is False


def test_gate_invalid_metric_fails():
    current = summary(1.0)
    current["aggregates"]["by_configuration"]["pipeline"]["fact_coverage_mean"] = float("nan")
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is False


def test_gate_dataset_mismatch_fails():
    baseline = summary(1.0)
    baseline["metadata"]["dataset_version"] = "interview_prep_v2"
    result = evaluate_gate(summary(1.0), baseline, policy())
    assert result.passed is False
    assert any(check.name == "compatibility.dataset_version" for check in result.checks)


def test_gate_scoring_version_mismatch_fails():
    baseline = summary(1.0)
    baseline["metadata"]["scoring_version"] = "2"
    result = evaluate_gate(summary(1.0), baseline, policy())
    assert result.passed is False
    assert any(check.name == "compatibility.scoring_version" for check in result.checks)


def test_gate_empty_evaluation_fails():
    current = summary(1.0)
    current["aggregates"]["by_configuration"] = {}
    result = evaluate_gate(current, summary(1.0), policy())
    assert result.passed is False


def test_gate_cli_exit_codes(tmp_path):
    summary_path = tmp_path / "summary.json"
    baseline_path = tmp_path / "baseline.json"
    policy_path = tmp_path / "policy.json"
    summary_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    baseline_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    policy_path.write_text(json.dumps(policy()), encoding="utf-8")
    assert gate_main([
        "--summary", str(summary_path),
        "--baseline", str(baseline_path),
        "--policy", str(policy_path),
        "--output-dir", str(tmp_path),
    ]) == 0

    bad = summary(0.1)
    summary_path.write_text(json.dumps(bad), encoding="utf-8")
    assert gate_main([
        "--summary", str(summary_path),
        "--baseline", str(baseline_path),
        "--policy", str(policy_path),
        "--output-dir", str(tmp_path),
    ]) == 1


def test_baseline_creation_and_validation(tmp_path):
    result_path = tmp_path / "summary.json"
    result_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    baseline_path = approve_baseline(result_path, "test", tmp_path)
    assert validate_baseline(baseline_path) == []


def test_invalid_result_cannot_be_baseline(tmp_path):
    result_path = tmp_path / "summary.json"
    result_path.write_text(json.dumps({"metadata": {}, "aggregates": {}}), encoding="utf-8")
    try:
        approve_baseline(result_path, "bad", tmp_path)
    except ValueError as exc:
        assert "dataset_version" in str(exc)
    else:
        raise AssertionError("invalid summary should not become a baseline")


def test_baseline_not_overwritten_without_force(tmp_path):
    result_path = tmp_path / "summary.json"
    result_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    approve_baseline(result_path, "test", tmp_path)
    try:
        approve_baseline(result_path, "test", tmp_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("baseline overwrite should require force")


def test_baseline_force_replacement(tmp_path):
    result_path = tmp_path / "summary.json"
    result_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    first = approve_baseline(result_path, "test", tmp_path)
    second = approve_baseline(result_path, "test", tmp_path, force=True)
    assert first == second


def test_baseline_provenance_retained(tmp_path):
    result_path = tmp_path / "summary.json"
    result_path.write_text(json.dumps(summary(1.0)), encoding="utf-8")
    baseline_path = approve_baseline(result_path, "test", tmp_path)
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert data["approved"] is True
    assert data["source_result"] == str(result_path)
    assert data["metadata"]["dataset_version"] == "interview_prep_v1"
