# Evaluation Report

## Executive Summary

Dataset: `interview_prep_v1`. Mode: `live`. Configurations: agent_no_assertions, agent_with_assertions, pipeline.

This report is generated from the machine-readable result files in this run directory.

## Dataset

Questions evaluated: 10. Runs per configuration: 1.

## Overall Results

| Configuration | Count | Fact Coverage | Faithfulness | Project Accuracy | Adversarial Refusal | Latency ms | Tool Calls | Model Calls | Retry Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 10 | 0.650 | 0.800 | 0.800 | 0.500 | 20214.153 | 4.800 | 4 | 0.000 |
| agent_with_assertions | 10 | 0.300 | 0.700 | 0.300 | 1.000 | 17057.152 | 5 | 4.600 | 0.600 |
| pipeline | 10 | 0.600 | 0.700 | 0.750 | 1.000 | 288.859 | 0 | 0.800 | 0.000 |

## Category Results

{
  "adversarial": {
    "count": 6,
    "fact_coverage_mean": 0.8333333333333334,
    "faithfulness_mean": 0.8333333333333334,
    "project_entity_mean": 0.8333333333333334,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": 0.8333333333333334,
    "latency_ms_mean": 7149.3116666666665,
    "latency_ms_std": 6270.24135873683,
    "tool_calls_mean": 1.5,
    "model_calls_mean": 2.5,
    "retry_count_mean": 0.3333333333333333,
    "correction_rate": 0.3333333333333333,
    "safe_fallback_rate": 0.16666666666666666,
    "input_tokens_mean": 6075.2,
    "output_tokens_mean": 267.4,
    "total_tokens_mean": 6342.6,
    "input_tokens_total": 30376,
    "output_tokens_total": 1337,
    "total_tokens_total": 31713
  },
  "comparative": {
    "count": 6,
    "fact_coverage_mean": 0.16666666666666666,
    "faithfulness_mean": 0.6666666666666666,
    "project_entity_mean": 0.3333333333333333,
    "multi_hop_mean": null,
    "comparative_mean": 0.16666666666666666,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 16632.426666666666,
    "latency_ms_std": 15142.239733255741,
    "tool_calls_mean": 5.833333333333333,
    "model_calls_mean": 3.5,
    "retry_count_mean": 0,
    "correction_rate": 0.0,
    "safe_fallback_rate": 0.0,
    "input_tokens_mean": 15371.4,
    "output_tokens_mean": 966,
    "total_tokens_mean": 16337.4,
    "input_tokens_total": 76857,
    "output_tokens_total": 4830,
    "total_tokens_total": 81687
  },
  "multi_hop": {
    "count": 9,
    "fact_coverage_mean": 0.2777777777777778,
    "faithfulness_mean": 0.7777777777777778,
    "project_entity_mean": 0.5,
    "multi_hop_mean": 0.2777777777777778,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 18506.39,
    "latency_ms_std": 15994.400548551706,
    "tool_calls_mean": 4.666666666666667,
    "model_calls_mean": 3.888888888888889,
    "retry_count_mean": 0.2222222222222222,
    "correction_rate": 0.2222222222222222,
    "safe_fallback_rate": 0.1111111111111111,
    "input_tokens_mean": 11992.222222222223,
    "output_tokens_mean": 897.3333333333334,
    "total_tokens_mean": 12889.555555555555,
    "input_tokens_total": 107930,
    "output_tokens_total": 8076,
    "total_tokens_total": 116006
  },
  "single_hop": {
    "count": 9,
    "fact_coverage_mean": 0.7777777777777778,
    "faithfulness_mean": 0.6666666666666666,
    "project_entity_mean": 0.7777777777777778,
    "multi_hop_mean": null,
    "comparative_mean": null,
    "adversarial_refusal_rate": null,
    "latency_ms_mean": 7372.633333333333,
    "latency_ms_std": 5137.38399403821,
    "tool_calls_mean": 1.3333333333333333,
    "model_calls_mean": 2.5555555555555554,
    "retry_count_mean": 0.2222222222222222,
    "correction_rate": 0.2222222222222222,
    "safe_fallback_rate": 0.2222222222222222,
    "input_tokens_mean": 3564,
    "output_tokens_mean": 279.1111111111111,
    "total_tokens_mean": 3843.1111111111113,
    "input_tokens_total": 32076,
    "output_tokens_total": 2512,
    "total_tokens_total": 34588
  }
}

## Assertion Results

{
  "total_run": 35,
  "total_passed": 20,
  "total_failed": 15,
  "pass_rate": 0.5714285714285714,
  "by_type": {
    "metrics_grounded": {
      "run": 6,
      "passed": 2,
      "failed": 4,
      "pass_rate": 0.3333333333333333,
      "failure_rate": 0.6666666666666666
    },
    "project_exists": {
      "run": 12,
      "passed": 7,
      "failed": 5,
      "pass_rate": 0.5833333333333334,
      "failure_rate": 0.4166666666666667
    },
    "scope_bounded": {
      "run": 9,
      "passed": 9,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "tech_stack_grounded": {
      "run": 8,
      "passed": 2,
      "failed": 6,
      "pass_rate": 0.25,
      "failure_rate": 0.75
    }
  },
  "retry_causes": {
    "metrics_grounded": 3,
    "project_exists": 3,
    "tech_stack_grounded": 3
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
