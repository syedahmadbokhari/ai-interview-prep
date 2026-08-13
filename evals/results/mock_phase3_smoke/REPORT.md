# Evaluation Report

## Executive Summary

Dataset: `interview_prep_v1`. Mode: `mock`. Configurations: agent_no_assertions, agent_with_assertions, pipeline.

This report is generated from the machine-readable result files in this run directory.

## Dataset

Questions evaluated: 43. Runs per configuration: 1.

## Overall Results

| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 43 | 0.744 | 0.767 | 0.581 | 0.000 | 55.142 | 1.419 | 2 | 0.000 |
| agent_with_assertions | 43 | 0.581 | 0.581 | 0.488 | 1.000 | 74.125 | 1.419 | 2.651 | 0.651 |
| pipeline | 43 | 0.744 | 0.767 | 0.581 | 0.000 | 0.007 | 0 | 0 | 0.000 |

## Category Results

{
  "adversarial": {
    "count": 30,
    "fact_coverage_mean": 0.3333333333333333,
    "faithfulness_mean": 0.3333333333333333,
    "project_entity_mean": 0.3333333333333333,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": 0.3333333333333333,
    "latency_ms_mean": 35.48,
    "latency_ms_std": 28.171974844988533,
    "tool_calls_mean": 0.6666666666666666,
    "model_calls_mean": 1.6666666666666667,
    "retry_count_mean": 0.3333333333333333,
    "correction_rate": 0.3333333333333333,
    "safe_fallback_rate": 0.0
  },
  "comparative": {
    "count": 27,
    "fact_coverage_mean": 0.7777777777777778,
    "faithfulness_mean": 0.7777777777777778,
    "project_entity_mean": 0.7777777777777778,
    "multi_hop_mean": null,
    "comparative_mean": 0.7777777777777778,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 54.217777777777776,
    "latency_ms_std": 50.01164015124163,
    "tool_calls_mean": 1.2592592592592593,
    "model_calls_mean": 1.5555555555555556,
    "retry_count_mean": 0.2222222222222222,
    "correction_rate": 0.2222222222222222,
    "safe_fallback_rate": 0.2222222222222222
  },
  "multi_hop": {
    "count": 36,
    "fact_coverage_mean": 0.7222222222222222,
    "faithfulness_mean": 0.7777777777777778,
    "project_entity_mean": 0.7777777777777778,
    "multi_hop_mean": 0.7222222222222222,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 47.048611111111114,
    "latency_ms_std": 38.72011852547127,
    "tool_calls_mean": 1.2222222222222223,
    "model_calls_mean": 1.5555555555555556,
    "retry_count_mean": 0.2222222222222222,
    "correction_rate": 0.2222222222222222,
    "safe_fallback_rate": 0.2222222222222222
  },
  "single_hop": {
    "count": 36,
    "fact_coverage_mean": 0.8888888888888888,
    "faithfulness_mean": 0.8888888888888888,
    "project_entity_mean": 0.3333333333333333,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 37.13194444444444,
    "latency_ms_std": 30.157007000349616,
    "tool_calls_mean": 0.6666666666666666,
    "model_calls_mean": 1.4444444444444444,
    "retry_count_mean": 0.1111111111111111,
    "correction_rate": 0.1111111111111111,
    "safe_fallback_rate": 0.1111111111111111
  }
}

## Assertion Results

{
  "total_run": 152,
  "total_passed": 79,
  "total_failed": 73,
  "pass_rate": 0.5197368421052632,
  "by_type": {
    "metrics_grounded": {
      "run": 26,
      "passed": 2,
      "failed": 24,
      "pass_rate": 0.07692307692307693,
      "failure_rate": 0.9230769230769231
    },
    "no_fabricated_dates": {
      "run": 3,
      "passed": 2,
      "failed": 1,
      "pass_rate": 0.6666666666666666,
      "failure_rate": 0.3333333333333333
    },
    "project_exists": {
      "run": 52,
      "passed": 44,
      "failed": 8,
      "pass_rate": 0.8461538461538461,
      "failure_rate": 0.15384615384615385
    },
    "scope_bounded": {
      "run": 40,
      "passed": 26,
      "failed": 14,
      "pass_rate": 0.65,
      "failure_rate": 0.35
    },
    "tech_stack_grounded": {
      "run": 31,
      "passed": 5,
      "failed": 26,
      "pass_rate": 0.16129032258064516,
      "failure_rate": 0.8387096774193549
    }
  },
  "retry_causes": {
    "metrics_grounded": 17,
    "no_fabricated_dates": 1,
    "project_exists": 5,
    "scope_bounded": 12,
    "tech_stack_grounded": 18
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
