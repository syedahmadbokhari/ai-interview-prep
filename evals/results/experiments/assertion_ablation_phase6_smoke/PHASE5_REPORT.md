# Phase 5 Assertion Ablation Study

**MOCK INFRASTRUCTURE VALIDATION ONLY. LIVE ABLATION STUDY NOT YET EXECUTED. Do not treat these results as live model evidence.**

## Scope

This run compares the retrieval pipeline, ReAct agent without assertions, ReAct agent with all assertions, and leave-one-out assertion ablations using the existing evaluation runner and `disabled_assertions` control.

## Primary Metrics

| Configuration | Count | Fact Coverage | Faithfulness | Adversarial Refusal | Safe Fallback | Latency ms |
|---|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 2 | 1.000 | 1.000 | n/a | 0.000 | 22.400 |
| agent_with_assertions | 2 | 1.000 | 1.000 | n/a | 0.000 | 26.380 |
| agent_without_dates_grounded | 2 | 1.000 | 1.000 | n/a | 0.000 | 28.115 |
| agent_without_metrics_grounded | 2 | 1.000 | 1.000 | n/a | 0.000 | 25.070 |
| agent_without_project_exists | 2 | 1.000 | 1.000 | n/a | 0.000 | 28.850 |
| agent_without_scope_bounded | 2 | 1.000 | 1.000 | n/a | 0.000 | 23.045 |
| agent_without_technology_grounded | 2 | 1.000 | 1.000 | n/a | 0.000 | 35.060 |
| pipeline | 2 | 1.000 | 1.000 | n/a | 0.000 | 0.000 |

## Marginal Deltas

Deltas are leave-one-out minus `agent_with_assertions`.

{
  "agent_without_dates_grounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": null,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": 1.7349999999999994
  },
  "agent_without_metrics_grounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": null,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": -1.3100000000000023
  },
  "agent_without_project_exists": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": null,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": 2.469999999999999
  },
  "agent_without_scope_bounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": null,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": -3.335000000000001
  },
  "agent_without_technology_grounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": null,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": 8.68
  }
}

## Failure Analysis

{}

## API Freeze Recommendation

- `EvidenceItem`: PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: keep stable; core citation contract is used across assertions.
- `AssertionResult`: PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: keep stable; add fields only with defaults.
- `ValidationResult`: PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: keep stable for gating and experiment serialization.
- `AssertionRunner(disabled_assertions=...)`: PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: keep; it is the ablation control point.
- `Individual assertion names`: PROVISIONAL - LIVE ABLATION STUDY NOT YET EXECUTED: avoid renames; aliases can expand without breaking results.

## Artifacts

- `manifest.json`, `results.json`, `results.csv`, `summary.json`, `failures.jsonl`
- `comparisons.json`, `failure_analysis.json`, `FAILURE_ANALYSIS.md`
- `human_review_phase5.csv`, `tables/`, `charts/`
