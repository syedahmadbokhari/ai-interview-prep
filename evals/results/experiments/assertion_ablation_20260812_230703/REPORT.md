# Evaluation Report

## Executive Summary

Dataset: `interview_prep_v1`. Mode: `mock`. Configurations: pipeline, agent_no_assertions, agent_with_assertions, agent_without_project_exists, agent_without_technology_grounded, agent_without_metrics_grounded, agent_without_dates_grounded, agent_without_scope_bounded.

This report is generated from the machine-readable result files in this run directory.

## Dataset

Questions evaluated: 43. Runs per configuration: 1.

## Overall Results

| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 43 | 0.744 | 0.767 | 0.581 | 0.000 | 31.567 | 1.419 | 2 | 0.000 |
| agent_with_assertions | 43 | 0.581 | 0.581 | 0.488 | 1.000 | 52.821 | 1.419 | 2.651 | 0.651 |
| agent_without_dates_grounded | 43 | 0.581 | 0.581 | 0.488 | 1.000 | 64.831 | 1.419 | 2.651 | 0.651 |
| agent_without_metrics_grounded | 43 | 0.721 | 0.721 | 0.558 | 1.000 | 65.484 | 1.419 | 2.512 | 0.512 |
| agent_without_project_exists | 43 | 0.640 | 0.651 | 0.558 | 1.000 | 65.340 | 1.419 | 2.581 | 0.581 |
| agent_without_scope_bounded | 43 | 0.581 | 0.581 | 0.488 | 1.000 | 64.143 | 1.419 | 2.651 | 0.651 |
| agent_without_technology_grounded | 43 | 0.744 | 0.744 | 0.651 | 1.000 | 62.604 | 1.419 | 2.488 | 0.488 |
| pipeline | 43 | 0.744 | 0.767 | 0.581 | 0.000 | 0.000 | 0 | 0 | 0.000 |

## Category Results

{
  "adversarial": {
    "count": 80,
    "fact_coverage_mean": 0.75,
    "faithfulness_mean": 0.75,
    "project_entity_mean": 0.75,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": 0.75,
    "latency_ms_mean": 42.04975,
    "latency_ms_std": 18.87308513300091,
    "tool_calls_mean": 0.875,
    "model_calls_mean": 2.5,
    "retry_count_mean": 0.75,
    "correction_rate": 0.75,
    "safe_fallback_rate": 0.0
  },
  "comparative": {
    "count": 72,
    "fact_coverage_mean": 0.5833333333333334,
    "faithfulness_mean": 0.5833333333333334,
    "project_entity_mean": 0.5833333333333334,
    "multi_hop_mean": null,
    "comparative_mean": 0.5833333333333334,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 59.61763888888889,
    "latency_ms_std": 32.12502548607098,
    "tool_calls_mean": 1.6527777777777777,
    "model_calls_mean": 2.1666666666666665,
    "retry_count_mean": 0.4166666666666667,
    "correction_rate": 0.4166666666666667,
    "safe_fallback_rate": 0.4166666666666667
  },
  "multi_hop": {
    "count": 96,
    "fact_coverage_mean": 0.546875,
    "faithfulness_mean": 0.5729166666666666,
    "project_entity_mean": 0.5729166666666666,
    "multi_hop_mean": 0.546875,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 54.6059375,
    "latency_ms_std": 30.60489001566733,
    "tool_calls_mean": 1.6041666666666667,
    "model_calls_mean": 2.1770833333333335,
    "retry_count_mean": 0.4270833333333333,
    "correction_rate": 0.4270833333333333,
    "safe_fallback_rate": 0.4270833333333333
  },
  "single_hop": {
    "count": 96,
    "fact_coverage_mean": 0.78125,
    "faithfulness_mean": 0.78125,
    "project_entity_mean": 0.3333333333333333,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 47.84791666666667,
    "latency_ms_std": 24.373119923932368,
    "tool_calls_mean": 0.875,
    "model_calls_mean": 1.96875,
    "retry_count_mean": 0.21875,
    "correction_rate": 0.21875,
    "safe_fallback_rate": 0.21875
  }
}

## Assertion Results

{
  "total_run": 739,
  "total_passed": 374,
  "total_failed": 365,
  "pass_rate": 0.5060893098782138,
  "by_type": {
    "metrics_grounded": {
      "run": 130,
      "passed": 10,
      "failed": 120,
      "pass_rate": 0.07692307692307693,
      "failure_rate": 0.9230769230769231
    },
    "no_fabricated_dates": {
      "run": 14,
      "passed": 9,
      "failed": 5,
      "pass_rate": 0.6428571428571429,
      "failure_rate": 0.35714285714285715
    },
    "project_exists": {
      "run": 250,
      "passed": 210,
      "failed": 40,
      "pass_rate": 0.84,
      "failure_rate": 0.16
    },
    "scope_bounded": {
      "run": 191,
      "passed": 121,
      "failed": 70,
      "pass_rate": 0.6335078534031413,
      "failure_rate": 0.36649214659685864
    },
    "tech_stack_grounded": {
      "run": 154,
      "passed": 24,
      "failed": 130,
      "pass_rate": 0.15584415584415584,
      "failure_rate": 0.8441558441558441
    }
  },
  "retry_causes": {
    "metrics_grounded": 85,
    "no_fabricated_dates": 5,
    "project_exists": 25,
    "scope_bounded": 60,
    "tech_stack_grounded": 90
  }
}

## Failure Analysis

See `failures.jsonl` for low-coverage, hallucination, failed-refusal, correction-failure, and safe-fallback cases. See `comparative_failures.json` for pipeline-vs-agent and assertion-helped/hurt cases.

## Human Review

`human_review_template.csv` is generated for optional 0-2 human scoring of correctness, completeness, relevance, and clarity.

## Limitations

- Mocked runs prove infrastructure and scoring, not live model quality.
- Deterministic scoring uses keyword/fact checks and should be supplemented with human review.
- No statistical significance is claimed from a single benchmark run.
