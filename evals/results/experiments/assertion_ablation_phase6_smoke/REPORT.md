# Evaluation Report

## Executive Summary

Dataset: `interview_prep_v1`. Mode: `mock`. Configurations: pipeline, agent_no_assertions, agent_with_assertions, agent_without_project_exists, agent_without_technology_grounded, agent_without_metrics_grounded, agent_without_dates_grounded, agent_without_scope_bounded.

This report is generated from the machine-readable result files in this run directory.

## Dataset

Questions evaluated: 2. Runs per configuration: 1.

## Overall Results

| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 2 | 1.000 | 1.000 | 0.500 | n/a | 22.400 | 1 | 2 | 0.000 |
| agent_with_assertions | 2 | 1.000 | 1.000 | 0.500 | n/a | 26.380 | 1 | 2 | 0.000 |
| agent_without_dates_grounded | 2 | 1.000 | 1.000 | 0.500 | n/a | 28.115 | 1 | 2 | 0.000 |
| agent_without_metrics_grounded | 2 | 1.000 | 1.000 | 0.500 | n/a | 25.070 | 1 | 2 | 0.000 |
| agent_without_project_exists | 2 | 1.000 | 1.000 | 0.500 | n/a | 28.850 | 1 | 2 | 0.000 |
| agent_without_scope_bounded | 2 | 1.000 | 1.000 | 0.500 | n/a | 23.045 | 1 | 2 | 0.000 |
| agent_without_technology_grounded | 2 | 1.000 | 1.000 | 0.500 | n/a | 35.060 | 1 | 2 | 0.000 |
| pipeline | 2 | 1.000 | 1.000 | 0.500 | n/a | 0.000 | 0 | 0 | 0.000 |

## Category Results

{
  "single_hop": {
    "count": 16,
    "fact_coverage_mean": 1.0,
    "faithfulness_mean": 1.0,
    "project_entity_mean": 0.5,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 23.615000000000002,
    "latency_ms_std": 11.793751523582308,
    "tool_calls_mean": 0.875,
    "model_calls_mean": 1.75,
    "retry_count_mean": 0,
    "correction_rate": 0.0,
    "safe_fallback_rate": 0.0
  }
}

## Assertion Results

{
  "total_run": 15,
  "total_passed": 15,
  "total_failed": 0,
  "pass_rate": 1.0,
  "by_type": {
    "project_exists": {
      "run": 5,
      "passed": 5,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "scope_bounded": {
      "run": 5,
      "passed": 5,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "tech_stack_grounded": {
      "run": 5,
      "passed": 5,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    }
  },
  "retry_causes": {}
}

## Failure Analysis

See `failures.jsonl` for low-coverage, hallucination, failed-refusal, correction-failure, and safe-fallback cases. See `comparative_failures.json` for pipeline-vs-agent and assertion-helped/hurt cases.

## Human Review

`human_review_template.csv` is generated for optional 0-2 human scoring of correctness, completeness, relevance, and clarity.

## Limitations

- Mocked runs prove infrastructure and scoring, not live model quality.
- Deterministic scoring uses keyword/fact checks and should be supplemented with human review.
- No statistical significance is claimed from a single benchmark run.
