# Phase 5 Assertion Ablation Study

**MOCK INFRASTRUCTURE VALIDATION ONLY. LIVE ABLATION STUDY NOT YET EXECUTED. Do not treat these results as live model evidence.**

## Scope

This run compares the retrieval pipeline, ReAct agent without assertions, ReAct agent with all assertions, and leave-one-out assertion ablations using the existing evaluation runner and `disabled_assertions` control.

## Primary Metrics

| Configuration | Count | Fact Coverage | Faithfulness | Adversarial Refusal | Safe Fallback | Latency ms |
|---|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 43 | 0.744 | 0.767 | 0.000 | 0.000 | 31.567 |
| agent_with_assertions | 43 | 0.581 | 0.581 | 1.000 | 0.419 | 52.821 |
| agent_without_dates_grounded | 43 | 0.581 | 0.581 | 1.000 | 0.419 | 64.831 |
| agent_without_metrics_grounded | 43 | 0.721 | 0.721 | 1.000 | 0.279 | 65.484 |
| agent_without_project_exists | 43 | 0.640 | 0.651 | 1.000 | 0.349 | 65.340 |
| agent_without_scope_bounded | 43 | 0.581 | 0.581 | 1.000 | 0.419 | 64.143 |
| agent_without_technology_grounded | 43 | 0.744 | 0.744 | 1.000 | 0.256 | 62.604 |
| pipeline | 43 | 0.744 | 0.767 | 0.000 | 0.000 | 0.000 |

## Marginal Deltas

Deltas are leave-one-out minus `agent_with_assertions`.

{
  "agent_without_dates_grounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": 0.0,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": 12.009534883720939
  },
  "agent_without_metrics_grounded": {
    "fact_coverage_mean": 0.13953488372093015,
    "faithfulness_mean": 0.13953488372093015,
    "adversarial_refusal_rate": 0.0,
    "safe_fallback_rate": -0.13953488372093026,
    "correction_rate": -0.13953488372093026,
    "latency_ms_mean": 12.662558139534887
  },
  "agent_without_project_exists": {
    "fact_coverage_mean": 0.05813953488372092,
    "faithfulness_mean": 0.06976744186046513,
    "adversarial_refusal_rate": 0.0,
    "safe_fallback_rate": -0.06976744186046513,
    "correction_rate": -0.06976744186046513,
    "latency_ms_mean": 12.518837209302326
  },
  "agent_without_scope_bounded": {
    "fact_coverage_mean": 0.0,
    "faithfulness_mean": 0.0,
    "adversarial_refusal_rate": 0.0,
    "safe_fallback_rate": 0.0,
    "correction_rate": 0.0,
    "latency_ms_mean": 11.32209302325581
  },
  "agent_without_technology_grounded": {
    "fact_coverage_mean": 0.16279069767441856,
    "faithfulness_mean": 0.16279069767441856,
    "adversarial_refusal_rate": 0.0,
    "safe_fallback_rate": -0.16279069767441862,
    "correction_rate": -0.16279069767441867,
    "latency_ms_mean": 9.783023255813958
  }
}

## Failure Analysis

{
  "comparative_reasoning_gap": 30,
  "correction_failure": 92,
  "date_assertion_failure": 5,
  "failed_refusal": 20,
  "incomplete_required_facts": 117,
  "metrics_assertion_failure": 85,
  "multi_hop_reasoning_gap": 46,
  "project_assertion_failure": 25,
  "scope_assertion_failure": 60,
  "technology_assertion_failure": 90,
  "ungrounded_answer": 112,
  "unnecessary_refusal_candidate": 92,
  "unsupported_claim_leaked": 20
}

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
