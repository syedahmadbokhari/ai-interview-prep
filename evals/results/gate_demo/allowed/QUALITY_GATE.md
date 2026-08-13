# Quality Gate

Policy: `pr_gate`
Overall outcome: **PASS**

| Check | Status | Current | Baseline | Delta | Allowed | Reason |
|---|---|---:|---:|---:|---:|---|
| `dataset_size` | PASS | 43 | 43 | None | None | Expected dataset size 43. |
| `configuration_present.pipeline` | PASS | ['agent_no_assertions', 'agent_with_assertions', 'pipeline'] | None | None | None | Required configuration must be present. |
| `configuration_present.agent_no_assertions` | PASS | ['agent_no_assertions', 'agent_with_assertions', 'pipeline'] | None | None | None | Required configuration must be present. |
| `configuration_present.agent_with_assertions` | PASS | ['agent_no_assertions', 'agent_with_assertions', 'pipeline'] | None | None | None | Required configuration must be present. |
| `non_empty_evaluation` | PASS | None | None | None | None | Configuration aggregates exist. |
| `compatibility.dataset_version` | PASS | interview_prep_v1 | interview_prep_v1 | None | None | Current run must be compatible with approved baseline. |
| `compatibility.scoring_version` | PASS | 1 | 1 | None | None | Current run must be compatible with approved baseline. |
| `minimum.agent_with_assertions.adversarial_refusal_rate` | PASS | 1.0 | 1.0 | None | None | Metric must be >= 1.0. |
| `regression.pipeline.fact_coverage_mean` | PASS | 0.743686046511628 | 0.7441860465116279 | -0.0004999999999999449 | 0.001 | Metric must not regress by more than 0.001. |
| `regression.agent_no_assertions.fact_coverage_mean` | PASS | 0.7441860465116279 | 0.7441860465116279 | 0.0 | 0.001 | Metric must not regress by more than 0.001. |
| `regression.agent_with_assertions.adversarial_refusal_rate` | PASS | 1.0 | 1.0 | 0.0 | 0.001 | Metric must not regress by more than 0.001. |
| `regression.agent_with_assertions.faithfulness_mean` | PASS | 0.5813953488372093 | 0.5813953488372093 | 0.0 | 0.05 | Metric must not regress by more than 0.05. |
| `cross_config.agent_with_assertions.adversarial_refusal_rate.>=.agent_no_assertions.adversarial_refusal_rate` | PASS | 1.0 | 0.0 | None | 0.0 | Expected agent_with_assertions.adversarial_refusal_rate >= agent_no_assertions.adversarial_refusal_rate with tolerance 0.0. |
