# Evaluation Report

## Executive Summary

Dataset: `interview_prep_v1`. Mode: `live`. Configurations: agent_no_assertions, agent_with_assertions, pipeline.

This report is generated from the machine-readable result files in this run directory.

## Dataset

Questions evaluated: 2. Runs per configuration: 1.

## Overall Results

| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 2 | 1.000 | 0.000 | 1.000 | n/a | 16502.705 | 3 | 4 | 0.000 |
| agent_with_assertions | 2 | 0.000 | 0.000 | 0.000 | n/a | 24570.070 | 4.500 | 5 | 1.000 |
| pipeline | 2 | 1.000 | 0.500 | 1.000 | n/a | 663.280 | 0 | 1 | 0.000 |

## Category Results

{
  "single_hop": {
    "count": 6,
    "fact_coverage_mean": 0.6666666666666666,
    "faithfulness_mean": 0.16666666666666666,
    "project_entity_mean": 0.6666666666666666,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 13912.018333333333,
    "latency_ms_std": 13118.03802426442,
    "tool_calls_mean": 2.5,
    "model_calls_mean": 3.3333333333333335,
    "retry_count_mean": 0.3333333333333333,
    "correction_rate": 0.3333333333333333,
    "safe_fallback_rate": 0.3333333333333333
  }
}

## Assertion Results

{
  "total_run": 16,
  "total_passed": 10,
  "total_failed": 6,
  "pass_rate": 0.625,
  "by_type": {
    "metrics_grounded": {
      "run": 2,
      "passed": 0,
      "failed": 2,
      "pass_rate": 0.0,
      "failure_rate": 1.0
    },
    "no_fabricated_dates": {
      "run": 2,
      "passed": 2,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "project_exists": {
      "run": 4,
      "passed": 4,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "scope_bounded": {
      "run": 4,
      "passed": 4,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "tech_stack_grounded": {
      "run": 4,
      "passed": 0,
      "failed": 4,
      "pass_rate": 0.0,
      "failure_rate": 1.0
    }
  },
  "retry_causes": {
    "metrics_grounded": 1,
    "tech_stack_grounded": 2
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
